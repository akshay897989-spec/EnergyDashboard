import streamlit as st
import feedparser
import json
from groq import Groq
from datetime import datetime

# ---------------- CONFIG ----------------
st.set_page_config(page_title="STRAT-INT TERMINAL", layout="wide")

SUBJECTS = [
    "Grid & Macro",
    "Renewables",
    "Battery Storage",
    "Hydrogen & PTX",
    "Nuclear and SMR",
    "Demand"
]

COUNTRIES = ["Australia", "New Zealand", "India", "South Korea", "Japan"]

FEEDS = [
    "https://reneweconomy.com.au/feed/",
    "https://www.utilitydive.com/feeds/news/",
    "https://www.energy-storage.news/feed/",
    "https://www.hydrogeninsight.com/?service=rss",
    "https://www.reuters.com/business/energy/feed/"
]

# ---------------- STYLE ----------------
st.markdown("""
<style>
body {background:#050a14;color:#e5e7eb;}
.card {background:#0b1220;border:1px solid #1f2937;padding:18px;border-radius:8px;margin-bottom:18px;}
.hdr {color:#22d3ee;font-weight:700;text-transform:uppercase;}
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

# ---------------- LLM PROMPT ----------------
SYSTEM_PROMPT = """
You are Head of Research at a global renewable energy investment firm.
Write as if briefing the CEO.

Return ONLY valid JSON:

{
 "core_thesis":"3-4 sentence executive summary",
 "drivers":[{"sign":"positive|negative","text":"driver"}],
 "bull_case":["..."],
 "bear_case":["..."],
 "verdict":"Bullish/Bearish/Neutral and why in one sentence",
 "technology_context":["global tech truths"],
 "news":[{"headline":"...","link":"..."}]
}

Rules:
- Think first principles.
- Judge economics, not sentiment.
- Commissioning capacity is POSITIVE unless it destroys pricing.
- Use ONLY country-relevant news.
"""

def fetch_country_news(country):
    results=[]
    for url in FEEDS:
        feed=feedparser.parse(url)
        for e in feed.entries[:30]:
            text=(e.title + e.get("summary","")).lower()
            if country.lower() in text:
                results.append({"headline":e.title,"link":e.link})
    return results[:10]

def analyze_block(block, country, news):
    if not st.session_state.key:
        return None
    client=Groq(api_key=st.session_state.key)
    context="\n".join([n["headline"] for n in news])
    msg=f"Block:{block}\nCountry:{country}\nNews:\n{context}"
    res=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":SYSTEM_PROMPT},
                  {"role":"user","content":msg}],
        temperature=0.2
    )
    return json.loads(res.choices[0].message.content)

# ---------------- MAIN ----------------
if not run:
    st.info("Enter key and run scan")
else:
    cols=st.columns(2)
    for i,block in enumerate(SUBJECTS):
        col=cols[i%2]
        with col:
            news=fetch_country_news(country)
            analysis=analyze_block(block,country,news)
            if not analysis:
                st.warning("No API key")
                continue

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

            st.markdown("**Global Technology Context**")
            for t in analysis["technology_context"]:
                st.markdown(f"- {t}")

            st.markdown("**Country News**")
            for n in analysis["news"]:
                st.markdown(f"- [{n['headline']}]({n['link']})")

            st.markdown("</div>",unsafe_allow_html=True)
