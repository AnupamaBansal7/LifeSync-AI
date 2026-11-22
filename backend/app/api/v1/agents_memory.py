import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory_service import ingest_knowledge_text, retrieve_relevant_memories, store_memory
from app.ai.orchestrator import execute_approved_tool, run_multi_agent_pipeline
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.ai_system import ActionApproval, AgentRun, Conversation, KnowledgeDocument, Memory, Message
from app.models.user import User
from app.schemas.ai import (
    ActionApprovalOut,
    AgentChatRequest,
    AgentChatResponse,
    ApprovalDecisionRequest,
    ConversationOut,
    ExecutionStepOut,
    KnowledgeDocOut,
    KnowledgeIngestRequest,
    MemoryCreate,
    MemoryOut,
    MessageOut,
    ScreenAnalysisRequest,
    ScreenAnalysisResponse,
)

router = APIRouter(tags=["Multi-Agent AI, Memory & RAG"])


@router.post("/agents/chat", response_model=AgentChatResponse)
async def chat_with_agents(
    payload: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conv, run, steps, approvals = await run_multi_agent_pipeline(
        db=db,
        user=current_user,
        user_message=payload.message,
        conversation_id=payload.conversation_id,
        active_role=payload.active_role,
        auto_approve_low_risk=payload.auto_approve_low_risk,
        screen_context=payload.screen_context,
    )
    plan_dict = getattr(run, "transaction_plan", None)
    card_dict = getattr(run, "clarification_card", None)
    spoken_reply = getattr(run, "spoken_reply", None)
    agent_trace = getattr(run, "agent_trace", None)
    return AgentChatResponse(
        conversation_id=conv.id,
        agent_run_id=run.id,
        detected_intent=run.detected_intent,
        status=run.status,
        reply=run.final_response or "",
        steps=[ExecutionStepOut.model_validate(s) for s in steps],
        pending_approvals=[ActionApprovalOut.model_validate(a) for a in approvals],
        latency_ms=run.latency_ms,
        transaction_plan=plan_dict,
        clarification_card=card_dict,
        spoken_reply=spoken_reply,
        agent_trace=agent_trace,
    )


@router.post("/agents/screen-analysis", response_model=ScreenAnalysisResponse)
async def analyze_screen_frame(
    payload: ScreenAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.ai.tools import get_tool
    tool = get_tool("analyze_screen_frame")
    result = await tool.execute(
        db=db,
        user_id=current_user.id,
        args={
            "image_data": payload.image_data,
            "query": payload.query,
            "active_role": payload.active_role,
        },
    )
    return ScreenAnalysisResponse(
        analysis=result.get("analysis", "Screen frame analyzed."),
        detected_elements=result.get("detected_elements", []),
        suggested_actions=result.get("suggested_actions", []),
        agent_name="ScreenAssistanceAgent",
        confidence_score=0.96,
    )



@router.get("/agents/conversations", response_model=List[ConversationOut])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Conversation).where(Conversation.user_id == current_user.id).order_by(Conversation.updated_at.desc()).limit(25)
    )
    return res.scalars().all()


@router.get("/agents/conversations/{conversation_id}/messages", response_model=List[MessageOut])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id, Message.user_id == current_user.id)
        .order_by(Message.created_at.asc())
    )
    return res.scalars().all()


@router.get("/agents/approvals", response_model=List[ActionApprovalOut])
async def list_approvals(
    status_filter: str = "pending",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ActionApproval).where(ActionApproval.user_id == current_user.id)
    if status_filter != "all":
        stmt = stmt.where(ActionApproval.status == status_filter)
    res = await db.execute(stmt.order_by(ActionApproval.created_at.desc()).limit(30))
    return res.scalars().all()


@router.post("/agents/approvals/{approval_id}/decide", response_model=ActionApprovalOut)
async def decide_action_approval(
    approval_id: uuid.UUID,
    payload: ApprovalDecisionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(ActionApproval).where(ActionApproval.id == approval_id, ActionApproval.user_id == current_user.id)
    )
    approval = res.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    if payload.decision == "rejected":
        approval.status = "rejected"
        await db.commit()
        await db.refresh(approval)
        return approval

    exec_result = await execute_approved_tool(db, current_user.id, approval.tool_name, approval.tool_arguments)
    approval.status = "executed"
    approval.execution_result = exec_result

    run_res = await db.execute(select(AgentRun).where(AgentRun.id == approval.agent_run_id))
    run = run_res.scalar_one_or_none()
    if run:
        run.status = "completed"

    await db.commit()
    await db.refresh(approval)
    return approval


# --- SEMANTIC MEMORY ---
@router.get("/memory", response_model=List[MemoryOut])
async def list_memories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(Memory).where(Memory.user_id == current_user.id).order_by(Memory.created_at.desc()).limit(50)
    )
    return res.scalars().all()


@router.post("/memory", response_model=MemoryOut, status_code=status.HTTP_201_CREATED)
async def add_memory(
    payload: MemoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await store_memory(
        db=db,
        user_id=current_user.id,
        content=payload.content,
        category=payload.category,
        role_context=payload.role_context,
        importance_score=payload.importance_score,
        source="manual",
        consent_for_training=payload.consent_for_training,
    )


@router.get("/memory/search", response_model=List[MemoryOut])
async def semantic_search_memories(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await retrieve_relevant_memories(db, current_user.id, q, limit=6)


# --- RAG KNOWLEDGE BASE ---
@router.post("/knowledge/ingest", response_model=List[KnowledgeDocOut], status_code=status.HTTP_201_CREATED)
async def ingest_knowledge(
    payload: KnowledgeIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await ingest_knowledge_text(
        db=db,
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        role_context=payload.role_context,
    )


@router.get("/knowledge", response_model=List[KnowledgeDocOut])
async def list_knowledge_docs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(
        select(KnowledgeDocument)
        .where(KnowledgeDocument.user_id == current_user.id)
        .order_by(KnowledgeDocument.created_at.desc())
        .limit(40)
    )
    return res.scalars().all()