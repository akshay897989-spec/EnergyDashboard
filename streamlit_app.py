# streamlit_app.py
import streamlit as st
import feedparser
import json
from datetime import datetime
from typing import List, Dict

# If using Groq client, import it here. If not available, the code will render a helpful message.
try:
    from groq import Groq
except Exception:
    Groq = None

# --------------------
# Page & Styling
# --------------------
st.set_page_config(page_title="STRAT-INT TERMINAL", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');

    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050a14;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }

    .intel-card {
        background: rgba(16, 22, 34, 0.85);
        border: 1px solid #1f2937;
        border-top: 2px solid #00d4ff;
        padding: 18px;
        border-radius: 6px;
        margin-bottom: 18px;
    }
    .module-header { color: #00d4ff; font-size: 0.9rem; font-weight:700; text-transform:uppercase; letter-spacing:1px; margin-bottom:10px; }
    .core-stance { font-weight:700; color:#ffffff; margin-bottom:8px; }
    .drivers { font-size:0.9rem; color:#cbd5e1; margin-bottom:8px; }
    .news-item { font-size:0.85rem; color:#9aa6b2; margin-bottom:6px; }
    .subtags { font-size:0.75rem; color:#7f8a94; }
    h1 { font-weight: 300 !important; color: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("STRAT-INT: RENEWABLE OUTLOOK")
st.caption(f"AS OF {datetime.now().strftime('%d %b %Y')} | NODES: TOKYO, DELHI, SYDNEY, SEOUL")

# --------------------
# Sidebar - Access + Filters
# --------------------
with st.sidebar:
    st.markdown("### ACCESS")
    st.session_state.groq_key = st.text_input("LLM_ACCESS_KEY (optional)", type="password")
    st.markdown("---")
    st.markdown("### GEOGRAPHY FILTERS")
    REGION = st.selectbox("Region", ["Asia Pacific"], index=0)
    apac_countries = ["Australia", "New Zealand", "India", "South Korea", "Japan"]
    selected_countries = st.multiselect("Countries (APAC)", apac_countries, default=apac_countries)
    st.markdown("---")
    st.markdown("### RUN")
    run_scan = st.button("EXECUTE GLOBAL SCAN")
    st.caption("SYSTEM STATUS: SIMULATION MODE" if not Groq else "SYSTEM STATUS: LLM CLIENT AVAILABLE")

# --------------------
# Feeds per block (you can add or replace URLs)
# --------------------
FEEDS = {
    "Grid & Macro": [
        "https://www.utilitydive.com/feeds/news/",
        "https://www.reuters.com/business/energy/feed/"
    ],
    "Renewables": [
        "https://www.pv-tech.org/feed/",
        "https://reneweconomy.com.au/feed/"
    ],
    "Battery Storage": [
        "https://www.energy-storage.news/feed/",
        "https://www.greentechmedia.com/feed"
    ],
    "Hydrogen & PTX": [
        "https://www.hydrogeninsight.com/?service=rss",
        "https://www.h2-view.com/rss"
    ],
    "Nuclear and SMR": [
        "https://www.world-nuclear-news.org/feeds/rss.xml"
    ],
    "Demand": [
        "https://www.iea.org/rss/news",
        "https://www.ft.com/energy?format=rss"
    ],
}

# keywords to detect legal updates per country (simple heuristics - expand as needed)
LAW_KEYWORDS = {
    "India": ["Amarchand", "AZB", "Trilegal", "Shardul Amarchand", "Khaitan"],
    "South Korea": ["Kim & Chang", "Shin & Kim", "Bae, Kim & Lee"],
    "Australia": ["MinterEllison", "King & Wood Mallesons", "Clayton Utz"],
    "Japan": ["Nishimura", "Anderson Mori", "TMI Associates"],
    "New Zealand": ["Bell Gully", "Chapman Tripp"]
}

# --------------------
# LLM Prompt (structured JSON output)
# --------------------
MODEL_SYSTEM_PROMPT = """
You are a senior strategic research lead preparing a concise investment-committee style analysis.
Output MUST be valid JSON (no extra commentary) with this structure:

{
  "topic": "<string - subject block>",
  "core_stance": "<one-line high-conviction statement>",
  "drivers": {
     "<region>": [
         {"country":"<country>", "driver":"<short driver>", "sign":"positive"|"negative", "notes":"<short reason>"}
     ],
     ...
  },
  "first_principles": ["<short bullets as strings>"],
  "bull_case": ["<short bullets with causal chain>"],
  "bear_case": ["<short bullets with causal chain>"],
  "winner": "<'bull'|'bear'|'balanced'>",
  "winner_rationale": "<one-line reason>",
  "news_items": [
    {"headline":"<headline>", "source":"<source>", "link":"<url>"}
  ],
  "legal_updates": [
    {"country":"<country>", "firm":"<firm name>", "summary":"<1-line summary if present>", "link":"<url or empty>"}
  ]
}

Rules:
- core_stance: 1 short sentence (no paragraphs).
- drivers: list up to 6 drivers PER country. Use sign 'positive' for ✅ and 'negative' for ❌.
- bull_case and bear_case: 2-4 bullets each, succinct causal chains (If X -> Then Y -> Result).
- winner: pick one of bull/bear/balanced and give a one-line rationale.
- news_items: include only the most relevant 3-5 items from the provided headlines.
- legal_updates: detect law-firm style reports; include if any headline/summary mentions known law firms or 'legal'/'regulation'/'policy' updates.

Be concise and formatted exactly as JSON.
"""

def call_llm_structured(topic: str, headlines: List[Dict[str, str]]) -> Dict:
    """
    Call LLM (Groq) to generate the structured JSON analysis.
    If Groq client not available or key missing, return a stub structure.
    """
    if not Groq or not st.session_state.groq_key:
        # Fallback stub - local summarizer that structures headlines
        # This keeps format predictable for UI demonstration.
        core = f"Monitor structural grid stress and contract exposure in {topic}."
        drivers = {}
        for country in selected_countries:
            drivers[country] = []
            # Quick heuristic: if headline contains country name, flag positive/negative
            for h in headlines[:3]:
                sign = "positive" if country.lower() in (h["headline"] + " " + h.get("summary","")).lower() else "negative"
                drivers[country].append({"country": country, "driver": h["headline"][:80], "sign": sign, "notes": "derived from headlines"})
        stub = {
            "topic": topic,
            "core_stance": core,
            "drivers": {REGION: drivers},
            "first_principles": ["Intermittency creates value for flexibility", "Financing drives buildout timing"],
            "bull_case": ["If capacity shortages persist -> prices rise -> merchant returns improve"],
            "bear_case": ["If storage and transmission scale rapidly -> prices compress -> merchant returns fall"],
            "winner": "balanced",
            "winner_rationale": "Offsetting supply/demand and policy risk",
            "news_items": headlines[:5],
            "legal_updates": []
        }
        return stub

    # If Groq available, make a predict call (expects Groq client and valid key)
    client = Groq(api_key=st.session_state.groq_key)
    # Build context lines
    context = "\n".join([f"- {h['headline']} ({h['source']}) {h.get('link','')}" for h in headlines[:10]])
    user_msg = f"Topic: {topic}\nHeadlines:\n{context}\n\nCountries: {', '.join(selected_countries)}\n\nProduce the JSON exactly as instructed in system prompt."
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": MODEL_SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        temperature=0.0,
        max_tokens=900
    )
    raw = completion.choices[0].message.content
    # Ensure valid JSON
    try:
        parsed = json.loads(raw)
        return parsed
    except Exception as e:
        # If parsing fails, return a fallback indicating LLM output issue
        return {
            "topic": topic,
            "core_stance": "LLM returned unparsable output; see raw.",
            "drivers": {},
            "first_principles": [],
            "bull_case": [],
            "bear_case": [],
            "winner": "balanced",
            "winner_rationale": "LLM parse error",
            "news_items": [{"headline": raw[:200], "source": "LLM_RAW", "link": ""}],
            "legal_updates": []
        }

# --------------------
# Helpers: fetch headlines & detect legal mentions
# --------------------
def fetch_headlines_for_block(feed_urls: List[str], country_filters: List[str]) -> List[Dict]:
    items = []
    for url in feed_urls:
        try:
            f = feedparser.parse(url)
            for e in f.entries[:6]:
                title = e.get("title", "")
                link = e.get("link", "")
                summary = e.get("summary", "")
                source = f.feed.get("title", url)
                # simple country filter tag
                country_tag_hits = [c for c in country_filters if c.lower() in (title + " " + summary).lower()]
                items.append({"headline": title, "link": link, "summary": summary, "source": source, "country_hits": country_tag_hits})
        except Exception:
            continue
    # dedupe by headline
    seen = set()
    dedup = []
    for it in items:
        if it["headline"] in seen:
            continue
        seen.add(it["headline"])
        dedup.append(it)
    return dedup

def detect_legal_updates(items: List[Dict]) -> List[Dict]:
    updates = []
    for it in items:
        text = (it.get("headline","") + " " + it.get("summary","")).lower()
        for country, keywords in LAW_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    updates.append({"country": country, "firm": kw, "summary": it.get("headline",""), "link": it.get("link","")})
    return updates

# --------------------
# Main Layout: Cards per subject
# --------------------
if not run_scan:
    st.info("Input LLM_ACCESS_KEY (optional) and click EXECUTE GLOBAL SCAN to initialize intelligence grid.")
else:
    # Two-column layout
    cols = st.columns(2)
    left_col, right_col = cols[0], cols[1]

    blocks = ["Grid & Macro", "Renewables", "Battery Storage", "Hydrogen & PTX", "Nuclear and SMR", "Demand"]

    for i, block in enumerate(blocks):
        target = left_col if i % 2 == 0 else right_col
        with target:
            st.markdown(f'<div class="intel-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="module-header">{block}</div>', unsafe_allow_html=True)

            # fetch headlines (limited to selected countries)
            feed_urls = FEEDS.get(block, [])
            headlines = fetch_headlines_for_block(feed_urls, selected_countries)

            # prepare simplified headlines for LLM input
            simple_headlines = [{"headline": h["headline"], "source": h["source"], "link": h["link"], "summary": h["summary"]} for h in headlines]

            with st.spinner(f"Analyzing {block}..."):
                analysis = call_llm_structured(block, simple_headlines)

            # render core stance
            core = analysis.get("core_stance", "—")
            st.markdown(f'<div class="core-stance">Core Stance: {core}</div>', unsafe_allow_html=True)

            # drivers: drivers are expected as mapping region -> countries dict (we accommodated a fallback shape)
            drivers = analysis.get("drivers", {})
            # Drivers can be either drivers[REGION][country] or drivers[country] depending on LLM; handle both
            if isinstance(drivers, dict):
                # If nested with REGION as top-level
                if REGION in drivers and isinstance(drivers[REGION], dict):
                    drivers_by_country = drivers[REGION]
                else:
                    # assume mapping country -> list
                    drivers_by_country = drivers
            else:
                drivers_by_country = {}

            # Render drivers per selected country
            st.markdown('<div class="drivers">Drivers (by country):</div>', unsafe_allow_html=True)
            for country in selected_countries:
                st.markdown(f"**{country}**")
                country_drivers = drivers_by_country.get(country, [])
                if not country_drivers:
                    st.markdown("• _No structured drivers detected._", unsafe_allow_html=True)
                else:
                    for d in country_drivers[:6]:
                        sign_emoji = "✅" if d.get("sign","positive") == "positive" else "❌"
                        notes = d.get("notes","")
                        st.markdown(f"- {sign_emoji} {d.get('driver')} — _{notes}_", unsafe_allow_html=True)

            # First principles
            fp = analysis.get("first_principles", [])
            if fp:
                st.markdown("**First Principles:**")
                for p in fp:
                    st.markdown(f"- {p}")

            # Bull / Bear / Winner
            st.markdown("**Bull Case:**")
            for b in analysis.get("bull_case", [])[:4]:
                st.markdown(f"- {b}")
            st.markdown("**Bear Case:**")
            for b in analysis.get("bear_case", [])[:4]:
                st.markdown(f"- {b}")

            winner = analysis.get("winner", "balanced")
            winner_rationale = analysis.get("winner_rationale", "")
            st.markdown(f"**Winner:** `{winner.upper()}` — {winner_rationale}")

            # News items
            if analysis.get("news_items"):
                st.markdown("**Key News / Updates:**")
                for n in analysis.get("news_items", [])[:5]:
                    src = n.get("source", "")
                    link = n.get("link", "")
                    headline = n.get("headline", "")
                    st.markdown(f'- <span class="news-item">{headline}</span> <span class="subtags">({src}) <a href="{link}" target="_blank">link</a></span>', unsafe_allow_html=True)

            # Legal updates (detected via feed scanning)
            legal_hits = detect_legal_updates(headlines)
            if analysis.get("legal_updates"):
                # if LLM returned legal_updates include them too
                lll = analysis.get("legal_updates", [])
                legal_hits.extend(lll)
            if legal_hits:
                st.markdown("**Legal / Policy Notes (firm mentions):**")
                for lu in legal_hits[:6]:
                    firm = lu.get("firm", lu.get("country",""))
                    summary = lu.get("summary", "")
                    link = lu.get("link", "")
                    country = lu.get("country", "")
                    st.markdown(f"- **{firm}** ({country}) — {summary} — <a href='{link}' target='_blank'>link</a>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # footer
    st.markdown("""
        <div style="text-align: center; color: #4b5563; font-size: 0.75rem; margin-top: 20px;">
            PROPRIETARY INVESTOR TERMINAL // FIRST-PRINCIPLES ANALYSIS ENGINE — FINAL VERSION
        </div>
    """, unsafe_allow_html=True)
