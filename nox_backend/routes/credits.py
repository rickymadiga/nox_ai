import os
import requests
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

from nox_backend.core.security import get_current_user

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PRICE_MAP = {}  # Fill your prices here

def init_tables():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                credits INTEGER DEFAULT 0,
                auto_recharge INTEGER DEFAULT 0,
                authorization_code TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS recharge_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                amount INTEGER NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_tables()

logger = logging.getLogger(__name__)
router = APIRouter()

class ToggleAutoRechargeRequest(BaseModel):
    enabled: bool

class AutoRechargeRequest(BaseModel):
    amount: int

class RechargeRequest(BaseModel):
    amount: int

router = APIRouter() 

@router.get("/credits")
async def get_credits(user: str = Depends(get_current_user)):
    with sqlite3.connect("users.db") as conn:
        row = conn.execute("SELECT credits FROM users WHERE username=?", (user,)).fetchone()
    credits = row[0] if row else 0
    return {"credits": credits}

@router.get("/recharge-history")
async def get_recharge_history(user: str = Depends(get_current_user)):
    with sqlite3.connect("users.db") as conn:
        rows = conn.execute(
            "SELECT amount, date FROM recharge_history WHERE username=? ORDER BY date DESC", 
            (user,)
        ).fetchall()
    history = [{"amount": r[0], "date": r[1]} for r in rows]
    return {"history": history}

@router.post("/toggle-auto-recharge")
async def toggle_auto_recharge(req: ToggleAutoRechargeRequest, user: str = Depends(get_current_user)):
    enabled = 1 if req.enabled else 0
    with sqlite3.connect("users.db") as conn:
        conn.execute("UPDATE users SET auto_recharge = ? WHERE username = ?", (enabled, user))
        conn.commit()
    return {"message": f"Auto recharge {'enabled' if req.enabled else 'disabled'} successfully"}

@router.post("/auto-recharge")
async def perform_auto_recharge(req: AutoRechargeRequest, user: str = Depends(get_current_user)):
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(status_code=500, detail="Paystack not configured")

    with sqlite3.connect("users.db") as conn:
        row = conn.execute("SELECT auto_recharge, authorization_code FROM users WHERE username=?", (user,)).fetchone()

    if not row or row[0] != 1 or not row[1]:
        raise HTTPException(status_code=400, detail="Auto-recharge not enabled or no saved card")

    auth_code = row[1]
    amount_credits = req.amount
    amount_kobo = PRICE_MAP.get(amount_credits)

    if not amount_kobo:
        raise HTTPException(status_code=400, detail="Invalid amount")

    headers = {"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}
    payload = {
        "authorization_code": auth_code,
        "amount": amount_kobo,
        "metadata": {"user_id": user, "credits": amount_credits, "source": "auto_recharge"}
    }

    try:
        res = requests.post("https://api.paystack.co/transaction/charge_authorization", 
                           json=payload, headers=headers, timeout=15)
        data = res.json()

        if data.get("status") and data["data"].get("status") in ["success", "processing"]:
            return {"status": "success", "message": f"Auto-recharged {amount_credits} credits"}
        else:
            raise HTTPException(status_code=400, detail=data.get("message", "Charge failed"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Auto-recharge failed: {str(e)}")

@router.post("/admin/add-credits")
async def admin_add_credits(data: dict):
    user = data.get("user")
    amount = int(data.get("amount", 0))
    return {"status": "ok", "user": user, "added": amount}

class RechargeRequest(BaseModel):
    amount: int

@router.post("/recharge")
async def recharge(req: RechargeRequest, user: str = Depends(get_current_user)):
    return {
        "status": "redirect",
        "message": "Use new endpoint",
        "new_endpoint": "/paystack/initiate",
        "payload": {"amount": req.amount}
    }