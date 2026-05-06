# ui/pages/code_fixer_page.py - CODE FIXER (Dedicated)

import streamlit as st
import logging
from datetime import datetime
from ui.utils.key_generator import KeyGenerator

logger = logging.getLogger(__name__)


def show():
    """Display Code Fixer page."""
    
    st.markdown("### 🔧 Code Fixer - Fix Bugs & Issues")
    st.markdown("Paste your buggy code and let AI fix it automatically")
    
    # Initialize session state for code fixer
    if "code_fixer_messages" not in st.session_state:
        st.session_state.code_fixer_messages = []
    if "code_fixer_result" not in st.session_state:
        st.session_state.code_fixer_result = None
    if "code_fixer_building" not in st.session_state:
        st.session_state.code_fixer_building = False
    
    # Input section
    with st.container(border=True):
        st.markdown("#### 📝 Enter Your Code")
        
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            code_input = st.text_area(
                "Paste code here:",
                height=120,
                placeholder="def broken_function():\n    x=5\n    return x",
                key="code_fixer_input"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🚀 Fix Code", use_container_width=True, key="code_fixer_btn"):
                if code_input.strip():
                    st.session_state.code_fixer_building = True
                    st.session_state.code_fixer_messages.append({
                        "role": "user",
                        "content": code_input,
                        "timestamp": datetime.now().isoformat()
                    })
    
    # Process if building
    if st.session_state.code_fixer_building and st.session_state.code_fixer_messages:
        _process_code_fixer_request()
    
    # Results section
    if st.session_state.code_fixer_result:
        _display_code_fixer_result(st.session_state.code_fixer_result)


def _process_code_fixer_request():
    """Process code fixer request."""
    from runtime.engine_runtime import EngineRuntime
    
    runtime = EngineRuntime()
    user_message = st.session_state.code_fixer_messages[-1]["content"]
    
    try:
        with st.spinner("🔄 Analyzing and fixing code..."):
            logger.info(f"[Code Fixer] 🚀 Sending: {user_message[:60]}")
            
            result = runtime.execute_agent(
                agent_name="code_assistant",
                task={
                    "prompt": f"fix the code provided, {user_message}",
                    "error_trace": "",
                    "context": {}
                }
            )
            
            st.session_state.code_fixer_result = result
            logger.info(f"[Code Fixer] Status: {result.get('status')}")
            
            st.session_state.code_fixer_building = False
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"[Code Fixer] Error: {e}", exc_info=True)
        st.session_state.code_fixer_building = False


def _display_code_fixer_result(result):
    """Display code fixer result."""
    if not isinstance(result, dict):
        st.error("Invalid result format")
        return
    
    status = result.get("status", "unknown")
    
    if status == "success":
        st.success("✅ Code Fixed Successfully!")
        
        # Display analysis
        if result.get("analysis"):
            with st.container(border=True):
                st.markdown("#### 📊 Analysis")
                st.write(result["analysis"])
        
        # Display fixed code
        updated_files = result.get("updated_files", {})
        if updated_files:
            with st.container(border=True):
                st.markdown("#### 📝 Fixed Code")
                
                for idx, (filename, code) in enumerate(updated_files.items()):
                    display_name = "Fixed Code" if filename == "<inline_code>" else filename
                    download_name = "fixed_code.py" if filename == "<inline_code>" else filename
                    
                    st.code(code, language="python")
                    
                    download_key = KeyGenerator.download_key(filename, idx)
                    st.download_button(
                        label=f"⬇️ Download {display_name}",
                        data=code,
                        file_name=download_name,
                        mime="text/plain",
                        key=download_key
                    )
        
        # Display summary
        if result.get("summary"):
            with st.container(border=True):
                st.markdown("#### 📈 Summary")
                st.markdown(result["summary"])
    
    elif status == "failed":
        st.error("❌ Could Not Fix Code")
        
        error = result.get("error", "Unknown error")
        root_cause = result.get("root_cause", error)
        
        with st.container(border=True):
            st.markdown("#### 🔍 Error Details")
            st.error(f"**Error:** {error}")
            st.warning(f"**Root Cause:** {root_cause}")
        
        # Display execution log
        exec_log = result.get("execution_log", [])
        if exec_log:
            with st.expander("📋 Execution Log"):
                for log in exec_log:
                    status_color = "🟢" if log.get("status") == "success" else "🔴"
                    st.write(f"{status_color} **[{log.get('stage')}]** {log.get('message')}")
    
    else:
        st.warning(f"⚠️ Status: {status}")