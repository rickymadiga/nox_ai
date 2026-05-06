import streamlit as st
import json

def show():
    st.title("📝 Code Editor")
    
    api = st.session_state.api
    user = st.session_state.get("user", {})
    
    if not st.session_state.token:
        st.warning("🔐 Please login first")
        st.stop()
    
    # Get last response with code
    last_res = st.session_state.get("last_response")
    
    if not last_res or not last_res.get("updated_files"):
        st.info("💡 No code to edit. Start a chat to get code suggestions!")
        return
    
    st.subheader("✏️ Edit Generated Code")
    
    # Tabs for each file
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
                if st.button(f"⬇️ Download {filename}", use_container_width=True):
                    st.download_button(
                        label=f"Download {filename}",
                        data=edited,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )
    
    # Save edited code
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save All Changes", use_container_width=True):
            st.session_state.edited_files = edited_code
            st.success("✅ Changes saved locally")
    
    with col2:
        if st.button("🔄 Reset All", use_container_width=True):
            st.rerun()
    
    # Show diffs if available
    diffs = last_res.get("diffs", {})
    if diffs:
        with st.expander("🔍 View Changes (Diff)"):
            for filename, diff_text in diffs.items():
                st.markdown(f"**{filename}**")
                st.code(diff_text, language="diff")
    
    # Analysis
    analysis = last_res.get("analysis")
    if analysis:
        with st.expander("🧠 AI Analysis"):
            st.write(analysis)