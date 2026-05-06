import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

ALGORITHM = "HS256"
DEV_USERS = {"nox", "admin", "cosmic ethic"}
BUILD_COST = 100

# Optional: Add a safety check
if not PAYSTACK_SECRET_KEY:
    print("⚠️  WARNING: PAYSTACK_SECRET_KEY is not set in .env file!")