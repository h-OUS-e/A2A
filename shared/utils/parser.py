"""
A file containing classes and functiosn to help parse
outputs of LLMs (from Langchain).
"""
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from dataclasses import dataclass

def render_messages(msgs):
    lines = []
    for i, msg in enumerate(msgs):
        if isinstance(msg, HumanMessage):
            role = "HUMAN"
            text = msg.content
        elif isinstance(msg, ToolMessage):
            role = f"TOOL:{msg}"
            text = msg.content
        elif isinstance(msg, AIMessage):
            role = "AI"
            text = msg.content or ""
        else:
            role = msg.__class__.__name__
            text = getattr(msg, "content", "")

        # compact preview
        preview = text.strip().replace("\n", "\\n")
        # if len(preview) > 220:
        #     preview = preview[:220] + "…"

        lines.append(f"{i:02d} [{role}] {preview}")
    return "\n".join(lines)

def render_messages2(msgs):
    lines = []
    for i, msg in enumerate(msgs):
        if isinstance(msg, HumanMessage):
            role = "HUMAN"
            text = msg
        elif isinstance(msg, ToolMessage):
            role = f"TOOL:{msg}"
            text = msg
        elif isinstance(msg, AIMessage):
            role = "AI"
            text = msg or ""
        else:
            role = msg.__class__.__name__
            text = msg

        # compact preview
        # preview = text.strip().replace("\n", "\\n")
        # if len(preview) > 220:
        #     preview = preview[:220] + "…"

        lines.append(f"{i:02d} [{role}] {text}\\n")
    return "\n".join(lines)



@dataclass
class ParsedMessage:
    """A single parsed message from the LangChain conversation."""
    type: str          # "user", "inter_agent_request", "inter_agent_response", "final_response"
    content: str       # The actual text
    from_agent: str    # Who sent it ("human", "person_a", "person_b", etc.)
    to_agent: str      # Who received it
    tool_name: str | None = None  # Original tool name if applicable


def parse_agent_messages(result: dict, agent_name: str = "person_a") -> list[ParsedMessage]:
    """
    Parse LangChain result["messages"] into a list of ParsedMessage.
    Only extracts send_message_to_agent interactions + the final response.
    Skips internal tools (get_free_slots, book_meeting, etc.).
    """
    messages = result["messages"]
    parsed = []

    # Step 1: Single pass — build tool_call_id -> agent_name map
    #         AND collect outgoing messages
    tool_call_to_agent = {}
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc['name'] == 'send_message_to_agent':
                    target = tc['args']['agent_name']
                    tool_call_to_agent[tc['id']] = target
                    parsed.append(ParsedMessage(
                        type="inter_agent_request",
                        content=tc['args']['message'],
                        from_agent=agent_name,
                        to_agent=target,
                        tool_name="send_message_to_agent",
                    ))

        elif isinstance(msg, ToolMessage) and msg.name == 'send_message_to_agent':
            responding_agent = tool_call_to_agent.get(msg.tool_call_id, "unknown")
            parsed.append(ParsedMessage(
                type="inter_agent_response",
                content=msg.content,
                from_agent=responding_agent,
                to_agent=agent_name,
                tool_name="send_message_to_agent",
            ))

    # Step 2: Add the final AI response (last message, should have content and no tool_calls)
    final_response = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            final_response = msg
            break

    if final_response:
        parsed.append(ParsedMessage(
            type="final_response",
            content=final_response.content,
            from_agent=agent_name,
            to_agent="human",
        ))

    return parsed
