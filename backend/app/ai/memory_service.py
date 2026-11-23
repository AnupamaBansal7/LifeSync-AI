import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import generate_embedding
from app.models.ai_system import KnowledgeDocument, Memory


async def store_memory(
    db: AsyncSession,
    user_id: uuid.UUID,
    content: str,
    category: str = "preference",
    role_context: str = "personal",
    importance_score: float = 0.7,
    source: str = "conversation",
    consent_for_training: bool = False,
) -> Memory:
    embedding = await generate_embedding(content)
    mem = Memory(
        user_id=user_id,
        category=category,
        role_context=role_context,
        content=content.strip(),
        importance_score=importance_score,
        source=source,
        consent_for_training=consent_for_training,
        embedding=embedding,
    )
    db.add(mem)
    await db.commit()
    await db.refresh(mem)
    return mem


_HAS_VECTOR_SUPPORT: Optional[bool] = None


async def has_vector_support(db: AsyncSession) -> bool:
    global _HAS_VECTOR_SUPPORT
    if _HAS_VECTOR_SUPPORT is not None:
        return _HAS_VECTOR_SUPPORT
    dialect_name = db.bind.dialect.name if db.bind else ""
    if "sqlite" in dialect_name:
        _HAS_VECTOR_SUPPORT = False
        return False
    try:
        from sqlalchemy import text
        res = await db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))
        _HAS_VECTOR_SUPPORT = (res.scalar() is not None)
    except Exception:
        _HAS_VECTOR_SUPPORT = False
    return _HAS_VECTOR_SUPPORT


async def retrieve_relevant_memories(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    role_context: Optional[str] = None,
    limit: int = 5,
) -> List[Memory]:
    stmt = select(Memory).where(Memory.user_id == user_id)
    if role_context and role_context != "all":
        stmt = stmt.where(Memory.role_context.in_([role_context, "personal"]))

    if not (await has_vector_support(db)):
        fallback_stmt = stmt.order_by(Memory.created_at.desc()).limit(limit)
        res = await db.execute(fallback_stmt)
        return list(res.scalars().all())

    query_vec = await generate_embedding(query)
    try:
        stmt_vec = stmt.order_by(Memory.embedding.cosine_distance(query_vec)).limit(limit)
        res = await db.execute(stmt_vec)
        return list(res.scalars().all())
    except Exception:
        fallback_stmt = stmt.order_by(Memory.created_at.desc()).limit(limit)
        res = await db.execute(fallback_stmt)
        return list(res.scalars().all())


async def ingest_knowledge_text(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str,
    role_context: str = "personal",
    chunk_size: int = 700,
) -> List[KnowledgeDocument]:
    words = content.split()
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)] or [content]
    created_docs: List[KnowledgeDocument] = []

    for idx, chunk in enumerate(chunks):
        emb = await generate_embedding(f"{title}: {chunk}")
        doc = KnowledgeDocument(
            user_id=user_id,
            title=title,
            role_context=role_context,
            chunk_index=idx,
            content=chunk,
            metadata_json={"total_chunks": len(chunks)},
            embedding=emb,
        )
        db.add(doc)
        created_docs.append(doc)

    await db.commit()
    for d in created_docs:
        await db.refresh(d)
    return created_docs


async def search_knowledge_docs(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    limit: int = 3,
) -> List[KnowledgeDocument]:
    if not (await has_vector_support(db)):
        fallback_stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.user_id == user_id)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(fallback_stmt)
        return list(res.scalars().all())

    query_vec = await generate_embedding(query)
    try:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.user_id == user_id)
            .order_by(KnowledgeDocument.embedding.cosine_distance(query_vec))
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())
    except Exception:
        fallback_stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.user_id == user_id)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
        )
        res = await db.execute(fallback_stmt)
        return list(res.scalars().all())