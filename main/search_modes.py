"""Four ways to search diagnostic_knowledge, so the UI can compare them side by side.

  vector   Atlas Vector Search + Automated Embedding (semantic, meaning-based)
  lexical  Atlas Search (keyword / fuzzy, full-text)
  hybrid   vector + lexical fused with Reciprocal Rank Fusion
           (server-side $rankFusion on MongoDB 8.0+, otherwise fused in Python)
  rerank   hybrid, then Voyage AI native $rerank (needs MongoDB 8.3+ and
           "Native Reranking" enabled in the Atlas project settings)

Every function returns a list of dicts with the same fields as gemini_agent.KNOWLEDGE_FIELDS
plus "score". Nothing here raises: use compare() to get per-mode results, timing and errors.
"""
import time

VECTOR_INDEX = "simdoctor_knowledge_vector_index"
TEXT_INDEX = "simdoctor_knowledge_text"
COLLECTION = "diagnostic_knowledge"
RRF_K = 60  # standard Reciprocal Rank Fusion constant

FIELDS = {"_id": 0, "title": 1, "fault_code": 1, "severity": 1,
          "symptoms": 1, "possible_causes": 1, "recommended_checks": 1}

TEXT_PATHS = ["title", "keywords", "symptoms", "search_text"]


# ---------------------------------------------------------------- pipeline pieces
def _vector_stage(query, limit):
    # Same string-query form your working gemini_agent.py uses.
    # Newer docs also accept  "query": {"text": query}  - switch if the string form is rejected.
    return {"$vectorSearch": {"index": VECTOR_INDEX, "path": "search_text", "query": query,
                              "numCandidates": max(50, limit * 10), "limit": limit}}


def _search_stage(query):
    return {"$search": {"index": TEXT_INDEX,
                        "text": {"query": query, "path": TEXT_PATHS,
                                 "fuzzy": {"maxEdits": 1, "prefixLength": 2}}}}


def vector_pipeline(query, limit=5):
    return [_vector_stage(query, limit),
            {"$project": {**FIELDS, "score": {"$meta": "vectorSearchScore"}}}]


def lexical_pipeline(query, limit=5):
    return [_search_stage(query), {"$limit": limit},
            {"$project": {**FIELDS, "score": {"$meta": "searchScore"}}}]


def hybrid_pipeline(query, limit=5, w_vector=1.0, w_text=1.0):
    """Server-side Reciprocal Rank Fusion (MongoDB 8.0+)."""
    return [
        {"$rankFusion": {
            "input": {"pipelines": {
                "vector": [_vector_stage(query, 20)],
                "text": [_search_stage(query), {"$limit": 20}],
            }},
            "combination": {"weights": {"vector": w_vector, "text": w_text}},
            "scoreDetails": True,
        }},
        {"$limit": limit},
        {"$project": {**FIELDS, "score": {"$meta": "score"}}},
    ]


def rerank_pipeline(query, limit=5, model="rerank-2.5"):
    """Hybrid candidates, then Voyage AI reranking inside the database."""
    return [
        {"$rankFusion": {
            "input": {"pipelines": {
                "vector": [_vector_stage(query, 20)],
                "text": [_search_stage(query), {"$limit": 20}],
            }},
        }},
        {"$limit": 10},
        {"$rerank": {"query": {"text": query}, "path": "search_text",
                     "numDocsToRerank": 10, "model": model}},
        {"$limit": limit},
        {"$project": FIELDS},
    ]


# ---------------------------------------------------------------- helpers
def _run(db, pipeline, retries=2):
    for attempt in range(retries + 1):
        try:
            return list(db[COLLECTION].aggregate(pipeline))
        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            raise


def rrf_merge(*ranked_lists, limit=5, k=RRF_K):
    """Client-side Reciprocal Rank Fusion. Fallback when $rankFusion is unavailable."""
    scores, docs = {}, {}
    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            key = doc.get("fault_code") or doc.get("title")
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            docs.setdefault(key, doc)
    merged = []
    for key in sorted(scores, key=scores.get, reverse=True)[:limit]:
        merged.append({**docs[key], "score": round(scores[key], 5)})
    return merged


# ---------------------------------------------------------------- public API
def vector_search(db, query, limit=5):
    return _run(db, vector_pipeline(query, limit))


def lexical_search(db, query, limit=5):
    return _run(db, lexical_pipeline(query, limit))


def hybrid_search(db, query, limit=5):
    """Returns (docs, method). Tries $rankFusion first, falls back to Python RRF."""
    try:
        return _run(db, hybrid_pipeline(query, limit)), "hybrid ($rankFusion)"
    except Exception:
        vec = vector_search(db, query, 20)
        lex = lexical_search(db, query, 20)
        return rrf_merge(vec, lex, limit=limit), "hybrid (RRF in app)"


def rerank_search(db, query, limit=5):
    """Returns (docs, method). Falls back to hybrid if native reranking is unavailable."""
    try:
        return _run(db, rerank_pipeline(query, limit)), "hybrid + Voyage rerank ($rerank)"
    except Exception:
        docs, method = hybrid_search(db, query, limit)
        return docs, method + " (rerank unavailable)"


def compare(db, query, limit=3):
    """Run every mode. Returns {mode: {"docs": [...], "ms": int, "method": str, "error": str|None}}."""
    out = {}
    runners = {
        "vector": lambda: (vector_search(db, query, limit), "Atlas Vector Search"),
        "lexical": lambda: (lexical_search(db, query, limit), "Atlas Search"),
        "hybrid": lambda: hybrid_search(db, query, limit),
    }
    for mode, run in runners.items():
        start = time.perf_counter()
        try:
            docs, method = run()
            error = None
        except Exception as e:  # index missing / still building / network
            docs, method, error = [], mode, f"{type(e).__name__}: {str(e)[:120]}"
        out[mode] = {"docs": docs, "method": method, "error": error,
                     "ms": int((time.perf_counter() - start) * 1000)}
    return out


if __name__ == "__main__":  # quick manual test:  python search_modes.py "steam from the bonnet"
    import os
    import sys
    from pathlib import Path

    from dotenv import load_dotenv
    from pymongo import MongoClient

    load_dotenv(Path(__file__).resolve().parent / ".env")
    q = " ".join(sys.argv[1:]) or "steam coming from under my bonnet"
    client = MongoClient(os.getenv("MONGODB_URI"), serverSelectionTimeoutMS=10000)
    for mode, r in compare(client["simdoctor"], q).items():
        print(f"\n== {mode}  [{r['method']}]  {r['ms']} ms  {r['error'] or ''}")
        for d in r["docs"]:
            print(f"   {d.get('score')!s:>10}  {d.get('title')}")

