"""Load the policy pages in kb/*.md into Postgres with embeddings.

The Markdown files are seed data; after ingest the agent reads only from the database.
Re-running is safe: unchanged pages are skipped, edited pages are re-embedded, and pages
whose file was deleted are removed from the database.

    uv run quickcart-ingest-kb [path/to/kb]
"""

import hashlib
import re
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .db.init import create_table, engine
from .db.models import KBChunk, KBDocument
from .knowledge import CATEGORIES, embeddings

DEFAULT_KB_DIR = Path(__file__).resolve().parents[2] / "kb"


def parse_page(path: Path) -> dict:
    """Split a page into its frontmatter fields and Markdown body."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", path.read_text(encoding="utf-8"), re.S)
    if not match:
        raise ValueError(f"{path.name}: missing --- frontmatter ---")
    meta = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    for field in ("title", "category"):
        if not meta.get(field):
            raise ValueError(f"{path.name}: frontmatter needs '{field}'")
    if meta["category"] not in CATEGORIES:
        raise ValueError(f"{path.name}: unknown category '{meta['category']}'")
    return {"slug": path.stem, "title": meta["title"], "category": meta["category"],
            "content": match.group(2).strip()}


def split_sections(content: str) -> list[tuple[str, str]]:
    """One chunk per '## ' section; the pages are short enough that sections fit whole."""
    sections = []
    for block in re.split(r"(?m)^## ", content):
        if not block.strip():
            continue
        heading, _, body = block.partition("\n")
        sections.append((heading.strip(), body.strip()))
    return sections


def ingest(kb_dir: Path = DEFAULT_KB_DIR) -> None:
    create_table()
    pages = [parse_page(p) for p in sorted(kb_dir.glob("*.md"))]
    if not pages:
        sys.exit(f"No .md pages found in {kb_dir}")

    added = updated = unchanged = 0
    with Session(engine) as session:
        existing = {d.slug: d for d in session.scalars(select(KBDocument))}

        for page in pages:
            content_hash = hashlib.sha256(
                f"{page['title']}\n{page['category']}\n{page['content']}".encode()
            ).hexdigest()
            doc = existing.pop(page["slug"], None)
            if doc and doc.content_hash == content_hash:
                unchanged += 1
                continue

            sections = split_sections(page["content"])
            # The title goes into the embedded text so a section like "Exceptions" is still findable.
            vectors = embeddings.embed_documents(
                [f"{page['title']} — {heading}\n\n{body}" for heading, body in sections]
            )
            if doc is None:
                doc = KBDocument(slug=page["slug"])
                session.add(doc)
                added += 1
            else:
                updated += 1
            doc.title, doc.category = page["title"], page["category"]
            doc.content, doc.content_hash = page["content"], content_hash
            doc.chunks = [
                KBChunk(chunk_index=i, section=heading, content=body, embedding=vec)
                for i, ((heading, body), vec) in enumerate(zip(sections, vectors))
            ]

        for stale in existing.values():
            session.delete(stale)
        session.commit()

    print(f"KB ingest from {kb_dir}: {added} added, {updated} updated, "
          f"{unchanged} unchanged, {len(existing)} removed.")


def main() -> None:
    ingest(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_KB_DIR)


if __name__ == "__main__":
    main()
