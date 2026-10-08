import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain.messages import HumanMessage
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError

from .db.init import create_table
from .main import agent, demo_context

log = logging.getLogger("quickcart.server")
WEB_DIR = Path(__file__).parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The agent's current tools don't touch the DB, so a stopped Postgres
    # shouldn't keep the storefront from loading.
    try:
        create_table()
    except OperationalError as exc:
        log.warning("Postgres unreachable, skipping create_table: %s", exc.orig)
    yield


app = FastAPI(title="QuickCart", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    thread_id: str


@app.get("/api/context")
def get_context() -> dict:
    """The signed-in customer's context, so the UI shows what the agent sees."""
    return demo_context()


@app.post("/api/chat")
def chat(req: ChatRequest) -> ChatResponse:
    thread_id = req.thread_id or str(uuid.uuid4())
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=req.message)], "context": demo_context()},
            config={"configurable": {"thread_id": thread_id}},
        )
    except Exception:
        log.exception("agent invoke failed")
        raise HTTPException(status_code=502, detail="The support agent didn't respond.")
    return ChatResponse(reply=result["messages"][-1].content, thread_id=thread_id)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def run() -> None:
    import uvicorn

    uvicorn.run("quickcart.server:app", host="127.0.0.1", port=8000, reload=True)
