import asyncio
from urllib import request
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from fastapi import Request

from nox_backend.core.database import get_db
from nox_backend.models.user import User
from nox_backend.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    get_current_user
)

router = APIRouter(tags=["auth"])

# ============================================================================
# REQUEST MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class DevLoginRequest(BaseModel):
    username: str


# ============================================================================
# RESPONSE HELPER
# ============================================================================

def success_response(data=None, message="Success"):
    return {
        "success": True,
        "message": message,
        "data": data or {}
    }


def error_response(message="Error"):
    return {
        "success": False,
        "error": message,
        "data": {}
    }


# ============================================================================
# AUTH ROUTES
# ============================================================================

@router.post("/signup")
def signup(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        # Check existing user
        existing_user = db.query(User).filter(
            (User.username == data.username) |
            (User.email == data.email)
        ).first()

        if existing_user:
            return error_response("Username or email already exists")

        # Create user
        user = User(
            username=data.username,
            email=data.email,                    # ← Now this will work
            password=hash_password(data.password)
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return success_response(
            data={
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            },
            message="User created successfully"
        )

    except Exception as e:
        return error_response(str(e))


# ----------------------------------------------------------------------------

@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(
            User.username == data.username
        ).first()

        if not user or not verify_password(data.password, user.password):
            return error_response("Invalid username or password")

        token = create_access_token(user.username)

        return success_response(
            data={
                "token": token,
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            },
            message="Login successful"
        )

    except Exception as e:
        return error_response(str(e))


# ----------------------------------------------------------------------------

@router.get("/verify")
def verify(authorization: str = Header(None), db: Session = Depends(get_db)):
    try:
        if not authorization:
            return error_response("Missing token")

        token = authorization.replace("Bearer ", "")
        payload = verify_token(token)

        username = payload.get("sub")

        user = db.query(User).filter(User.username == username).first()
        if not user:
            return error_response("User not found")

        return success_response(
            data={
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.username in ["admin", "nox", "cosmic ethic"]
                }
            },
            message="Token valid"
        )

    except Exception:
        return error_response("Invalid token")


# ----------------------------------------------------------------------------

@router.post("/refresh")
def refresh(authorization: str = Header(None)):
    try:
        if not authorization:
            return error_response("Missing token")

        token = authorization.replace("Bearer ", "")
        payload = verify_token(token)

        new_token = create_access_token(payload.get("sub"))

        return success_response(
            data={
                "token": new_token
            },
            message="Token refreshed"
        )

    except Exception:
        return error_response("Invalid token")


# ----------------------------------------------------------------------------

@router.post("/admin_login")
def admin_login(payload: DevLoginRequest):
    try:
        username = payload.username.strip().lower()

        if username not in ["nox", "admin", "cosmic ethic"]:
            return error_response("Not a valid admin user")

        token = create_access_token(username)

        return success_response(
            data={
                "token": token,
                "user": {
                    "username": username,
                    "email": "",
                    "is_admin": True
                }
            },
            message="Admin login successful"
        )

    except Exception as e:
        return error_response(str(e))


# ============================================================================
# STREAM LOGS
# ============================================================================

@router.get("/stream")
async def stream_logs(request: Request, user: str = Depends(get_current_user)):
    engine = request.app.state.engine
    user_id = str(user).lower().strip()

    async def event_stream():
        last_index = 0

        while True:
            try:
                logs = engine.runtime.get_logs(user_id)

                if logs and last_index < len(logs):
                    for log in logs[last_index:]:
                        yield f"data: {log}\n\n"
                    last_index = len(logs)

                await asyncio.sleep(0.2)

            except Exception as e:
                yield f"data: ERROR: {str(e)}\n\n"
                await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )