import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "instalily-case-study")

LOW_STOCK_THRESHOLD = 5

# i used a cheaper llm for routing - less cost :) 
SUPERVISOR_MODEL = "llama-3.1-8b-instant"

GROQ_MODEL = "llama-3.1-8b-instant"


