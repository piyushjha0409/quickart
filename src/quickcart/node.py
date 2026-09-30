from langchain.messages import SystemMessage, ToolMessage

from .init import model_with_tools, tool_by_name

def llm_call(state: dict):
    """LLM decides to call a tool or not"""

# Modify the prompt for the agent acting as a customer support agent
    return {
        "messages": [
             model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic operations on a set of inputs"
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


def tool_node(state: dict):
    """Performs the tool call"""

    result=[]

    for tool_call in state["messages"][-1].tool_calls:
        tool=tool_by_name[tool_call["name"]]
        observation=tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))

    return {"messages": result}
