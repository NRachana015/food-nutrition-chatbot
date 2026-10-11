
"""
NutriBot configuration.

Priority:
1. Streamlit Cloud Secrets
2. Local environment variable / .env file
"""

import os

import streamlit as st
from dotenv import load_dotenv

# Load local .env variables when available.
load_dotenv()

# Read the API key from Streamlit Secrets first.
USDA_API_KEY = ""

try:
    USDA_API_KEY = str(st.secrets.get("USDA_API_KEY", "")).strip()
except (FileNotFoundError, RuntimeError):
    # Streamlit Secrets may not exist in a local environment.
    pass

# Fall back to the environment variable or local .env file.
if not USDA_API_KEY:
    USDA_API_KEY = os.getenv("USDA_API_KEY", "").strip()

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

if not USDA_API_KEY:
    raise RuntimeError(
        "USDA_API_KEY was not found. "
        "Add it to Streamlit Secrets or your local .env file."
    )
