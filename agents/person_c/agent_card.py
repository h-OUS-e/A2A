"""Builds the A2A AgentCard for Person C's agent."""

from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
)


def build_agent_card(host: str = "localhost", port: int = 10003) -> AgentCard:
    return AgentCard(
        name="Person C Scheduling Agent",
        description=(
            "Personal scheduling agent for Sam Rivera (Design Lead). "
            "Responds to meeting requests and checks availability."
        ),
        url=f"http://{host}:{port}/",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        version="0.1.0",
        capabilities=AgentCapabilities(
            streaming=False,
            pushNotifications=False,
        ),
        skills=[
            AgentSkill(
                id="check_availability",
                name="Check Availability",
                description="Check calendar availability for given time slots.",
                tags=["calendar", "availability"],
                examples=[
                    "Are you free Tuesday 2-3pm?",
                    "What's your availability this week?",
                ],
            ),
        ],
    )
