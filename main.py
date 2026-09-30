import operator
from typing import Literal
from langchain.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from .node import tool_node, llm_call
from .state import ClientContext, SupportState


# Function for continuing the tool call loop
def should_continue(state: dict) -> Literal["tool_node", END]:
    """Dictate the logic that wether we should continue the loop or not"""

    messages = state["messages"]
    last_message = messages[-1]  # getting the most recent message

    # if the llm makes a tool call then perform an action
    if last_message.tool_calls:
        return "tool_node"



    # Otherwise end the convo
    return END

# Build the workflow
agent_builder = StateGraph(SupportState)

# Add the nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add the edges: START -> llm_call -> (tool_node -> llm_call)* -> END
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()


# main driver function
def main() -> None:
    messages = [HumanMessage(content="Add 12 and 24, then multiply the result by 12.")]
    result = agent.invoke({"messages": messages})

    for message in result["messages"]:
        message.pretty_print()


if __name__ == "__main__":
    main()
