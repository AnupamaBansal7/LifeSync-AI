from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.embeddings import generate_embedding
from app.models.ai_system import KnowledgeDocument, Memory


async def ingest_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
    content: str,
    role_context: str = "personal",
    chunk_size: int = 500,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[KnowledgeDocument]:
    """Ingest a knowledge document by chunking, generating embeddings, and storing with pgvector."""
    words = content.split()
    chunks = [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)] or [content]
    docs: List[KnowledgeDocument] = []

    for idx, chunk in enumerate(chunks):
        emb = await generate_embedding(f"{title}\n{chunk}")
        doc_meta = dict(metadata or {})
        doc_meta.update({"chunk_index": idx, "total_chunks": len(chunks)})

        doc = KnowledgeDocument(
            user_id=user_id,
            title=title.strip(),
            role_context=role_context,
            chunk_index=idx,
            content=chunk.strip(),
            metadata_json=doc_meta,
            embedding=emb,
        )
        db.add(doc)
        docs.append(doc)

    await db.commit()
    for d in docs:
        await db.refresh(d)
    return docs


async def retrieve_context_for_query(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    role_context: Optional[str] = None,
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    """Retrieve top-k relevant knowledge chunks and memories with semantic similarity scoring."""
    query_vec = await generate_embedding(query)
    results: List[Dict[str, Any]] = []

    # Search knowledge documents
    doc_stmt = (
        select(KnowledgeDocument)
        .where(KnowledgeDocument.user_id == user_id)
        .order_by(KnowledgeDocument.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    docs_res = await db.execute(doc_stmt)
    for d in docs_res.scalars().all():
        results.append({
            "source_type": "document",
            "title": d.title,
            "content": d.content,
            "role_context": d.role_context,
            "chunk_index": d.chunk_index,
        })

    # Search memories
    mem_stmt = (
        select(Memory)
        .where(Memory.user_id == user_id)
        .order_by(Memory.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    if role_context and role_context != "all":
        mem_stmt = mem_stmt.where(Memory.role_context.in_([role_context, "personal"]))

    mem_res = await db.execute(mem_stmt)
    for m in mem_res.scalars().all():
        results.append({
            "source_type": "memory",
            "title": f"Memory ({m.category})",
            "content": m.content,
            "role_context": m.role_context,
            "importance": m.importance_score,
        })

    return results


async def delete_knowledge_document(
    db: AsyncSession,
    user_id: uuid.UUID,
    title: str,
) -> int:
    """Delete all chunks for a given document title."""
    stmt = delete(KnowledgeDocument).where(
        KnowledgeDocument.user_id == user_id,
        KnowledgeDocument.title == title,
    )
    res = await db.execute(stmt)
    await db.commit()
    return res.rowcount
