"""
Person B's scheduling agent — responder only, no orchestration tools.
Uses the base SchedulingAgent as-is.
"""

from pathlib import Path
from agents.base_agent import SchedulingAgent

AGENT_DIR = Path(__file__).parent

# Person B only knows Person A
KNOWN_AGENTS = {
    "person_a": "http://localhost:10001",
}


def create_person_b_agent() -> SchedulingAgent:
    """Create Person B's scheduling agent — no extra tools."""
    return SchedulingAgent(
        soul_path=str(AGENT_DIR / "soul.md"),
        context_path=str(AGENT_DIR / "person_context.md"),
        calendar_path=str(AGENT_DIR / "calendar.csv"),
        agent_name="person_b_scheduling_agent",
    )
