import streamlit as st

def prompt_input(label="Enter prompt"):
    st.markdown("### 🧠 Input")
    return st.text_area(label)