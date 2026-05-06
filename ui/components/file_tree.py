import streamlit as st

def render_tree(files: dict):
    st.markdown("### 📂 Project Files")

    for path, content in files.items():
        with st.expander(f"📄 {path}"):
            st.code(content, language="python")