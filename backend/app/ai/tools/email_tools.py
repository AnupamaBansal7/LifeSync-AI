from typing import Any, Dict
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool
from app.services.integrations_service import IntegrationsService


class ComposeEmailDraftTool(BaseTool):
    @property
    def name(self) -> str:
        return "compose_email_draft"

    @property
    def description(self) -> str:
        return "Draft an email message with recipient, subject line, and body content."

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Email address of the recipient"},
                "subject": {"type": "string", "description": "Subject line of the email"},
                "body": {"type": "string", "description": "Full email message body content"},
            },
            "required": ["recipient", "subject", "body"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        recipient = args.get("recipient", "")
        subject = args.get("subject", "")
        body = args.get("body", "")
        draft_res = await IntegrationsService.create_draft(db, user_id, recipient, subject, body)
        return draft_res


class SendEmailTool(BaseTool):
    @property
    def name(self) -> str:
        return "send_email"

    @property
    def description(self) -> str:
        return "Send an email message via connected Gmail account. Requires explicit user approval."

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
                "recipient": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Subject line of the email"},
                "body": {"type": "string", "description": "Body content of the email"},
            },
            "required": ["recipient", "subject", "body"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        recipient = args.get("recipient", "")
        subject = args.get("subject", "")
        body = args.get("body", "")
        return await IntegrationsService.send_email(db, user_id, recipient, subject, body)
