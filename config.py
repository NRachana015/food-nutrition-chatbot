
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Prefer Streamlit Cloud Secrets, with local .env fallback.
try:
    USDA_API_KEY = st.secrets.get("USDA_API_KEY")
except (FileNotFoundError, RuntimeError):
    USDA_API_KEY = None

USDA_API_KEY = USDA_API_KEY or os.getenv("USDA_API_KEY")

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

if not USDA_API_KEY:
    raise RuntimeError(
        "USDA_API_KEY was not found. "
        "Add it to Streamlit Secrets or your local .env file."
    )
