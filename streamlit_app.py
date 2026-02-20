import streamlit as st
import feedparser
import pandas as pd
from groq import Groq

# Set up the UI
st.set_page_config(page_title="Energy Strategic Monitor", layout="wide")
st.title("⚡ Renewable Investor: Strategic Outlook")

# Sidebar for the API Key (Securely handled)
groq_key = st.sidebar.text_input("Enter Groq API Key", type="password")

# Your "High Signal" Feeds
FEEDS = {
    "Grid/Macro": "https://www.utilitydive.com/feeds/news/",
    "Hydrogen/SMR": "https://www.hydrogeninsight.com/?service=rss",
    "Tech/Innovation": "https://cleantechnica.com/feed"
}

if groq_key:
    client = Groq(api_key=groq_key)
    category = st.selectbox("Select Intelligence Vertical", list(FEEDS.keys()))
    
    if st.button("Fetch & Analyze News"):
        feed = feedparser.parse(FEEDS[category])
        
        for entry in feed.entries[:5]: # Let's start with 5 articles to keep it clean
            with st.expander(f"📌 {entry.title}"):
                st.write(f"*Source: {entry.link}*")
                
                # AI Analysis Request
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a strategic energy investment analyst. Be concise, cynical, and focused on 2nd order effects."},
                        {"role": "user", "content": f"Analyze this headline for strategic risk and maturity: {entry.title}. Context: {entry.summary}"}
                    ]
                )
                st.info(completion.choices[0].message.content)
else:
    st.warning("Please enter your Groq API Key in the sidebar to begin.")
