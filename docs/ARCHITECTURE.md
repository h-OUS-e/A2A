# A2A Meeting Scheduling — Architecture

## Scenario
3 people in SF need to schedule a meeting. Each has a personal AI agent. Person A initiates, Person B expects it, Person C doesn't. Agents negotiate via the A2A protocol using natural language.

## Structure
```
A2A/
├── config.py                  # Known agent URLs, ports, model config
├── run_all.py                 # Starts all 3 agents
├── requirements.txt
│
├── shared/                    # Prototype plumbing only
│   ├── calendar_store.py     # CSV calendar read/write
│   └── agent_registry.py    # Agent discovery from config
│
├── agents/
│   ├── base_agent.py         # Base class: loads soul + context, builds LangChain agent
│   │
│   ├── person_a/             # Orchestrator (port 10001)
│   │   ├── soul.md           # Agent personality & rules
│   │   ├── person_context.md # Human's info & preferences
│   │   ├── calendar.csv      # Schedule
│   │   ├── models.py         # Internal negotiation tracking
│   │   ├── agent_card.py     # A2A AgentCard
│   │   ├── agent_executor.py # A2A ↔ LangChain bridge
│   │   ├── scheduling_agent.py # LangChain agent + orchestration tools
│   │   └── server.py
│   │
│   ├── person_b/             # Responder (port 10002) — same structure, no models.py
│   └── person_c/             # Responder (port 10003) — same structure, protective soul.md
│
├── cli/
│   └── trigger.py            # Human sends meeting request to Person A's agent
│
└── data/                     # Templates for new agents
```

## How Agents Talk
Natural language over A2A. No shared schemas. Each agent uses its LLM to understand messages and respond. Person A may track state internally with Pydantic models, but nothing is shared across agents.

## Flow
1. Human triggers Person A's agent via CLI
2. Person A checks own calendar, picks available slots
3. Person A sends natural language proposals to B and C via A2A
4. B and C check their calendars, respond in natural language
5. Person A finds common slot, sends confirmation
6. Everyone books on their calendar
7. Up to 3 negotiation rounds before escalating to human

## Tech
- `a2a-sdk` — A2A protocol
- `langchain-openai` — GPT-5.2
- CSV files — fake calendars (swappable later)
- Uvicorn/Starlette — agent servers

## Key Decisions
- **Hybrid autonomy**: Agents auto-decide by default; soul.md can flag scenarios for human approval
- **Static discovery**: config.py maps agent names to URLs
- **Pre-populated calendars**: Realistic schedules with conflicts
- **Natural language comms**: Agents are opaque to each other, just like in the real world
