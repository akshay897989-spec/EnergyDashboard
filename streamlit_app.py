import streamlit as st
import feedparser
import pandas as pd
from groq import Groq
from datetime import datetime

# 1. Page Configuration (Institutional Minimalist)
st.set_page_config(page_title="Strategic Energy Outlook", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for Dark Mode Refinement
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stExpander { border: 1px solid #262730 !important; background-color: #161b22 !important; }
    .stButton>button { width: 100%; background-color: #238636; color: white; border-radius: 5px; }
    .metric-box { padding: 10px; border-radius: 5px; background-color: #0d1117; border: 1px solid #30363d; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Sidebar & Intelligence Verticals
with st.sidebar:
    st.title("⚙️ Controls")
    groq_key = st.text_input("Groq API Key", type="password")
    
    vertical = st.radio(
        "Intelligence Vertical",
        ["Grid / Macro", "Generation (Solar/Wind)", "Storage & Flexibility", 
         "Hydrogen & Power-to-X", "Transmission", "Policy & Regulation", "Asia-Pacific (AU/IN/JP/KR)"]
    )
    
    st.divider()
    st.caption("Investment Thesis: Focus on Bottlenecks & Risk Absorption.")

# 3. Feed Mapping (Targeting your specific regions & tech)
FEED_MAP = {
    "Grid / Macro": ["https://www.utilitydive.com/feeds/news/", "https://www.iea.org/news/rss"],
    "Generation (Solar/Wind)": ["https://www.renewableenergyworld.com/feed/", "https://cleantechnica.com/feed/"],
    "Storage & Flexibility": ["https://www.energy-storage.news/feed/"],
    "Hydrogen & Power-to-X": ["https://www.hydrogeninsight.com/?service=rss"],
    "Transmission": ["https://www.powergridinternational.com/feed/"],
    "Policy & Regulation": ["https://www.carbonbrief.org/feed/"],
    "Asia-Pacific (AU/IN/JP/KR)": [
        "https://reneweconomy.com.au/feed/", # Australia
        "https://mercomindia.com/feed/",      # India
        "https://asia.nikkei.com/rss/feed/nar" # Regional/Japan/Korea
    ]
}

# 4. The "First Principles" System Prompt
SYSTEM_PROMPT = """You are a Strategic Renewable Energy Investment Agent.
Your role is to identify where durable economic power and excess returns concentrate.

THINK FROM FIRST PRINCIPLES:
1. Physics: Energy density, intermittency, transmission limits.
2. Cost Stack: Which components fall with scale vs. rise with penetration?
3. Market Structure: Who controls interconnection? Who bears price risk?
4. Profit Pools: Classify as Commodity, Scale-advantaged, Bottlenecked, or Risk-absorbing.

ALWAYS USE CAUSAL CHAINS: If X -> then Y -> causing Z.
NEVER provide static summaries. Focus on 2nd and 3rd order effects.
"""

# 5. Main Dashboard UI
st.title("⚡ Renewable Investor: Strategic Outlook")
st.subheader(f"Vertical: {vertical}")

if not groq_key:
    st.warning("Please enter your Groq API Key in the sidebar to access the intelligence layer.")
else:
    client = Groq(api_key=groq_key)

    if st.button("Generate Strategic Analysis"):
        with st.spinner("Analyzing Causal Chains..."):
            all_entries = []
            for url in FEED_MAP[vertical]:
                feed = feedparser.parse(url)
                all_entries.extend(feed.entries[:5]) # Top 5 from each source

            for entry in all_entries:
                with st.expander(f"📌 {entry.title.upper()}"):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # The Strategic AI Request
                        prompt = f"""Analyze this news for a renewable investor:
                        Headline: {entry.title}
                        Context: {entry.summary if 'summary' in entry else 'N/A'}
                        
                        Provide output in this exact structure:
                        - SUMMARY (2 lines)
                        - WHY IT MATTERS (The structural constraint involved)
                        - WHO GAINS / WHO LOSES
                        - SECOND-ORDER EFFECTS (Causal chain)
                        - INVESTMENT IMPLICATION
                        """
                        
                        try:
                            response = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.1 # Low temperature for analytical consistency
                            )
                            analysis = response.choices[0].message.content
                            st.markdown(analysis)
                        except Exception as e:
                            st.error(f"Analysis Error: {e}")

                    with col2:
                        st.markdown("**Intelligence Meta**")
                        # Mocked tags based on title keywords for institutional feel
                        tags = []
                        if "grid" in entry.title.lower(): tags.append("🟢 Bottleneck")
                        if "policy" in entry.title.lower(): tags.append("⚖️ Policy Shock")
                        if "price" in entry.title.lower(): tags.append("📉 Volatility")
                        
                        for tag in tags:
                            st.info(tag)
                        
                        st.caption(f"Source: {entry.link}")
                        st.caption(f"Time: {datetime.now().strftime('%Y-%m-%d')}")

# 6. Bottom Hierarchy (Footer)
st.divider()
st.caption("Strategic News Engine | Built for Energy First-Principles Analysis")
