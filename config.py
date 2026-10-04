import os

from dotenv import load_dotenv


load_dotenv()


USDA_API_KEY = os.getenv("USDA_API_KEY")

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"


if not USDA_API_KEY:
    raise RuntimeError(
        "USDA_API_KEY was not found. "
        "Please add it to the .env file."
    )