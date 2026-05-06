import streamlit as st
from ui.services import api
import logging

logger = logging.getLogger(__name__)

def show():
    """Display login/signup interface"""
    st.markdown('<div class="login-section">', unsafe_allow_html=True)
    st.subheader("🔐 Login to Get Started")
    st.info("Please log in or sign up to start building with NOX.")
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mode = st.radio("Select Mode", ["Login", "Sign Up"], horizontal=True)

        username = st.text_input("Username", placeholder="Enter username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if mode == "Login":
            if st.button("🚀 Login", use_container_width=True, key="login_btn"):
                _handle_login(username, password)
        else:  # Sign Up
            if st.button("Create Account", use_container_width=True, key="signup_btn"):
                _handle_signup(username, password)

        st.divider()

        if st.button("🔥 Dev Login (admin)", use_container_width=True, key="dev_login"):
            _handle_dev_login()


def _handle_login(username: str, password: str):
    """Handle login"""
    if not username or not password:
        st.warning("⚠️ Please enter credentials")
        return
    
    data = api.login(username, password)
    if data and "access_token" in data:
        st.session_state.token = data["access_token"]
        st.session_state.user_id = username.lower().strip()
        st.session_state.is_admin = False
        st.success("✅ Logged in successfully")
        st.rerun()
    else:
        st.error("❌ Invalid credentials")


def _handle_signup(username: str, password: str):
    """Handle signup"""
    if not username or not password:
        st.warning("⚠️ Please enter credentials")
        return
    
    if len(password) < 6:
        st.warning("⚠️ Password must be 6+ characters")
        return
    
    data = api.signup(username, password)
    if data:
        st.success("✅ Account created!")
    else:
        st.error("❌ Failed to create account")


def _handle_dev_login():
    """Handle dev/admin login"""
    data = api.dev_login()
    if data and "access_token" in data:
        st.session_state.token = data["access_token"]
        st.session_state.user_id = "admin"
        st.session_state.is_admin = True
        st.success("🔥 God Mode Activated")
        st.rerun()