import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain.messages import AIMessage, HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError

from .db.init import create_table
from .main import agent, demo_context
from .models import DEFAULT_MODEL, EFFORTS, MODELS, choose_effort, cost_usd

log = logging.getLogger("quickcart.server")
WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A stopped Postgres shouldn't keep the storefront from loading; chats that
    # need search_kb fail with a 502 until the database is back.
    try:
        create_table()
    except OperationalError as exc:
        log.warning("Postgres unreachable, skipping create_table: %s", exc.orig)
    yield


app = FastAPI(title="QuickCart", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = None
    model: str = DEFAULT_MODEL
    effort: Literal["auto", "minimal", "low", "medium", "high"] = "auto"


class ChatResponse(BaseModel):
    reply: str
    thread_id: str
    model: str
    effort: str
    effort_reason: str | None  # why auto picked this level; None when the customer chose it
    seconds: float
    cost_usd: float


@app.get("/api/models")
def list_models() -> dict:
    return {
        "default": DEFAULT_MODEL,
        "efforts": ["auto", *EFFORTS],
        "models": [{"id": k, "label": v["label"], "price": v["price"]} for k, v in MODELS.items()],
    }


@app.get("/api/context")
def get_context() -> dict:
    """The signed-in customer's context, so the UI shows what the agent sees."""
    return demo_context()


@app.post("/api/chat")
def chat(req: ChatRequest) -> ChatResponse:
    if req.model not in MODELS:
        raise HTTPException(status_code=422, detail=f"Unknown model {req.model!r}.")
    thread_id = req.thread_id or str(uuid.uuid4())
    effort, reason = choose_effort(req.message) if req.effort == "auto" else (req.effort, None)

    started = time.perf_counter()
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=req.message)], "context": demo_context()},
            config={"configurable": {"thread_id": thread_id, "model": req.model, "effort": effort}},
        )
    except Exception:
        log.exception("agent invoke failed")
        raise HTTPException(status_code=502, detail="The support agent didn't respond.")
    seconds = time.perf_counter() - started

    # The thread holds every turn; this turn's LLM calls are the AI messages after the last human one.
    turn = []
    for message in reversed(result["messages"]):
        if isinstance(message, HumanMessage):
            break
        turn.append(message)
    cost = sum(cost_usd(req.model, m.usage_metadata) for m in turn if isinstance(m, AIMessage) and m.usage_metadata)

    return ChatResponse(
        reply=result["messages"][-1].text, thread_id=thread_id, model=req.model,
        effort=effort, effort_reason=reason, seconds=round(seconds, 2), cost_usd=round(cost, 6),
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run() -> None:
    import uvicorn

    uvicorn.run("quickcart.server:app", host="127.0.0.1", port=8000, reload=True)
