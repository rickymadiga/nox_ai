from fastapi import APIRouter, Depends

from nox_backend.core.security import require_admin

router = APIRouter()

@router.get("/stats")
def stats(user=Depends(require_admin)):
    return {"status": "admin ok 🔥"}