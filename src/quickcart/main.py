import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from .db.init import create_table
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
# In-memory checkpointer keeps the conversation across turns within one process.
# Swap for the Postgres checkpointer when the API server lands.
agent = agent_builder.compile(checkpointer=InMemorySaver())




def demo_context() -> ClientContext:
    """Stand-in for the authenticated payload the chat UI will send with each turn.
    Replace with real seeded data once the seed script exists."""
    now = datetime.now(timezone.utc)
    return {
        "user_id": "u_1042",
        "location": {"lat": 12.9716, "lng": 77.5946, "store_id": "blr_koramangala_02"},
        "credits": 85.0,
        "recent_orders": [
            {
                "id": "ord_88213",
                "placed_at": (now - timedelta(minutes=25)).isoformat(),
                "status": "delivered",
                "total": 642.0,
            }
        ],
    }


def chat() -> None:
    """Interactive multi-turn session with one test customer."""
    create_table()

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    context = demo_context()

    print(f"QuickCart support — signed in as {context['user_id']}. Type 'exit' to quit.\n")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in {"exit", "quit", "q"}:
            break

        # Context is passed every turn so a client can refresh it (new order, credits change).
        result = agent.invoke(
            {"messages": [HumanMessage(content=text)], "context": context},
            config=config,
        )
        print(f"agent> {result['messages'][-1].content}\n")


def main() -> None:
    chat()


if __name__ == "__main__":
    main()
