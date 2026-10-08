from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Numeric, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

EMBEDDING_DIM = 1536  # text-embedding-3-small

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str]
    credits: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    orders: Mapped[list["Order"]] = relationship(back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str]
    placed_at: Mapped[datetime]
    user: Mapped["User"] = relationship(back_populates="orders")

class KBDocument(Base):
    """One policy page. The database is the source of truth the agent reads from."""
    __tablename__ = "kb_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str]
    category: Mapped[str] = mapped_column(String, index=True)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str]  # skip re-embedding pages that haven't changed
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    chunks: Mapped[list["KBChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="KBChunk.chunk_index"
    )

class KBChunk(Base):
    """One section of a policy page, embedded for vector search."""
    __tablename__ = "kb_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("kb_documents.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int]
    section: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
    document: Mapped["KBDocument"] = relationship(back_populates="chunks")
