import streamlit as st
import base64
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# ZIP PROCESSING
# ─────────────────────────────────────────────
def process_zip_data(zip_data: Optional[Dict[str, Any]]) -> bool:
    """Process ZIP data from backend response"""
    if not zip_data:
        return False
    
    try:
        zip_b64 = zip_data.get("data")
        filename = zip_data.get("filename", "nox_app.zip")
        
        if not zip_b64:
            st.error("❌ No ZIP data received")
            return False
        
        zip_bytes = base64.b64decode(zip_b64)
        
        st.session_state.last_zip_bytes = zip_bytes
        st.session_state.last_filename = filename
        st.session_state.current_zip_data = zip_data
        st.session_state.last_download = True
        st.session_state.build_complete = True
        st.session_state.build_status = "completed"
        
        logger.info(f"[Frontend] ✅ ZIP processed: {filename}")
        return True
        
    except Exception as e:
        st.error(f"❌ ZIP error: {str(e)}")
        logger.error(f"[Frontend] ZIP Error: {e}")
        return False


# ─────────────────────────────────────────────
# CODE DISPLAY
# ─────────────────────────────────────────────
def render_code_block(file_path: str, code: str) -> None:
    """Display a code block with file path"""
    st.markdown(f"**📄 {file_path}**")
    st.code(code, language="python", line_numbers=True)


def display_fixed_code(updated_files: Dict[str, str], diffs: Dict[str, str]) -> None:
    """Display fixed code in expandable sections"""
    if not updated_files:
        return
    
    st.success("🔧 Code has been analyzed and fixed!")
    st.subheader("📝 Fixed Files")
    
    for file_path, code in updated_files.items():
        with st.expander(f"📄 {file_path}", expanded=True):
            st.code(code, language="python", line_numbers=True)
            
            if file_path in diffs and diffs[file_path]:
                with st.expander("📊 View Changes (Diff)"):
                    st.code(diffs[file_path], language="diff", line_numbers=True)
            
            st.caption(f"📦 Size: {len(code)} characters | Lines: {len(code.splitlines())}")