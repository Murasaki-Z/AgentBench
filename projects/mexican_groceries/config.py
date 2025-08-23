import os
from dotenv import load_dotenv

load_dotenv()
DEFAULT_MODEL = 'gpt-4.1-mini-2025-04-14'

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")


