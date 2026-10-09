"""Which chat model answers, and how hard it thinks.

The customer-facing choice is a model plus an effort level (minimal, low, medium, high),
or "auto", where `choose_effort` picks the level from the customer's message. Each model
is called through OpenAI's Responses API: the newer models only accept a reasoning effort
alongside function tools there, not in Chat Completions.
"""

import re
from functools import lru_cache

from langchain.chat_models import init_chat_model

from .init import tools

# USD per 1M tokens (input, cached input, output), from developers.openai.com/api/docs/pricing, 2026-10-09.
MODELS = {
    "gpt-6-luna": {"label": "GPT-6 Luna", "price": (0.10, 0.01, 0.50), "lowest": "none"},
    "gpt-5.6-luna": {"label": "GPT-5.6 Luna", "price": (0.20, 0.02, 1.20), "lowest": "none"},
    "gpt-5-nano": {"label": "GPT-5 nano", "price": (0.05, 0.005, 0.40), "lowest": "minimal"},
}
DEFAULT_MODEL = "gpt-6-luna"
EFFORTS = ("minimal", "low", "medium", "high")

# Small talk, thanks, yes/no replies ("ok thanks", "great, bye!"): nothing to work out.
_SMALL_TALK = re.compile(
    r"^(?:\s*(?:hi+|hello|hey|thanks?|thank you|thx|ok(?:ay)?|cool|great|yes|no|yep|nope|sure|bye|"
    r"good (?:morning|evening|night)|done|got it|perfect)\b[\s,!.?]*)+$", re.I)
# Situations where a wrong call costs money or trust: think harder.
_HARD = re.compile(
    r"\b(dispute|contest|unfair|not acceptable|charged twice|double charged|debited|deducted|"
    r"fraud|scam|harass|unsafe|rude rider|police|legal|consumer court|lawyer|"
    r"again and again|every time|third time|escalate|manager)\b", re.I)
_ISSUES = re.compile(
    r"\b(missing|damaged|broken|spoiled|rotten|leak\w*|melted|expired|wrong|late|delay\w*|"
    r"not (received|delivered)|never (came|arrived|got)|refund|cancel\w*|return)\b", re.I)


def choose_effort(message: str) -> tuple[str, str]:
    """Pick an effort level for one customer message; returns (effort, reason).

    Rules, not a model call, so the choice adds no latency or cost. "high" is never
    chosen automatically: at default effort a turn already took 15-44 s.
    """
    text = message.strip()
    if _SMALL_TALK.match(text):
        return "minimal", "small talk"
    if _HARD.search(text):
        return "medium", "dispute, payment or safety issue"
    if len(text.split()) > 60 or len({m.group(0).lower() for m in _ISSUES.finditer(text)}) >= 3:
        return "medium", "several issues in one message"
    if _ISSUES.search(text):
        return "low", "single order issue"
    return "low", "question"


def api_effort(model: str, effort: str) -> str:
    """The newer models call their lowest level "none" instead of "minimal"."""
    return MODELS[model]["lowest"] if effort == "minimal" else effort


@lru_cache(maxsize=None)
def get_model(model: str, effort: str):
    """A chat model for this (model, effort) pair with the agent's tools bound."""
    if model not in MODELS:
        raise ValueError(f"Unknown model {model!r}; choose from {list(MODELS)}")
    if effort not in EFFORTS:
        raise ValueError(f"Unknown effort {effort!r}; choose from {EFFORTS}")
    llm = init_chat_model(
        f"openai:{model}",
        use_responses_api=True,
        reasoning={"effort": api_effort(model, effort)},
    )
    return llm.bind_tools(tools)


def cost_usd(model: str, usage: dict) -> float:
    """Cost of one LLM call from its usage_metadata."""
    price_in, price_cached, price_out = MODELS[model]["price"]
    cached = (usage.get("input_token_details") or {}).get("cache_read", 0)
    fresh = usage.get("input_tokens", 0) - cached
    return (fresh * price_in + cached * price_cached + usage.get("output_tokens", 0) * price_out) / 1e6
