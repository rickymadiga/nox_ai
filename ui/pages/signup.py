import streamlit as st
import time

def show():
    st.title("📝 Create Account")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Already have an account?")
        st.markdown("[Go to Login](/?page=login)")
    
    with col2:
        st.markdown("### Sign up to NOX")
        
        with st.form("signup_form"):
            username = st.text_input(
                "Username",
                placeholder="Choose a username",
                key="signup_username"
            )
            
            email = st.text_input(
                "Email",
                placeholder="your@email.com",
                key="signup_email"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Strong password",
                key="signup_password"
            )
            
            password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Repeat password",
                key="signup_password_confirm"
            )
            
            terms = st.checkbox("I agree to the terms of service")
            
            submit = st.form_submit_button("🚀 Create Account", use_container_width=True)
        
        if submit:
            # Validation
            if not all([username, email, password, password_confirm]):
                st.error("⚠️ Please fill all fields")
                return
            
            if len(username) < 3:
                st.error("⚠️ Username must be at least 3 characters")
                return
            
            if len(password) < 8:
                st.error("⚠️ Password must be at least 8 characters")
                return
            
            if password != password_confirm:
                st.error("⚠️ Passwords do not match")
                return
            
            if not terms:
                st.error("⚠️ Please accept terms of service")
                return
            
            # Sign up
            api = st.session_state.api
            
            with st.spinner("🔄 Creating account..."):
                res = api.signup(username, email, password, password_confirm)
            
            if res and res.get("success"):
                st.success("✅ Account created! Redirecting to login...")
                time.sleep(1)
                st.session_state.page = "login"
                st.rerun()
            else:
                error = res.get("error") if res else "Unknown error"
                st.error(f"❌ {error}")