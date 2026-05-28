import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "instalily-case-study")

LOW_STOCK_THRESHOLD = 5

# for higher-quality outputs with fewer tokens and fewer retries
SUPERVISOR_MODEL = 'gpt-5.5-2026-04-23'

AGENT_MODEL = 'gpt-5.4-mini'

REASON_MODEL = 'claude-sonnet-4-6'