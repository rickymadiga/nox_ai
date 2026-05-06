
from turtle import st


api = st.session_state.api

if api.health():
    st.sidebar.success("🟢 Backend connected")
else:
    st.sidebar.warning("🟡 Backend offline")