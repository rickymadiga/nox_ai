from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/paystack/callback")
async def paystack_callback(request: Request):

    reference = request.query_params.get("reference")

    # 🔥 TODO:
    # Verify payment with Paystack
    # Add credits to user

    return {
        "status": "success",
        "message": f"Payment completed for {reference}"
    }