"""Streamlit frontend for the Web Crawler Agent."""

from __future__ import annotations

import streamlit as st

from agent import run_agent

st.set_page_config(page_title="Web Crawler Agent", page_icon="🕷️")

st.title("🕷️ Web Crawler Agent")
st.caption("Bedrock-style agent (local simulation) · `web_scrape` tool → Lambda handler")

with st.sidebar:
    st.header("How it works")
    st.markdown(
        "1. You send a message with a URL.\n"
        "2. The agent runtime calls the **`web_scrape`** tool.\n"
        "3. The tool runs through the **Lambda handler** (Bedrock event shape).\n"
        "4. The scraper fetches, follows redirects, decodes gzip, caps size, "
        "and returns clean text.\n"
        "5. The agent answers from that text."
    )
    st.divider()
    st.markdown("**Try:**")
    st.code("Crawl this URL: https://example.com", language=None)

if "messages" not in st.session_state:
    st.session_state.messages = []  # UI transcript
if "history" not in st.session_state:
    st.session_state.history = []   # model-facing history (user/assistant text)

# Replay transcript.
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

prompt = st.chat_input("Ask the agent to crawl a URL...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        answer = ""
        for kind, payload in run_agent(prompt, history=st.session_state.history):
            if kind == "tool_call":
                st.info(f"🔧 Calling `web_scrape` → {payload['url']}")
            elif kind == "tool_result":
                if payload.get("error"):
                    st.warning(f"Scraper error: {payload['error']}")
                else:
                    label = payload.get("title") or payload.get("url", "")
                    trunc = " (truncated)" if payload.get("truncated") else ""
                    with st.expander(
                        f"📄 Fetched: {label} · {payload.get('bytes', 0):,} bytes{trunc}"
                    ):
                        st.text(payload.get("text", "")[:3000])
            else:  # answer
                answer = payload
                st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    # Keep a compact text-only history for the next turn.
    st.session_state.history.append({"role": "user", "content": prompt})
    st.session_state.history.append({"role": "assistant", "content": answer})
