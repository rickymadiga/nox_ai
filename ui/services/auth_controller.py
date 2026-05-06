import streamlit as st
from datetime import datetime, timedelta
from services.api import get_api_service


class AuthController:
    """Centralized authentication manager"""

    def __init__(self):
        self.api = get_api_service()

    # ------------------------------------------------------------------
    # LOGIN
    # ------------------------------------------------------------------
    def login(self, username: str, password: str) -> bool:
        response = self.api.auth.login(username, password)

        if not response or not response.success:
            return False

        # token already stored by API layer
        st.session_state.username = username
        st.session_state.login_time = datetime.now().isoformat()

        return self.verify()

    # ------------------------------------------------------------------
    # VERIFY TOKEN
    # ------------------------------------------------------------------
    def verify(self) -> bool:
        response = self.api.auth.verify_token()

        if not response or not response.success:
            self.logout()
            return False

        user = response.data.get("user", {})

        st.session_state.is_admin = user.get("is_admin", False)

        return True

    # ------------------------------------------------------------------
    # REFRESH TOKEN
    # ------------------------------------------------------------------
    def refresh(self) -> bool:
        response = self.api.auth.refresh_token()

        if response and response.success:
            token = response.data.get("token")
            if token:
                st.session_state.token = token
                return True

        return False

    # ------------------------------------------------------------------
    # LOGOUT
    # ------------------------------------------------------------------
    def logout(self):
        try:
            self.api.auth.logout()
        except:
            pass

        keys = [
            "token", "username", "is_admin",
            "login_time", "remember_until"
        ]

        for k in keys:
            st.session_state[k] = None

    # ------------------------------------------------------------------
    # STATE HELPERS
    # ------------------------------------------------------------------
    def is_authenticated(self) -> bool:
        return bool(st.session_state.get("token"))

    def is_admin(self) -> bool:
        return bool(st.session_state.get("is_admin"))