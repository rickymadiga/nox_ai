"""Common Components"""
import streamlit as st
from config.ui import PRIMARY_GREEN

def render_status_badge(status: str):
    """Render status badge"""
    if status == "success":
        st.markdown(
            '<div class="status-badge status-success">✅ Success</div>',
            unsafe_allow_html=True
        )
    elif status == "error":
        st.markdown(
            '<div class="status-badge status-error">❌ Error</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div class="status-badge status-pending">⏳ Pending</div>',
            unsafe_allow_html=True
        )


def render_code_block(file_path: str, code: str, language: str = "python"):
    """Render code block"""
    st.markdown(f"**📄 {file_path}**")
    st.code(code, language=language, line_numbers=True)


def render_card(title: str, content: str, status: str = "default"):
    """Render card component"""
    card_class = "card"
    if status == "success":
        card_class += " card-success"
    elif status == "error":
        card_class += " card-error"
    
    st.markdown(f"""
    <div class="{card_class}">
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)


def render_metrics(metrics: dict):
    """Render metrics grid"""
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics.items()):
        with col:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)