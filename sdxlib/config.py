# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get BASE_URL from environment variable with a default fallback
BASE_URL = os.getenv("SDX_BASE_URL", "https://sdxapi.atlanticwave-sdx.ai/")

