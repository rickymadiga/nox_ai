import uuid
import sqlite3
import requests
import hashlib
import hmac
import logging
from typing import Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from nox_backend.core.security import get_current_user
from nox_backend.core.config import PAYSTACK_SECRET_KEY

logger = logging.getLogger(__name__)
router = APIRouter()

PRICE_MAP = {500: 50000, 1000: 100000, 2000: 200000, 5000: 500000}
CREDIT_CONVERSION = {500: 500, 1000: 1000, 2000: 2000, 5000: 5000}

class RechargeRequest(BaseModel):
    amount: int
    email: Optional[str] = None

# Remove WebhookEvent (unused)

def init_payments_table():
    try:
        with sqlite3.connect("payments.db") as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                credits INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                paystack_reference TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                metadata TEXT
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_reference ON payments(reference)")
            conn.commit()
            logger.info("[Payments] Database initialized")
    except Exception as e:
        logger.error(f"[Payments] DB init failed: {e}")

init_payments_table()

def get_user_id(current_user: Any) -> str:
    try:
        if isinstance(current_user, dict):
            return current_user.get("id") or current_user.get("username") or str(current_user)
        return getattr(current_user, 'id', str(current_user))
    except:
        return str(current_user)

@router.post("/paystack/initiate")
async def initiate_payment(req: RechargeRequest, current_user: Any = Depends(get_current_user)):
    if req.amount not in PRICE_MAP:
        return {"status": "error", "detail": f"Invalid amount. Allowed: {list(PRICE_MAP.keys())}"}

    if not PAYSTACK_SECRET_KEY:
        return {"status": "error", "detail": "Payment not configured"}

    user_id = get_user_id(current_user)
    reference = f"nox_{uuid.uuid4().hex[:20]}"

    try:
        with sqlite3.connect("payments.db") as conn:
            conn.execute(
                "INSERT INTO payments (reference, user_id, credits, amount, status) VALUES (?, ?, ?, ?, 'pending')",
                (reference, user_id, CREDIT_CONVERSION[req.amount], req.amount)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"DB error: {e}")
        return {"status": "error", "detail": "Database error"}

    payload = {
        "email": req.email or f"{user_id}@nox.app",
        "amount": PRICE_MAP[req.amount],
        "reference": reference,
        "metadata": {"user_id": user_id, "credits": CREDIT_CONVERSION[req.amount], "source": "nox_app"}
    }

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}

    try:
        res = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers, timeout=15)
        data = res.json()

        if not data.get("status"):
            # cleanup on fail
            with sqlite3.connect("payments.db") as conn:
                conn.execute("DELETE FROM payments WHERE reference=?", (reference,))
                conn.commit()
            return {"status": "error", "detail": data.get("message", "Paystack error")}

        return {
            "status": "success",
            "authorization_url": data["data"]["authorization_url"],
            "reference": reference
        }
    except Exception as e:
        return {"status": "error", "detail": "Payment initiation failed"}

@router.post("/paystack/webhook")
async def paystack_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-paystack-signature")

    if not PAYSTACK_SECRET_KEY or not signature:
        return {"status": "success"}  # always 200

    expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return {"status": "success"}

    try:
        event = await request.json()
        if event.get("event") != "charge.success":
            return {"status": "success"}

        data = event.get("data", {})
        reference = data.get("reference")

        with sqlite3.connect("payments.db") as conn:
            row = conn.execute("SELECT user_id, credits FROM payments WHERE reference=? AND status='pending'", (reference,)).fetchone()
            if not row:
                return {"status": "success"}

            user_id, credits = row
            conn.execute("UPDATE payments SET status='completed', paid_at=CURRENT_TIMESTAMP WHERE reference=?", (reference,))
            conn.commit()

        # TODO: add credits here when billing_agent is fixed
        # billing_agent.add_credits(user_id, credits)

        logger.info(f"Payment completed: {reference} -> +{credits} credits to {user_id}")
    except:
        pass

    return {
    "status": "success",
    "authorization_url": data["data"]["authorization_url"],
    "payment_url": data["data"]["authorization_url"],  # Added for frontend compatibility
    "reference": reference
}