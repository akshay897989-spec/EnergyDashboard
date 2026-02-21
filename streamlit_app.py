import streamlit as st
import feedparser
import pandas as pd
from groq import Groq
from datetime import datetime

# 1. INSTITUTIONAL TERMINAL STYLING (QuantAI Inspired)
st.set_page_config(page_title="STRAT-INT TERMINAL", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #050a14;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Grid Module Styling */
    .intel-card {
        background: rgba(16, 22, 34, 0.8);
        border: 1px solid #1f2937;
        border-top: 2px solid #00d4ff;
        padding: 20px;
        border-radius: 4px;
        height: 100%;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    .intel-card:hover {
        border-color: #00d4ff;
        box-shadow: 0 0 15px rgba(0, 212, 255, 0.1);
    }
    
    .module-header {
        color: #00d4ff;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 15px;
        border-bottom: 1px solid #1f2937;
        padding-bottom: 5px;
    }
    
    .gist-text {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #b0b8c4;
    }
    
    .tag {
        display: inline-block;
        font-size: 0.7rem;
        padding: 2px 8px;
        border-radius: 3px;
        margin-right: 5px;
        background: #1e293b;
        color: #00d4ff;
        border: 1px solid #00d4ff;
    }

    /* Minimalist Headers */
    h1 { font-weight: 300 !important; letter-spacing: -1px; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 2. STRATEGIC ENGINE SETUP
client = None
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""

with st.sidebar:
    st.session_state.groq_key = st.text_input("ACCESS_KEY", type="password")
    st.caption("SYSTEM STATUS: SIMULATION MODE")

# Intelligence Verticals & Feeds
VERTICALS = {
    "MACRO & GRID": "https://www.utilitydive.com/feeds/news/",
    "GEN & STORAGE": "https://www.energy-storage.news/feed/",
    "HYDROGEN & PTX": "https://www.hydrogeninsight.com/?service=rss",
    "ASIA-PACIFIC": "https://reneweconomy.com.au/feed/",
    "CAPITAL MARKETS": "https://www.ft.com/energy?format=rss"
}

# 3. MCKINSEY ANALYST PROMPT
MCKINSEY_PROMPT = """
Act as a Senior Research Lead at a tier-1 strategic consultancy. 
Synthesize the provided news flow into a 'Strategic Gist'. 

CRITERIA:
1. NO BULLET POINTS for the summary. Provide a single, dense, high-conviction paragraph.
2. CONNECT THE DOTS: Link news to fossil fuel price volatility (Coal/Gas), Data Center power demand, and grid congestion.
3. CAUSAL CHAIN: Explain If X -> Then Y -> Impact Z.
4. INVESTMENT WINDOW: Judge the timing (Early/Optimal/Late) based on structural bottlenecks.
5. FOCUS: Identify bottlenecks, risk-absorption advantages, and profit pool shifts.
"""

def get_strategic_gist(topic, headlines):
    if not st.session_state.groq_key:
        return "Access Key Required."
    
    client = Groq(api_key=st.session_state.groq_key)
    context = "\n".join([f"- {h}" for h in headlines])
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": MCKINSEY_PROMPT},
            {"role": "user", "content": f"Topic: {topic}\nNews Items: {context}\nAnalyze current market conditions and strategic timing."}
        ],
        temperature=0.2
    )
    return completion.choices[0].message.content

# 4. MAIN LAYOUT
st.title("STRAT-INT: RENEWABLE OUTLOOK")
st.caption(f"AS OF {datetime.now().strftime('%d %b %Y')} | NODES: TOKYO, DELHI, SYDNEY, SEOUL")

if st.button("EXECUTE GLOBAL SCAN"):
    # Grid Layout: 2 Columns
    col1, col2 = st.columns(2)
    
    # Process Verticals
    v_keys = list(VERTICALS.keys())
    
    for i, key in enumerate(v_keys):
        target_col = col1 if i % 2 == 0 else col2
        
        with target_col:
            st.markdown(f"""<div class="intel-card">
                <div class="module-header">{key}</div>
            """, unsafe_allow_html=True)
            
            # Fetch & Analyze
            with st.spinner(f"Processing {key}..."):
                feed = feedparser.parse(VERTICALS[key])
                headlines = [e.title for e in feed.entries[:5]]
                gist = get_strategic_gist(key, headlines)
                
                st.markdown(f'<div class="gist-text">{gist}</div>', unsafe_allow_html=True)
                
                # Metadata Tags
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<span class="tag">CONVICTION: HIGH</span> <span class="tag">WINDOW: OPEN</span>', unsafe_allow_html=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("Input ACCESS_KEY in sidebar and EXECUTE GLOBAL SCAN to initialize intelligence grid.")

# 5. FOOTER
st.markdown("""
    <div style="text-align: center; color: #4b5563; font-size: 0.7rem; margin-top: 50px;">
        PROPRIETARY INVESTOR TERMINAL // FIRST-PRINCIPLES ANALYSIS ENGINE
    </div>
    """, unsafe_allow_html=True)
