import streamlit as st

def show_logs(logs):
    st.markdown("### ⚙️ Live Logs")
    st.code("\n".join(logs))