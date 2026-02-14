"""
Manual SSE streaming client - bypasses A2A SDK to test real-time event handling.
Usage: python cli/trigger2.py "Schedule a meeting with Person B"
"""

import sys
import asyncio
import logging
import time
import json

import httpx
from httpx_sse import aconnect_sse

from a2a.types import Message, Part, TextPart, Role
from shared.utils.a2a_parts import extract_text, get_metadata_parts
from config import KNOWN_AGENTS
from shared.logging_config import setup_logging

from rich.console import Console
console = Console(markup=False)

PERSON_A_URL = KNOWN_AGENTS["person_a"]

# Global buffer for artifact reassembly
artifact_buffers = {}


async def send_request_sse(message_text: str):
    """Send a message using direct SSE connection."""
    logger = logging.getLogger("trigger2_sse")
    request_id = f"cli_sse_{int(time.time() * 1000)}"

    console.print(f"[bold cyan]Sending to Person A's agent:[/bold cyan] {message_text}\n")
    logger.info(f"[{request_id}] Starting SSE request to {PERSON_A_URL}")

    # Build the A2A request payload
    a2a_request = {
        "jsonrpc": "2.0",
        "method": "sendTask",
        "params": {
            "id": request_id,
            "message": {
                "role": "user",
                "parts": [{"text": message_text}],
                "messageId": f"trigger-msg-{request_id}"
            },
            "metadata": {"sender": "human"}
        },
        "id": 1
    }

    # Construct the SSE endpoint
    sse_url = f"{PERSON_A_URL}/send-task/stream"

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            logger.info(f"[{request_id}] Connecting to SSE stream at {sse_url}")

            async with aconnect_sse(client, "POST", sse_url, json=a2a_request) as event_source:
                console.print(f"[green]✓ SSE connection established[/green]\n")

                async for sse in event_source.aiter_sse():
                    logger.debug(f"[{request_id}] SSE event: {sse.event}, data preview: {sse.data[:100]}...")

                    try:
                        # Parse the JSON-RPC response
                        response_data = json.loads(sse.data)

                        # Check for errors
                        if "error" in response_data and response_data["error"]:
                            error = response_data["error"]
                            console.print(f"[red]ERROR:[/red] {error.get('code')} - {error.get('message')}")
                            break

                        # Process the result
                        result = response_data.get("result")
                        if not result:
                            logger.warning(f"[{request_id}] No result in response")
                            continue

                        result_type = result.get("type")
                        task_id = result.get("id", request_id)
                        is_final = result.get("final", False)

                        # Handle status updates
                        if result_type == "taskStatus":
                            status = result.get("status", {})
                            state = status.get("state", "unknown")
                            message = status.get("message", {})

                            if message:
                                parts = message.get("parts", [])
                                if parts:
                                    # Extract text from parts
                                    text_parts = [p.get("text") for p in parts if p.get("text")]
                                    if text_parts:
                                        text = " ".join(text_parts)

                                        # Extract metadata
                                        metadata_parts = [p for p in parts if p.get("metadata")]
                                        metadata = metadata_parts[0].get("metadata") if metadata_parts else {}
                                        from_to = metadata.get("from_to", "Agent")

                                        console.print(f"[yellow]{state}[/yellow] | {from_to}:")
                                        console.print(f"  {text}\n")
                            else:
                                console.print(f"[yellow]{state}[/yellow]")

                        # Handle artifact updates
                        elif result_type == "taskArtifact":
                            artifact = result.get("artifact", {})
                            name = artifact.get("name", "unnamed")
                            index = artifact.get("index", 0)
                            append = artifact.get("append", False)
                            last_chunk = artifact.get("lastChunk", False)
                            parts = artifact.get("parts", [])

                            logger.info(f"[{request_id}] Artifact: {name} (idx={index}, append={append}, last={last_chunk})")

                            # Buffer artifact parts
                            if task_id not in artifact_buffers:
                                artifact_buffers[task_id] = {}

                            if not append:
                                artifact_buffers[task_id][index] = parts
                            else:
                                if index in artifact_buffers[task_id]:
                                    artifact_buffers[task_id][index].extend(parts)
                                else:
                                    artifact_buffers[task_id][index] = parts

                            # Process complete artifact
                            if last_chunk:
                                complete_parts = artifact_buffers[task_id].pop(index, [])
                                text_parts = [p.get("text") for p in complete_parts if p.get("text")]
                                if text_parts:
                                    text = " ".join(text_parts)
                                    console.print(f"\n[bold green]Artifact: {name}[/bold green]")
                                    console.print(f"{text}\n")

                        # Check if final
                        if is_final:
                            logger.info(f"[{request_id}] Received final event, closing stream")
                            console.print(f"[green]✓ Task completed[/green]")
                            break

                    except json.JSONDecodeError as e:
                        logger.error(f"[{request_id}] Failed to parse JSON: {e}")
                        console.print(f"[red]Failed to parse event data[/red]")
                    except Exception as e:
                        logger.error(f"[{request_id}] Error processing event: {e}", exc_info=True)
                        console.print(f"[red]Error: {e}[/red]")

    except httpx.RequestError as e:
        logger.error(f"[{request_id}] HTTP request error: {e}")
        console.print(f"[red]Connection error: {e}[/red]")
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error: {e}", exc_info=True)
        console.print(f"[red]Error: {e}[/red]")
    finally:
        # Cleanup
        if request_id in artifact_buffers:
            del artifact_buffers[request_id]
        logger.info(f"[{request_id}] Request completed")


def main():
    setup_logging("trigger2_sse", level=logging.INFO)

    if len(sys.argv) < 2:
        print("Usage: python cli/trigger2.py \"Your message here\"")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    asyncio.run(send_request_sse(message))


if __name__ == "__main__":
    main()
