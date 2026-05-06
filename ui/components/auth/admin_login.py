"""
Admin Authentication & UI (Clean + Integrated)
Uses backend auth + preserves UI helpers
"""

import streamlit as st
import time
from datetime import datetime
from services.api import get_api_service, APIEndpoint
from services.state import AdminManager, StateManager, on_user_login

# ============================================================================
# ADMIN LOGIN UI
# ============================================================================

def show_admin_login():
    """Display admin login interface."""

    if StateManager.is_admin():
        st.success("✅ Already logged in as Admin")
        return

    st.title("🔐 Admin Panel")
    st.markdown("---")

    with st.form("admin_login_form", clear_on_submit=True):
        username = st.text_input("Admin Username")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            login_btn = st.form_submit_button("🔓 Login", use_container_width=True)

        with col2:
            back_btn = st.form_submit_button("← Back", use_container_width=True)

        if login_btn:
            handle_admin_login(username)

        if back_btn:
            st.session_state.show_admin_login = False
            st.rerun()


# ============================================================================
# LOGIN HANDLER
# ============================================================================

def handle_admin_login(username: str):
    """Authenticate admin via backend."""

    if not username:
        st.error("❌ Username required")
        return

    with st.spinner("🔐 Authenticating..."):
        api = get_api_service()

        response = api.client.post(
            APIEndpoint.ADMIN_LOGIN,
            data={"username": username},
            require_auth=False
        )

    if response and response.success:
        token = response.data.get("access_token")

        if not token:
            st.error("❌ Invalid server response")
            return

        # Store session
        st.session_state.token = token
        st.session_state.username = username
        st.session_state.is_admin = True
        st.session_state.login_time = datetime.now().isoformat()

        # Sync admin manager
        AdminManager.set_admin_user(
            username=username,
            admin_level=3,  # Full access (adjust if backend sends roles later)
            permissions=["all"]
        )

        # Sync global state
        on_user_login(username, f"{username}@admin.local", token, is_admin=True)

        st.success(f"✅ Welcome Admin {username}")
        st.balloons()

        time.sleep(1)
        st.rerun()

    else:
        error = response.error if response else "No response"
        st.error(f"❌ Login failed: {error}")


# ============================================================================
# ADMIN HEADER
# ============================================================================

def show_admin_panel_header():
    """Display admin panel header."""

    admin_state = AdminManager.get_admin_state()

    if not admin_state.is_admin:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👤 Role", get_admin_level_name(admin_state.admin_level))

    with col2:
        st.metric("🔐 Status", "Active")

    with col3:
        if admin_state.admin_login_time:
            login_time = datetime.fromisoformat(admin_state.admin_login_time)
            duration = datetime.now() - login_time
            st.metric("⏱ Session", f"{int(duration.total_seconds()/60)} min")

    with col4:
        st.metric("🔑 Permissions", len(admin_state.admin_permissions))


# ============================================================================
# PERMISSIONS UI
# ============================================================================

def show_admin_permissions():
    """Display permissions."""

    admin_state = AdminManager.get_admin_state()

    if not admin_state.is_admin:
        st.warning("⚠️ Not authenticated as admin")
        return

    st.subheader("🔑 Permissions")

    if admin_state.admin_permissions:
        for perm in admin_state.admin_permissions:
            st.write(f"✅ {perm}")
    else:
        st.write("No permissions assigned")


# ============================================================================
# ACCESS CONTROL PANEL
# ============================================================================

def render_admin_access_control():
    """Render admin access control UI."""

    if not is_admin_authenticated():
        st.warning("⚠️ Admin access required")
        return

    st.subheader("🔐 Access Control")

    admin_state = AdminManager.get_admin_state()

    st.info(f"Level: {get_admin_level_name(admin_state.admin_level)}")

    features = []

    if admin_state.admin_level >= 2:
        features.append("👥 User Management")

    if admin_state.admin_level >= 3:
        features.append("⚙️ System Settings")

    for f in features:
        st.write(f"✅ {f}")


# ============================================================================
# SESSION INFO
# ============================================================================

def render_admin_session_info():
    """Render admin session info."""

    admin_state = AdminManager.get_admin_state()

    if not admin_state.is_admin:
        return

    with st.expander("📊 Session Info"):
        st.write(f"User: {admin_state.username}")
        st.write(f"Level: {get_admin_level_name(admin_state.admin_level)}")

        if admin_state.admin_login_time:
            st.write(f"Login: {admin_state.admin_login_time}")


# ============================================================================
# LOGOUT
# ============================================================================

def handle_admin_logout():
    """Logout admin."""

    AdminManager.clear_admin()

    st.session_state.token = None
    st.session_state.username = None
    st.session_state.is_admin = False

    st.success("✅ Logged out")
    time.sleep(1)
    st.rerun()


# ============================================================================
# HELPERS
# ============================================================================

def get_admin_level_name(level: int) -> str:
    return {
        0: "User",
        1: "Moderator",
        2: "Admin",
        3: "Super Admin"
    }.get(level, "Unknown")


def is_admin_authenticated() -> bool:
    admin_state = AdminManager.get_admin_state()
    return admin_state.is_admin