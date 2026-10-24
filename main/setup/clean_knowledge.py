import json, re
from pathlib import Path

path = Path(__file__).parent / "knowledge_data.json"
text = re.sub(r"\s*\n\s*", " ", path.read_text(encoding="utf-8"))   # removes line breaks inside strings
text = re.sub(r"\]\s*\[", ",", text)                                # joins the two arrays into one
data = json.loads(text)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(len(data), "entries,", len({d["topic"] for d in data}), "unique topics,",
      len({d["fault_code"] for d in data}), "unique fault codes")
