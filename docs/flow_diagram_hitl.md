# A2A Meeting Scheduling — Human-in-the-Loop Flow

## Full meeting scheduling flow WITH human approval

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
    │                        │                         │                        │
    │  ┌─────────────────────────────────────────┐    │                        │
    │  │ 🚦 HUMAN APPROVAL REQUIRED              │    │                        │
    │  │                                         │    │                        │
    │  │ Found common availability:              │    │                        │
    │  │   • Wed Feb 14, 2-3pm                   │    │                        │
    │  │                                         │    │                        │
    │  │ Attendees:                              │    │                        │
    │  │   • You (Person A / Alex)               │    │                        │
    │  │   • Person B (Jordan Kim)               │    │                        │
    │  │   • Person C (Sam Rivera)               │    │                        │
    │  │                                         │    │                        │
    │  │ Action: Book meeting for all 3 people?  │    │                        │
    │  │                                         │    │                        │
    │  │ [✓ Approve] [✗ Reject] [Edit Time]     │    │                        │
    │  └─────────────────────────────────────────┘    │                        │
    │                        │                         │                        │
    │  [User clicks Approve] │                         │                        │
    │───────────────────────>│                         │                        │
    │                        │                         │                        │
    │                        │  "Confirmed: Wed 2-3pm" │                        │
    │                        │────────────────────────>│                        │
    │                        │────────────────────────────────────────────────>│
    │                        │                         │                        │
    │                        │                    books on CSV            books on CSV
    │                        │                         │                        │
    │                   books on own CSV               │                        │
    │                        │                         │                        │
    │  "✓ Meeting booked:    │                         │                        │
    │   Wed 2-3pm with       │                         │                        │
    │   Jordan and Sam"      │                         │                        │
    │<───────────────────────│                         │                        │
    │                        │                         │                        │
```

## Alternative: Human rejects and suggests different time

```
    │                        │                         │                        │
    │  ┌─────────────────────────────────────────┐    │                        │
    │  │ 🚦 HUMAN APPROVAL REQUIRED              │    │                        │
    │  │                                         │    │                        │
    │  │ Found common availability:              │    │                        │
    │  │   • Wed Feb 14, 2-3pm                   │    │                        │
    │  │                                         │    │                        │
    │  │ [✓ Approve] [✗ Reject] [Edit Time]     │    │                        │
    │  └─────────────────────────────────────────┘    │                        │
    │                        │                         │                        │
    │  [User clicks Reject]  │                         │                        │
    │  "Actually, I prefer   │                         │                        │
    │   Thursday 10-11am"    │                         │                        │
    │───────────────────────>│                         │                        │
    │                        │                         │                        │
    │                   ┌────┴────┐                    │                        │
    │                   │ LLM     │                    │                        │
    │                   │ tries   │                    │                        │
    │                   │ new time│                    │                        │
    │                   └────┬────┘                    │                        │
    │                        │                         │                        │
    │                        │  "Are you free          │                        │
    │                        │   Thu 10-11am?"         │                        │
    │                        │────────────────────────>│                        │
    │                        │─────────────────────────────────────────────────>│
    │                        │                         │                        │
    │                        │  "Yes, I'm free"        │                        │
    │                        │<────────────────────────│                        │
    │                        │<────────────────────────────────────────────────│
    │                        │                         │                        │
    │  ┌─────────────────────────────────────────┐    │                        │
    │  │ 🚦 HUMAN APPROVAL REQUIRED              │    │                        │
    │  │                                         │    │                        │
    │  │ Updated availability:                   │    │                        │
    │  │   • Thu Feb 15, 10-11am ✓               │    │                        │
    │  │                                         │    │                        │
    │  │ [✓ Approve] [✗ Reject] [Edit Time]     │    │                        │
    │  └─────────────────────────────────────────┘    │                        │
    │                        │                         │                        │
    │  [User approves]       │                         │                        │
    │───────────────────────>│                         │                        │
    │                        │                         │                        │
    │                        │  "Confirmed: Thu 10-11" │                        │
    │                        │────────────────────────>│                        │
    │                        │────────────────────────────────────────────────>│
    │                        │                         │                        │
    │  "✓ Meeting booked"    │                    books on CSV            books on CSV
    │<───────────────────────│                         │                        │
    │                        │                         │                        │
