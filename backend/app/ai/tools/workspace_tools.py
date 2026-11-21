from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool
from app.services.integrations_service import IntegrationsService


class SearchEmailsTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_emails"

    @property
    def description(self) -> str:
        return "Search Gmail inbox and conversations using queries, sender, subject keywords, or date."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term, sender name, or subject keyword"},
                "max_results": {"type": "integer", "default": 5},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")
        max_results = int(args.get("max_results", 5))
        return await IntegrationsService.search_emails(db, user_id, query=query, max_results=max_results)


class ReadEmailThreadTool(BaseTool):
    @property
    def name(self) -> str:
        return "read_email_thread"

    @property
    def description(self) -> str:
        return "Read the full contents of an email thread or message and extract action items."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "The Gmail message ID or thread ID"},
            },
            "required": ["message_id"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = args.get("message_id", "msg-001")
        return await IntegrationsService.read_email_thread(db, user_id, message_id=msg_id)


class ReplyEmailTool(BaseTool):
    @property
    def name(self) -> str:
        return "reply_email"

    @property
    def description(self) -> str:
        return "Reply to an existing email thread. Requires user confirmation if sent externally."

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
                "message_id": {"type": "string", "description": "ID of the email to reply to"},
                "body": {"type": "string", "description": "Response content"},
            },
            "required": ["message_id", "body"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = args.get("message_id", "")
        body = args.get("body", "")
        return await IntegrationsService.reply_email(db, user_id, message_id=msg_id, body=body)


class ArchiveEmailTool(BaseTool):
    @property
    def name(self) -> str:
        return "archive_email"

    @property
    def description(self) -> str:
        return "Archive an email message or remove it from the inbox."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "ID of the email to archive"},
            },
            "required": ["message_id"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        msg_id = args.get("message_id", "")
        return await IntegrationsService.archive_email(db, user_id, message_id=msg_id)


class CreateGoogleCalendarEventTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_google_calendar_event"

    @property
    def description(self) -> str:
        return "Schedule a new event on Google Calendar with conflict checking and attendee invitations."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title or subject of the event"},
                "start_time": {"type": "string", "description": "ISO 8601 start timestamp"},
                "end_time": {"type": "string", "description": "ISO 8601 end timestamp"},
                "description": {"type": "string", "description": "Event notes or agenda"},
                "attendees": {"type": "array", "items": {"type": "string"}, "description": "Email addresses to invite"},
                "location": {"type": "string", "description": "Meeting room or virtual link"},
            },
            "required": ["title", "start_time", "end_time"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        title = args.get("title", "LifeSync Focus Session")
        start = args.get("start_time", "")
        end = args.get("end_time", "")
        desc = args.get("description", "")
        attendees = args.get("attendees", [])
        loc = args.get("location", "")
        return await IntegrationsService.create_google_calendar_event(
            db, user_id, title=title, start_time=start, end_time=end, description=desc, attendees=attendees, location=loc
        )


class SearchDriveFilesTool(BaseTool):
    @property
    def name(self) -> str:
        return "search_drive_files"

    @property
    def description(self) -> str:
        return "Search files, folders, and shared documents in Google Drive."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "File name or keyword"},
            },
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        query = args.get("query", "")
        return await IntegrationsService.search_drive_files(db, user_id, query=query)


class CreateGoogleDocTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_google_doc"

    @property
    def description(self) -> str:
        return "Create a new Google Document with formatted title and structured text content."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Document title"},
                "content": {"type": "string", "description": "Initial text content or report"},
            },
            "required": ["title"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        title = args.get("title", "Untitled Document")
        content = args.get("content", "")
        return await IntegrationsService.create_google_doc(db, user_id, title=title, content=content)


class CreateGoogleSheetTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_google_sheet"

    @property
    def description(self) -> str:
        return "Create a new Google Spreadsheet with custom columns and data rows."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Spreadsheet title"},
                "headers": {"type": "array", "items": {"type": "string"}, "description": "Column header names"},
                "initial_rows": {"type": "array", "description": "List of rows"},
            },
            "required": ["title", "headers"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        title = args.get("title", "Untitled Sheet")
        headers = args.get("headers", ["Item", "Status", "Date"])
        rows = args.get("initial_rows", [])
        return await IntegrationsService.create_google_sheet(db, user_id, title=title, headers=headers, initial_rows=rows)


class SyncGoogleTasksTool(BaseTool):
    @property
    def name(self) -> str:
        return "sync_google_tasks"

    @property
    def description(self) -> str:
        return "Synchronize tasks between Google Tasks and LifeSync AI database."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "low"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        return await IntegrationsService.sync_google_tasks_with_db(db, user_id)
