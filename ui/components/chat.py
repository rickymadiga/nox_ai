# ui/components/chat.py - FIXED (Unique Download Keys)
from ..utils.key_generator import KeyGenerator
import streamlit as st
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def show():
    """Display chat interface."""
    
    st.markdown("### 💬 Code Assistant Chat")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "building" not in st.session_state:
        st.session_state.building = False
    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    # Chat input
    with st.container():
        col1, col2 = st.columns([0.85, 0.15])
        
        with col1:
            user_input = st.text_area(
                "Enter your code or issue:",
                height=100,
                placeholder="Paste code here or describe the issue...",
                key="user_input"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🚀 Fix Code", use_container_width=True):
                if user_input.strip():
                    st.session_state.building = True
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_input,
                        "timestamp": datetime.now().isoformat()
                    })
    
    # Process request if building
    if st.session_state.building and st.session_state.messages:
        _process_build_request()


def _process_build_request():
    """Process the build/fix request."""
    from ...nox.runtime.engine_runtime import EngineRuntime
    
    runtime = EngineRuntime()
    user_message = st.session_state.messages[-1]["content"]
    
    try:
        with st.spinner("🔄 Processing your request..."):
            logger.info(f"[Frontend] 🚀 Sending: {user_message[:60]}")
            
            # Call the engine
            result = runtime.execute_agent(
                agent_name="code_assistant",
                task={
                    "prompt": user_message,
                    "error_trace": "",
                    "context": {}
                }
            )
            
            st.session_state.last_result = result
            
            # Log result
            result_status = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
            result_type = result.get("type", "unknown") if isinstance(result, dict) else "unknown"
            logger.info(f"[Frontend] Type: {result_type} | Status: {result_status}")
            
            # Store assistant message
            st.session_state.messages.append({
                "role": "assistant",
                "content": result,
                "timestamp": datetime.now().isoformat()
            })
            
            # Display result
            _display_result(result)
            
            st.session_state.building = False
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"[Frontend] Error: {e}", exc_info=True)
        st.session_state.building = False


# ui/components/chat.py - UPDATED (Use KeyGenerator)

def _display_result(result):
    """Display the result from the agent."""
    if not isinstance(result, dict):
        st.error("Invalid result format")
        return
    
    status = result.get("status", "unknown")
    
    if status == "success":
        st.success("✅ Fix completed successfully!")
        
        # Display analysis
        if result.get("analysis"):
            st.markdown("### 📊 Analysis")
            st.info(result["analysis"])
        
        # Display updated files
        updated_files = result.get("updated_files", {})
        if updated_files:
            st.markdown("### 📝 Fixed Code")
            
            for idx, (filename, code) in enumerate(updated_files.items()):
                with st.container():
                    st.subheader(f"📄 {filename}")
                    st.code(code, language="python")
                    
                    # 🔥 USE KeyGenerator
                    download_key = KeyGenerator.download_key(filename, idx)
                    
                    st.download_button(
                        label=f"⬇️ Download {filename}",
                        data=code,
                        file_name=filename if filename != "<inline_code>" else "fixed_code.py",
                        mime="text/plain",
                        key=download_key
                    )

def show_chat_history():
    """Display chat history."""
    if "messages" not in st.session_state or not st.session_state.messages:
        st.info("No messages yet. Start a conversation!")
        return
    
    for message in st.session_state.messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        timestamp = message.get("timestamp", "")
        
        if role == "user":
            with st.chat_message("user"):
                # Display truncated for large content
                if isinstance(content, str) and len(content) > 200:
                    st.text(content[:200] + "...")
                else:
                    st.text(content)
        else:
            with st.chat_message("assistant"):
                if isinstance(content, dict):
                    status = content.get("status", "unknown")
                    st.markdown(f"**Status:** {status}")
                    if status == "success":
                        st.success("✅ Completed")
                    else:
                        st.error("❌ Failed")
                else:
                    st.text(content)