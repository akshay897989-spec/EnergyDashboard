import streamlit as st
import feedparser, json, re
from groq import Groq
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Renewable Investor — Strategic Outlook", layout="wide")

SUBJECTS = [
    "Grid & Macro",
    "Renewables",
    "Battery Storage",
    "Hydrogen & PTX",
    "Nuclear and SMR",
    "Demand"
]

COUNTRIES = ["Australia", "New Zealand", "India", "South Korea", "Japan"]

# --------- MODULE-SPECIFIC FEEDS ----------
FEEDS = {
    "Grid & Macro": [
        "https://www.utilitydive.com/feeds/news/",
        "https://www.reuters.com/business/energy/feed/"
    ],
    "Renewables": [
        "https://reneweconomy.com.au/feed/",
        "https://www.pv-tech.org/feed/"
    ],
    "Battery Storage": [
        "https://www.energy-storage.news/feed/"
    ],
    "Hydrogen & PTX": [
        "https://www.hydrogeninsight.com/?service=rss"
    ],
    "Nuclear and SMR": [
        "https://www.world-nuclear-news.org/feeds/rss.xml"
    ],
    "Demand": [
        "https://www.iea.org/rss/news",
        "https://www.datacenterdynamics.com/en/rss/"
    ]
}

# ---------- KEYWORD FILTER PER MODULE ----------
KEYWORDS = {
    "Grid & Macro": ["grid", "transmission", "interconnection", "tariff", "utility", "congestion"],
    "Renewables": ["solar", "wind", "renewable", "ppa", "module", "turbine"],
    "Battery Storage": ["battery", "storage", "bess", "lithium"],
    "Hydrogen & PTX": ["hydrogen", "electrolyser", "ammonia", "ptx"],
    "Nuclear and SMR": ["nuclear", "smr", "reactor"],
    "Demand": ["data center", "electricity demand", "load growth", "ai power"]
}

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {background:#050a14;color:#e5e7eb;}
.card {background:#0b1220;border:1px solid #1f2937;padding:18px;border-radius:8px;margin-bottom:18px;}
.hdr {color:#22d3ee;font-weight:700;}
.good {color:#22c55e;}
.bad {color:#ef4444;}
</style>
""", unsafe_allow_html=True)

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.session_state.key = st.text_input("GROQ KEY", type="password")
    country = st.selectbox("Country", COUNTRIES)
    run = st.button("RUN SCAN")

st.title("Renewable Investor — Strategic Outlook")
st.caption(f"{country} | {datetime.now().strftime('%d %b %Y')}")

# ---------------- PROMPT ----------------
SYSTEM_PROMPT = """
You are Head of Research at a renewable infrastructure investment firm.
Write like an executive briefing the CIO.

Return ONLY valid JSON:

{
 "core_thesis":"2–3 sentence investment stance",
 "drivers":[{"sign":"positive|negative","text":"driver"}],
 "bull_case":["..."],
 "bear_case":["..."],
 "verdict":"one sentence",
 "news":[{"headline":"...","link":"..."}]
}

Rules:
- Drivers must be structural, not descriptive.
- Commissioning capacity is POSITIVE unless it collapses pricing.
- Use only supplied news.
- Output must start with { and end with }.
"""

# ---------------- HELPERS ----------------
def extract_json(text):
    try:
        return json.loads(text)
    except:
        match=re.search(r"\{.*\}",text,re.DOTALL)
        if match:
            try: return json.loads(match.group())
            except: return None
    return None

def fetch_news(block, country):
    results=[]
    for url in FEEDS[block]:
        feed=feedparser.parse(url)
        for e in feed.entries[:40]:
            text=(e.title + e.get("summary","")).lower()
            if country.lower() in text and any(k in text for k in KEYWORDS[block]):
                results.append({"headline":e.title,"link":e.link})
    return results[:8]

def analyze(block, news):
    if not st.session_state.key:
        return None
    client=Groq(api_key=st.session_state.key)
    context="\n".join(n["headline"] for n in news)
    res=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":context}
        ],
        temperature=0.2
    )
    raw=res.choices[0].message.content.strip()
    parsed=extract_json(raw)
    if parsed: return parsed
    return {"core_thesis":"Parsing failed","drivers":[],"bull_case":[],"bear_case":[],"verdict":"N/A","news":news}

# ---------------- MAIN ----------------
if not run:
    st.info("Enter key and run scan.")
else:
    cols=st.columns(2)
    for i,block in enumerate(SUBJECTS):
        col=cols[i%2]
        with col:
            news=fetch_news(block,country)
            analysis=analyze(block,news)

            st.markdown(f"<div class='card'><div class='hdr'>{block}</div>",unsafe_allow_html=True)
            st.markdown("**Core Thesis**")
            st.write(analysis["core_thesis"])

            st.markdown("**Drivers**")
            for d in analysis["drivers"]:
                icon="✅" if d["sign"]=="positive" else "❌"
                st.markdown(f"{icon} {d['text']}")

            st.markdown("**Bull Case**")
            for b in analysis["bull_case"]:
                st.markdown(f"- {b}")

            st.markdown("**Bear Case**")
            for b in analysis["bear_case"]:
                st.markdown(f"- {b}")

            st.markdown(f"**Verdict:** {analysis['verdict']}")

            st.markdown("**Country-Specific News**")
            for n in analysis["news"]:
                st.markdown(f"- [{n['headline']}]({n['link']})")

            st.markdown("</div>",unsafe_allow_html=True)
