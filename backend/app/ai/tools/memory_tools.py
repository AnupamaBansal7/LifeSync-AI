from typing import Any, Dict
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.memory_service import retrieve_relevant_memories, store_memory
from app.ai.tools.base import BaseTool


class StoreLongTermMemoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "store_long_term_memory"

    @property
    def description(self) -> str:
        return "Save a user preference, life detail, or decision into persistent pgvector semantic memory."

    @property
    def requires_approval(self) -> bool:
        return False

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        content = args.get("content", "").strip()
        if not content:
            return {"error": "Empty memory content"}

        mem = await store_memory(
            db=db,
            user_id=user_id,
            content=content,
            category=args.get("category", "preference"),
            role_context=args.get("role_context", "personal"),
            importance_score=float(args.get("importance_score", 0.75)),
            source=args.get("source", "agent_extraction"),
            consent_for_training=bool(args.get("consent_for_training", False)),
        )
        return {"stored_memory_id": str(mem.id), "category": mem.category}


class SearchMemoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_memory"

    @property
    def description(self) -> str:
        return "Retrieve semantically similar user memories matching a natural language query."

    @property
    def requires_approval(self) -> bool:
        return False

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")
        memories = await retrieve_relevant_memories(
            db=db,
            user_id=user_id,
            query=query,
            role_context=args.get("role_context"),
            limit=int(args.get("limit", 4)),
        )
        return {
            "matched_count": len(memories),
            "memories": [{"id": str(m.id), "content": m.content, "category": m.category} for m in memories],
        }


class DeleteMemoryTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_memory"

    @property
    def description(self) -> str:
        return "Delete a memory entry upon user request. Higher-risk action requiring confirmation."

    @property
    def requires_approval(self) -> bool:
        return True

    @property
    def risk_level(self) -> str:
        return "high"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "memory_id": {"type": "string"},
                "content_query": {"type": "string"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        from sqlalchemy import select
        from app.models.ai_system import Memory
        mem_id = args.get("memory_id")
        q = args.get("content_query")
        mem = None
        if mem_id:
            try:
                res = await db.execute(select(Memory).where(Memory.id == uuid.UUID(mem_id), Memory.user_id == user_id))
                mem = res.scalar_one_or_none()
            except ValueError:
                pass

        if not mem and q:
            res = await db.execute(select(Memory).where(Memory.user_id == user_id))
            for m in res.scalars().all():
                if q.lower() in m.content.lower():
                    mem = m
                    break

        if not mem:
            return {"error": "Memory entry to delete not found"}

        mid = str(mem.id)
        content_preview = mem.content[:60]
        await db.delete(mem)
        await db.commit()
        return {"deleted": True, "memory_id": mid, "content_preview": content_preview}

