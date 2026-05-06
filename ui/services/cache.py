"""Caching Service"""
import streamlit as st
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)
def cache_builds():
    """Cache builds data for 5 minutes"""
    from services.api import api_get
    return api_get("/builds?limit=50", auth=True)


@st.cache_data(ttl=300)
def cache_stats():
    """Cache statistics for 5 minutes"""
    from services.api import api_get
    return api_get("/builds/stats", auth=True)


def clear_cache():
    """Clear all cached data"""
    st.cache_data.clear()
    logger.info("Cache cleared")