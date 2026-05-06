from ui.services import api
from typing import Optional, Dict

def conduct_research(query: str, research_type: str = "general") -> Optional[Dict]:
    """Call research endpoint"""
    return api.api_post(
        "/research",
        {
            "prompt": query,
            "research_type": research_type
        },
        auth=True,
        timeout=300
    )

def get_research_history(user_id: str, limit: int = 10) -> Optional[Dict]:
    """Get research history"""
    return api.api_get(
        f"/research/history/{user_id}?limit={limit}",
        auth=True
    )