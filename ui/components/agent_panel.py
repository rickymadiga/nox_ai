import streamlit as st

AGENTS = ["🧠 Planner", "🏗 Builder", "🧪 Tester", "🔧 Fixer"]

def show_agents(status_map):
    st.markdown("### 🤖 Agents")

    for agent in AGENTS:
        status = status_map.get(agent, "idle")

        if status == "working":
            st.warning(f"{agent} → Working...")
        elif status == "done":
            st.success(f"{agent} → Done")
        else:
            st.info(f"{agent} → Idle")