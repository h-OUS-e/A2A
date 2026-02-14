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
from shared.utils.a2a_parts import get_metadata_parts, extract_text

from config import KNOWN_AGENTS
from shared.logging_config import setup_logging

# for prettier printing inside console
from rich.console import Console
console = Console(markup=False)
# from rich import print


PERSON_A_URL = KNOWN_AGENTS["person_a"]



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
                streaming=True,
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
            # print("EVENT", event)
            
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
                task, update_event  = event
                
                # # Check if there's a status message (intermediate events)
                if task.status and task.status.message:
                    print("State Task: ", f"{task.status.state or "no state"}")
                    print("State Update Event: ", f"{update_event.status.state or "no state"}")
                    print("Update Event Message Id: ", f"{update_event.status.message.message_id or "no id"}")
                    text = extract_text(update_event.status.message.parts)
                    metadata = get_metadata_parts(update_event.status.message.parts)
                    # console.print("TEST METADATA EXTRACTION: ", metadata)
                    console.print("What is update event?", update_event)                    
                    console.print("What is task?", task)
                    if text:
                        from_to = (metadata.get("from_to") if isinstance(metadata, dict) else getattr(metadata, "from_to", None))
                        console.print(f"A2A Chat:\n{from_to}:    \n {text}\n\n")

                        # print(f"INTERMEDIATE UPDATE EVENT TEXT:\n{text_update_event}")
                    
                # # No need to check history for the final response since we set final_response=True in base_agent.py
                # if task.history:
                #     for msg in task.history:
                #         text = extract_text(msg.parts)
                #         if text:
                #             print(f"HISTORY:\n{text}")

                         
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
