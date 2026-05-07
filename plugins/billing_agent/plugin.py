import sqlite3
from typing import Dict, Optional
import time
from datetime import timedelta

DEV_USERS = ["nox", "admin", "cosmic ethic"]

class BillingError(Exception):
    pass

class PlanLimitExceeded(BillingError):
    pass


class Billing:
    def __init__(self, db_path: str = "billing.db"):
        self.db_path = db_path

        self.PLANS = {
            "free": {
                "name": "Free",
                "monthly_builds": 3,
                "debug_requests": 15,
                "research_requests": 30,
                "content_gen": 10,
                "max_complexity": "medium",
                "priority": "low"
            },
            "pro": {
                "name": "Pro",
                "monthly_builds": 20,
                "debug_requests": 150,
                "research_requests": 300,
                "content_gen": 80,
                "max_complexity": "complex",
                "priority": "high"
            },
            "enterprise": {
                "name": "Enterprise",
                "monthly_builds": 999,
                "debug_requests": 999,
                "research_requests": 999,
                "content_gen": 999,
                "max_complexity": "unlimited",
                "priority": "ultra"
            }
        }

        self._init_db()

    # =========================================================
    # DB INIT + MIGRATION
    # =========================================================
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    plan TEXT DEFAULT 'free',
                    plan_expires_at REAL,
                    builds_this_month INTEGER DEFAULT 0,
                    debug_this_month INTEGER DEFAULT 0,
                    research_this_month INTEGER DEFAULT 0,
                    content_this_month INTEGER DEFAULT 0,
                    is_admin INTEGER DEFAULT 0,
                    created_at REAL
                )
            """)

            # Safe migrations
            for column in ["plan_expires_at", "builds_this_month", "debug_this_month", 
                          "research_this_month", "content_this_month"]:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {column} { 'REAL' if column == 'plan_expires_at' else 'INTEGER DEFAULT 0' }")
                except sqlite3.OperationalError:
                    pass

            conn.commit()

    # =========================================================
    # HELPERS
    # =========================================================
    def _is_dev(self, user_id: str) -> bool:
        return user_id.lower() in [u.lower() for u in DEV_USERS]

    def _get_or_create_user(self, c, user_id: str):
        if self._is_dev(user_id):
            return ("enterprise", None, 0, 0, 0, 0, 1)  # plan, expires, builds, debug, research, content, admin

        c.execute("""
            SELECT plan, plan_expires_at, builds_this_month, debug_this_month,
                   research_this_month, content_this_month, is_admin 
            FROM users WHERE user_id=?
        """, (user_id,))
        row = c.fetchone()

        if row:
            return row

        now = time.time()
        c.execute("""
            INSERT INTO users (user_id, plan, plan_expires_at, created_at)
            VALUES (?, 'free', NULL, ?)
        """, (user_id, now))
        return ("free", None, 0, 0, 0, 0, 0)

    def _reset_monthly_usage(self, user_id: str):
        """Reset usage and extend plan by 30 days"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            new_expiry = time.time() + (30 * 24 * 3600)
            c.execute("""
                UPDATE users 
                SET builds_this_month=0, debug_this_month=0,
                    research_this_month=0, content_this_month=0,
                    plan_expires_at = ?
                WHERE user_id=?
            """, (new_expiry, user_id))
            conn.commit()

    # =========================================================
    # PUBLIC API
    # =========================================================
    def get_plan_status(self, user_id: str) -> Dict:
        if self._is_dev(user_id):
            return {
                "plan": "god_mode",
                "is_active": True,
                "plan_expires_at": None,
                "limits": self.PLANS["enterprise"],
                "usage": {"builds": 0, "debug": 0, "research": 0, "content": 0},
                "is_admin": True
            }

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            data = self._get_or_create_user(c, user_id)
            plan, expires, builds, debug, research, content, is_admin = data

            now = time.time()

            # Auto-reset if plan expired
            if expires and now > expires:
                self._reset_monthly_usage(user_id)
                # Re-fetch
                data = self._get_or_create_user(c, user_id)
                plan, expires, builds, debug, research, content, is_admin = data

            usage = {
                "builds": builds,
                "debug": debug,
                "research": research,
                "content": content
            }

            return {
                "plan": plan,
                "is_active": not expires or now <= expires,
                "plan_expires_at": expires,
                "limits": self.PLANS.get(plan, self.PLANS["free"]),
                "usage": usage,
                "is_admin": bool(is_admin)
            }

    def can_perform_action(self, user_id: str, action: str, complexity: str = "medium") -> Dict:
        """Check if user can perform action under their plan"""
        if self._is_dev(user_id):
            return {"allowed": True, "reason": "dev_god_mode"}

        status = self.get_plan_status(user_id)
        if not status["is_active"]:
            return {"allowed": False, "reason": "plan_expired"}

        limits = status["limits"]
        usage = status["usage"]

        if action == "build":
            if usage["builds"] >= limits["monthly_builds"]:
                return {"allowed": False, "reason": "monthly_build_limit_reached"}
            if complexity == "complex" and limits["max_complexity"] == "medium":
                return {"allowed": False, "reason": "plan_does_not_support_complex_builds"}

        elif action == "debug":
            if usage["debug"] >= limits["debug_requests"]:
                return {"allowed": False, "reason": "debug_limit_reached"}

        elif action == "research":
            if usage["research"] >= limits["research_requests"]:
                return {"allowed": False, "reason": "research_limit_reached"}

        elif action in ["content_generator", "content_gen"]:
            if usage["content"] >= limits["content_gen"]:
                return {"allowed": False, "reason": "content_generation_limit_reached"}

        return {"allowed": True, "reason": "ok", "remaining": 
                {k: limits[k.replace("content", "content_gen")] - v 
                 for k, v in usage.items() if k in limits}}

    def record_usage(self, user_id: str, action: str):
        """Record usage after successful action"""
        if self._is_dev(user_id):
            return {"status": "recorded", "dev": True}

        field_map = {
            "build": "builds_this_month",
            "debug": "debug_this_month",
            "research": "research_this_month",
            "content_generator": "content_this_month",
            "content_gen": "content_this_month"
        }

        field = field_map.get(action)
        if not field:
            return {"status": "skipped", "reason": "unknown_action"}

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(f"UPDATE users SET {field} = {field} + 1 WHERE user_id=?", (user_id,))
            conn.commit()

        return {"status": "recorded"}

    def set_plan(self, user_id: str, new_plan: str, days: int = 30) -> Dict:
        """Admin method to change user plan"""
        if new_plan not in self.PLANS:
            return {"status": "error", "message": "Invalid plan"}

        expires = time.time() + (days * 24 * 3600)

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE users 
                SET plan=?, plan_expires_at=?, 
                    builds_this_month=0, debug_this_month=0,
                    research_this_month=0, content_this_month=0
                WHERE user_id=?
            """, (new_plan, expires, user_id))
            conn.commit()

        return {"status": "success", "plan": new_plan, "expires_at": expires}

    def add_credits(self, *args, **kwargs):
        """Deprecated - kept for backward compatibility"""
        return {"status": "deprecated", "message": "Use subscription plans instead"}


def register(runtime):
    billing = Billing()
    runtime.register_agent("billing_agent", billing)
    print("[PLUGIN] ✅ Billing (Plan-based) agent registered")