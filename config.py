import os

# OpenAI — bridge env var so LangChain's ChatOpenAI can find it
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY_SDIC")
if OPENAI_API_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
OPENAI_MODEL = "gpt-5.2"

# Agent servers
KNOWN_AGENTS = {
    "person_a": "http://localhost:10001",
    "person_b": "http://localhost:10002",
    "person_c": "http://localhost:10003",
}
