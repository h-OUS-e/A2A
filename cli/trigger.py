"""
Human interface — sends a natural language message to Person A's agent, and receives a response.
This is like a low-level frontend. Ideally, we would connect this to a nicer visualization,
and stream text and show options on the fly. We would also have "human-in-the-loop",
and store previous message history (compacted).
Usage: python cli/trigger.py "Schedule a 1-hour meeting with Person B and Person C"
"""

import sys
import asyncio
import logging
import time

import httpx
from a2a.client import ClientFactory
from a2a.client.client import ClientConfig
from a2a.types import Message, Part, TextPart, Role
from a2a.utils.parts import get_text_parts

from config import KNOWN_AGENTS
from shared.logging_config import setup_logging


PERSON_A_URL = KNOWN_AGENTS["person_a"]


def extract_text(parts: list[Part]) -> str:
    """Extract text from a list of A2A Part objects."""
    return "\n".join(get_text_parts(parts))


async def send_request(message_text: str):
    """Send a message to Person A's agent and print the response."""
    logger = logging.getLogger("trigger_client")
    request_id = f"cli_{int(time.time() * 1000)}"

    # logger.info(f"[{request_id}] Sending to Person A's agent: {message_text}")
    # print(f"Sending to Person A's agent: {message_text}\n")

    try:
        # Create httpx client with increased timeout
        http_client = httpx.AsyncClient(timeout=180.0)  # 3 minutes
        logger.debug(f"[{request_id}] Created HTTP client with 180s timeout")

        # Connect to Person A's A2A server
        connect_start = time.time()
        logger.info(f"[{request_id}] Connecting to {PERSON_A_URL}...")

        client = await ClientFactory.connect(
            agent=PERSON_A_URL,
            client_config=ClientConfig(
                streaming=False,
                httpx_client=http_client
            ),
        )

        connect_duration = time.time() - connect_start
        logger.info(f"[{request_id}] Connected in {connect_duration:.2f}s")

        # Build the message
        request = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=message_text))],
            messageId=f"trigger-msg-{request_id}",
        )

        # Send and collect response
        send_start = time.time()
        logger.info(f"[{request_id}] Sending request...")

        # We send the message with client.send_message() async, then wait for event.
        async for event in client.send_message(
            request, request_metadata={"sender": "human"}
        ):
            event_duration = time.time() - send_start
            logger.debug(f"[{request_id}] Received event after {event_duration:.2f}s")

            # Extracting info from received event.
            # Event is either a Message or (Task, UpdateEvent)
            if isinstance(event, Message):
                text = extract_text(event.parts)
                if text:
                    total_duration = time.time() - send_start
                    logger.info(f"[{request_id}] Received response in {total_duration:.2f}s")
                    print(f"Response:\n{text}")
                else:
                    logger.warning(f"[{request_id}] Received message with no text")
                    print(f"Response (no text): {event}")
            
            elif isinstance(event, tuple):
                task, _ = event
                if task.history:
                    last_msg = task.history[-1]
                    text = extract_text(last_msg.parts)
                    if text:
                        total_duration = time.time() - send_start
                        logger.info(f"[{request_id}] Received task history in {total_duration:.2f}s")
                        print(f"Response:\n{text}")
                elif task.artifacts:
                    for artifact in task.artifacts:
                        text = extract_text(artifact.parts)
                        if text:
                            total_duration = time.time() - send_start
                            logger.info(f"[{request_id}] Received artifacts in {total_duration:.2f}s")
                            print(f"Response:\n{text}")
                else:
                    logger.info(f"[{request_id}] Task status: {task.status}")
                    print(f"Task status: {task.status}")
            else:
                logger.warning(f"[{request_id}] Received unexpected event type")
                print(f"Raw response:\n{event}")

        logger.info(f"[{request_id}] Request completed")

    except httpx.TimeoutException as e:
        logger.error(f"[{request_id}] Request timed out after 180s: {e}")
        print("ERROR: Request timed out after 180 seconds")
    except Exception as e:
        logger.error(f"[{request_id}] Request failed: {e}", exc_info=True)
        print(f"ERROR: {e}")


def main():
    # Setup logging
    setup_logging("trigger_client", level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python cli/trigger.py \"Your message here\"")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    asyncio.run(send_request(message))


if __name__ == "__main__":
    main()
