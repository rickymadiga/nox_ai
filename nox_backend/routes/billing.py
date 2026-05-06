import sqlite3
import uuid
import hmac
import hashlib
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from nox_backend.core.security import get_current_user
from nox_backend.core.config import PAYSTACK_SECRET_KEY
from nox_backend.models.schemas import RechargeRequest
from pydantic import BaseModel

# Mapping of credits to prices in kobo (100 kobo = 1 naira)
PRICE_MAP = {
    500: 50000,
    1000: 100000,
    2000: 200000,
    5000: 500000
}

router = APIRouter()

class Billing:
    """Simple in-memory billing store. Replace with DB for persistence."""
    def __init__(self):
        self.user_credits = {}

    def add_credits(self, user: str, amount: int):
        self.user_credits[user] = self.user_credits.get(user, 0) + amount

    def get_credits(self, user: str) -> int:
        return self.user_credits.get(user, 0)

billing = Billing()

def get_safe_email(user):
    """Extract safe email from user object or return a default email."""
    if hasattr(user, 'email'):
        return user.email
    elif isinstance(user, dict) and 'email' in user:
        return user['email']
    else:
        return f"{user}@example.com"

class AutoRechargeRequest(BaseModel):
    amount: int
    email: str

    """Schema for auto recharge requests."""
    amount: int

@router.post("/paystack/initiate")
async def initiate_payment(req: RechargeRequest, user: str = Depends(get_current_user)):
    if req.amount not in PRICE_MAP:
        raise HTTPException(status_code=400, detail="Invalid amount. Allowed: 500, 1000, 2000, 5000")

    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Paystack not configured")

    reference = f"nox_{uuid.uuid4().hex[:16]}"
    safe_email = get_safe_email(user)

    with sqlite3.connect("payments.db") as conn:
        conn.execute(
            "INSERT INTO payments (reference, user_id, credits, amount, status) VALUES (?, ?, ?, ?, 'pending')",
            (reference, user, req.amount, req.amount)
        )
        conn.commit()

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "email": safe_email,
        "amount": PRICE_MAP[req.amount],
        "reference": reference,
        "metadata": {"user_id": user, "credits": req.amount}
    }

    try:
        res = requests.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers, timeout=15)
        data = res.json()

        if not data.get("status"):
            raise HTTPException(status_code=400, detail=data.get("message", "Paystack error"))

        return {
            "status": "success",
            "authorization_url": data["data"]["authorization_url"],
            "reference": reference
        }
    except Exception:
        raise HTTPException(status_code=502, detail="Could not connect to Paystack")

@router.post("/paystack/webhook")
async def paystack_webhook(request: Request):
    if not PAYSTACK_SECRET_KEY:
        return {"status": "error"}

    body = await request.body()
    signature = request.headers.get("x-paystack-signature")

    expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()

    if not signature or signature != expected:
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid payload")

    if payload.get("event") != "charge.success":
        return {"status": "ignored"}

    data = payload.get("data", {})
    reference = data.get("reference")
    authorization = data.get("authorization", {})

    with sqlite3.connect("payments.db") as conn:
        row = conn.execute(
            "SELECT status, user_id, credits FROM payments WHERE reference=?", (reference,)
        ).fetchone()

        if not row or row[0] == "completed":
            return {"status": "ignored"}

        user_id = row[1]
        credits = row[2]

        conn.execute("UPDATE payments SET status='completed' WHERE reference=?", (reference,))
        conn.commit()

    # Save authorization code
    auth_code = authorization.get("authorization_code")
    last4 = authorization.get("last4")
    brand = authorization.get("brand") or authorization.get("card_type")

    if auth_code:
        with sqlite3.connect("users.db") as conn:
            conn.execute(
                """UPDATE users 
                   SET authorization_code = ?, last4 = ?, card_brand = ? 
                   WHERE username = ?""",
                (auth_code, last4, brand, user_id)
            )
            conn.commit()

    # Actually use our Billing instance
    billing.add_credits(user_id, credits)

    return {
    "status": "success",
    "authorization_url": data["data"]["authorization_url"],
    "payment_url": data["data"]["authorization_url"],  # Added for frontend compatibility
    "reference": reference
}
