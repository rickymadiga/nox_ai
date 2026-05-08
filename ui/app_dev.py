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
    """Make POST request to API with better token handling"""
    try:
        headers = get_headers()
        
        response = requests.post(
            f"{API_BASE}{endpoint}",
            json=data,
            headers=headers,
            timeout=45
        )
        
        # Handle token expiration
        if response.status_code == 401:
            st.error("🔐 Session expired. Please login again.")
            st.session_state.token = None
            st.session_state.user = None
            time.sleep(1)
            st.rerun()
            return None
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to server. Is it running?")
        return None
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            st.error("🔐 Invalid or expired token. Please login again.")
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()
            return None
        try:
            error_detail = e.response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        st.error(f"❌ Server error: {error_detail}")
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
    """Enhanced Pre-Login Experience"""
    st.sidebar.title("🔐 NOX Workspace")

    if not st.session_state.token:
        st.sidebar.markdown("### Welcome to NOX")
        st.sidebar.markdown("The AI Agentic Workspace")

        # Hero-like info in sidebar
        st.sidebar.markdown("""
        ---
        **🚀 What you can do:**
        - Build full apps with one prompt
        - Debug & fix code instantly  
        - Research any topic with sources
        - Generate images & videos
        - Smart AI assistant
        """)

        st.sidebar.markdown("---")

        # Login Form
        username = st.sidebar.text_input("Username", placeholder="Enter username", key="login_username")
        password = st.sidebar.text_input("Password", type="password", placeholder="Enter password", key="login_password")

        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔓 Login", width="stretch"):
                if not username or not password:
                    st.sidebar.error("Please enter credentials")
                else:
                    with st.spinner("Logging in..."):
                        res = api_post("/auth/login", {"username": username, "password": password})
                    
                    if res and res.get("success"):
                        st.session_state.token = res["data"]["token"]
                        st.session_state.user = res["data"]["user"].get("username", username)
                        st.sidebar.success("✅ Login successful!")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Invalid credentials")

        with col2:
            if st.button("📝 Sign Up", width="stretch"):
                st.session_state.page = "signup"
                st.rerun()

        # Feature highlights
        st.sidebar.markdown("---")
        st.sidebar.caption("✨ Powered by advanced AI agents")

    else:
        # Logged in user
        st.sidebar.success(f"👤 **{st.session_state.user}**")
        if st.sidebar.button("🔓 Logout", width="stretch"):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.messages = []
            st.rerun()


# ═════════════════════════════════════════════
# PAGE COMPONENTS
# ═════════════════════════════════════════════

