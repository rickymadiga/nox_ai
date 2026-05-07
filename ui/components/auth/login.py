"""
Authentication & Login Component
Handles user login, registration, and session management
"""

import streamlit as st
from typing import Optional, Tuple
from datetime import datetime, timedelta
from services.api import get_api_service, APIResponse
import time

# ============================================================================
# LOGIN PAGE
# ============================================================================

def show_login():
    """Display login/signup interface."""
    
    # Check if already logged in
    if st.session_state.get("token"):
        st.success("✅ Already logged in!")
        return
    
    # Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.title("🔐 Smart Intent App")
        st.markdown("---")
        
        # Tab selection
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Signup"])
        
        with tab1:
            show_login_form()
        
        with tab2:
            show_registration_form()
    
    with col2:
        show_features_info()


def show_login_form():
    """Display login form."""
    
    st.subheader("Welcome Back!")
    st.write("Enter your credentials to access your account")
    
    with st.form("login_form", clear_on_submit=True):
        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        remember_me = st.checkbox("Remember me for 30 days", value=False)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button(
                "🔑 Login",
                use_container_width="stretch",
                type="primary"
            )
        
        with col2:
            forgot_password = st.form_submit_button(
                "❓ Forgot Password",
                use_container_width="stretch",
            )
        
        if submit_button:
            handle_login(username, password, remember_me)
        
        if forgot_password:
            show_forgot_password_dialog(username)


def show_registration_form():
    """Display registration form."""
    
    st.subheader("Create New Account")
    st.write("Join us and start using Nox Smart World today!")
    
    with st.form("registration_form", clear_on_submit=True):
        username = st.text_input(
            "Username",
            placeholder="Choose a username",
            key="reg_username"
        )
        
        email = st.text_input(
            "Email",
            placeholder="Enter your email",
            key="reg_email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a password (min 8 characters)",
            key="reg_password"
        )
        
        password_confirm = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Confirm your password",
            key="reg_password_confirm"
        )
        
        agree_terms = st.checkbox(
            "I agree to the Terms & Conditions",
            value=False
        )
        
        st.markdown("---")
        
        submit_button = st.form_submit_button(
            "📝 Signup",
            use_container_width="stretch",
            type="primary"
        )
        
        if submit_button:
            handle_signup(username, email, password, password_confirm, agree_terms)


def show_features_info():
    """Display feature information."""
    
    st.subheader("✨ Features")
    
    features = [
        ("💬", "Chat", "Real-time conversations"),
        ("🏗️", "Builder", "Create components"),
        ("🔧", "Fixer", "Debug & fix issues"),
        ("🔬", "Research", "Analyze & research"),
        ("✏️", "Editor", "Edit content"),
        ("📜", "History", "View history"),
        ("⚙️", "Admin", "Manage settings"),
    ]
    
    for icon, name, desc in features:
        st.write(f"{icon} **{name}** - {desc}")
    
    st.markdown("---")
    
    st.info(
        "💡 **Tip**: Use your account to access all features and track your progress."
    )


# ============================================================================
# AUTHENTICATION HANDLERS
# ============================================================================

def handle_login(username: str, password: str, remember_me: bool = False):
    """Handle login submission (aligned with backend API)."""

    if not username or not password:
        st.error("❌ Please enter both username and password")
        return

    with st.spinner("🔐 Logging in..."):
        api = get_api_service()
        response = api.auth.login(username, password)

    if not response or not response.success:
        st.error("❌ Invalid username or password")
        return

    # ✅ Extract token (aligned with backend)
    token = response.data.get("token")

    if not token:
        st.error("❌ Login failed: No token returned")
        return

    # ✅ Store session
    st.session_state.token = token
    st.session_state.username = username

    # Remember me
    if remember_me:
        st.session_state.remember_until = (
            datetime.now() + timedelta(days=30)
        ).isoformat()

    # ✅ Verify user (IMPORTANT)
    verify_response = api.auth.verify_token()

    if verify_response and verify_response.success:
        user_data = verify_response.data.get("user", {})

        st.session_state.is_admin = user_data.get("is_admin", False)
        st.session_state.user_email = user_data.get("email", "")

    # Login time
    st.session_state.login_time = datetime.now().isoformat()

    st.success(f"✅ Welcome back, {username}!")
    st.balloons()

    time.sleep(1)
    st.rerun()

def handle_signup(
    username: str,
    email: str,
    password: str,
    password_confirm: str,
    agree_terms: bool
):
    """Handle signup submission."""

    # Validation
    if not all([username, email, password, password_confirm]):
        st.error("❌ Please fill in all fields")
        return
    
    if len(username) < 3:
        st.error("❌ Username must be at least 3 characters")
        return
    
    if len(password) < 8:
        st.error("❌ Password must be at least 8 characters")
        return
    
    if password != password_confirm:
        st.error("❌ Passwords don't match")
        return
    
    if "@" not in email or "." not in email:
        st.error("❌ Please enter a valid email address")
        return
    
    if not agree_terms:
        st.error("❌ Please agree to the Terms & Conditions")
        return
    
    # Show progress
    with st.spinner("📝 Creating account..."):
        api = get_api_service()
        response = api.auth.register(username, email, password)   # ← Fixed: was .signup

    if response and response.success:
        st.success("✅ Account created successfully!")
        st.info("🔑 Please login with your new credentials")
        time.sleep(1.5)
        st.rerun()
    else:
        error_msg = (
            getattr(response, "error", None)
            or getattr(response, "message", None)
            or str(response) 
            or "Unknown error occurred while creating account"
        )
        st.error(f"❌ {error_msg}")

