import streamlit as st
import requests
import time
from datetime import datetime
from collections import deque

# ═════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════
API_BASE = "http://localhost:8000/api"

st.set_page_config(
    layout="wide", 
    page_title="NOX Workspace",
    initial_sidebar_state="expanded"
)

# ═════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═════════════════════════════════════════════
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "user": None,
        "token": None,
        "messages": [],
        "streaming": False,
        "live_logs": deque(maxlen=100),
        "ws_connected": False,
        "chat_history": [],
        "last_response": None,
        "page": "chat",
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()

# ═════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════
def get_headers():
    """Get authorization headers"""
    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_post(endpoint, data):
    """Make POST request to API"""
    try:
        response = requests.post(
            f"{API_BASE}{endpoint}",
            json=data,
            headers=get_headers(),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server. Is it running?")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timeout. Server took too long to respond.")
        return None
    except requests.exceptions.HTTPError as e:
        try:
            error_msg = e.response.json().get("detail", str(e))
        except:
            error_msg = str(e)
        st.error(f"❌ Server error: {error_msg}")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def api_get(endpoint):
    """Make GET request to API"""
    try:
        response = requests.get(
            f"{API_BASE}{endpoint}",
            headers=get_headers(),
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server.")
        return None
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


# ═════════════════════════════════════════════
# AUTH SECTION
# ═════════════════════════════════════════════
def show_auth_sidebar():
    """Show authentication in sidebar"""
    st.sidebar.title("🔐 Authentication")

    if not st.session_state.token:
        auth_tab = st.sidebar
        
        username = auth_tab.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username"
        )
        password = auth_tab.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        col1, col2 = auth_tab.columns(2)
        
        with col1:
            if st.button("🔓 Login", use_container_width=True):
                if not username or not password:
                    st.sidebar.error("⚠️ Please enter credentials")
                else:
                    with st.spinner("🔄 Logging in..."):
                        res = api_post("/auth/login", {
                            "username": username,
                            "password": password
                        })
                    
                    if res and res.get("success"):
                        st.session_state.token = res["data"]["token"]
                        st.session_state.user = res["data"]["user"].get("username", username)
                        st.sidebar.success("✅ Logged in!")
                        time.sleep(0.5)
                        st.rerun()
                    elif res:
                        st.sidebar.error(f"❌ {res.get('error', 'Login failed')}")
        
        with col2:
            if st.button("📝 Sign Up", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
    else:
        # Show logged-in user
        st.sidebar.markdown("---")
        st.sidebar.success(f"👤 **{st.session_state.user}**")
        
        if st.sidebar.button("🔓 Logout", use_container_width=True):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.messages = []
            st.session_state.page = "chat"
            st.sidebar.info("✅ Logged out")
            time.sleep(0.5)
            st.rerun()
        
        st.sidebar.markdown("---")


# ═════════════════════════════════════════════
# PAGE COMPONENTS
# ═════════════════════════════════════════════

def show_chat_page():
    """Chat page"""
    st.title("⚡ NOX Workspace - Chat")

    left, right = st.columns([3, 1], gap="medium")

    # RIGHT PANEL → LIVE LOGS
    with right:
        st.subheader("📊 Live Activity")
        
        log_container = st.container(border=True, height=500)
        
        with log_container:
            if st.session_state.live_logs:
                for i, log in enumerate(st.session_state.live_logs, 1):
                    if isinstance(log, dict):
                        log_text = log.get("message", str(log))
                    else:
                        log_text = str(log)
                    
                    if "error" in log_text.lower() or "❌" in log_text:
                        st.error(f"{i}. {log_text}")
                    elif "warning" in log_text.lower() or "⚠️" in log_text:
                        st.warning(f"{i}. {log_text}")
                    elif "success" in log_text.lower() or "✅" in log_text:
                        st.success(f"{i}. {log_text}")
                    else:
                        st.text(f"{i}. {log_text}")
            else:
                st.info("💤 Waiting for activity...")
        
        if st.button("🔄 Refresh Logs", use_container_width=True):
            st.rerun()

    # LEFT PANEL → CHAT
    with left:
        st.subheader("💬 Chat History")
        
        def render_response(res):
            """Render API response - Enhanced with Video support"""
            if not res:
                st.error("❌ Invalid response")
                return
            
            action = (res.get("action") or res.get("type") or "chat").lower().strip()
            response_type = res.get("type", "message")
            job_id = res.get("job_id") or res.get("data", {}).get("job_id")
            video_url = res.get("data", {}).get("video_url")

            # Icons
            icons = {
                "chat": "💬",
                "quote": "💰",
                "build": "📦",
                "debug": "🔧",
                "research": "🔬",
                "content_generator": "🎨",
                "video": "🎬",
                "image": "🖼️",
                "message": "💬",
            }
            
            icon = icons.get(action, icons.get(response_type, "❓"))
            
            st.markdown(f"### {icon} {action.upper() or response_type.upper()}")

            # Main response text
            response_text = res.get("response") or res.get("message") or "No response text"
            st.write(response_text)

            # Status and Type
            col1, col2 = st.columns(2)
            with col1:
                st.caption(f"📊 Status: `{res.get('status', 'unknown')}`")
            with col2:
                st.caption(f"📋 Type: `{response_type}`")

            # ==================== VIDEO JOB HANDLING ====================
            if action in ["content_generator", "video"] or response_type == "video":
                st.markdown("### 🎬 Video Generation Job")
                
                job_id = res.get("job_id") or res.get("data", {}).get("job_id")
                video_url = res.get("data", {}).get("video_url") or res.get("video_url")

                if job_id:
                    st.success(f"**Job ID:** `{job_id}`")
                
                if video_url:
                    st.success("✅ Video Ready!")
                    
                    # Play video
                    try:
                        st.video(video_url)
                    except Exception as play_error:
                        st.warning(f"Player error: {play_error}")
                        st.markdown(f"[▶️ Open Video]({video_url})")
                    
                    # DOWNLOAD - Force byte download
                    try:
                        import requests
                        with st.spinner("Preparing full video download..."):
                            video_bytes = requests.get(video_url, timeout=30).content
                        
                        st.download_button(
                            label="⬇️ Download Full MP4",
                            data=video_bytes,
                            file_name=f"video_{job_id}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
                    except Exception as download_error:
                        st.error(f"Download failed: {download_error}")
                        st.markdown(f"[Direct Link]({video_url})")
                else:
                    st.info("⏳ Video is being generated...")
                    with st.expander("Job Details"):
                        st.json(res.get("data", {}))      

            # ==================== IMAGE ====================
            elif action == "content_generator" and response_type == "image":
                data = res.get("data", {})
                if data.get("url"):
                    st.image(data["url"], caption="Generated Image", use_column_width=True)

            # ==================== DEBUG / CODE ====================
            elif action in ["debug", "code_result"]:
                if res.get("analysis"):
                    st.markdown("#### 🔍 Analysis")
                    st.write(res.get("analysis"))
                if res.get("root_cause"):
                    st.markdown("#### 🎯 Root Cause")
                    st.error(res.get("root_cause"))
                updated_files = res.get("updated_files", {})
                if updated_files:
                    with st.expander(f"📄 Updated Files ({len(updated_files)})"):
                        for filename, code in updated_files.items():
                            st.code(code, language="python", line_numbers=True)

            # ==================== BUILD ====================
            if action == "build" or res.get("zip"):
                zip_data = res.get("zip")
                if zip_data:
                    st.markdown("#### 📦 Build Output")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Filename", zip_data.get("filename", "nox_app.zip"))
                    with col2:
                        size_kb = zip_data.get("size", 0) / 1024
                        st.metric("Size", f"{size_kb:.2f} KB")
                    try:
                        import base64
                        zip_bytes = base64.b64decode(zip_data.get("data", ""))
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_bytes,
                            file_name=zip_data.get("filename", "nox_app.zip"),
                            mime="application/zip",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"❌ Download error: {str(e)}")

            # ==================== LOGS ====================
            logs = res.get("logs", [])
            if logs:
                with st.expander(f"📜 Logs ({len(logs)})", expanded=False):
                    for log in logs[-30:]:
                        if isinstance(log, dict):
                            st.text(log.get("message", str(log)))
                        else:
                            st.text(str(log))

            if res.get("price"):
                st.warning(f"💰 Cost: {res.get('price')} credits")
        
        # Render chat history
        for i, msg in enumerate(st.session_state.messages):
            with st.chat_message("user"):
                st.write(f"**You:** {msg['prompt']}")
            
            with st.chat_message("assistant"):
                render_response(msg["response"])
            
            st.divider()

    st.divider()

    prompt = st.chat_input("Ask NOX...")

    if prompt:
        with st.chat_message("user"):
            st.write(f"**You:** {prompt}")
        
        with st.chat_message("assistant"):
            with st.spinner("⚙️ NOX is thinking..."):
                res = api_post("/chat/message", {"prompt": prompt})
            
            if res:
                st.session_state.messages.append({
                    "prompt": prompt,
                    "response": res,
                    "timestamp": datetime.now().isoformat()
                })
                st.session_state.last_response = res
                render_response(res)
                st.rerun()
            else:
                st.error("❌ Failed to get response")


def show_signup_page():
    """Sign up page"""
    st.title("📝 Create Account")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### Already have an account?")
        if st.button("← Back to Login", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()
    
    with col2:
        st.markdown("### Sign up to NOX")
        
        with st.form("signup_form"):
            username = st.text_input(
                "Username",
                placeholder="Choose a username",
            )
            
            email = st.text_input(
                "Email",
                placeholder="your@email.com",
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Strong password",
            )
            
            password_confirm = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Repeat password",
            )
            
            terms = st.checkbox("I agree to the terms of service")
            
            submit = st.form_submit_button("🚀 Create Account", use_container_width=True)
        
        if submit:
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
            
            with st.spinner("🔄 Creating account..."):
                res = api_post("/auth/signup", {
                    "username": username,
                    "email": email,
                    "password": password
                })
            
            if res and res.get("success"):
                st.success("✅ Account created! Redirecting to login...")
                time.sleep(1)
                st.session_state.page = "chat"
                st.rerun()
            else:
                error = res.get("error") if res else "Unknown error"
                st.error(f"❌ {error}")


def show_editor_page():
    """Code editor page"""
    st.title("📝 Code Editor")
    
    if not st.session_state.token:
        st.warning("🔐 Please login first")
        st.stop()
    
    last_res = st.session_state.get("last_response")
    
    if not last_res or not last_res.get("updated_files"):
        st.info("💡 No code to edit. Start a chat to get code suggestions!")
        return
    
    st.subheader("✏️ Edit Generated Code")
    
    updated_files = last_res.get("updated_files", {})
    
    if not updated_files:
        st.warning("No files to edit")
        return
    
    tabs = st.tabs([f"📄 {fname}" for fname in updated_files.keys()])
    
    edited_code = {}
    
    for tab, (filename, code) in zip(tabs, updated_files.items()):
        with tab:
            st.markdown(f"**File:** `{filename}`")
            
            edited = st.text_area(
                f"Edit {filename}",
                value=code,
                height=400,
                key=f"editor_{filename}",
                label_visibility="collapsed"
            )
            
            edited_code[filename] = edited
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📋 Copy {filename}", use_container_width=True):
                    st.success(f"✅ Copied {filename}")
            with col2:
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=edited,
                    file_name=filename,
                    mime="text/plain",
                    use_container_width=True,
                    key=f"dl_{filename}"
                )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save All Changes", use_container_width=True):
            st.session_state.edited_files = edited_code
            st.success("✅ Changes saved locally")
    
    with col2:
        if st.button("🔄 Reset All", use_container_width=True):
            st.rerun()


