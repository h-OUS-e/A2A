"""
Base classes for all scheduling agents.
Each person's agent inherits from these and adds their own tools.
"""

import logging
import time
from pathlib import Path
from openai import AuthenticationError

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    TaskState, TaskStatus, TaskStatusUpdateEvent, 
    TextPart, Part, Message, Role
)

from config import OPENAI_API_KEY, OPENAI_MODEL
from shared.calendar_store import CalendarStore


# Logger will be initialized per-agent instance
# (see SchedulingAgent.__init__)


llm_model = ChatOpenAI(
    model=OPENAI_MODEL,
    stream_usage=False,
    # temperature=None,
    # max_tokens=None,
    # timeout=None,
    # reasoning_effort="low",
    # max_retries=2,
    api_key=OPENAI_API_KEY,  # If you prefer to pass api key in directly
    # base_url="...",
    # organization="...",
    # other params...
)


# TODO: Define response format
# TODO: Add memory (MemorySaver from langgraph?)


class SchedulingAgent:
    """LangChain-powered scheduling agent. Each person gets one."""

    def __init__(
        self,
        soul_path: str,
        context_path: str,
        calendar_path: str,
        extra_tools: list | None = None,
        agent_name: str = "unknown",
    ):
        self.agent_name = agent_name
        self.logger = logging.getLogger(agent_name)
        self.soul = Path(soul_path).read_text()
        self.person_context = Path(context_path).read_text()
        self.calendar = CalendarStore(calendar_path)

        self.logger.info("Initializing scheduling agent")

        # Build calendar tools bound to this agent's CSV
        calendar_tools = self._build_calendar_tools()
        all_tools = calendar_tools + (extra_tools or [])
        self.logger.info(f"Loaded {len(all_tools)} tools")
        
        # Get system prompt (instruction + person context)
        system_prompt = self._build_system_prompt()

        self.agent = create_agent(
            model=llm_model,
            tools=all_tools,
            system_prompt=system_prompt,
        )

    def _build_system_prompt(self) -> str:
        system_prompt = f"{self.soul}\n\n## Person Context\n{self.person_context}"
        return system_prompt

    # TODO: move calendar tools to shared/tools since not all base agents may have calendar tools!
    def _build_calendar_tools(self) -> list:
        calendar = self.calendar

        @tool
        def check_availability(date: str, start_time: str, end_time: str) -> str:
            """Check if my person is free at a specific time.
            Args:
                date: Date in YYYY-MM-DD format
                start_time: Start time in HH:MM format
                end_time: End time in HH:MM format
            """
            from datetime import date as d, time as t
            available = calendar.is_available(
                d.fromisoformat(date),
                t.fromisoformat(start_time),
                t.fromisoformat(end_time),
            )
            return "Available" if available else "Busy - conflict with existing event"

        @tool
        def get_free_slots(date: str, duration_minutes: int) -> str:
            """List my person's open time slots for a given date.
            Args:
                date: Date in YYYY-MM-DD format
                duration_minutes: How long the meeting needs to be
            """
            from datetime import date as d
            slots = calendar.get_free_slots(d.fromisoformat(date), duration_minutes)
            if not slots:
                return "No available slots on this date."
            lines = [f"  {s['start_time']}-{s['end_time']}" for s in slots]
            return f"Available slots on {date}:\n" + "\n".join(lines)

        @tool
        def get_schedule(date: str) -> str:
            """Get my person's full schedule for a date.
            Args:
                date: Date in YYYY-MM-DD format
            """
            from datetime import date as d
            events = calendar.get_events(d.fromisoformat(date))
            if not events:
                return f"No events on {date}."
            lines = [f"  {e['start_time']}-{e['end_time']}: {e['title']}" for e in events]
            return f"Schedule for {date}:\n" + "\n".join(lines)

        @tool
        def book_meeting(
            title: str, date: str, start_time: str, end_time: str,
            attendees: str = "", location: str = "",
        ) -> str:
            """Book a meeting on my person's calendar.
            Args:
                title: Meeting title
                date: Date in YYYY-MM-DD format
                start_time: Start time in HH:MM format
                end_time: End time in HH:MM format
                attendees: Semicolon-separated list of attendee names
                location: Meeting location
            """
            from datetime import date as d, time as t
            result = calendar.book_event(
                title=title,
                target_date=d.fromisoformat(date),
                start=t.fromisoformat(start_time),
                end=t.fromisoformat(end_time),
                location=location,
                attendees=attendees.split(";") if attendees else [],
            )
            if result:
                return f"Booked: {title} on {date} {start_time}-{end_time}"
            return "Failed to book - time slot is no longer available."

        return [check_availability, get_free_slots, get_schedule, book_meeting]

    async def invoke(self, message: str, sender: str = "unknown") -> dict:
        """Run the agent with a message and return the response text."""
        request_id = f"req_{int(time.time() * 1000)}"
        self.logger.info(f"[{request_id}] Received request from '{sender}'")
        self.logger.info(f"[{request_id}] >>> {message[:150]}{'...' if len(message) > 150 else ''}")

        content = f"Sender: {sender}\n{message}"

        try:
            llm_start = time.time()
            print("SENDER: ", sender)
            self.logger.info(f"[{request_id}] Starting LLM invocation")

            result = await self.agent.ainvoke({
                "messages": [{"role": "user", "content": content}]
            })

            llm_duration = time.time() - llm_start
            self.logger.info(f"[{request_id}] LLM completed in {llm_duration:.2f}s")

            response = result["messages"][-1].content
            self.logger.info(f"[{request_id}] <<< {response[:150]}{'...' if len(response) > 150 else ''}")

            return result

        except AuthenticationError as e:
            self.logger.error(f"[{request_id}] Authentication failed: {e}")
            print("Invalid API key! Please check your OpenAI key.")
            raise
        except Exception as e:
            self.logger.error(f"[{request_id}] Error during invocation: {e}", exc_info=True)
            raise


