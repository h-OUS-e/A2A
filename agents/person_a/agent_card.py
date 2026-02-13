"""Builds the A2A AgentCard for Person A's agent."""

from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
)


def build_agent_card(host: str = "localhost", port: int = 10001) -> AgentCard:
    return AgentCard(
        name="Person A Scheduling Agent",
        description=(
            "Personal scheduling agent for Alex Chen (Engineering Lead). "
            "Can initiate and coordinate meetings with other agents."
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
                id="schedule_meeting",
                name="Schedule Meeting",
                description=(
                    "Initiate and negotiate meetings with other agents. "
                    "Proposes times, collects availability, and confirms."
                ),
                tags=["scheduling", "calendar", "meeting"],
                examples=[
                    "Schedule a 1-hour meeting with Person B and Person C next week",
                    "Find a time that works for everyone on Tuesday",
                ],
            ),
            AgentSkill(
                id="check_availability",
                name="Check Availability",
                description="Check calendar availability for given time slots.",
                tags=["calendar", "availability"],
                examples=["What's your availability on Monday?"],
            ),
        ],
    )