```

## Key Human-in-the-Loop Integration Points

### 1. **Before booking** (shown above)
- Agent finds available time across all participants
- Agent pauses and asks human for approval
- Shows: proposed time, attendees, action to be taken
- Human can: Approve, Reject, or Edit

### 2. **When multiple options exist**
```
┌─────────────────────────────────────────┐
│ 🚦 MULTIPLE OPTIONS FOUND               │
│                                         │
│ Which time works best for you?         │
│                                         │
│ ○ Option 1: Wed Feb 14, 2-3pm          │
│   All 3 people available               │
│                                         │
│ ○ Option 2: Thu Feb 15, 10-11am        │
│   All 3 people available               │
│                                         │
│ ○ Option 3: Fri Feb 16, 3-4pm          │
│   All 3 people available               │
│                                         │
│ [Select and Book]                       │
└─────────────────────────────────────────┘
```

### 3. **When conflicts arise**
```
┌─────────────────────────────────────────┐
│ ⚠️ SCHEDULING CONFLICT                  │
│                                         │
│ Person B (Jordan) is unavailable for   │
│ all suggested times this week.          │
│                                         │
│ What should I do?                       │
│                                         │
│ ○ Try next week                         │
│ ○ Schedule without Person B             │
│ ○ Let me suggest a time manually       │
│ ○ Cancel request                        │
│                                         │
│ [Confirm Choice]                        │
└─────────────────────────────────────────┘
```

### 4. **Before contacting other agents** (proactive)
```
┌─────────────────────────────────────────┐
│ 🤝 READY TO COORDINATE                  │
│                                         │
│ To schedule this meeting, I need to:    │
│   1. Contact Person B (Jordan Kim)      │
│   2. Contact Person C (Sam Rivera)      │
│                                         │
│ This will share:                        │
│   • That you want to meet               │
│   • Proposed time options               │
│                                         │
│ Proceed?                                │
│ [✓ Yes, contact them] [✗ Cancel]       │
└─────────────────────────────────────────┘
```

## Implementation Approaches

### Option A: Synchronous (blocks agent until human responds)
- Agent pauses execution and waits for human input
- Uses A2A's task status to indicate "waiting_for_human"
- Human sees prompt in UI, responds
- Agent receives response and continues

### Option B: Asynchronous (agent creates subtask)
- Agent creates a "human approval" subtask
- Returns to human: "I've found some options and need your input"
- Human reviews separately (e.g., in a UI)
- Once human responds, agent resumes with a new request

### Option C: Tool-based (human approval as a tool)
- Agent has access to `request_human_approval(options, context)` tool
- LLM decides when to invoke it based on soul.md instructions
- Tool returns human's choice
- Agent continues based on response

## Modified soul.md for HITL

```markdown
# Person A's Soul (with human-in-the-loop)

You are Person A's scheduling assistant with **human oversight**.

## Core Principles
1. **Always get approval before booking meetings** involving other people
2. **Present options clearly** when multiple choices exist
3. **Explain your reasoning** when asking for approval
4. **Respect the human's decisions** - if they reject, try a different approach

## When to ask for approval
- Before booking any meeting
- Before contacting other agents on behalf of the human
- When conflicts arise and you need to make a judgment call
- When the request is ambiguous

## How to present approval requests
Use the `request_human_approval` tool with:
- **Context**: What you're trying to do
- **Options**: Clear choices (Approve/Reject/Alternative)
- **Recommendation**: Your suggestion and why
- **Impact**: What will happen if approved

Example:
"I found that all three people are available Wed 2-3pm. This is the earliest available slot this week. Should I book it?"
```

## Benefits of Human-in-the-Loop

| Without HITL | With HITL |
|--------------|-----------|
| Agent autonomously books meetings | Human approves before booking |
| Might schedule at inconvenient times | Human picks best time for their preferences |
| Hard to undo mistakes | Mistakes prevented before they happen |
| No visibility into agent's reasoning | Human sees options and rationale |
| Agent makes all judgment calls | Human makes final decisions |

## When NOT to use HITL

- Checking calendar availability (read-only, safe)
- Gathering options from other agents (information gathering)
- Simple status updates ("I'm checking with Person B...")
- When user explicitly says "book it automatically"
