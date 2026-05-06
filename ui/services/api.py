# services/api.py
import asyncio

from fastapi import websockets
import asyncio

import requests
from typing import Dict, Any, Optional
import base64

import websockets
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"  # ✅ Fixed: Changed from /app to /api


class API:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user = None

    # =========================
    # AUTH
    # =========================

    def login(self, username: str, password: str) -> Dict[str, Any]:
        try:
            r = requests.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            data = r.json()

            if data.get("success"):
                self.token = data["data"]["token"]
                self.user = data["data"].get("user")

            return data
        except Exception as e:
            return {"success": False, "error": str(e)}

    def signup(self, username: str, email: str, password: str, password_confirm: str) -> Dict[str, Any]:
        if password != password_confirm:
            return {"success": False, "error": "Passwords do not match"}

        try:
            r = requests.post(
                f"{self.base_url}/auth/signup",
                json={"username": username, "email": email, "password": password},
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
        

    def verify(self) -> Dict[str, Any]:
        """Verify current token"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/auth/verify",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def refresh(self) -> Dict[str, Any]:
        """Refresh token"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.post(
                f"{self.base_url}/auth/refresh",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=5
            )
            data = r.json()

            if data.get("success"):
                self.token = data["data"]["token"]

            return data

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================
    # CHAT
    # =========================

    def chat(self, message: str) -> Dict[str, Any]:
        if not self.token:
            return {"success": False, "error": "Not authenticated"}

        try:
            r = requests.post(
                f"{self.base_url}/chat/message",
                json={"prompt": message},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=60
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    # =========================
    # OTHER METHODS (cleaned)
    # =========================

    def get_logs(self, user_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        if not self.token:
            return {"success": False, "error": "No token"}
        try:
            r = requests.get(
                f"{self.base_url}/logs/logs",
                params={"limit": limit},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}    

    # =========================
    # LOGS
    # =========================

    def get_logs(self, user_id: Optional[str] = None, limit: int = 100) -> Dict[str, Any]:
        """Get logs for user"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            url = f"{self.base_url}/logs/logs"
            params = {"limit": limit}
            if user_id:
                params["user_id"] = user_id

            r = requests.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_logs(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Search logs by keyword"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/logs/logs/search",
                params={"query": query, "limit": limit},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_log_stats(self) -> Dict[str, Any]:
        """Get log statistics"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            user_id = self.user.get("id") if self.user else "me"
            r = requests.get(
                f"{self.base_url}/logs/logs/stats/{user_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================
    # BUILDS
    # =========================

    def get_builds(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Get build history"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/builds/builds",
                params={"limit": limit, "offset": offset},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_build_stats(self) -> Dict[str, Any]:
        """Get build statistics"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/builds/builds/stats",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_build(self, build_id: str) -> Dict[str, Any]:
        """Get specific build details"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/builds/builds/{build_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_builds(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search builds by project name"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/builds/builds/search",
                params={"query": query, "limit": limit},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================
    # DOWNLOADS
    # =========================

    def download_latest(self) -> Dict[str, Any]:
        """Download latest ZIP build"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.post(
                f"{self.base_url}/download/download/latest",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_build(self, build_id: str) -> Dict[str, Any]:
        """Download specific build"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/download/download/{build_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_zip_bytes(self, zip_data: Dict[str, Any]) -> Optional[bytes]:
        """Decode base64 ZIP data to bytes"""
        try:
            b64_data = zip_data.get("data", "")
            if not b64_data:
                return None
            return base64.b64decode(b64_data)
        except Exception as e:
            print(f"Error decoding ZIP: {e}")
            return None

    # =========================
    # RESEARCH
    # =========================

    def conduct_research(self, prompt: str, research_type: str = "general") -> Dict[str, Any]:
        """Conduct research"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.post(
                f"{self.base_url}/research/research",
                json={"prompt": prompt, "research_type": research_type},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=60
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_research_history(self, limit: int = 10) -> Dict[str, Any]:
        """Get research history"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            user_id = self.user.get("id") if self.user else "me"
            r = requests.get(
                f"{self.base_url}/research/research/history/{user_id}",
                params={"limit": limit},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================
    # USER & PROFILE
    # =========================

    def get_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/user/profile",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def update_profile(self, **kwargs) -> Dict[str, Any]:
        """Update user profile"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.put(
                f"{self.base_url}/user/profile",
                json=kwargs,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================
    # CREDITS & PAYMENTS
    # =========================

    def get_credits(self) -> Dict[str, Any]:
        """Get user credits balance"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/credits/balance",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def purchase_credits(self, amount: int, package: str = "standard") -> Dict[str, Any]:
        """Purchase credits"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.post(
                f"{self.base_url}/credits/purchase",
                json={"amount": amount, "package": package},
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================
    # ADMIN STATS
    # =========================

    def get_forge_stats(self) -> Dict[str, Any]:
        """Get forge statistics (admin only)"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/forge-stats/admin/forge-stats",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_build_metrics(self) -> Dict[str, Any]:
        """Get build metrics (admin only)"""
        if not self.token:
            return {"success": False, "error": "No token"}

        try:
            r = requests.get(
                f"{self.base_url}/forge-stats/admin/build-metrics",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()

        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def edit(self, payload):
        return self._post("/api/edit", payload)
    
    def get_video_status(self, job_id: str) -> Dict[str, Any]:
        """Check status of a video job"""
        if not self.token:
            return {"success": False, "error": "Not authenticated"}

        try:
            r = requests.get(
                f"{self.base_url}/video/status/{job_id}",
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10
            )
            return r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    async def listen():
        uri = "websocket://127.0.0.1:8000/api/websocket"

        async with websockets.connect(uri) as websocket:
            while True:
                msg = await websocket.recv()
                print("LIVE:", msg)

    asyncio.run(listen())    

    # =========================
    # HEALTH & STATUS
    # =========================

    def health(self) -> bool:
        try:
            r = requests.get("http://127.0.0.1:8000/health", timeout=5)
            return r.status_code == 200
        except:
            return False

    def get_server_status(self) -> Dict[str, Any]:
        """Get detailed server status"""
        try:
            r = requests.get("http://127.0.0.1:8000/", timeout=5)
            return r.json()
        except:
            return {"status": "offline"}