from langchain.messages import SystemMessage, ToolMessage

from .init import model_with_tools, tool_by_name
from .prompts import build_system_prompt


def llm_call(state: dict):
    """LLM decides to call a tool or not"""
    system = SystemMessage(content=build_system_prompt(state.get("context")))
    return {
        "messages": [model_with_tools.invoke([system] + state["messages"])],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tool_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=str(observation), tool_call_id=tool_call["id"]))
    return {"messages": result}
