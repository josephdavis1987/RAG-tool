import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

TOP_K_CHUNKS = 5
INCLUDE_NEIGHBOR_CHUNKS = True

MAX_CONTEXT_TOKENS = 8000
MAX_RESPONSE_TOKENS = 1500