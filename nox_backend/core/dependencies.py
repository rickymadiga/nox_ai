from fastapi import Request, HTTPException, Depends

from nox_backend.core.rate_limiter import rate_limiter
from nox_backend.core.security import get_current_user


def limit_requests(limit: int, window: int):
    def dependency(request: Request):
        ip = request.client.host

        key = f"ip:{ip}"

        if not rate_limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Slow down."
            )

    return dependency


def limit_user_requests(limit: int, window: int):
    def dependency(
        request: Request,
        user: str = Depends(get_current_user)
    ):
        key = f"user:{user}"

        if not rate_limiter.is_allowed(key, limit, window):
            raise HTTPException(
                status_code=429,
                detail="Too many requests (user limit)."
            )

    return dependency