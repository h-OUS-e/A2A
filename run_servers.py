"""
Starts all 3 agent servers.
Usage: python run_servers.py
Press Ctrl+C to stop all agents.
"""

import subprocess
import sys
import time
import signal
from langchain_openai import ChatOpenAI
from openai import AuthenticationError, APIStatusError
import os

AGENTS = [
    ("Person A", "agents/person_a/server.py"),
    ("Person B", "agents/person_b/server.py"),
    ("Person C", "agents/person_c/server.py"),
]


def validate_openai_key(api_key: str) -> ChatOpenAI:
    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        api_key=api_key,               # supported in latest docs
        max_completion_tokens=1,       # keep it cheap (LangChain maps legacy max_tokens too)
        temperature=0,
    )
    try:
        llm.invoke("ping")            # real request -> forces auth check
        return llm
    except AuthenticationError as e:
        raise ValueError("Invalid OpenAI API key") from e
    except APIStatusError as e:
        # extra safety: if a 401 comes back as a status error
        if getattr(e, "status_code", None) == 401:
            raise ValueError("Invalid OpenAI API key") from e
        raise

def main():
    llm = validate_openai_key(os.getenv("OPENAI_API_KEY_SDIC"))
    print(llm)
    processes = []

    for name, script in AGENTS:
        print(f"Starting {name} ({script})...")
        proc = subprocess.Popen(
            [sys.executable, "-u", "-m", script.replace("/", ".").replace(".py", "")],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        processes.append((name, proc))
        time.sleep(1)  # stagger startup

    print(f"\nAll {len(processes)} agents started. Press Ctrl+C to stop.\n")

    def shutdown(sig, frame):
        print("\nShutting down all agents...")
        for name, proc in processes:
            proc.terminate()
        for name, proc in processes:
            proc.wait()
            print(f"  {name} stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Wait for any process to exit
    while True:
        for name, proc in processes:
            
            ret = proc.poll()
            if ret is not None:
                print(f"\n{name} exited with code {ret}. Stopping all...")
                shutdown(None, None)
        time.sleep(1)


if __name__ == "__main__":
    main()
