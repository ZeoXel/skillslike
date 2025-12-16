"""Core agent implementation using LangGraph."""

import logging
from typing import Literal

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from skillslike.agent.state import AgentState

logger = logging.getLogger(__name__)


def create_agent(
    tools_subset: list[StructuredTool],
    *,
    model_name: str = "claude-3-5-sonnet-20241022",
    system_prompt: str | None = None,
    checkpointer: MemorySaver | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> StateGraph:
    """Create a LangGraph agent with the given tools.

    Args:
        tools_subset: List of tools to bind to the agent.
        model_name: Name of the Anthropic model to use.
        system_prompt: Optional system prompt for the agent.
        checkpointer: Optional checkpointer for state persistence.
        base_url: Optional custom API base URL for third-party providers.
        api_key: Optional API key (defaults to environment variable).

    Returns:
        Compiled StateGraph ready for invocation.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    if system_prompt is None:
        system_prompt = (
            "You are a helpful assistant with access to specialized skills. "
            "Use tools when helpful to accomplish tasks. "
            "Maintain context across the conversation thread."
        )

    # Initialize the model with optional custom base_url
    model_kwargs = {"model": model_name, "temperature": 0}
    if base_url:
        model_kwargs["base_url"] = base_url
    if api_key:
        model_kwargs["api_key"] = api_key

    model = ChatAnthropic(**model_kwargs)

    # Bind tools to the model
    if tools_subset:
        model = model.bind_tools(tools_subset)
        logger.info("Bound %d tools to model", len(tools_subset))

    # Define graph nodes
    def call_model(state: AgentState) -> dict[str, list[AIMessage]]:
        """Call the LLM with the current state.

        Args:
            state: Current agent state.

        Returns:
            Dictionary with updated messages.
        """
        messages = state["messages"]

        # Add system prompt if this is the first message
        if len(messages) == 1 and isinstance(messages[0], HumanMessage):
            system_msg = {"role": "system", "content": system_prompt}
            messages = [system_msg] + messages

        response = model.invoke(messages)
        logger.debug("Model response: %s", response.content[:100])

        return {"messages": [response]}

    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Determine whether to continue to tools or end.

        Args:
            state: Current agent state.

        Returns:
            Next node to execute.
        """
        last_message = state["messages"][-1]

        # If the last message has tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.debug("Continuing to tools: %d calls", len(last_message.tool_calls))
            return "tools"

        # Otherwise, end
        logger.debug("No tool calls, ending")
        return "end"

    def process_tool_output(state: AgentState) -> dict[str, list[str]]:
        """Process tool outputs to extract file IDs.

        Args:
            state: Current agent state.

        Returns:
            Dictionary with updated file_ids.
        """
        file_ids = state.get("file_ids", [])
        messages = state["messages"]

        # Extract file IDs from recent ToolMessages
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                # Look for file_id in tool output
                # Expected format: {"text": "...", "file_id": "..."}
                if isinstance(msg.content, str) and "file_id:" in msg.content:
                    # Simple extraction (can be improved)
                    parts = msg.content.split("file_id:")
                    if len(parts) > 1:
                        file_id = parts[1].split()[0].strip()
                        if file_id and file_id not in file_ids:
                            file_ids.append(file_id)
                            logger.info("Extracted file_id: %s", file_id)

        return {"file_ids": file_ids}

    # Build the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", call_model)

    if tools_subset:
        # Create tool node
        tool_node = ToolNode(tools_subset)
        workflow.add_node("tools", tool_node)
        workflow.add_node("process_output", process_tool_output)

        # Add edges
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "process_output")
        workflow.add_edge("process_output", "agent")
    else:
        # No tools, just direct to end
        workflow.add_edge(START, "agent")
        workflow.add_edge("agent", END)

    # Compile with checkpointer
    app = workflow.compile(checkpointer=checkpointer)

    logger.info("Agent graph compiled successfully")
    return app


def invoke_agent(
    app: StateGraph,
    message: str,
    *,
    thread_id: str = "default",
) -> dict[str, list[str] | str]:
    """Invoke the agent with a message.

    Args:
        app: Compiled agent graph.
        message: User message.
        thread_id: Thread ID for checkpointing.

    Returns:
        Dictionary with `text` response and `file_ids` list.
    """
    # Invoke the graph
    result = app.invoke(
        {"messages": [HumanMessage(content=message)], "file_ids": []},
        config={"configurable": {"thread_id": thread_id}},
    )

    # Extract text from messages
    messages = result.get("messages", [])
    text_parts = []

    for msg in messages:
        if isinstance(msg, AIMessage):
            if isinstance(msg.content, str):
                text_parts.append(msg.content)
            elif isinstance(msg.content, list):
                # Handle structured content
                for item in msg.content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("text", ""))

    text = "\n".join(text_parts).strip()
    file_ids = result.get("file_ids", [])

    return {"text": text, "file_ids": file_ids}
