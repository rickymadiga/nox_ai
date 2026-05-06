import requests
import os
from typing import Dict

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_BASE_URL = os.getenv("PAYSTACK_BASE_URL", "https://api.paystack.co")


class PaystackService:

    @staticmethod
    def initialize_payment(email: str, amount: int, reference: str) -> Dict:
        """
        Initialize Paystack transaction
        amount MUST be in kobo (₦100 = 10000)
        """

        url = f"{PAYSTACK_BASE_URL}/transaction/initialize"

        headers = {
            "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "email": email,
            "amount": amount * 100,  # convert to kobo
            "reference": reference,
            "callback_url": "http://localhost:8000/paystack/callback"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
        except Exception as e:
            # Catch network and HTTP exceptions
            return {"status": False, "message": f"Request to Paystack failed: {e}"}

        try:
            data = response.json()
        except Exception:
            return {"status": False, "message": "Invalid JSON in Paystack response"}

        # Defensive: If data['status'] is not True, dump reason
        if not data.get("status"):
            return {
                "status": False,
                "message": data.get("message", "Paystack init failed"),
            }

        # Defensive: Guard against missing 'data' or 'authorization_url'
        result_data = data.get("data", {})
        payment_url = result_data.get("authorization_url")
        reference_rsp = result_data.get("reference")

        if not payment_url or not reference_rsp:
            # Sometimes Paystack gives status=True but with missing data (rare)
            return {
                "status": False,
                "message": "Payment URL or reference missing in Paystack response."
            }

        return {
            "status": True,
            "payment_url": payment_url,
            "reference": reference_rsp
        }