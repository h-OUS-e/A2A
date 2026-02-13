# A2A Prototype — Build Progress

## Completed
- [x] `requirements.txt` + `.gitignore`
- [x] `config.py` — OpenAI API key (from `OPENAI_API_KEY_SDIC` env var), model (`gpt-5.2`)
- [x] `shared/calendar_store.py` — CalendarStore class for CSV read/write (get_events, get_free_slots, is_available, book_event, cancel_event)
- [x] `shared/agent_registry.py` — AgentRegistry class, takes known_agents dict per agent (not global)
- [x] `agents/base_agent.py` — SchedulingAgent (LangChain `create_agent` + calendar tools) and SchedulingAgentExecutor (A2A bridge)
- [x] `agents/person_a/` — Full orchestrator agent: soul.md, person_context.md, calendar.csv (8 events), models.py (NegotiationState), agent_card.py, scheduling_agent.py (with `send_message_to_agent` + `list_available_agents` tools), server.py (port 10001)

## Remaining

### 7. Person B agent (aware responder) — `agents/person_b/`
- Same structure as Person A but **no orchestration tools** (no send_message_to_agent)
- soul.md: cooperative, expects meetings, auto-accepts from known colleagues
- person_context.md: Jordan Kim, Product Manager, expects Q3 roadmap meeting from Person A
- calendar.csv: 5-8 realistic events with some conflicts
- agent_card.py: skills = check_availability only
- scheduling_agent.py: just uses base SchedulingAgent as-is (no extra tools)
- server.py: port 10002
- KNOWN_AGENTS: only knows person_a

### 8. Person C agent (unaware responder) — `agents/person_c/`
- Same as Person B but with **protective soul.md**
- soul.md: cautious, guards person's time, checks relationships before accepting unexpected requests
- person_context.md: Sam Rivera, Design Lead, does NOT expect a meeting, but knows Person A as a colleague
- calendar.csv: 5-8 events, different schedule pattern
- server.py: port 10003
- KNOWN_AGENTS: only knows person_a

### 9. CLI trigger — `cli/trigger.py`
- Simple script that sends a natural language message to Person A's agent via A2A client
- Usage: `python cli/trigger.py "Schedule a 1-hour meeting with Person B and Person C to discuss Q3 roadmap"`
- Prints the response/negotiation result

### 10. Startup script — `run_all.py`
- Starts all 3 agent servers (person_a, person_b, person_c)
- Waits for all to be healthy before printing ready message

### 11. Seed data & templates — `data/`
- `calendar_template.csv` — empty CSV with headers
- `soul_template.md` — template for creating new agent souls
- `person_context_template.md` — template for new person contexts

### 12. End-to-end test
- Start all 3 agents via run_all.py
- Trigger a meeting request via cli/trigger.py
- Verify all 3 calendar.csv files have the meeting booked
- Verify no conflicts with existing events

## Key Architecture Decisions
- Agents communicate in **natural language** over A2A — no shared schemas
- Each agent has its own `KNOWN_AGENTS` dict (not global)
- `shared/` is prototype plumbing only (CalendarStore, AgentRegistry)
- Person A has orchestration tools; Person B and C only respond
- Hybrid autonomy: agents auto-decide by default, soul.md can flag scenarios for human review via `input_required`

## Essential SDK/API Knowledge

### A2A Python SDK (`a2a-sdk==0.3.22`)
- Install: `pip install a2a-sdk`
- Key imports:
  ```python
  from a2a.server.agent_execution import AgentExecutor  # Abstract base - implement execute() and cancel()
  from a2a.server.agent_execution.context import RequestContext  # Has .get_user_input() to read incoming message
  from a2a.server.events.event_queue import EventQueue  # Use .enqueue_event() to send responses
  from a2a.server.apps import A2AStarletteApplication  # Starlette HTTP server wrapper
  from a2a.server.request_handlers import DefaultRequestHandler  # Wires executor + task store
  from a2a.server.tasks import InMemoryTaskStore  # In-memory task persistence
  from a2a.types import AgentCard, AgentSkill, AgentCapabilities  # AgentCard definition
  from a2a.utils import new_agent_text_message  # Helper to create text response message
  from a2a.client import A2AClient  # Client for calling other agents
  from a2a.types import MessageSendParams, Message, TextPart, Role  # For building client messages
  ```
- AgentExecutor requires two async methods: `execute(context, event_queue)` and `cancel(context, event_queue)`
- `context.get_user_input()` extracts text from incoming message
- `await event_queue.enqueue_event(new_agent_text_message("response"))` sends response back
- Client usage: `client = await A2AClient.get_client_from_agent_card_url(url)` then `client.send_message(params)`
- AgentCard served at `/.well-known/agent.json` automatically
- Task states: working → completed | failed | canceled | input_required | auth_required

### LangChain (`langchain==1.2.10`, `langchain-openai==1.1.8`)
- Modern agent creation (NOT legacy AgentExecutor):
  ```python
  from langchain.agents import create_agent
  from langchain_openai import ChatOpenAI
  from langchain_core.tools import tool

  llm = ChatOpenAI(model="gpt-5.2", api_key=key)
  agent = create_agent(model=llm, tools=[...], prompt="system prompt")
  result = await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
  response_text = result["messages"][-1].content
  ```
- Tools use `@tool` decorator with docstrings for LLM descriptions
- `create_agent` replaced legacy `create_react_agent` and `create_tool_calling_agent`

### OpenAI GPT-5.2
- Model ID: `gpt-5.2`
- Use via LangChain's `ChatOpenAI(model="gpt-5.2")`
- Supports tool calling natively
