import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Research settings
RESEARCH_MAX_SOURCES = int(os.getenv("RESEARCH_MAX_SOURCES", "10"))
RESEARCH_TIMEOUT = int(os.getenv("RESEARCH_TIMEOUT", "60"))
RESEARCH_DEPTH = os.getenv("RESEARCH_DEPTH", "advanced")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///builds.db")

# Backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")