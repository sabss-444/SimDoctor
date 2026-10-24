"""
app.py - SimDoctor dashboard (Streamlit).

Run with:  streamlit run app.py

Reads vehicles / sensor_readings from MongoDB Atlas (database "simdoctor"),
uses fault_detector.detect_faults for detection, and saves reports to
"diagnostic_reports". If Atlas can't be reached it falls back to a built-in
demo mode so the UI always works for the demo.
"""

import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

from fault_detector import detect_faults, save_fault

load_dotenv(Path(__file__).parent / ".env")

st.set_page_config(page_title="SimDoctor", page_icon="🚗", layout="wide")

# ──────────────────────────────────────────────────────────────
# Styling
# ──────────────────────────────────────────────────────────────
TEAL = "#14b8a6"
RED = "#ef4444"
GREEN = "#22c55e"
AMBER = "#f59e0b"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }
.stApp {
  background: radial-gradient(1200px 600px at 80% -10%, #0f3d3e 0%, #0b1416 45%, #080b0c 100%);
  color: #e5e7eb;
}
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: #0d0f10; border-right: 1px solid #1f2527; min-width: 250px;
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
.brand { font-size: 1.5rem; font-weight: 800; letter-spacing: .12em; color: #fff; }
.brand span { color: %(teal)s; }
.brand-sub { font-size: .65rem; letter-spacing: .3em; color: #6b7280; margin-bottom: 1.4rem; }

section[data-testid="stSidebar"] div[role="radiogroup"] { gap: .35rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  background: transparent; border-radius: 12px; padding: .65rem .9rem;
  transition: all .15s; cursor: pointer; width: 100%%;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: #1a2022; }
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child { display: none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label p {
  font-weight: 600; letter-spacing: .08em; font-size: .85rem; color: #9ca3af;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: %(teal)s;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p { color: #fff; }

/* Top bar */
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  background: linear-gradient(135deg, #10201f, #0d1213); border: 1px solid #1f2d2c;
  border-radius: 18px; padding: 1rem 1.5rem; margin-bottom: 1rem;
}
.topbar h1 { margin: 0; font-size: 1.35rem; letter-spacing: .2em; font-weight: 800; color: #fff; }
.topbar p { margin: 0; font-size: .7rem; letter-spacing: .35em; color: %(teal)s; }
.pill {
  display: inline-flex; align-items: center; gap: .5rem; padding: .4rem .9rem;
  border-radius: 999px; font-size: .72rem; font-weight: 700; letter-spacing: .12em;
  border: 1px solid #1f3a37; background: #0b1514; color: #d1fae5;
}
.dot { width: 9px; height: 9px; border-radius: 50%%; display: inline-block; }
.dot.on { background: %(green)s; box-shadow: 0 0 10px %(green)s; animation: pulse 1.6s infinite; }
.dot.off { background: %(amber)s; box-shadow: 0 0 10px %(amber)s; }
@keyframes pulse { 50%% { opacity: .35; } }

/* Cards */
.card {
  background: linear-gradient(160deg, #161a1c, #101314); border: 1px solid #222a2c;
  border-radius: 20px; padding: 1.2rem 1.4rem; height: 100%%;
}
.card-title { font-size: .7rem; letter-spacing: .22em; color: #6b7280; font-weight: 700; margin-bottom: .5rem; }
.vehicle-card {
  text-align: center; background:
    radial-gradient(500px 220px at 50%% 40%%, rgba(20,184,166,.18), transparent 70%%),
    linear-gradient(160deg, #161a1c, #0f1213);
}
.plate {
  display: inline-block; background: #facc15; color: #111; font-weight: 800;
  letter-spacing: .12em; padding: .2rem .8rem; border-radius: 6px; font-size: .95rem;
}
.vehicle-name { margin-top: .5rem; font-weight: 700; letter-spacing: .15em; color: #e5e7eb; }
.vehicle-meta { color: #6b7280; font-size: .75rem; letter-spacing: .1em; margin-top: .15rem; }

.metric { text-align: left; }
.metric .label { font-size: .7rem; letter-spacing: .2em; color: #6b7280; font-weight: 700; }
.metric .value { font-size: 2.4rem; font-weight: 800; line-height: 1.15; margin-top: .3rem; }
.metric .unit { font-size: 1rem; color: #9ca3af; font-weight: 600; margin-left: .15rem; }
.metric .hint { font-size: .72rem; color: #6b7280; margin-top: .2rem; }
.metric.bad { border-color: #5b1f1f; box-shadow: 0 0 28px rgba(239,68,68,.12); }
.metric.good { border-color: #1d4a33; }
.c-red { color: %(red)s; } .c-green { color: %(green)s; } .c-amber { color: %(amber)s; } .c-teal { color: %(teal)s; }

.mini { display: flex; gap: 1rem; }
.mini .box { flex: 1; background: #0f1213; border: 1px solid #1f2527; border-radius: 14px; padding: .7rem 1rem; }
.mini .box .l { font-size: .65rem; letter-spacing: .18em; color: #6b7280; font-weight: 700; }
.mini .box .v { font-size: 1.25rem; font-weight: 700; color: #e5e7eb; }

/* AI investigation */
.alert {
  display: flex; align-items: center; gap: .7rem; background: rgba(239,68,68,.1);
  border: 1px solid #5b1f1f; color: #fecaca; border-radius: 14px;
  padding: .8rem 1rem; font-weight: 700; letter-spacing: .08em; font-size: .9rem; margin-bottom: 1rem;
}
.alert.ok { background: rgba(34,197,94,.08); border-color: #1d4a33; color: #bbf7d0; }
.cause-list { list-style: none; padding: 0; margin: .3rem 0 0 0; }
.cause-list li {
  padding: .55rem .9rem; margin-bottom: .45rem; background: #0f1213; border: 1px solid #1f2527;
  border-left: 3px solid %(teal)s; border-radius: 10px; font-size: .92rem;
}
.sub { font-size: .72rem; letter-spacing: .2em; color: #6b7280; font-weight: 700; margin: 1rem 0 .4rem; }
.note { font-size: .75rem; color: #6b7280; margin-top: .8rem; line-height: 1.5; }

/* Pipeline */
.pipeline { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; margin-top: 1rem; }
.step {
  padding: .5rem 1rem; border-radius: 999px; font-size: .75rem; font-weight: 700;
  letter-spacing: .1em; border: 1px solid #263032; color: #6b7280; background: #0f1213;
}
.step.done { color: #ccfbf1; border-color: %(teal)s; background: rgba(20,184,166,.14); }
.arrow { color: #374151; }

/* Buttons */
.stButton > button {
  background: #12181a; color: #e5e7eb; border: 1px solid #263032; border-radius: 12px;
  font-weight: 600; letter-spacing: .04em; padding: .55rem 1rem; width: 100%%; transition: all .15s;
}
.stButton > button:hover { border-color: %(teal)s; color: #fff; box-shadow: 0 0 16px rgba(20,184,166,.25); }
.stButton > button[kind="primary"] { background: %(teal)s; border-color: %(teal)s; color: #04201d; }

div[data-baseweb="select"] > div { background: #12181a; border-color: #263032; border-radius: 12px; }
[data-testid="stDataFrame"] { border-radius: 14px; overflow: hidden; }
h2, h3 { color: #fff; letter-spacing: .06em; }
</style>
""" % {"teal": TEAL, "red": RED, "green": GREEN, "amber": AMBER}

st.markdown(CSS, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# Demo data + illustrative knowledge (replace with Atlas knowledge retrieval)
# ──────────────────────────────────────────────────────────────
DEMO_VEHICLES = [
    {"registration_number": "AB18 CDE", "make": "Ford", "model": "Fiesta", "year": 2018, "mileage": 65000},
    {"registration_number": "XY18 FGH", "make": "Ford", "model": "Fiesta", "year": 2018, "mileage": 72000},
]

# Illustrative, UNVERIFIED knowledge. Swap for results from the diagnostic_knowledge collection.
KNOWLEDGE = {
    "ENGINE_OVERHEAT": {
        "title": "HIGH TEMPERATURE DETECTED",
        "causes": ["Cooling system issue", "Low coolant", "Thermostat issue", "Faulty temperature sensor"],
        "checks": ["Check coolant level when the engine is cold", "Inspect hoses and radiator for leaks",
                   "Confirm thermostat opens at operating temperature", "Cross-check the reading with a second sensor"],
        "urgency": "High - avoid driving until assessed",
    },
    "LOW_BATTERY_VOLTAGE": {
        "title": "LOW VOLTAGE DETECTED",
        "causes": ["Weak or ageing battery", "Alternator not charging", "Loose or corroded terminals"],
        "checks": ["Measure battery voltage at rest and while running", "Inspect terminals and earth connections",
                   "Test alternator output"],
        "urgency": "Medium - further assessment needed",
    },
    "LOW_OIL_PRESSURE": {
        "title": "LOW OIL PRESSURE DETECTED",
        "causes": ["Low oil level", "Worn oil pump", "Blocked oil filter", "Faulty pressure sensor"],
        "checks": ["Check oil level and condition", "Inspect for leaks",
                   "Verify with a mechanical pressure gauge"],
        "urgency": "High - stop driving if the warning persists",
    },
}

SCENARIOS = {
    "normal": "✅ Normal",
    "overheat": "🌡️ Overheat",
    "low_voltage": "🔋 Low voltage",
    "low_oil": "🛢️ Low oil",
}

CAR_SVG = """
<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" style="width:100%%;max-width:520px">
  <defs>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#e2e8f0"/><stop offset="1" stop-color="#64748b"/>
    </linearGradient>
    <filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <ellipse cx="300" cy="172" rx="250" ry="14" fill="#000" opacity=".45"/>
  <ellipse cx="300" cy="172" rx="230" ry="9" fill="none" stroke="%(c)s" stroke-width="1.5" opacity=".6" filter="url(#glow)"/>
  <path d="M60 140 Q64 112 118 102 L190 64 Q220 46 270 46 L370 46 Q420 48 452 82 L520 100
           Q560 108 560 138 L560 148 Q560 156 548 156 L74 156 Q60 156 60 146 Z"
        fill="url(#body)" stroke="%(c)s" stroke-width="2" filter="url(#glow)"/>
  <path d="M208 78 L240 56 L300 56 L300 100 L196 100 Z" fill="#0b1c1e" opacity=".9"/>
  <path d="M312 56 L372 56 Q402 60 424 98 L312 100 Z" fill="#0b1c1e" opacity=".9"/>
  <line x1="100" y1="120" x2="540" y2="120" stroke="%(c)s" stroke-width="2" opacity=".7" filter="url(#glow)"/>
  <circle cx="160" cy="152" r="32" fill="#0b0d0e" stroke="#94a3b8" stroke-width="4"/>
  <circle cx="160" cy="152" r="14" fill="#1f2937" stroke="%(c)s" stroke-width="2"/>
  <circle cx="456" cy="152" r="32" fill="#0b0d0e" stroke="#94a3b8" stroke-width="4"/>
  <circle cx="456" cy="152" r="14" fill="#1f2937" stroke="%(c)s" stroke-width="2"/>
</svg>
"""


# ──────────────────────────────────────────────────────────────
# Data layer (Atlas with demo fallback)
# ──────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_db():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        return client["simdoctor"]
    except Exception:
        return None


DB = get_db()

st.session_state.setdefault("demo_readings", {})
st.session_state.setdefault("demo_reports", [])
st.session_state.setdefault("investigated", {})


def load_vehicles():
    if DB is not None:
        found = list(DB["vehicles"].find().sort("registration_number", 1))
        if found:
            return found
    return DEMO_VEHICLES


def load_readings(reg, limit=30):
    """Newest first."""
    if DB is not None:
        return list(DB["sensor_readings"].find({"registration_number": reg})
                    .sort("timestamp", -1).limit(limit))
    return list(reversed(st.session_state["demo_readings"].get(reg, [])))[:limit]


def make_series(vehicle, scenario, n=10):
    now = datetime.now(timezone.utc)
    rows = []
    for i in range(n):
        r = {
            "registration_number": vehicle["registration_number"],
            "timestamp": now - timedelta(seconds=n - 1 - i),
            "time_seconds": i,
            "temperature": round(random.uniform(85, 98), 2),
            "voltage": round(random.uniform(12.6, 14.2), 2),
            "speed": round(random.uniform(20, 90), 2),
            "rpm": random.randint(1200, 4000),
            "oil_pressure": round(random.uniform(2.0, 4.5), 2),
        }
        if vehicle.get("_id") is not None:
            r["vehicle_id"] = vehicle["_id"]
        if scenario == "overheat":
            r["temperature"] = round(92 + i * 3.6, 2)
        elif scenario == "low_voltage":
            r["voltage"] = round(13.6 - i * 0.4, 2)
        elif scenario == "low_oil":
            r["oil_pressure"] = round(3.5 - i * 0.33, 2)
        rows.append(r)
    return rows


def run_scenario(vehicle, scenario):
    rows = make_series(vehicle, scenario)
    if DB is not None:
        result = DB["sensor_readings"].insert_many(rows)
        for row, _id in zip(rows, result.inserted_ids):
            row["_id"] = _id
            for fault in detect_faults(row):
                save_fault(DB["faults"], row, fault)
    else:
        st.session_state["demo_readings"].setdefault(vehicle["registration_number"], []).extend(rows)
    st.session_state["investigated"].pop(vehicle["registration_number"], None)


def save_report(report):
    if DB is not None:
        DB["diagnostic_reports"].insert_one(dict(report))
    else:
        st.session_state["demo_reports"].append(dict(report))


def load_reports(reg=None):
    query = {"registration_number": reg} if reg else {}
    if DB is not None:
        return list(DB["diagnostic_reports"].find(query).sort("created_at", -1).limit(50))
    reports = st.session_state["demo_reports"]
    return [r for r in reversed(reports) if not reg or r["registration_number"] == reg]


def build_report(vehicle, reading, faults):
    primary = faults[0]
    know = KNOWLEDGE.get(primary["code"], {})
    return {
        "registration_number": vehicle["registration_number"],
        "created_at": datetime.now(timezone.utc),
        "fault_detected": True,
        "fault_code": primary["code"],
        "sensor": primary["field"],
        "observed_value": primary["value"],
        "threshold": primary["threshold"],
        "possible_causes": know.get("causes", []),
        "evidence": (f"{primary['field']} = {primary['value']} {primary['unit']} "
                     f"crossed the configured test threshold of {primary['threshold']} {primary['unit']}."),
        "urgency": know.get("urgency", "Requires further assessment"),
        "recommendations": know.get("checks", []),
        "note": "Hypotheses only - not a confirmed diagnosis.",
    }


# ──────────────────────────────────────────────────────────────
# UI helpers
# ──────────────────────────────────────────────────────────────
def topbar():
    online = DB is not None
    dot = "on" if online else "off"
    label = "AI SYSTEM ONLINE" if online else "DEMO MODE · ATLAS OFFLINE"
    st.markdown(
        f'<div class="topbar"><div><h1>SIMDOCTOR</h1><p>VEHICLE INTELLIGENCE</p></div>'
        f'<div class="pill"><span class="dot {dot}"></span>{label}</div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, unit, state, hint=""):
    cls = {"bad": "bad", "good": "good"}.get(state, "")
    colour = {"bad": "c-red", "good": "c-green", "warn": "c-amber"}.get(state, "")
    icon = {"bad": "🔴", "good": "🟢", "warn": "🟡"}.get(state, "")
    return (f'<div class="card metric {cls}"><div class="label">{label}</div>'
            f'<div class="value {colour}">{value}<span class="unit">{unit}</span> {icon}</div>'
            f'<div class="hint">{hint}</div></div>')


def pipeline(active):
    steps = ["Evidence", "Knowledge", "AI reasoning", "Report"]
    parts = []
    for i, s in enumerate(steps):
        parts.append(f'<span class="step {"done" if i < active else ""}">{s}</span>')
        if i < len(steps) - 1:
            parts.append('<span class="arrow">→</span>')
    return f'<div class="pipeline">{"".join(parts)}</div>'


def vehicle_label(v):
    return f'{v["registration_number"]} - {v["year"]} {v["make"]} {v["model"]}'


# ──────────────────────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────────────────────
def page_dashboard(vehicles):
    topbar()

    sel_col, _ = st.columns([2, 3])
    with sel_col:
        choice = st.selectbox("Vehicle", [vehicle_label(v) for v in vehicles],
                              label_visibility="collapsed")
    vehicle = next(v for v in vehicles if vehicle_label(v) == choice)
    reg = vehicle["registration_number"]

    readings = load_readings(reg)
    latest = readings[0] if readings else None
    faults = detect_faults(latest) if latest else []

    # Vehicle view + controls
    left, right = st.columns([3, 2])
    with left:
        st.markdown(
            f'<div class="card vehicle-card"><div class="card-title">VEHICLE VIEW</div>'
            f'{CAR_SVG % {"c": TEAL}}'
            f'<div class="plate">{reg}</div>'
            f'<div class="vehicle-name">{vehicle["make"].upper()} {vehicle["model"].upper()}</div>'
            f'<div class="vehicle-meta">{vehicle["year"]} · {vehicle.get("mileage", 0):,} MILES</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown('<div class="card"><div class="card-title">SIMULATE SCENARIO</div>',
                    unsafe_allow_html=True)
        for key, label in SCENARIOS.items():
            if st.button(label, key=f"sc_{key}"):
                run_scenario(vehicle, key)
                st.rerun()
        st.markdown('<div class="note">Generates 10 readings and runs the fault detector '
                    'on each. Thresholds are for simulation only.</div></div>',
                    unsafe_allow_html=True)

    st.write("")

    # Metrics
    if latest:
        temp, volt = latest.get("temperature"), latest.get("voltage")
        temp_bad = any(f["field"] == "temperature" for f in faults)
        volt_bad = any(f["field"] == "voltage" for f in faults)
        c1, c2, c3 = st.columns(3)
        c1.markdown(metric_card("TEMP", f"{temp:.0f}", "°C", "bad" if temp_bad else "good",
                                "Limit 105 °C (test)"), unsafe_allow_html=True)
        c2.markdown(metric_card("VOLTAGE", f"{volt:.1f}", "V", "bad" if volt_bad else "good",
                                "Limit 12.0 V (test)"), unsafe_allow_html=True)
        status = "FAULT DETECTED" if faults else "ALL NORMAL"
        c3.markdown(
            f'<div class="card metric {"bad" if faults else "good"}"><div class="label">STATUS</div>'
            f'<div class="value {"c-red" if faults else "c-green"}" style="font-size:1.6rem;padding-top:.55rem">'
            f'{status} {"🔴" if faults else "🟢"}</div>'
            f'<div class="hint">{len(faults)} issue(s) in latest reading</div></div>',
            unsafe_allow_html=True,
        )
        st.write("")
        oil, speed, rpm = latest.get("oil_pressure"), latest.get("speed"), latest.get("rpm")
        oil_txt = f"{oil:.1f} bar" if isinstance(oil, (int, float)) else "-"
        st.markdown(
            f'<div class="mini"><div class="box"><div class="l">OIL PRESSURE</div><div class="v">{oil_txt}</div></div>'
            f'<div class="box"><div class="l">SPEED</div><div class="v">{speed:.0f} km/h</div></div>'
            f'<div class="box"><div class="l">RPM</div><div class="v">{rpm}</div></div></div>',
            unsafe_allow_html=True,
        )
        st.write("")

        # Trend
        df = pd.DataFrame(list(reversed(readings)))
        if "timestamp" in df:
            st.markdown('<div class="card"><div class="card-title">TEMPERATURE TREND</div>',
                        unsafe_allow_html=True)
            st.line_chart(df.set_index("timestamp")[["temperature"]], height=180, color=TEAL)
            st.markdown("</div>", unsafe_allow_html=True)
            st.write("")
    else:
        st.info("No readings for this vehicle yet. Pick a scenario above to generate some.")

    # AI investigation
    st.markdown('<div class="card"><div class="card-title">AI INVESTIGATION</div>', unsafe_allow_html=True)

    if not latest:
        st.markdown('<div class="note">Waiting for sensor data…</div>', unsafe_allow_html=True)
        st.markdown(pipeline(0) + "</div>", unsafe_allow_html=True)
        return

    if not faults:
        st.markdown('<div class="alert ok">✔ NO ABNORMALITIES DETECTED</div>', unsafe_allow_html=True)
        st.markdown(pipeline(0) + "</div>", unsafe_allow_html=True)
        return

    primary = faults[0]
    know = KNOWLEDGE.get(primary["code"], {"title": primary["message"].upper(), "causes": [], "checks": []})
    investigated = st.session_state["investigated"].get(reg)

    st.markdown(f'<div class="alert">⚠ {know["title"]}</div>', unsafe_allow_html=True)

    if not investigated:
        st.markdown(
            f'<div class="note" style="margin-top:0">Detector: {primary["field"]} = {primary["value"]} '
            f'{primary["unit"]} (limit {primary["threshold"]} {primary["unit"]}).</div>',
            unsafe_allow_html=True,
        )
        st.markdown(pipeline(1), unsafe_allow_html=True)
        if st.button("🔍 Start AI Investigation", type="primary", key="investigate"):
            with st.spinner("Retrieving knowledge and reasoning over the evidence…"):
                # Hook: call your friend's agent here, e.g. report = gemini_agent.investigate(...)
                report = build_report(vehicle, latest, faults)
            st.session_state["investigated"][reg] = report
            st.rerun()
    else:
        causes = "".join(f"<li>{c}</li>" for c in investigated["possible_causes"])
        checks = "".join(f"<li>{c}</li>" for c in investigated["recommendations"])
        st.markdown(
            f'<div class="sub">POSSIBLE CAUSES</div><ul class="cause-list">{causes}</ul>'
            f'<div class="sub">RECOMMENDED CHECKS</div><ul class="cause-list">{checks}</ul>'
            f'<div class="sub">URGENCY</div><div style="font-weight:600">{investigated["urgency"]}</div>'
            f'<div class="note">{investigated["note"]} Knowledge shown is illustrative until reviewed.</div>',
            unsafe_allow_html=True,
        )
        st.markdown(pipeline(4), unsafe_allow_html=True)
        if st.button("💾 Save report to Atlas" if DB is not None else "💾 Save report", key="save_report"):
            save_report(investigated)
            st.success("Report saved.")
    st.markdown("</div>", unsafe_allow_html=True)


def page_vehicles(vehicles):
    topbar()
    st.markdown("### VEHICLES")
    df = pd.DataFrame([{k: v for k, v in x.items() if k != "_id"} for x in vehicles])
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_history(vehicles):
    topbar()
    st.markdown("### SENSOR HISTORY")
    choice = st.selectbox("Vehicle", [vehicle_label(v) for v in vehicles])
    reg = choice.split(" - ")[0]
    readings = load_readings(reg, limit=100)
    if not readings:
        st.info("No readings yet for this vehicle.")
        return
    df = pd.DataFrame(readings).drop(columns=["_id", "vehicle_id"], errors="ignore")
    st.line_chart(df.set_index("timestamp")[["temperature", "voltage"]], height=260)
    st.dataframe(df, use_container_width=True, hide_index=True)


def page_reports(vehicles):
    topbar()
    st.markdown("### DIAGNOSTIC REPORTS")
    reports = load_reports()
    if not reports:
        st.info("No reports saved yet. Run an investigation from the dashboard.")
        return
    for r in reports:
        created = r.get("created_at")
        stamp = created.strftime("%d %b %Y %H:%M") if hasattr(created, "strftime") else str(created)
        with st.expander(f'{r["registration_number"]} · {r.get("fault_code", "")} · {stamp}'):
            st.write(f'**Evidence:** {r["evidence"]}')
            st.write(f'**Urgency:** {r["urgency"]}')
            st.write("**Possible causes:** " + ", ".join(r["possible_causes"]))
            st.write("**Recommended checks:**")
            for c in r["recommendations"]:
                st.write(f"- {c}")
            st.caption(r.get("note", ""))


# ──────────────────────────────────────────────────────────────
# Navigation
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="brand">SIM<span>DOCTOR</span></div>'
                '<div class="brand-sub">VEHICLE INTELLIGENCE</div>', unsafe_allow_html=True)
    page = st.radio("Navigation", ["DASHBOARD", "VEHICLES", "HISTORY", "REPORTS"],
                    label_visibility="collapsed")

all_vehicles = load_vehicles()

if page == "DASHBOARD":
    page_dashboard(all_vehicles)
elif page == "VEHICLES":
    page_vehicles(all_vehicles)
elif page == "HISTORY":
    page_history(all_vehicles)
else:
    page_reports(all_vehicles)