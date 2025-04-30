import os
import sys
# Set environment variable to disable file watcher for packages
os.environ["STREAMLIT_SERVER_WATCH_DIRS"] = "false"

import streamlit as st
from retriever import retrieve_chunks
from generator import generate_answer

st.set_page_config(page_title="Restaurant Chatbot", layout="wide")
st.title("🍽️ Restaurant Query Assistant")

query = st.text_input("Ask a question about any restaurant:", placeholder="e.g. What are the vegetarian dishes at Citrus?")

if query:
    with st.spinner("Retrieving information..."):
        chunks = retrieve_chunks(query, top_k=5)
        answer = generate_answer(query, chunks)

    st.subheader("Answer")
    st.markdown(answer)

    st.subheader("Top 5 Retrieved Chunks")
    for i, chunk in enumerate(chunks, 1):
        st.markdown(f"**{i}.** {chunk}")