class SchedulingAgentExecutor(AgentExecutor):
    """Bridges A2A protocol to our LangChain SchedulingAgent."""

    def __init__(self, scheduling_agent: SchedulingAgent):
        self.agent = scheduling_agent
        self.logger = scheduling_agent.logger

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        request_id = f"exec_{int(time.time() * 1000)}"
        self.logger.info(f"[{request_id}] === {self.agent.agent_name} started processing an A2A execution ===")

        # A2A method to extract text from input message
        user_input = context.get_user_input()

        # Extract sender from A2A message metadata
        sender = context.metadata.get("sender", "unknown_agent")
        self.logger.info(f"[{request_id}] Sender: {sender}")

        try:
            # Stream events from LangChain as they happen, enqueuing each one
            # immediately so the browser sees steps in real time.
            agent_start = time.time()
            content = f"Sender: {sender}\n{user_input}"
            pending_tool_calls: dict[str, str] = {}  # run_id -> agent_name
            final_content: str | None = None

            async for event in self.agent.agent.astream_events(
                {"messages": [{"role": "user", "content": content}]},
                config={"recursion_limit": 50}, #TODO: add to global config
                version="v2",
            ):
                etype = event["event"]
                name = event.get("name", "")

                # Inter-agent REQUEST — fires before the tool body runs
                if etype == "on_tool_start" and name == "send_message_to_agent":
                    run_id = event["run_id"]
                    tool_input = event["data"].get("input", {})
                    to_agent = tool_input.get("agent_name", "unknown")
                    message_text = tool_input.get("message", "")
                    pending_tool_calls[run_id] = to_agent

                    from_to_tag = f"[{self.agent.agent_name} -> {to_agent}]"
                    await event_queue.enqueue_event(TaskStatusUpdateEvent(
                        taskId=context.task_id,
                        contextId=context.context_id,
                        status=TaskStatus(
                            state=TaskState.working,
                            message=Message(
                                role=Role.agent,
                                parts=[Part(root=TextPart(
                                    metadata={"from_to": from_to_tag},
                                    text=message_text,
                                ))],
                                messageId=f"intermediate-{self.agent.agent_name}-{to_agent}",
                            ),
                        ),
                        final=False,
                    ))

                # Inter-agent RESPONSE — fires after the tool returns
                elif etype == "on_tool_end" and name == "send_message_to_agent":
                    run_id = event["run_id"]
                    to_agent = pending_tool_calls.pop(run_id, "unknown")
                    raw_output = event["data"].get("output", "")
                    content = raw_output.content if hasattr(raw_output, "content") else raw_output
                    if isinstance(content, list):
                        response_text = "\n".join(str(item) for item in content)
                    else:
                        response_text = str(content)

                    from_to_tag = f"[{to_agent} -> {self.agent.agent_name}]"
                    await event_queue.enqueue_event(TaskStatusUpdateEvent(
                        taskId=context.task_id,
                        contextId=context.context_id,
                        status=TaskStatus(
                            state=TaskState.working,
                            message=Message(
                                role=Role.agent,
                                parts=[Part(root=TextPart(
                                    metadata={"from_to": from_to_tag},
                                    text=response_text,
                                ))],
                                messageId=f"intermediate-{to_agent}-{self.agent.agent_name}",
                            ),
                        ),
                        final=False,
                    ))

                # Final LLM turn — chat model ended with no further tool calls
                elif etype == "on_chat_model_end":
                    output = event["data"].get("output")
                    if output and not getattr(output, "tool_calls", None):
                        final_content = output.content

            agent_duration = time.time() - agent_start
            self.logger.info(f"[{request_id}] Total execution: {agent_duration:.2f}s")

            # Emit the final response (closes the stream)
            if final_content:
                from_to_tag = f"[{self.agent.agent_name} -> user]"
                await event_queue.enqueue_event(TaskStatusUpdateEvent(
                    taskId=context.task_id,
                    contextId=context.context_id,
                    status=TaskStatus(
                        state=TaskState.completed,
                        message=Message(
                            role=Role.agent,
                            parts=[Part(root=TextPart(
                                metadata={"from_to": from_to_tag},
                                text=final_content,
                            ))],
                            messageId=f"final-{self.agent.agent_name}-user",
                        ),
                    ),
                    final=True,
                ))

        except Exception as e:
            self.logger.error(f"[{request_id}] Execution failed: {e}", exc_info=True)
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Method that allows agent to cancel a particular task/event. Current not suppoerted."""
        raise Exception("Cancel not supported")
