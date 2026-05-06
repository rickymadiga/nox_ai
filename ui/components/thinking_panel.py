import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime


# ============================================================================
# SESSION STATE INIT
# ============================================================================

def _init_state():
    if "thinking_steps" not in st.session_state:
        st.session_state.thinking_steps = []


# ============================================================================
# ADD STEP (CAN BE CALLED FROM ANYWHERE)
# ============================================================================

def add_thinking_step(
    title: str,
    content: str,
    step_type: str = "info"
):
    """
    Add a reasoning/thinking step.

    step_type:
        - info
        - tool
        - decision
        - error
    """
    _init_state()

    st.session_state.thinking_steps.append({
        "title": title,
        "content": content,
        "type": step_type,
        "time": datetime.utcnow().strftime("%H:%M:%S")
    })


# ============================================================================
# CLEAR STEPS
# ============================================================================

def clear_thinking():
    st.session_state.thinking_steps = []


# ============================================================================
# RENDER PANEL
# ============================================================================

def show_thinking(debug: bool = False):
    """
    Main UI renderer.
    Safe to import in chat_page.py
    """
    _init_state()

    with st.expander("🧠 Thinking Process", expanded=debug):

        if not st.session_state.thinking_steps:
            st.caption("No reasoning steps yet...")
            return

        for step in st.session_state.thinking_steps:
            _render_step(step)


# ============================================================================
# INTERNAL RENDER
# ============================================================================

def _render_step(step: Dict):
    step_type = step.get("type", "info")

    icon = {
        "info": "ℹ️",
        "tool": "🛠",
        "decision": "🧠",
        "error": "❌"
    }.get(step_type, "•")

    title = step.get("title", "Step")
    content = step.get("content", "")
    time = step.get("time", "")

    with st.container():
        st.markdown(f"**{icon} {title}**  \n`{time}`")
        st.markdown(content)
        st.divider()


# ============================================================================
# OPTIONAL: QUICK TRACE LOADER
# ============================================================================

def load_from_response(response: dict):
    """
    Auto-load thinking steps from backend response if available.
    Expected format:
    response["trace"] = [
        {"title": "...", "content": "...", "type": "..."}
    ]
    """
    trace = response.get("trace")

    if not trace:
        return

    clear_thinking()

    for step in trace:
        add_thinking_step(
            title=step.get("title", "Step"),
            content=step.get("content", ""),
            step_type=step.get("type", "info")
        )