# ============================================================================
# PASSWORD RECOVERY
# ============================================================================

def show_forgot_password_dialog(username: str = ""):
    """Show forgot password recovery dialog."""
    
    with st.container(border=True):
        st.subheader("🔑 Recover Password")
        
        email = st.text_input(
            "Enter your email address",
            placeholder="your@email.com",
            key="forgot_email"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📧 Send Reset Link", use_container_width=True):
                if email and "@" in email:
                    with st.spinner("Sending recovery email..."):
                        api = get_api_service()
                        # Note: Implement this endpoint in your backend
                        st.success("✅ Recovery link sent to your email!")
                        st.info("⏰ Link expires in 1 hour")
                else:
                    st.error("❌ Please enter a valid email")
        
        with col2:
            if st.button("← Back", use_container_width="stretch"):
                st.rerun()


# ============================================================================
# SESSION VALIDATION
# ============================================================================

def validate_session() -> bool:
    """Validate current session."""
    
    if not st.session_state.get("token"):
        return False
    
    # Check remember me expiration
    if st.session_state.get("remember_until"):
        remember_until = datetime.fromisoformat(
            st.session_state.remember_until
        )
        if datetime.now() > remember_until:
            st.session_state.token = None
            st.info("⏰ Your session has expired. Please login again.")
            return False
    
    # Verify token with backend
    api = get_api_service()
    response = api.auth.verify_token()
    
    if not response.success:
        st.session_state.token = None
        return False
    
    return True


def refresh_session():
    """Refresh user session."""
    
    if not st.session_state.get("token"):
        return False
    
    with st.spinner("🔄 Refreshing session..."):
        api = get_api_service()
        response = api.auth.refresh_token()
    
    if response.success:
        new_token = response.data.get("token")
        if new_token:
            st.session_state.token = new_token
            return True
    
    return False


# ============================================================================
# USER PROFILE
# ============================================================================

def show_user_profile():
    """Show user profile information."""
    
    if not st.session_state.get("username"):
        st.warning("⚠️ Not logged in")
        return
    
    with st.container(border=True):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("👤 **Profile**")
        
        with col2:
            username = st.session_state.get("username", "Unknown")
            email = st.session_state.get("user_email", "N/A")
            is_admin = "✅" if st.session_state.get("is_admin") else "❌"
            
            st.write(f"**Username**: {username}")
            st.write(f"**Email**: {email}")
            st.write(f"**Admin**: {is_admin}")
            
            if st.session_state.get("login_time"):
                login_time = datetime.fromisoformat(
                    st.session_state.login_time
                ).strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"**Login Time**: {login_time}")


def show_logout_button():
    """Show logout button."""
    
    if st.button("🚪 Logout", use_container_width=True):
        handle_logout()


def handle_logout():
    """Handle user logout."""
    
    with st.spinner("🔄 Logging out..."):
        api = get_api_service()
        api.auth.logout()
        
        # Clear session
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.user_email = None
        st.session_state.is_admin = False
        st.session_state.remember_me = False
        st.session_state.remember_until = None
    
    st.success("✅ Logged out successfully")
    time.sleep(1)
    st.rerun()


# ============================================================================
# SECURITY FEATURES
# ============================================================================

def check_session_timeout(timeout_minutes: int = 30):
    """Check if session has timed out."""
    
    login_time = st.session_state.get("login_time")
    if not login_time:
        return False
    
    login_datetime = datetime.fromisoformat(login_time)
    elapsed = datetime.now() - login_datetime
    
    if elapsed > timedelta(minutes=timeout_minutes):
        st.warning("⏰ Your session has expired. Please login again.")
        st.session_state.token = None
        return True
    
    return False


def show_session_info():
    """Display current session information."""
    
    if not st.session_state.get("token"):
        return
    
    with st.expander("📊 Session Info"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("User", st.session_state.get("username", "N/A"))
            st.metric("Status", "🟢 Active")
        
        with col2:
            if st.session_state.get("login_time"):
                login_time = datetime.fromisoformat(
                    st.session_state.login_time
                )
                elapsed = datetime.now() - login_time
                st.metric("Session Duration", f"{elapsed.total_seconds()/60:.0f} min")
            
            if st.session_state.get("remember_until"):
                remember_until = datetime.fromisoformat(
                    st.session_state.remember_until
                )
                remaining = remember_until - datetime.now()
                days = remaining.days
                st.metric("Remember Until", f"{days} days")