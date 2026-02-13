"""Person C's A2A server — unaware responder agent."""

import logging
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
import uvicorn

from agents.base_agent import SchedulingAgentExecutor
from agents.person_c.agent_card import build_agent_card
from agents.person_c.scheduling_agent import create_person_c_agent
from shared.logging_config import setup_logging


PORT = 10003

def _init_logging():
    # Make idempotent so reload doesn't duplicate handlers
    logger = logging.getLogger("person_c")
    if not logger.handlers:
        setup_logging("person_c", level=logging.INFO)


def create_app():
    _init_logging()
    logging.getLogger("person_c").info("Building app...")

    agent = create_person_c_agent()
    executor = SchedulingAgentExecutor(agent)

    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(), # What does InMemoryTaskStore give us?
    )

    card = build_agent_card(port=PORT)
    app = A2AStarletteApplication(agent_card=card, http_handler=handler)
    return app.build()

def main():
    # Start uvicorn in reload mode, but using an import string so it can re-import on changes
    uvicorn.run(
        "agents.person_c.server:create_app",
        factory=True,
        host="0.0.0.0",
        port=PORT,
        reload=True,
        # Ensures uvicorn doesn't clobber your custom logging
        log_config=None,
        # Optional: if changes aren't detected reliably
        # reload_dirs=["agents", "shared"],
    )

if __name__ == "__main__":
    main()
