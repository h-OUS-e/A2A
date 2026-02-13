# A2A Meeting Scheduling — Flow Diagram

## How a single agent works (the stack)

```
┌─────────────────────────────────────────────────┐
│                  A2A NETWORK                     │
│         (other agents send messages here)        │
└──────────────────────┬──────────────────────────┘
                       │ HTTP (JSON-RPC)
                       ▼
┌─────────────────────────────────────────────────┐
│          A2A SDK (server.py)                     │
│  - Uvicorn / Starlette HTTP server               │
│  - Serves AgentCard at /.well-known/agent.json   │
│  - DefaultRequestHandler routes requests          │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│     SchedulingAgentExecutor (base_agent.py)      │
│  - A2A → LangChain bridge                        │
│  - context.get_user_input() → text in            │
│  - event_queue.enqueue_event() → text out         │
└──────────────────────┬──────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────┐
│        SchedulingAgent (base_agent.py)           │
│  - LangChain create_agent + GPT-5.2              │
│  - System prompt = soul.md + person_context.md    │
│  - LLM decides which tools to call                │
└──────────┬───────────┬──────────────────────────┘
           │           │
           ▼           ▼
┌──────────────┐ ┌──────────────────┐
│ Calendar     │ │ Orchestration    │
│ Tools        │ │ Tools            │
│              │ │ (Person A only)  │
│ - check_     │ │                  │
│   availability│ │ - send_message_ │
│ - get_free_  │ │   to_agent      │
│   slots      │ │ - list_available│
│ - get_       │ │   _agents       │
│   schedule   │ │                  │
│ - book_      │ └────────┬─────── │
│   meeting    │          │        │
└──────┬───────┘          │
       │                  │
       ▼                  ▼
┌──────────────┐ ┌──────────────────┐
│ CalendarStore│ │ AgentRegistry    │
│ (CSV file)   │ │ + A2AClient      │
└──────────────┘ │ (calls other     │
                 │  agents via A2A) │
                 └──────────────────┘
```

## Full meeting scheduling flow

```
  HUMAN                 PERSON A (10001)           PERSON B (10002)          PERSON C (10003)
    │                   (orchestrator)              (aware)                   (unaware)
    │                        │                         │                         │
    │  "Schedule meeting     │                         │                         │
    │   with B and C"        │                         │                         │
    │───────────────────────>│                         │                         │
    │     (A2A SendMessage)  │                         │                         │
    │                        │                         │                         │
    │                   ┌────┴────┐                    │                         │
    │                   │ LLM     │                    │                         │
    │                   │ reads   │                    │                         │
    │                   │ soul.md │                    │                         │
    │                   │ +context│                    │                         │
    │                   └────┬────┘                    │                         │
    │                        │                         │                         │
    │                   check own calendar             │                         │
    │                   (calendar tool)                │                         │
    │                        │                         │                         │
    │                        │  "Are you free          │                         │
    │                        │   Tue 10-11am,          │                         │
    │                        │   Wed 2-3pm?"           │                         │
    │                        │────────────────────────>│                         │
    │                        │   (A2A SendMessage)     │                         │
    │                        │                         │                         │
    │                        │  same question          │                         │
    │                        │─────────────────────────────────────────────────>│
    │                        │                         │    (A2A SendMessage)    │
    │                        │                         │                         │
    │                        │                    ┌────┴────┐             ┌──────┴──────┐
    │                        │                    │ LLM     │             │ LLM         │
    │                        │                    │ checks  │             │ checks      │
    │                        │                    │ calendar│             │ soul.md:    │
    │                        │                    │ (aware, │             │ "is Person A│
    │                        │                    │ expects │             │  known?"    │
    │                        │                    │ this)   │             │ → yes, ok   │
    │                        │                    └────┬────┘             │ checks cal  │
    │                        │                         │                 └──────┬──────┘
    │                        │                         │                        │
    │                        │  "Available Tue 10-11"  │                        │
    │                        │<────────────────────────│                        │
    │                        │                         │                        │
    │                        │         "Busy Tue, available Wed 2-3"            │
    │                        │<────────────────────────────────────────────────│
    │                        │                         │                        │
    │                   ┌────┴────┐                    │                        │
    │                   │ LLM     │                    │                        │
    │                   │ finds   │                    │                        │
    │                   │ common  │                    │                        │
    │                   │ slot    │                    │                        │
    │                   └────┬────┘                    │                        │
    │                        │                         │                        │
    │                        │  "Confirmed: Wed 2-3pm" │                        │
    │                        │────────────────────────>│                        │
    │                        │────────────────────────────────────────────────>│
    │                        │                         │                        │
    │                        │                    books on CSV            books on CSV
    │                        │                         │                        │
    │                   books on own CSV                │                        │
    │                        │                         │                        │
    │  "Meeting booked:      │                         │                        │
    │   Wed 2-3pm with       │                         │                        │
    │   B and C"             │                         │                        │
    │<───────────────────────│                         │                        │
    │                        │                         │                        │
```

## What each layer does

| Layer | Role | Without it... |
|-------|------|---------------|
| **A2A SDK** | HTTP server + protocol (AgentCard, tasks, messages) | Agents can't discover or talk to each other |
| **SchedulingAgentExecutor** | Translates A2A message ↔ plain text | LangChain doesn't understand A2A format |
| **SchedulingAgent** | LLM + tools, decides what to do | No intelligence, just dumb endpoints |
| **Calendar Tools** | Read/write CSV calendar | LLM can't check or book availability |
| **Orchestration Tools** | Send A2A messages to other agents | Person A can't coordinate with B and C |
| **soul.md + person_context.md** | Personality + human knowledge | LLM has no idea who it represents or how to behave |
