"""
app/config.py
Loads all environment variables via python-dotenv.
Zero hardcoded credentials.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# GitHub Gist
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

# HuggingFace
HF_API_TOKEN: str = os.getenv("HF_API_TOKEN", "")

# App settings
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "4000"))
