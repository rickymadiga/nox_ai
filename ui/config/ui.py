import streamlit as st

def setup_ui():
    """Setup Streamlit UI configuration."""
    st.set_page_config(
        page_title="Nox Smart World",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "Get Help": "https://github.com",
            "Report a bug": "https://github.com/issues",
            "About": "Smart Intent Router App v1.0"
        }
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main { padding-top: 2rem; }
        .sidebar .sidebar-content { padding-top: 2rem; }
        </style>
    """, unsafe_allow_html=True)