import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: Optional[uuid.UUID] = None
    active_role: str = "personal"
    auto_approve_low_risk: bool = False
    screen_context: Optional[Dict[str, Any]] = None


class ScreenAnalysisRequest(BaseModel):
    image_data: str
    query: Optional[str] = "Analyze this screen and tell me what actions I should take."
    active_role: str = "personal"


class ScreenAnalysisResponse(BaseModel):
    analysis: str
    detected_elements: List[str] = []
    suggested_actions: List[str] = []
    agent_name: str = "ScreenAssistanceAgent"
    confidence_score: float = 0.95



class ExecutionStepOut(BaseModel):
    id: uuid.UUID
    step_order: int
    agent_name: str
    tool_name: Optional[str]
    input_summary: Dict[str, Any]
    output_summary: Dict[str, Any]
    status: str

    model_config = {"from_attributes": True}


class ActionApprovalOut(BaseModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID
    agent_name: str
    tool_name: str
    action_summary: str
    tool_arguments: Dict[str, Any]
    status: str
    execution_result: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")


class AgentChatResponse(BaseModel):
    conversation_id: uuid.UUID
    agent_run_id: uuid.UUID
    detected_intent: str
    status: str
    reply: str
    steps: List[ExecutionStepOut] = []
    pending_approvals: List[ActionApprovalOut] = []
    latency_ms: Optional[int] = None
    transaction_plan: Optional[Dict[str, Any]] = None
    clarification_card: Optional[Dict[str, Any]] = None


class MemoryCreate(BaseModel):
    category: str = Field(default="preference", pattern="^(preference|goal|responsibility|decision|academic|work)$")
    role_context: str = "personal"
    content: str = Field(min_length=3, max_length=2000)
    importance_score: float = Field(default=0.7, ge=0.0, le=1.0)
    consent_for_training: bool = False


class MemoryOut(BaseModel):
    id: uuid.UUID
    category: str
    role_context: str
    content: str
    importance_score: float
    source: str
    consent_for_training: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeIngestRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    role_context: str = "personal"
    content: str = Field(min_length=10)


class KnowledgeDocOut(BaseModel):
    id: uuid.UUID
    title: str
    role_context: str
    chunk_index: int
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: uuid.UUID
    title: str
    active_role: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    sender: str
    content: str
    agent_run_id: Optional[uuid.UUID]
    structured_payload: Dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}