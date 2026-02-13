"""
Agent discovery.
Each agent passes in its own known_agents dict.
"""

import httpx


class AgentRegistry:
    """Lookup and fetch AgentCards for agents this agent knows about."""

    def __init__(self, known_agents: dict[str, str]):
        """
        Args:
            known_agents: {"person_b": "http://localhost:10002", ...}
        """
        self.known_agents = known_agents

    async def get_agent_card(self, agent_name: str) -> dict:
        """Fetch an agent's AgentCard JSON from its well-known URL."""
        base_url = self.known_agents.get(agent_name)
        if not base_url:
            raise ValueError(f"Unknown agent: {agent_name}")

        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{base_url}/.well-known/agent.json")
            resp.raise_for_status()
            return resp.json()

    async def get_all_agent_cards(self) -> dict[str, dict]:
        """Fetch AgentCards for all known agents."""
        cards = {}
        for name in self.known_agents:
            try:
                cards[name] = await self.get_agent_card(name)
            except Exception:
                cards[name] = None
        return cards

    def get_agent_url(self, agent_name: str) -> str:
        """Get the base URL for a known agent."""
        url = self.known_agents.get(agent_name)
        if not url:
            raise ValueError(f"Unknown agent: {agent_name}")
        return url

    def list_known_agents(self) -> list[str]:
        """List all known agent names."""
        return list(self.known_agents.keys())
