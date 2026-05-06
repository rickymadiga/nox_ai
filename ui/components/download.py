# ui/components/download.py - FIXED (Better Download Handling)

import streamlit as st
import json
from datetime import datetime


def show():
    """Display download options."""
    
    if "last_result" not in st.session_state or not st.session_state.last_result:
        st.info("No results to download yet. Process a request first.")
        return
    
    result = st.session_state.last_result
    
    st.markdown("### 📥 Download Results")
    
    # Download fixed files
    updated_files = result.get("updated_files", {})
    if updated_files:
        st.markdown("**Fixed Code Files:**")
        
        for idx, (filename, code) in enumerate(updated_files.items()):
            # 🔥 FIX: Create truly unique keys
            timestamp = int(datetime.now().timestamp() * 1000)  # Milliseconds for uniqueness
            
            # Handle <inline_code> filenames
            if filename == "<inline_code>":
                download_name = f"fixed_code_{timestamp}.py"
                display_name = "Fixed Code"
            else:
                download_name = filename
                display_name = filename
            
            unique_key = f"dl_{idx}_{timestamp}"
            
            col1, col2 = st.columns([0.7, 0.3])
            
            with col1:
                st.code(code[:200] + "..." if len(code) > 200 else code, language="python")
            
            with col2:
                st.download_button(
                    label=f"⬇️ {display_name}",
                    data=code,
                    file_name=download_name,
                    mime="text/plain",
                    key=unique_key
                )
    
    # Download full result as JSON
    st.markdown("**Full Result:**")
    
    json_str = json.dumps(result, indent=2, default=str)
    json_key = f"json_download_{int(datetime.now().timestamp() * 1000)}"
    
    st.download_button(
        label="⬇️ Download as JSON",
        data=json_str,
        file_name=f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json",
        key=json_key
    )
    
    # Display summary
    if result.get("summary"):
        st.markdown("### 📊 Summary")
        st.write(result["summary"])