import streamlit as st
from ui.services import research_api

def show():
    """Display research interface"""
    st.subheader("🔬 Research Assistant")
    
    research_query = st.text_area(
        "What would you like to research?",
        placeholder="e.g., Latest AI safety breakthroughs in 2024",
        height=100
    )
    
    research_type = st.selectbox(
        "Research Type",
        ["General", "Academic", "Technical", "News", "Business"]
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🔍 Start Research", use_container_width=True):
            if research_query:
                _conduct_research(research_query, research_type.lower())
            else:
                st.warning("Please enter a research query")

def _conduct_research(query: str, research_type: str):
    """Conduct research"""
    with st.spinner("🔬 Researching..."):
        result = research_api.conduct_research(query, research_type)
        
        if result and result.get("status") == "success":
            data = result.get("result", {})
            
            # Display findings
            st.success("✅ Research Complete")
            
            # Executive Summary
            if data.get("report"):
                report = data["report"]
                st.markdown(f"## {report.get('title', 'Research Report')}")
                st.markdown(f"**{report.get('executive_summary', '')}**")
            
            # Sources
            if data.get("sources"):
                with st.expander(f"📚 Sources ({len(data['sources'])})"):
                    for i, source in enumerate(data["sources"][:10], 1):
                        st.write(f"**{i}. {source.get('title', 'Unknown')}**")
                        if source.get("url") != "direct_answer":
                            st.caption(f"🔗 {source.get('url', '')}")
            
            # Key Findings
            if data.get("analysis"):
                with st.expander("🔍 Key Findings"):
                    findings = data["analysis"].get("findings", [])
                    for finding in findings[:5]:
                        st.write(f"• {finding.get('finding', '')}")
            
            # Conclusions
            if data.get("synthesis"):
                with st.expander("✅ Conclusions"):
                    for conclusion in data["synthesis"].get("conclusions", []):
                        st.write(f"• {conclusion}")
        else:
            st.error("Research failed")