def show_downloads_page():
    """Downloads page"""
    st.title("📥 Downloads")
    
    if not st.session_state.token:
        st.warning("🔐 Please login first")
        st.stop()
    
    st.subheader("💾 Your Builds & Exports")
    
    tab1, tab2, tab3 = st.tabs(["📦 Latest", "📜 History", "⚙️ Settings"])
    
    with tab1:
        st.markdown("### 🏗️ Latest Build")
        
        with st.spinner("📥 Fetching latest build..."):
            latest = api_post("/download/download/latest", {})
        
        if latest and latest.get("success"):
            st.success("✅ Build found!")
            
            zip_data = latest.get("zip")
            if zip_data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📁 Filename", zip_data.get("filename", "N/A"))
                with col2:
                    size_kb = zip_data.get("size", 0) / 1024
                    st.metric("💾 Size", f"{size_kb:.2f} KB")
                with col3:
                    st.metric("📊 Status", "Ready")
                
                st.divider()
                
                try:
                    import base64
                    zip_bytes = base64.b64decode(zip_data.get("data", ""))
                    st.download_button(
                        label="⬇️ Download Latest Build",
                        data=zip_bytes,
                        file_name=zip_data.get("filename", "nox_app.zip"),
                        mime="application/zip",
                        use_container_width=True,
                        key="download_latest"
                    )
                    st.success("✅ Ready for download")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.info("ℹ️ No build available yet")
    
    with tab2:
        st.markdown("### 📜 Build History")
        st.info("ℹ️ History feature coming soon")
    
    with tab3:
        st.markdown("### ⚙️ Settings")
        st.info("⚙️ Settings coming soon")


