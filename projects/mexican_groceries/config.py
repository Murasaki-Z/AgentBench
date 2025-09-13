import os
from dotenv import load_dotenv

load_dotenv()
DEFAULT_MODEL = 'gpt-5-mini-2025-08-07'

SMALL_MODEL = 'gpt-5-nano-2025-08-07'

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

DISCORD_TEST_CHANNEL_ID = os.getenv("DISCORD_TEST_CHANNEL_ID")

DISCORD_BOT_USER_ID = os.getenv("DISCORD_BOT_USER_ID")

DISCORD_TEST_BOT_TOKEN = os.getenv("DISCORD_TEST_BOT_TOKEN")

DISCORD_TEST_BOT_USER_ID = os.getenv("DISCORD_TEST_BOT_USER_ID")



if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found. Please set it in your .env file.")


if not DISCORD_BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN not found. Please set it in your .env file.")


if not DISCORD_TEST_CHANNEL_ID:
    raise ValueError("DISCORD_TEST_CHANNEL_ID not found. Please set it in your .env file.")


if not DISCORD_BOT_USER_ID:
    raise ValueError("DISCORD_BOT_USER_ID not found. Please set it in your .env file.")


if not DISCORD_TEST_BOT_TOKEN:
    raise ValueError("DISCORD_TEST_BOT_TOKEN not found. Please set it in your .env file.")

if not DISCORD_TEST_BOT_USER_ID:
    raise ValueError("DISCORD_TEST_BOT_USER_ID not found. Please set it in your .env file.")


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
IMAGE_GENERATION_PROVIDER = os.getenv("IMAGE_GENERATION_PROVIDER", "openai").lower()

if not GOOGLE_API_KEY:
    print("--- WARNING: GOOGLE_API_KEY not found. Gemini image generation will be disabled. ---")

if IMAGE_GENERATION_PROVIDER not in ["gemini", "openai"]:
    raise ValueError(f"Invalid IMAGE_GENERATION_PROVIDER: '{IMAGE_GENERATION_PROVIDER}'. Must be 'gemini' or 'openai'.")