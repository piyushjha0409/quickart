from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .init import tool_by_name
from .models import DEFAULT_MODEL, choose_effort, get_model
from .prompts import build_system_prompt


def llm_call(state: dict, config: RunnableConfig):
    """LLM decides to call a tool or not"""
    settings = config.get("configurable", {})
    effort = settings.get("effort", "auto")
    if effort == "auto":
        last_human = next(m for m in reversed(state["messages"]) if isinstance(m, HumanMessage))
        effort, _ = choose_effort(last_human.text)
    model = get_model(settings.get("model", DEFAULT_MODEL), effort)

    system = SystemMessage(content=build_system_prompt(state.get("context")))
    return {
        "messages": [model.invoke([system] + state["messages"])],
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