# ═════════════════════════════════════════════
# MAIN APP
# ═════════════════════════════════════════════

show_auth_sidebar()

# Auth guard
if not st.session_state.token and st.session_state.page != "signup":
    st.warning("🔐 Please login to continue")
    st.stop()

# Page routing
pages = {
    "chat": show_chat_page,
    "editor": show_editor_page,
    "downloads": show_downloads_page,
    "signup": show_signup_page,
}

# Navigation
if st.session_state.token:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📱 Pages")
    
    cols = st.sidebar.columns(3)
    with cols[0]:
        if st.button("💬 Chat", use_container_width=True, key="nav_chat"):
            st.session_state.page = "chat"
            st.rerun()
    with cols[1]:
        if st.button("✏️ Editor", use_container_width=True, key="nav_editor"):
            st.session_state.page = "editor"
            st.rerun()
    with cols[2]:
        if st.button("📥 Downloads", use_container_width=True, key="nav_downloads"):
            st.session_state.page = "downloads"
            st.rerun()
    
    st.sidebar.markdown("---")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.messages = []
            st.info("✅ Cleared")
            st.rerun()
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Stats")
    st.sidebar.metric("Messages", len(st.session_state.messages))
    st.sidebar.metric("Logs", len(st.session_state.live_logs))

# Show current page
page = st.session_state.get("page", "chat")
if page in pages:
    pages[page]()
else:
    show_chat_page()