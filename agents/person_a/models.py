"""
Person A's internal models for tracking negotiation state.
These are never shared with other agents — purely internal bookkeeping.
"""

from pydantic import BaseModel


class ProposedSlot(BaseModel):
    date: str       # YYYY-MM-DD
    start_time: str # HH:MM
    end_time: str   # HH:MM


class NegotiationState(BaseModel):
    meeting_id: str
    title: str
    attendees: list[str]
    proposed_slots: list[ProposedSlot]
    responses: dict[str, str]  # agent_name -> their natural language response
    round: int = 1
    confirmed_slot: ProposedSlot | None = None
