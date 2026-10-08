"""Knowledge base retrieval. Policy text is read from Postgres (kb_chunks), never from files."""

from langchain.tools import tool
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import select
from sqlalchemy.orm import Session

from .db.init import engine
from .db.models import KBChunk, KBDocument

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

CATEGORIES = (
    "refunds", "returns", "delivery", "delivery_issues", "fees", "orders", "payments",
    "credits", "membership", "offers", "inventory", "operations", "disputes", "support", "account",
)


def search(query: str, category: str | None = None, k: int = 4) -> list[dict]:
    query_vec = embeddings.embed_query(query)
    distance = KBChunk.embedding.cosine_distance(query_vec)
    stmt = (
        select(KBDocument.title, KBDocument.slug, KBChunk.section, KBChunk.content, distance.label("distance"))
        .join(KBChunk.document)
        .order_by(distance)
        .limit(k)
    )
    if category:
        stmt = stmt.where(KBDocument.category == category)
    with Session(engine) as session:
        rows = session.execute(stmt).all()
    return [
        {"title": r.title, "slug": r.slug, "section": r.section, "content": r.content,
         "similarity": round(1 - r.distance, 3)}
        for r in rows
    ]


@tool
def search_kb(query: str, category: str | None = None) -> str:
    """Search QuickCart's policy knowledge base: refunds, returns, reporting windows, delivery
    SLAs and late compensation, fees, cancellations, substitutions, payments, COD, credits,
    QuickCart Pass, coupons, store hours, serviceable areas, disputes, escalation, account.

    Write `query` as a specific question, e.g. "reporting window for broken eggs".
    Optionally narrow with `category`, one of: refunds, returns, delivery, delivery_issues,
    fees, orders, payments, credits, membership, offers, inventory, operations, disputes,
    support, account.
    """
    if category not in (None, *CATEGORIES):
        category = None
    results = search(query, category)
    if not results:
        return "No matching policy found in the knowledge base."
    return "\n\n---\n\n".join(
        f"[{i}] {r['title']} › {r['section']} (source: {r['slug']})\n{r['content']}"
        for i, r in enumerate(results, 1)
    )
