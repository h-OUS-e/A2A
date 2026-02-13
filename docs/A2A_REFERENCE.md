# A2A Protocol — Quick Reference

## What Is It
Agent-to-Agent protocol by Google (now Linux Foundation). Lets AI agents discover each other and communicate over HTTP using JSON-RPC 2.0. Agents are opaque — they don't share memory, tools, or code.

## Core Concepts

**AgentCard** — JSON at `/.well-known/agent.json`. Describes what an agent can do.
- `name`, `description`, `url`
- `skills[]` — what the agent can do (id, name, description, tags)
- `capabilities` — streaming, push notifications

**Task** — A unit of work with a lifecycle.
- States: `working` → `completed` | `failed` | `canceled` | `input_required` | `auth_required`
- Terminal states are immutable

**Message** — A conversation turn. Has `role` (user/agent) and `parts[]` (text, data, file).

**Context** — `contextId` groups related messages/tasks into a conversation.

## Python SDK

```bash
pip install a2a-sdk
```

### Server (your agent)
```python
from a2a.server.apps.starlette import A2AStarletteApplication
from a2a.server.request_handling import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor
from a2a.server.events import EventQueue
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
import uvicorn

# 1. Define your AgentCard
card = AgentCard(
    name="My Agent",
    description="Does things",
    url="http://localhost:9999/",
    version="0.1.0",
    capabilities=AgentCapabilities(streaming=False),
    skills=[AgentSkill(id="my_skill", name="My Skill", description="...")]
)

# 2. Implement AgentExecutor
class MyExecutor(AgentExecutor):
    async def execute(self, context, event_queue):
        # Read incoming message from context
        # Do your logic
        # Push response events to event_queue
        ...
    async def cancel(self, context, event_queue):
        ...

# 3. Wire it up
handler = DefaultRequestHandler(
    agent_executor=MyExecutor(),
    task_store=InMemoryTaskStore()
)
app = A2AStarletteApplication(agent_card=card, http_handler=handler)
uvicorn.run(app.build(), host="0.0.0.0", port=9999)
```

### Client (calling another agent)
```python
from a2a.client import A2AClient

client = await A2AClient.get_client_from_agent_card_url("http://localhost:9999")
response = await client.send_message(message)
```

## Key JSON-RPC Methods
| Method | What it does |
|--------|-------------|
| `SendMessage` | Send a message, get back a Task or Message |
| `GetTask` | Check task status and history |
| `CancelTask` | Cancel a running task |
| `ListTasks` | List tasks in a context |

## Links
- Spec: https://a2a-protocol.org/latest/
- Python SDK: https://github.com/a2aproject/a2a-python
- Samples: https://github.com/a2aproject/a2a-samples
