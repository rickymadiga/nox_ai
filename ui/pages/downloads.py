import streamlit as st
import base64
from datetime import datetime

def show():
    st.title("📥 Downloads")
    
    api = st.session_state.api
    user = st.session_state.get("user", {})
    
    if not st.session_state.token:
        st.warning("🔐 Please login first")
        st.stop()
    
    st.subheader("💾 Your Builds & Exports")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📦 Builds", "📜 History", "⚙️ Settings"])
    
    # ═════════════════════════════════
    # TAB 1: DOWNLOADS
    # ═════════════════════════════════
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### 🏗️ Latest Build")
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        # Get latest build
        with st.spinner("📥 Fetching latest build..."):
            latest = api.download_latest()
        
        if latest and latest.get("success"):
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
                
                # Download button
                try:
                    zip_bytes = base64.b64decode(zip_data.get("data", ""))
                    st.download_button(
                        label="⬇️ Download Latest Build",
                        data=zip_bytes,
                        file_name=zip_data.get("filename", "nox_app.zip"),
                        mime="application/zip",
                        use_container_width=True,
                        key="download_latest"
                    )
                    
                    st.success("✅ Build ready for download")
                
                except Exception as e:
                    st.error(f"❌ Download error: {str(e)}")
            else:
                st.info("ℹ️ No build available yet")
        else:
            st.warning("⚠️ Could not fetch latest build")
    
    # ═════════════════════════════════
    # TAB 2: BUILD HISTORY
    # ═════════════════════════════════
    with tab2:
        st.markdown("### 📜 Build History")
        
        col1, col2 = st.columns(2)
        with col1:
            limit = st.number_input("Results per page", min_value=5, max_value=100, value=10)
        with col2:
            if st.button("🔄 Reload History", use_container_width=True):
                st.rerun()
        
        # Get builds
        with st.spinner("📥 Loading build history..."):
            builds_res = api.get_builds(limit=limit)
        
        if builds_res and builds_res.get("status") == "success":
            builds = builds_res.get("builds", [])
            total = builds_res.get("total", 0)
            
            st.info(f"📊 Showing {len(builds)} of {total} builds")
            
            if builds:
                for build in builds:
                    with st.expander(
                        f"📦 {build.get('project_name', 'Unknown')} - {build.get('status', 'pending').upper()}",
                        expanded=False
                    ):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Build ID", build.get("id", "N/A")[:8])
                        with col2:
                            st.metric("Status", build.get("status", "pending"))
                        with col3:
                            size_kb = build.get("size", 0) / 1024
                            st.metric("Size", f"{size_kb:.2f} KB")
                        with col4:
                            st.metric("Created", build.get("created_at", "N/A")[:10])
                        
                        st.markdown("---")
                        
                        # Download button for specific build
                        if st.button(
                            f"⬇️ Download {build.get('filename', 'nox_app.zip')}",
                            key=f"download_{build.get('id')}",
                            use_container_width=True
                        ):
                            with st.spinner("⬇️ Downloading..."):
                                download_res = api.download_build(build.get("id"))
                            
                            if download_res and download_res.get("success"):
                                try:
                                    zip_bytes = base64.b64decode(download_res.get("data", ""))
                                    st.download_button(
                                        label="💾 Save File",
                                        data=zip_bytes,
                                        file_name=build.get("filename", "nox_app.zip"),
                                        mime="application/zip",
                                        use_container_width=True,
                                        key=f"save_{build.get('id')}"
                                    )
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                            else:
                                st.error("❌ Failed to download")
            else:
                st.info("ℹ️ No builds yet")
        else:
            st.error("❌ Could not load build history")
    
    # ═════════════════════════════════
    # TAB 3: SETTINGS
    # ═════════════════════════════════
    with tab3:
        st.markdown("### ⚙️ Download Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_rename = st.checkbox(
                "Auto-rename files",
                value=True,
                help="Add timestamp to filename"
            )
        
        with col2:
            include_metadata = st.checkbox(
                "Include metadata",
                value=True,
                help="Add build info to ZIP"
            )
        
        st.divider()
        
        st.markdown("### 📊 Download Statistics")
        
        # Get build stats
        with st.spinner("📊 Loading statistics..."):
            stats_res = api.get_build_stats()
        
        if stats_res and stats_res.get("status") == "success":
            stats = stats_res.get("stats", {})
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Builds", stats.get("total_builds", 0))
            with col2:
                st.metric("Successful", stats.get("successful", 0))
            with col3:
                st.metric("Failed", stats.get("failed", 0))
            with col4:
                success_rate = stats.get("success_rate", 0)
                st.metric("Success Rate", f"{success_rate:.1f}%")
        else:
            st.warning("⚠️ Could not load statistics")
        
        st.divider()
        
        st.markdown("### 🗑️ Cleanup")
        
        if st.button("🗑️ Clear Download Cache", use_container_width=True, type="secondary"):
            st.session_state.pop("last_download", None)
            st.success("✅ Cache cleared")