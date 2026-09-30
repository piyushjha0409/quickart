from typing import Annotated, Literal
from langchain.messages import AnyMessage
from typing_extensions import TypedDict

from langgraph.graph.message import add_messages

class ClientContext(TypedDict):
    user_id: str
    location: dict            # lat/lng + serviceable store id
    credits: float
    recent_orders: list[dict] # ids, timestamps, status — last few only

class SupportState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    context: ClientContext
    category: Literal[
        "order_status", "delivery_issue", "refund", "dispute",
        "policy_question", "off_topic", "escalate"
    ] | None
    order_id: str | None             # the order this conversation is about
    pending_action: dict | None      # the gated write awaiting approval
    approval_status: Literal["pending", "approved", "rejected", "auto"] | None
    tool_iterations: int             # guards against loops
    escalated: bool
    resolution: str | None
