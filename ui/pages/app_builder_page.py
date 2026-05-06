# ui/pages/app_builder_page.py - APP BUILDER (Dedicated)

import streamlit as st
import logging
from datetime import datetime
from ui.utils.key_generator import KeyGenerator

logger = logging.getLogger(__name__)


def show():
    """Display App Builder page."""
    
    st.markdown("### 🏗️ App Builder - Generate Full Applications")
    st.markdown("Describe your app idea and let AI build it for you")
    
    # Initialize session state
    if "app_builder_messages" not in st.session_state:
        st.session_state.app_builder_messages = []
    if "app_builder_result" not in st.session_state:
        st.session_state.app_builder_result = None
    if "app_builder_building" not in st.session_state:
        st.session_state.app_builder_building = False
    
    # Input section
    with st.container(border=True):
        st.markdown("#### 💡 Describe Your App")
        
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            app_description = st.text_area(
                "Describe your app:",
                height=120,
                placeholder="Create a todo list app with React that stores items in localStorage...",
                key="app_builder_input"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🚀 Build App", use_container_width=True, key="app_builder_btn"):
                if app_description.strip():
                    st.session_state.app_builder_building = True
                    st.session_state.app_builder_messages.append({
                        "role": "user",
                        "content": app_description,
                        "timestamp": datetime.now().isoformat()
                    })
    
    # Process if building
    if st.session_state.app_builder_building and st.session_state.app_builder_messages:
        _process_app_builder_request()
    
    # Results section
    if st.session_state.app_builder_result:
        _display_app_builder_result(st.session_state.app_builder_result)


def _process_app_builder_request():
    """Process app builder request."""
    from runtime.engine_runtime import EngineRuntime
    
    runtime = EngineRuntime()
    user_message = st.session_state.app_builder_messages[-1]["content"]
    
    try:
        with st.spinner("🔨 Building your app..."):
            logger.info(f"[App Builder] 🚀 Building: {user_message[:60]}")
            
            result = runtime.execute_agent(
                agent_name="app_builder",  # Different agent
                task={
                    "prompt": f"build an app: {user_message}",
                    "error_trace": "",
                    "context": {}
                }
            )
            
            st.session_state.app_builder_result = result
            logger.info(f"[App Builder] Status: {result.get('status')}")
            
            st.session_state.app_builder_building = False
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"[App Builder] Error: {e}", exc_info=True)
        st.session_state.app_builder_building = False


def _display_app_builder_result(result):
    """Display app builder result."""
    if not isinstance(result, dict):
        st.error("Invalid result format")
        return
    
    status = result.get("status", "unknown")
    
    if status == "success":
        st.success("✅ App Generated Successfully!")
        
        # Display description
        if result.get("analysis"):
            with st.container(border=True):
                st.markdown("#### 📋 App Description")
                st.write(result["analysis"])
        
        # Display generated files
        updated_files = result.get("updated_files", {})
        if updated_files:
            with st.container(border=True):
                st.markdown("#### 📂 Generated Files")
                
                tabs = st.tabs([f.split('/')[-1] for f in updated_files.keys()])
                
                for tab, (filename, code) in zip(tabs, updated_files.items()):
                    with tab:
                        language = _get_language(filename)
                        st.code(code, language=language)
                        
                        download_key = KeyGenerator.download_key(filename, 0)
                        st.download_button(
                            label=f"⬇️ Download {filename.split('/')[-1]}",
                            data=code,
                            file_name=filename.split('/')[-1],
                            mime=_get_mime_type(filename),
                            key=download_key
                        )
        
        # Display summary
        if result.get("summary"):
            with st.container(border=True):
                st.markdown("#### 📈 Summary")
                st.markdown(result["summary"])
    
    elif status == "failed":
        st.error("❌ Failed to Build App")
        error = result.get("error", "Unknown error")
        st.error(f"**Error:** {error}")
    
    else:
        st.warning(f"⚠️ Status: {status}")


def _get_language(filename: str) -> str:
    """Get language for code highlighting."""
    ext = filename.split('.')[-1].lower()
    lang_map = {
        'py': 'python',
        'js': 'javascript',
        'jsx': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'html': 'html',
        'css': 'css',
        'json': 'json'
    }
    return lang_map.get(ext, 'text')


def _get_mime_type(filename: str) -> str:
    """Get MIME type for download."""
    ext = filename.split('.')[-1].lower()
    mime_map = {
        'py': 'text/plain',
        'js': 'text/javascript',
        'jsx': 'text/javascript',
        'ts': 'text/typescript',
        'tsx': 'text/typescript',
        'html': 'text/html',
        'css': 'text/css',
        'json': 'application/json'
    }
    return mime_map.get(ext, 'text/plain')