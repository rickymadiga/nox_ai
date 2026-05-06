import base64
import hashlib
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# NOX Imports
from nox.runtime.engine_runtime import engine
from orchestrator.lily import register as register_lily
from plugins.billing_agent.plugin import register as register_billing

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
ALGORITHM = "HS256"

BUILD_COST = 10

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

runtime = engine.runtime

os.makedirs("generated_apps", exist_ok=True)

# Register agents
register_lily(runtime)
register_billing(runtime)

print("🚀 NOX Backend Initialized | Agents:", list(runtime.agents.keys()))

# ────────────────────────────────────────────────
# PASSWORD HELPERS
# ────────────────────────────────────────────────
def hash_password(password: str) -> str:
    return pwd_context.hash(hashlib.sha256(password.encode()).hexdigest()[:72])


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(hashlib.sha256(plain.encode()).hexdigest()[:72], hashed)
    except:
        return False


# ────────────────────────────────────────────────
# DATABASE
# ────────────────────────────────────────────────
def init_db():
    with sqlite3.connect("users.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """)

    with sqlite3.connect("payments.db") as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                reference TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                credits INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_reference
            ON payments(reference)
        """)


init_db()


# ────────────────────────────────────────────────
# MODELS
# ────────────────────────────────────────────────
class AuthRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    prompt: str
    files: dict = {}


class RechargeRequest(BaseModel):
    amount: int


# ────────────────────────────────────────────────
# AUTH
# ────────────────────────────────────────────────
def create_access_token(username: str):
    return jwt.encode(
        {"sub": username, "exp": datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])["sub"]
    except:
        raise HTTPException(401, "Invalid token")


# ────────────────────────────────────────────────
# APP
# ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Backend running...")
    yield
    print("🛑 Shutdown")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ────────────────────────────────────────────────
# ROOT
# ────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "NOX backend live 🔥"}


# ────────────────────────────────────────────────
# AUTH
# ────────────────────────────────────────────────
@app.post("/signup")
async def signup(data: AuthRequest):
    try:
        with sqlite3.connect("users.db") as conn:
            conn.execute(
                "INSERT INTO users VALUES (?, ?)",
                (data.username, hash_password(data.password))
            )
    except sqlite3.IntegrityError:
        raise HTTPException(400, "User already exists")

    return {"message": "created"}


@app.post("/login")
async def login(data: AuthRequest):
    with sqlite3.connect("users.db") as conn:
        row = conn.execute(
            "SELECT password FROM users WHERE username=?",
            (data.username,)
        ).fetchone()

    if not row or not verify_password(data.password, row[0]):
        raise HTTPException(401, "Invalid credentials")

    return {"access_token": create_access_token(data.username)}


# ────────────────────────────────────────────────
# CREDITS
# ────────────────────────────────────────────────
@app.get("/credits")
async def credits(user=Depends(get_current_user)):
    billing = runtime.get_agent("billing")
    return billing.get_balance(user)


# ────────────────────────────────────────────────
# PAYSTACK INITIATE
# ────────────────────────────────────────────────
@app.post("/paystack/initiate")
async def initiate(request: RechargeRequest, user=Depends(get_current_user)):
    reference = f"nox_{user}_{int(time.time())}"

    resp = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"},
        json={
            "email": f"{user}@nox.ai",
            "amount": request.amount * 100,
            "reference": reference,
            "metadata": {"user_id": user, "credits": request.amount}
        }
    ).json()

    with sqlite3.connect("payments.db") as conn:
        conn.execute(
            "INSERT INTO payments VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)",
            (reference, user, request.amount, request.amount * 100)
        )

    return {
        "url": resp["data"]["authorization_url"],
        "reference": reference
    }


# ────────────────────────────────────────────────
# PAYSTACK VERIFY (HARDENED)
# ────────────────────────────────────────────────
processed_refs = set()

@app.get("/paystack/verify/{reference}")
async def verify(reference: str, user=Depends(get_current_user)):
    if reference in processed_refs:
        return {"status": "duplicate_ignored"}

    processed_refs.add(reference)

    resp = requests.get(
        f"https://api.paystack.co/transaction/verify/{reference}",
        headers={"Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"}
    ).json()

    if resp["data"]["status"] != "success":
        raise HTTPException(400, "Payment failed")

    credits = resp["data"]["metadata"]["credits"]

    with sqlite3.connect("payments.db") as conn:
        conn.execute(
            "UPDATE payments SET status='success' WHERE reference=?",
            (reference,)
        )

    billing = runtime.get_agent("billing")
    billing.add_credits(user, credits)

    return {"status": "credited", "credits": credits}


# ────────────────────────────────────────────────
# CHAT (HARDENED BILLING FLOW)
# ────────────────────────────────────────────────
@app.post("/chat")
async def chat(data: ChatRequest, user=Depends(get_current_user)):
    prompt = data.prompt.strip()

    if not prompt:
        raise HTTPException(400, "Empty prompt")

    billing = runtime.get_agent("billing")

    runtime.last_zip.pop(user, None)

    result = await engine.handle_prompt(prompt, user_id=user)

    price = int(result.get("price", BUILD_COST))

    zip_data = runtime.last_zip.get(user)

    # ─────────────────────────────
    # SAFE BILLING
    # ─────────────────────────────
    if zip_data and zip_data.get("bytes"):
        balance = billing.get_balance(user)

        credits = (
            balance.get("credits")
            or balance.get("available")
            or 0
        )

        if credits < price:
            return {
                "response": f"❌ Not enough credits. Need {price}, have {credits}"
            }

        billing.deduct_credits(user, price)

    encoded_zip = None
    if zip_data and zip_data.get("bytes"):
        encoded_zip = {
            "bytes": base64.b64encode(zip_data["bytes"]).decode(),
            "filename": zip_data.get("filename", "app.zip")
        }

    return {
        "response": result.get("response") or result.get("message"),
        "price": price,
        "zip": encoded_zip,
        "credits_left": billing.get_balance(user),
        "success": True
    }


# ────────────────────────────────────────────────
# DOWNLOAD
# ────────────────────────────────────────────────
@app.get("/download/latest")
async def download(user=Depends(get_current_user)):
    zip_data = runtime.last_zip.get(user)

    if zip_data and os.path.exists(zip_data["path"]):
        return FileResponse(zip_data["path"], filename=zip_data["filename"])

    raise HTTPException(404, "No build")