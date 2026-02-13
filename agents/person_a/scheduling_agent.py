"""
Person A's scheduling agent — extends the base with orchestration tools.
Can send messages to other agents via A2A to coordinate meetings.
"""

import logging
import time
from pathlib import Path

import httpx
from langchain_core.tools import tool
from a2a.client import ClientFactory
from a2a.client.client import ClientConfig
from a2a.types import Message, Part, TextPart, Role
from a2a.utils.parts import get_text_parts

from agents.base_agent import SchedulingAgent
from shared.agent_registry import AgentRegistry


# Initialize logger - will use person_a logger from server setup
logger = logging.getLogger("person_a")


# Person A's known agents — who this agent can talk to
KNOWN_AGENTS = {
    "person_b": "http://localhost:10002",
    "person_c": "http://localhost:10003",
}

AGENT_DIR = Path(__file__).parent


def build_orchestration_tools(registry: AgentRegistry) -> list:
    """Build tools that let Person A's agent talk to other agents."""

    @tool
    async def send_message_to_agent(agent_name: str, message: str) -> str:
        """Send a natural language message to another person's agent via A2A.
        Use this to propose meeting times or confirm meetings.
        Args:
            agent_name: The agent to contact (e.g. "person_b", "person_c")
            message: The natural language message to send
        """
        request_id = f"a2a_{agent_name}_{int(time.time() * 1000)}"
        logger.info(f"[{request_id}] Sending message to '{agent_name}'")
        logger.info(f"[{request_id}] >>> {message[:150]}{'...' if len(message) > 150 else ''}")
        try:
            # Lookup agent URL
            url = registry.get_agent_url(agent_name)

            # Create httpx client with timeout
            http_client = httpx.AsyncClient(timeout=180.0)  # 3 minutes

            # Connect to agent
            connect_start = time.time()
            logger.info(f"[{request_id}] Connecting to {agent_name}...")

            client = await ClientFactory.connect(
                agent=url,
                client_config=ClientConfig(
                    streaming=False,
                    httpx_client=http_client
                ),
            )

            connect_duration = time.time() - connect_start
            logger.info(f"[{request_id}] Connected in {connect_duration:.2f}s")

            # Build and send request
            request = Message(
                role=Role.user,
                parts=[Part(root=TextPart(text=message))],
                messageId=f"msg-{request_id}",
            )

            send_start = time.time()
            logger.info(f"[{request_id}] Sending request to {agent_name}...")

            # Collect response from async iterator
            async for event in client.send_message(
                request, request_metadata={"sender": "person_a"}
            ):
                event_duration = time.time() - send_start

                if isinstance(event, Message):
                    texts = get_text_parts(event.parts)
                    response = "\n".join(texts) if texts else str(event)
                    logger.info(f"[{request_id}] Got response in {event_duration:.2f}s")
                    logger.info(f"[{request_id}] <<< {response[:150]}{'...' if len(response) > 150 else ''}")
                    return response
                elif isinstance(event, tuple):
                    task, _ = event
                    if task.history:
                        last_msg = task.history[-1]
                        texts = get_text_parts(last_msg.parts)
                        response = "\n".join(texts) if texts else str(last_msg)
                        logger.info(f"[{request_id}] Got task history in {event_duration:.2f}s")
                        logger.info(f"[{request_id}] <<< {response[:150]}{'...' if len(response) > 150 else ''}")
                        return response
                    if task.artifacts:
                        for artifact in task.artifacts:
                            texts = get_text_parts(artifact.parts)
                            if texts:
                                response = "\n".join(texts)
                                logger.info(f"[{request_id}] Got artifacts in {event_duration:.2f}s")
                                logger.info(f"[{request_id}] <<< {response[:150]}{'...' if len(response) > 150 else ''}")
                                return response
                    logger.warning(f"[{request_id}] Task status: {task.status}")
                    return f"Task status: {task.status}"

            logger.warning(f"[{request_id}] No response received from {agent_name}")
            return "No response received"

        except Exception as e:
            logger.error(f"[{request_id}] Failed to contact {agent_name}: {e}", exc_info=True)
            return f"Failed to contact {agent_name}: {e}"

    @tool
    def list_available_agents() -> str:
        """List all agents I can communicate with."""
        agents = registry.list_known_agents()
        return f"Known agents: {', '.join(agents)}"

    return [send_message_to_agent, list_available_agents]


def create_person_a_agent() -> SchedulingAgent:
    """Create Person A's scheduling agent with orchestration tools."""
    logger.info("Creating Person A's agent with orchestration tools")
    registry = AgentRegistry(KNOWN_AGENTS)
    extra_tools = build_orchestration_tools(registry)

    return SchedulingAgent(
        soul_path=str(AGENT_DIR / "soul.md"),
        context_path=str(AGENT_DIR / "person_context.md"),
        calendar_path=str(AGENT_DIR / "calendar.csv"),
        extra_tools=extra_tools,
        agent_name="person_a_scheduling_agent",
    )
