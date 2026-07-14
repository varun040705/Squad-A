import os
from dotenv import load_dotenv

# This automatically searches for a .env file and loads your key!
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your_api_key_here")
ELEMENT_CEILINGS = {
    "COLUMN": 95,
    "BEAM": 80,
    "WALL": 75,
    "SLAB": 55,
    "FOUNDATION": 35
}