def show_landing_page():
    """Beautiful pre-login landing page"""
    st.title("⚡ Welcome to NOX")
    st.markdown("### The Intelligent AI Workspace")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        **Build faster. Think deeper.**

        NOX combines powerful AI agents to help you:
        - Create full applications from a single prompt
        - Research any topic with real sources
        - Debug and fix code automatically
        - Generate content, images & videos
        """)

        if st.button("🚀 Get Started - Login Now", type="primary", width="stretch"):
            st.info("👈 Use the login form in the sidebar")

    with col2:
        # Fixed: use 'use_container_width' instead of deprecated 'use_column_width'
        st.image(
            "https://picsum.photos/600/400", 
            caption="AI Workspace",
            width="stretch"
        )

    # Feature cards
    st.markdown("### ✨ Core Features")
    cols = st.columns(3)

    with cols[0]:
        st.metric("🏗️", "App Builder", "Turn ideas into working apps")
    with cols[1]:
        st.metric("🔬", "Deep Research", "With real web sources")
    with cols[2]:
        st.metric("🛠️", "Code Assistant", "Debug + Fix instantly")

    st.divider()
    st.caption("Login to start building with AI agents")

def show_chat_page():
    """Chat page"""
    st.title("⚡ NOX Workspace - Chat")

    # Mobile Optimization
    if st.session_state.get("page") == "chat":
        st.markdown("""
            <style>
                .stMarkdown, .stExpander, .element-container {
                    max-width: 100% !important;
                }
                .stButton button {
                    width: 100%;
                }
                @media (max-width: 768px) {
                    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
                        font-size: 1.4rem !important;
                    }
                }
            </style>
        """, unsafe_allow_html=True)

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
        
        if st.button("🔄 Refresh Logs", width="stretch"):
            st.rerun()

    # LEFT PANEL → CHAT
    with left:
        st.subheader("💬 Chat History")
        
        def render_response(res):
            """Render API response - Enhanced with Video support"""

            action = (res.get("action") or res.get("type") or "chat").lower().strip()
            response_type = res.get("type", "message")
            
            # Force build_result type if zip is present
            if res.get("zip") and not action.startswith("build"):
                action = "build"
                response_type = "build_result"

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
                            use_container_width="stretch",
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
                    st.image(data["url"], caption="Generated Image", use_column_width="content")

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

            # ==================== RESEARCH - MOBILE OPTIMIZED ====================
            elif action == "research" or response_type == "research_result":
                st.markdown("### 🔬 Research Results")
                
                query = res.get("research_query") or res.get("prompt", "Your search")
                st.markdown(f"**Query:** `{query}`")
                
                # Main Response / Answer
                main_text = res.get("response", "")
                if main_text and len(main_text) > 10:
                    st.markdown(main_text)
                
                # Summary
                summary = res.get("summary") or res.get("data", {}).get("summary", "")
                if summary:
                    st.markdown(summary)
                
                # Key Findings
                key_findings = res.get("key_findings", []) or res.get("data", {}).get("key_findings", [])
                if key_findings:
                    st.markdown("#### 🔑 Key Findings")
                    for finding in key_findings[:5]:
                        st.markdown(f"• {finding}")
                
                # Sources - Mobile Friendly
                sources = res.get("sources", []) or res.get("data", {}).get("sources", [])
                if sources:
                    with st.expander(f"📚 Sources ({len(sources)})", expanded=False):
                        for i, source in enumerate(sources[:8], 1):
                            title = source.get("title", "Source")
                            content = (source.get("content") or "")[:220]
                            url = source.get("url", "")
                            
                            st.markdown(f"**{i}. {title}**")
                            if content:
                                st.caption(content + "...")
                            
                            if url and url.startswith("http"):
                                st.markdown(f"[🔗 Open Source]({url})")
                            st.divider()
                
                # Conclusions & Recommendations - Better on mobile
                conclusions = res.get("conclusions", []) or res.get("data", {}).get("conclusions", [])
                if conclusions:
                    st.markdown("#### 🎯 Conclusions")
                    for c in conclusions:
                        st.success(f"• {c}")
                
                recommendations = res.get("recommendations", []) or res.get("data", {}).get("recommendations", [])
                if recommendations:
                    st.markdown("#### 💡 Recommendations")
                    for r in recommendations:
                        st.info(f"• {r}")
                
                # Raw Data (collapsed by default)
                with st.expander("🔍 Debug - Full Data", expanded=False):
                    st.json({k: v for k, v in res.items() if k != "logs"})

            # ==================== BUILD ====================
            if action == "build" or response_type == "build_result" or res.get("zip"):
                zip_data = res.get("zip")
                if zip_data and isinstance(zip_data, dict) and zip_data.get("data"):
                    st.markdown("#### 📦 Build Output - Ready to Download")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📁 Filename", zip_data.get("filename", "nox_app.zip"))
                    with col2:
                        size_kb = zip_data.get("size", 0) / 1024
                        st.metric("💾 Size", f"{size_kb:.2f} KB")
                    
                    try:
                        import base64
                        zip_bytes = base64.b64decode(zip_data.get("data", ""))
                        st.download_button(
                            label="⬇️ Download ZIP",
                            data=zip_bytes,
                            file_name=zip_data.get("filename", "nox_app.zip"),
                            mime="application/zip",
                            width="stretch",
                            key=f"download_{int(time.time())}"  # prevent duplicate key
                        )
                        st.success("✅ ZIP Ready!")
                    except Exception as e:
                        st.error(f"❌ Download preparation failed: {str(e)}")
                        if zip_data.get("download_url"):
                            st.markdown(f"[🔗 Direct Download]({zip_data['download_url']})")
                else:
                    st.warning("⚠️ Build completed but ZIP data is missing")

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
    """Fixed & Improved Sign Up Page"""
    st.title("📝 Create Account")
    
    # Back button
    if st.button("← Back to Login", width="stretch"):
        st.session_state.page = "chat"
        st.rerun()

    st.markdown("### Sign up to NOX")

    with st.form("signup_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", placeholder="Choose a username")
            email = st.text_input("Email", placeholder="your@email.com")
        
        with col2:
            password = st.text_input("Password", type="password", placeholder="Strong password")
            password_confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
        
        terms = st.checkbox("I agree to the terms of service", value=False)
        
        submit = st.form_submit_button("🚀 Create Account", width="stretch", type="primary")

    # ← This must be OUTSIDE the form but at the same indentation level
    if submit:
        # Validation
        if not username or not email or not password or not password_confirm:
            st.error("⚠️ All fields are required!")
            st.stop()
        
        if len(username) < 3:
            st.error("⚠️ Username must be at least 3 characters long")
            st.stop()
        
        if len(password) < 6:
            st.error("⚠️ Password must be at least 6 characters")
            st.stop()
        
        if password != password_confirm:
            st.error("⚠️ Passwords do not match!")
            st.stop()
        
        if not terms:
            st.error("⚠️ You must agree to the terms of service")
            st.stop()

        # Call API
        with st.spinner("Creating your account..."):
            res = api_post("/auth/signup", {
                "username": username.strip(),
                "email": email.strip(),
                "password": password
            })
        
        if res and res.get("success"):
            st.success("✅ Account created successfully! You can now login.")
            time.sleep(1.5)
            st.session_state.page = "chat"
            st.rerun()
        else:
            error_msg = ""
            if res:
                error_msg = res.get("detail") or res.get("error") or str(res)
            st.error(f"❌ Failed to create account: {error_msg}")


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
                if st.button(f"📋 Copy {filename}", width="stretch"):
                    st.success(f"✅ Copied {filename}")
            with col2:
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=edited,
                    file_name=filename,
                    mime="text/plain",
                    width="stretch",
                    key=f"dl_{filename}"
                )
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save All Changes", width="stretch"):
            st.session_state.edited_files = edited_code
            st.success("✅ Changes saved locally")
    
    with col2:
        if st.button("🔄 Reset All", width="stretch"):
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
                        width="stretch",
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
# MAIN APP ROUTING (FIXED)
# ═════════════════════════════════════════════

show_auth_sidebar()

# Define pages dictionary
pages = {
    "chat": show_chat_page,
    "editor": show_editor_page,
    "downloads": show_downloads_page,
    "signup": show_signup_page,
}

# ─────────────────────────────────────────────
# FIXED ROUTING LOGIC
# ─────────────────────────────────────────────
if st.session_state.page == "signup":
    show_signup_page()
elif not st.session_state.token:
    show_landing_page()
else:
    current_page = st.session_state.get("page", "chat")
    if current_page in pages:
        pages[current_page]()
    else:
        show_chat_page()


# ─────────────────────────────────────────────
# CLEAN SIDEBAR NAVIGATION (Logged-in only)
# ─────────────────────────────────────────────
if st.session_state.token:
    st.sidebar.markdown("---")
    st.sidebar.subheader("📱 Navigation")
    
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("💬 Chat", width="stretch", key="nav_chat"):
            st.session_state.page = "chat"
            st.rerun()
    with col2:
        if st.button("✏️ Editor", width="stretch", key="nav_editor"):
            st.session_state.page = "editor"
            st.rerun()
    with col3:
        if st.button("📥 Downloads", width="stretch", key="nav_downloads"):
            st.session_state.page = "downloads"
            st.rerun()

    st.sidebar.markdown("---")
    col_a, col_b = st.sidebar.columns(2)
    with col_a:
        if st.button("🗑️ Clear History", width="stretch"):
            st.session_state.messages = []
            st.success("✅ Cleared")
            st.rerun()
    with col_b:
        if st.button("🔄 Refresh", width="stretch"):
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Stats")
    st.sidebar.metric("Messages", len(st.session_state.messages))
    st.sidebar.metric("Logs", len(st.session_state.live_logs))