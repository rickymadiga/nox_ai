"""
Performance Monitor Component
Displays real-time performance metrics and analytics
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional

# ============================================================================
# PERFORMANCE MONITOR UI
# ============================================================================

def render_performance_monitor() -> None:
    """Render performance monitoring dashboard."""
    
    st.subheader("📊 Performance Monitor")
    
    perf_monitor = st.session_state.get("perf_monitor")
    if not perf_monitor:
        st.warning("Performance monitor not available")
        return
    
    # Summary section
    render_performance_summary(perf_monitor)
    
    st.divider()
    
    # Detailed metrics
    if st.checkbox("Show Detailed Metrics"):
        render_detailed_metrics(perf_monitor)
    
    st.divider()
    
    # Analytics section
    render_analytics_section()


def render_performance_summary(perf_monitor) -> None:
    """Render performance summary metrics."""
    
    summary = perf_monitor.get_summary()
    
    if summary:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "⏱️ Avg Execution Time",
                f"{summary.get('average_execution_time', 0):.3f}s"
            )
        
        with col2:
            st.metric(
                "💾 Total Memory",
                f"{summary.get('total_memory_used', 0):.1f} MB"
            )
        
        with col3:
            st.metric(
                "📍 Monitored Components",
                summary.get('total_monitored_components', 0)
            )
        
        # Additional metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "⏱️ Max Execution Time",
                f"{summary.get('max_execution_time', 0):.3f}s"
            )
        
        with col2:
            st.metric(
                "💾 Avg Memory Used",
                f"{summary.get('average_memory_used', 0):.1f} MB"
            )
        
        with col3:
            st.metric(
                "⏱️ Total Execution Time",
                f"{summary.get('total_execution_time', 0):.1f}s"
            )
    else:
        st.info("ℹ️ No performance metrics available yet")


def render_detailed_metrics(perf_monitor) -> None:
    """Render detailed component metrics."""
    
    metrics = perf_monitor.get_all_metrics()
    
    if not metrics:
        st.info("ℹ️ No detailed metrics available")
        return
    
    st.write("**Component Performance Details:**")
    
    for component, metric in metrics.items():
        with st.expander(f"📍 {component}", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"⏱️ **Execution Time**: {metric.execution_time:.3f}s")
                st.write(f"💾 **Memory Used**: {metric.memory_used:.1f} MB")
                
                if metric.start_time:
                    start_time = metric.start_time.strftime('%Y-%m-%d %H:%M:%S')
                    st.write(f"🕐 **Started**: {start_time}")
            
            with col2:
                st.write(f"🔧 **CPU**: {metric.cpu_percent:.1f}%")
                
                if metric.end_time:
                    end_time = metric.end_time.strftime('%Y-%m-%d %H:%M:%S')
                    st.write(f"🕑 **Ended**: {end_time}")
                
                st.write(f"✅ **Status**: Completed")


def render_analytics_section() -> None:
    """Render analytics dashboard."""
    
    if not st.checkbox("Show Analytics"):
        return
    
    analytics = st.session_state.get("analytics")
    if not analytics:
        st.warning("Analytics service not available")
        return
    
    st.write("**Analytics Summary:**")
    
    stats = analytics.get_all_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total Events", stats.get('total_events', 0))
    
    with col2:
        success_rate = stats.get('success_rate', 0)
        st.metric("✅ Success Rate", f"{success_rate:.1f}%")
    
    with col3:
        st.metric("🎯 Unique Intents", stats.get('unique_intents', 0))
    
    st.divider()
    
    # Event breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "✅ Successful Events",
            stats.get('successful_events', 0)
        )
    
    with col2:
        st.metric(
            "❌ Failed Events",
            stats.get('failed_events', 0)
        )


def render_cache_stats() -> None:
    """Render cache statistics."""
    
    cache_manager = st.session_state.get("cache")
    if not cache_manager:
        st.warning("Cache manager not available")
        return
    
    st.write("**Cache Statistics:**")
    
    cache_stats = cache_manager.get_stats()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📦 Cache Size",
            f"{cache_stats['size']}/{cache_stats['max_size']}"
        )
    
    with col2:
        st.metric(
            "📊 Utilization",
            f"{cache_stats['utilization']:.1f}%"
        )
    
    with col3:
        st.metric(
            "🎯 Max Size",
            cache_stats['max_size']
        )


def render_intent_metrics() -> None:
    """Render intent-specific metrics."""
    
    router = st.session_state.get("intent_router")
    if not router:
        st.warning("Intent router not available")
        return
    
    st.write("**Intent Performance Metrics:**")
    
    all_metrics = router.get_all_metrics()
    
    if not all_metrics:
        st.info("ℹ️ No intent metrics available")
        return
    
    # Create metrics table
    metrics_data = []
    
    for intent, metrics in all_metrics.items():
        metrics_data.append({
            "Intent": intent.value,
            "Executions": metrics.success_count + metrics.error_count,
            "Successful": metrics.success_count,
            "Failed": metrics.error_count,
            "Avg Time": f"{metrics.execution_time:.3f}s",
            "Memory": f"{metrics.memory_usage:.1f} MB",
            "Last Executed": metrics.last_executed.strftime('%H:%M:%S')
        })
    
    st.table(metrics_data)


def render_system_health() -> None:
    """Render system health status."""
    
    st.write("**System Health:**")
    
    col1, col2, col3 = st.columns(3)
    
    # Get cache status
    cache_manager = st.session_state.get("cache")
    cache_status = "✅ Healthy" if cache_manager else "❌ Unavailable"
    
    with col1:
        st.metric("💾 Cache", cache_status)
    
    # Get analytics status
    analytics = st.session_state.get("analytics")
    analytics_status = "✅ Healthy" if analytics else "❌ Unavailable"
    
    with col2:
        st.metric("📊 Analytics", analytics_status)
    
    # Get performance monitor status
    perf_monitor = st.session_state.get("perf_monitor")
    perf_status = "✅ Healthy" if perf_monitor else "❌ Unavailable"
    
    with col3:
        st.metric("⚡ Performance", perf_status)


# ============================================================================
# ADVANCED MONITORING
# ============================================================================

def render_advanced_monitoring() -> None:
    """Render advanced monitoring dashboard."""
    
    st.subheader("🔬 Advanced Monitoring")
    
    tabs = st.tabs([
        "📊 Performance",
        "📈 Analytics",
        "💾 Cache",
        "🎯 Intents",
        "🏥 Health"
    ])
    
    with tabs[0]:
        render_performance_monitor()
    
    with tabs[1]:
        render_analytics_section()
    
    with tabs[2]:
        render_cache_stats()
    
    with tabs[3]:
        render_intent_metrics()
    
    with tabs[4]:
        render_system_health()


# ============================================================================
# DEBUG MODE MONITOR
# ============================================================================

def render_debug_mode_monitor() -> None:
    """Render debug mode monitoring panel."""
    
    if not st.session_state.get("debug_mode"):
        return
    
    with st.sidebar:
        st.divider()
        
        with st.expander("🐛 Debug Panel", expanded=True):
            st.write("**Debug Information:**")
            
            # Session info
            from services.state import get_session_info
            session_info = get_session_info()
            
            st.write("**Session:**")
            for key, value in session_info.items():
                st.caption(f"{key}: {value}")
            
            st.divider()
            
            # Performance monitor
            perf_monitor = st.session_state.get("perf_monitor")
            if perf_monitor:
                st.write("**Performance:**")
                summary = perf_monitor.get_summary()
                if summary:
                    st.caption(f"Avg Time: {summary.get('average_execution_time', 0):.3f}s")
                    st.caption(f"Total Memory: {summary.get('total_memory_used', 0):.1f} MB")
            
            st.divider()
            
            # Cache stats
            cache_manager = st.session_state.get("cache")
            if cache_manager:
                st.write("**Cache:**")
                cache_stats = cache_manager.get_stats()
                utilization = cache_stats.get('utilization', 0)
                st.caption(f"Utilization: {utilization:.1f}%")


# ============================================================================
# MONITORING UTILITIES
# ============================================================================

def format_duration(seconds: float) -> str:
    """Format duration for display."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = seconds / 60
        return f"{minutes:.1f}min"


def format_size(bytes: int) -> str:
    """Format byte size for display."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"


def get_health_status(metrics: Dict[str, Any]) -> str:
    """Get health status based on metrics."""
    
    avg_time = metrics.get('average_execution_time', 0)
    
    if avg_time > 2:
        return "⚠️ Slow"
    elif avg_time > 1:
        return "ℹ️ Normal"
    else:
        return "✅ Fast"