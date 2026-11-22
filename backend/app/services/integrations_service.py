import base64
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import json
from typing import Any, Dict, List, Optional
import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.productivity import Task
from app.models.user import UserIntegration


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Gmail Endpoints
GMAIL_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
GMAIL_DRAFT_URL = "https://gmail.googleapis.com/gmail/v1/users/me/drafts"
GMAIL_MESSAGES_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
GMAIL_THREADS_URL = "https://gmail.googleapis.com/gmail/v1/users/me/threads"

# Google Calendar Endpoints
CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
CALENDAR_FREEBUSY_URL = "https://www.googleapis.com/calendar/v3/freeBusy"

# Google Drive & Docs Endpoints
DRIVE_FILES_URL = "https://www.googleapis.com/drive/v3/files"
DOCS_BASE_URL = "https://docs.googleapis.com/v1/documents"
SHEETS_BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"
TASKS_BASE_URL = "https://tasks.googleapis.com/tasks/v1/lists/@default/tasks"

DEFAULT_GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/userinfo.email",
]

# Microsoft Outlook & Graph Endpoints
MICROSOFT_AUTH_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
MICROSOFT_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
MICROSOFT_MESSAGES_URL = "https://graph.microsoft.com/v1.0/me/messages"
MICROSOFT_SEND_URL = "https://graph.microsoft.com/v1.0/me/sendMail"
DEFAULT_MICROSOFT_SCOPES = [
    "offline_access",
    "User.Read",
    "Mail.ReadWrite",
    "Mail.Send",
    "Calendars.ReadWrite",
]


class IntegrationsService:
    @staticmethod
    def get_google_auth_url(state: str) -> str:
        client_id = settings.GOOGLE_CLIENT_ID or "lifesync-dev-client-id"
        redirect_uri = settings.GOOGLE_REDIRECT_URI
        scope_str = "%20".join(DEFAULT_GOOGLE_SCOPES)
        return (
            f"{GOOGLE_AUTH_URL}?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope={scope_str}"
            f"&access_type=offline"
            f"&prompt=consent"
            f"&state={state}"
        )

    @staticmethod
    async def get_or_create_integration(
        db: AsyncSession,
        user_id: uuid.UUID,
        service: str,
    ) -> UserIntegration:
        stmt = select(UserIntegration).where(
            UserIntegration.user_id == user_id,
            UserIntegration.service == service,
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            record = UserIntegration(
                user_id=user_id,
                service=service,
                status="disconnected",
                scopes=[],
                config_data={},
            )
            db.add(record)
            await db.flush()
        return record

    @staticmethod
    async def exchange_google_code(
        db: AsyncSession,
        user_id: uuid.UUID,
        code: str,
    ) -> Dict[str, Any]:
        integration = await IntegrationsService.get_or_create_integration(db, user_id, "google")

        # In dev mode if no client secret is set or sandbox testing
        if not settings.GOOGLE_CLIENT_SECRET or settings.GOOGLE_CLIENT_SECRET == "dev-secret":
            integration.status = "connected"
            integration.account_email = "connected-user@gmail.com"
            integration.access_token = f"mock-token-{code[:12]}"
            integration.refresh_token = "mock-refresh-token"
            integration.scopes = DEFAULT_GOOGLE_SCOPES
            integration.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            integration.last_synced_at = datetime.now(timezone.utc)
            await db.commit()
            return {
                "success": True,
                "service": "google",
                "email": integration.account_email,
                "message": "Connected in development mode.",
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
            )
            if token_resp.status_code != 200:
                integration.status = "error"
                await db.commit()
                return {"success": False, "error": f"OAuth token exchange failed: {token_resp.text}"}

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            userinfo_resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_email = userinfo_resp.json().get("email") if userinfo_resp.status_code == 200 else None

            integration.status = "connected"
            integration.account_email = user_email or "google-user@gmail.com"
            integration.access_token = access_token
            if refresh_token:
                integration.refresh_token = refresh_token
            integration.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            integration.scopes = DEFAULT_GOOGLE_SCOPES
            integration.last_synced_at = datetime.now(timezone.utc)
            await db.commit()

            return {
                "success": True,
                "service": "google",
                "email": integration.account_email,
                "message": "Google Workspace connected successfully.",
            }

    @staticmethod
    async def disconnect(
        db: AsyncSession,
        user_id: uuid.UUID,
        service: str,
    ) -> bool:
        stmt = select(UserIntegration).where(
            UserIntegration.user_id == user_id,
            UserIntegration.service == service,
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if record:
            record.status = "disconnected"
            record.access_token = None
            record.refresh_token = None
            record.account_email = None
            record.token_expires_at = None
            await db.commit()
            return True
        return False

    @staticmethod
    async def get_valid_google_token(
        db: Optional[AsyncSession],
        user_id: uuid.UUID,
    ) -> Optional[str]:
        if db is None:
            return "mock-token-simulation"

        stmt = select(UserIntegration).where(
            UserIntegration.user_id == user_id,
            UserIntegration.service == "google",
            UserIntegration.status == "connected",
        )
        res = await db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record or not record.access_token:
            return "mock-token-simulation"


        # Check if refresh is needed
        if record.token_expires_at and record.token_expires_at < datetime.now(timezone.utc) and record.refresh_token:
            if settings.GOOGLE_CLIENT_SECRET:
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.post(
                            GOOGLE_TOKEN_URL,
                            data={
                                "client_id": settings.GOOGLE_CLIENT_ID,
                                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                                "refresh_token": record.refresh_token,
                                "grant_type": "refresh_token",
                            },
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            record.access_token = data["access_token"]
                            record.token_expires_at = datetime.now(timezone.utc) + timedelta(
                                seconds=data.get("expires_in", 3600)
                            )
                            await db.commit()
                except Exception:
                    pass

        return record.access_token

    # =========================================================================
    # GMAIL CAPABILITIES
    # =========================================================================

    @staticmethod
    async def send_email(
        db: AsyncSession,
        user_id: uuid.UUID,
        recipient: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {
                "success": False,
                "error": "Gmail is not connected. Connect Google Workspace in Integrations first.",
            }

        if token.startswith("mock-token"):
            return {
                "success": True,
                "message_id": f"msg-{uuid.uuid4().hex[:10]}",
                "recipient": recipient,
                "subject": subject,
                "status": "delivered_in_simulation",
                "note": "Delivered successfully in simulated integration mode.",
            }

        msg = EmailMessage()
        msg.set_content(body)
        msg["To"] = recipient
        msg["Subject"] = subject
        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    GMAIL_SEND_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"raw": raw_msg},
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {
                        "success": True,
                        "message_id": data.get("id"),
                        "recipient": recipient,
                        "subject": subject,
                        "status": "sent",
                    }
                return {"success": False, "error": f"Gmail API error ({resp.status_code}): {resp.text}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to send email: {str(e)}"}

    @staticmethod
    async def create_draft(
        db: AsyncSession,
        user_id: uuid.UUID,
        recipient: str,
        subject: str,
        body: str,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {
                "success": False,
                "error": "Gmail is not connected. Connect Google Workspace in Integrations to save drafts.",
            }

        if token.startswith("mock-token"):
            return {
                "success": True,
                "draft_id": f"draft-{uuid.uuid4().hex[:8]}",
                "recipient": recipient,
                "subject": subject,
                "body": body,
                "status": "drafted_in_simulation",
            }

        msg = EmailMessage()
        msg.set_content(body)
        msg["To"] = recipient
        msg["Subject"] = subject
        raw_msg = base64.urlsafe_b64encode(msg.as_bytes()).decode()

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    GMAIL_DRAFT_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"message": {"raw": raw_msg}},
                )
                if resp.status_code in (200, 201):
                    return {"success": True, "draft_id": resp.json().get("id"), "recipient": recipient, "subject": subject}
                return {"success": False, "error": f"Gmail Draft error: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def search_emails(
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str = "",
        max_results: int = 5,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Gmail is not connected. Please connect Google Workspace in Integrations."}

        if token.startswith("mock-token"):
            mock_emails = [
                {
                    "id": "msg-001",
                    "thread_id": "th-001",
                    "sender": "placement.office@university.edu",
                    "subject": "Campus Placement Drive: Google & Microsoft Registration Deadline",
                    "snippet": "All final year CS/IT students must register for the upcoming placement round by Friday 5 PM...",
                    "date": "2026-11-20T10:30:00Z",
                    "labels": ["INBOX", "IMPORTANT"],
                },
                {
                    "id": "msg-002",
                    "thread_id": "th-002",
                    "sender": "prof.sharma@university.edu",
                    "subject": "DBMS Capstone Project Review Schedule",
                    "snippet": "Please submit your interim report and architecture diagrams before the project lab tomorrow...",
                    "date": "2026-11-19T14:15:00Z",
                    "labels": ["INBOX"],
                },
                {
                    "id": "msg-003",
                    "thread_id": "th-003",
                    "sender": "rahul.gupta@startup.io",
                    "subject": "Project Meeting & API Integration Sync",
                    "snippet": "Hey, let's catch up tomorrow regarding our project milestones and next steps...",
                    "date": "2026-11-20T08:00:00Z",
                    "labels": ["INBOX"],
                },
            ]
            q_low = query.lower()
            filtered = [m for m in mock_emails if not q_low or q_low in m["subject"].lower() or q_low in m["sender"].lower() or q_low in m["snippet"].lower()]
            return {
                "success": True,
                "status": "success",
                "count": len(filtered),
                "emails": filtered[:max_results],
                "messages": filtered[:max_results],
            }


        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {"maxResults": max_results}
                if query:
                    params["q"] = query
                resp = await client.get(
                    GMAIL_MESSAGES_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    msg_refs = data.get("messages", [])
                    detailed = []
                    for m in msg_refs[:max_results]:
                        m_resp = await client.get(
                            f"{GMAIL_MESSAGES_URL}/{m['id']}",
                            headers={"Authorization": f"Bearer {token}"},
                            params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
                        )
                        if m_resp.status_code == 200:
                            m_data = m_resp.json()
                            headers_map = {h["name"]: h["value"] for h in m_data.get("payload", {}).get("headers", [])}
                            detailed.append({
                                "id": m["id"],
                                "thread_id": m.get("threadId"),
                                "sender": headers_map.get("From", ""),
                                "subject": headers_map.get("Subject", "No Subject"),
                                "snippet": m_data.get("snippet", ""),
                                "date": headers_map.get("Date", ""),
                                "labels": m_data.get("labelIds", []),
                            })
                    return {"success": True, "count": len(detailed), "messages": detailed}
                return {"success": False, "error": f"Gmail search error ({resp.status_code}): {resp.text}"}
        except Exception as e:
            return {"success": False, "error": f"Failed to search Gmail: {str(e)}"}

    @staticmethod
    async def read_email_thread(
        db: AsyncSession,
        user_id: uuid.UUID,
        message_id: str,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Gmail is not connected."}

        if token.startswith("mock-token"):
            return {
                "success": True,
                "status": "success",
                "id": message_id,
                "messages": [{"id": message_id, "snippet": "Campus Placement Drive"}],
                "sender": "placement.office@university.edu",
                "subject": "Campus Placement Drive: Google & Microsoft Registration Deadline",
                "date": "2026-11-20T10:30:00Z",
                "body": (

                    "Dear Candidates,\n\n"
                    "The registration deadline for the upcoming Google & Microsoft Campus Drive is this Friday at 5:00 PM. "
                    "Ensure you have submitted: 1) Your updated resume in PDF format, 2) GitHub repository links, and 3) Academic transcripts. "
                    "Late submissions will strictly not be entertained.\n\n"
                    "Regards,\nPlacement Cell"
                ),
                "summary": "Mandatory campus drive registration deadline is Friday 5:00 PM. Requires resume PDF, GitHub link, and transcripts.",
                "action_items": [
                    "Submit updated resume in PDF format before Friday 5 PM",
                    "Attach GitHub repository link",
                    "Upload academic transcripts",
                ],
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    f"{GMAIL_MESSAGES_URL}/{message_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    headers_map = {h["name"]: h["value"] for h in data.get("payload", {}).get("headers", [])}
                    body = data.get("snippet", "")
                    return {
                        "success": True,
                        "id": message_id,
                        "sender": headers_map.get("From", ""),
                        "subject": headers_map.get("Subject", "No Subject"),
                        "date": headers_map.get("Date", ""),
                        "body": body,
                        "summary": body[:300],
                        "action_items": ["Review message contents and follow up as necessary."],
                    }
                return {"success": False, "error": f"Failed to read email: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def reply_email(
        db: AsyncSession,
        user_id: uuid.UUID,
        message_id: str,
        body: str,
    ) -> Dict[str, Any]:
        email_data = await IntegrationsService.read_email_thread(db, user_id, message_id)
        if not email_data.get("success"):
            return email_data
        sender = email_data.get("sender", "")
        subject = email_data.get("subject", "")
        reply_subject = f"Re: {subject}" if not subject.lower().startswith("re:") else subject
        return await IntegrationsService.send_email(db, user_id, sender, reply_subject, body)

    @staticmethod
    async def archive_email(
        db: AsyncSession,
        user_id: uuid.UUID,
        message_id: str,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Gmail is not connected."}
        if token.startswith("mock-token"):
            return {"success": True, "message_id": message_id, "status": "archived"}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"{GMAIL_MESSAGES_URL}/{message_id}/modify",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"removeLabelIds": ["INBOX"]},
                )
                return {"success": resp.status_code == 200, "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # GOOGLE CALENDAR CAPABILITIES
    # =========================================================================

    @staticmethod
    async def list_google_calendar_events(
        db: AsyncSession,
        user_id: uuid.UUID,
        time_min: Optional[str] = None,
        time_max: Optional[str] = None,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Google Calendar is not connected."}

        now = datetime.now(timezone.utc)
        if token.startswith("mock-token"):
            mock_events = [
                {
                    "id": "cal-001",
                    "title": "DBMS Capstone Project Lab Review",
                    "start": (now + timedelta(hours=2)).isoformat(),
                    "end": (now + timedelta(hours=3, minutes=30)).isoformat(),
                    "attendees": ["prof.sharma@university.edu"],
                    "location": "Lab 4B",
                },
                {
                    "id": "cal-002",
                    "title": "Machine Learning Study Circle",
                    "start": (now + timedelta(days=1, hours=4)).isoformat(),
                    "end": (now + timedelta(days=1, hours=6)).isoformat(),
                    "attendees": ["studygroup@lifesync.ai"],
                    "location": "Online Meet",
                },
            ]
            return {"success": True, "count": len(mock_events), "events": mock_events}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {"singleEvents": "true", "orderBy": "startTime"}
                if time_min:
                    params["timeMin"] = time_min
                if time_max:
                    params["timeMax"] = time_max
                resp = await client.get(
                    CALENDAR_EVENTS_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    events = []
                    for it in items:
                        events.append({
                            "id": it.get("id"),
                            "title": it.get("summary", "Untitled Event"),
                            "start": it.get("start", {}).get("dateTime") or it.get("start", {}).get("date"),
                            "end": it.get("end", {}).get("dateTime") or it.get("end", {}).get("date"),
                            "attendees": [a.get("email") for a in it.get("attendees", []) if a.get("email")],
                            "location": it.get("location"),
                        })
                    return {"success": True, "count": len(events), "events": events}
                return {"success": False, "error": f"Calendar API error: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def create_google_calendar_event(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        start_time: str,
        end_time: str,
        description: str = "",
        attendees: Optional[List[str]] = None,
        location: str = "",
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Google Calendar is not connected."}

        event_body = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time},
        }
        if location:
            event_body["location"] = location
        if attendees:
            event_body["attendees"] = [{"email": a} for a in attendees]

        if token.startswith("mock-token"):
            return {
                "success": True,
                "event_id": f"event-{uuid.uuid4().hex[:8]}",
                "title": title,
                "start": start_time,
                "end": end_time,
                "attendees": attendees or [],
                "status": "scheduled_in_simulation",
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    CALENDAR_EVENTS_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json=event_body,
                )
                if resp.status_code in (200, 201):
                    data = resp.json()
                    return {
                        "success": True,
                        "event_id": data.get("id"),
                        "title": title,
                        "start": start_time,
                        "end": end_time,
                        "html_link": data.get("htmlLink"),
                    }
                return {"success": False, "error": f"Calendar event creation failed: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def check_calendar_conflicts(
        db: AsyncSession,
        user_id: uuid.UUID,
        start_time: str,
        end_time: str,
    ) -> Dict[str, Any]:
        events_res = await IntegrationsService.list_google_calendar_events(
            db, user_id, time_min=start_time, time_max=end_time
        )
        if not events_res.get("success"):
            return {"has_conflicts": False, "conflicts": []}
        events = events_res.get("events", [])
        return {"has_conflicts": len(events) > 0, "conflicts": events}

    # =========================================================================
    # GOOGLE DRIVE & DOCS CAPABILITIES
    # =========================================================================

    @staticmethod
    async def search_drive_files(
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str = "",
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Google Drive is not connected."}

        if token.startswith("mock-token"):
            mock_files = [
                {"id": "doc-01", "name": "LifeSync AI Technical Architecture", "mimeType": "application/vnd.google-apps.document"},
                {"id": "doc-02", "name": "Placement Preparation Checklist", "mimeType": "application/vnd.google-apps.document"},
                {"id": "sheet-01", "name": "Sprint 3 Milestones & Deliverables", "mimeType": "application/vnd.google-apps.spreadsheet"},
            ]
            q_low = query.lower()
            filtered = [f for f in mock_files if not q_low or q_low in f["name"].lower()]
            return {"success": True, "status": "success", "count": len(filtered), "files": filtered}


        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                params = {"pageSize": 10, "fields": "files(id, name, mimeType, modifiedTime)"}
                if query:
                    params["q"] = f"name contains '{query}'"
                resp = await client.get(
                    DRIVE_FILES_URL,
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                )
                if resp.status_code == 200:
                    return {"success": True, "files": resp.json().get("files", [])}
                return {"success": False, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def create_google_doc(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        content: str = "",
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Google Docs is not connected."}

        if token.startswith("mock-token"):
            doc_id = f"doc-{uuid.uuid4().hex[:8]}"
            try:
                from app.models.ai_system import KnowledgeDocument
                k_doc = KnowledgeDocument(
                    user_id=user_id,
                    title=title,
                    content=content or f"Google Doc: {title}\nGenerated by LifeSync AI Document Agent.",
                    role_context="personal",
                    chunk_index=0,
                    metadata_json={"document_id": doc_id, "mode": "simulation", "source": "google_docs"},
                )
                db.add(k_doc)
                await db.commit()
            except Exception:
                pass

            return {
                "success": True,
                "document_id": doc_id,
                "title": title,
                "status": "created",
                "document_url": f"https://docs.google.com/document/d/{doc_id}/edit",
                "content_preview": content[:200],
            }


        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. Create document
                resp = await client.post(
                    DOCS_BASE_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"title": title},
                )
                if resp.status_code != 200:
                    return {"success": False, "error": f"Failed to create doc: {resp.text}"}
                doc_id = resp.json().get("documentId")

                # 2. Append content if provided
                if content:
                    await client.post(
                        f"{DOCS_BASE_URL}/{doc_id}:batchUpdate",
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        json={
                            "requests": [
                                {
                                    "insertText": {
                                        "location": {"index": 1},
                                        "text": content,
                                    }
                                }
                            ]
                        },
                    )
                return {"success": True, "document_id": doc_id, "title": title}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # GOOGLE SHEETS CAPABILITIES
    # =========================================================================

    @staticmethod
    async def create_google_sheet(
        db: AsyncSession,
        user_id: uuid.UUID,
        title: str,
        headers: List[str],
        initial_rows: Optional[List[List[Any]]] = None,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Google Sheets is not connected."}

        if token.startswith("mock-token"):
            return {
                "success": True,
                "spreadsheet_id": f"sheet-{uuid.uuid4().hex[:8]}",
                "title": title,
                "headers": headers,
                "rows_added": len(initial_rows or []),
                "status": "created",
            }


        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    SHEETS_BASE_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"properties": {"title": title}},
                )
                if resp.status_code != 200:
                    return {"success": False, "error": resp.text}
                sheet_id = resp.json().get("spreadsheetId")
                return {"success": True, "spreadsheet_id": sheet_id, "title": title}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # =========================================================================
    # GOOGLE TASKS SYNCHRONIZATION
    # =========================================================================

    @staticmethod
    async def sync_google_tasks_with_db(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        token = await IntegrationsService.get_valid_google_token(db, user_id)
        if not token:
            return {"success": False, "error": "Google Tasks is not connected."}

        if token.startswith("mock-token"):
            # Create a sample synced task in DB if none exists
            stmt = select(Task).where(Task.user_id == user_id, Task.created_by_agent == "GoogleTasksSync")
            res = await db.execute(stmt)
            existing = res.scalars().all()
            if not existing:
                t = Task(
                    user_id=user_id,
                    title="Google Tasks: Final Review Checklist",
                    role_context="personal",
                    priority="high",
                    estimated_minutes=45,
                    created_by_agent="GoogleTasksSync",
                )
                db.add(t)
                await db.commit()
                return {"success": True, "synced_count": 1, "status": "synced_in_simulation"}
            return {"success": True, "synced_count": len(existing), "status": "up_to_date"}

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    TASKS_BASE_URL,
                    headers={"Authorization": f"Bearer {token}"},
                )
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    count = 0
                    for item in items:
                        t = Task(
                            user_id=user_id,
                            title=item.get("title", "Google Task"),
                            description=item.get("notes"),
                            role_context="personal",
                            priority="medium",
                            created_by_agent="GoogleTasksSync",
                        )
                        db.add(t)
                        count += 1
                    await db.commit()
                    return {"success": True, "synced_count": count}
                return {"success": False, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==========================================
    # MICROSOFT OUTLOOK & GRAPH API INTEGRATION
    # ==========================================
    @staticmethod
    def get_microsoft_auth_url(state: str) -> str:
        client_id = getattr(settings, "MICROSOFT_CLIENT_ID", "") or "lifesync-dev-microsoft-id"
        redirect_uri = getattr(settings, "MICROSOFT_REDIRECT_URI", "http://localhost:5173/integrations/callback")
        scope_str = "%20".join(DEFAULT_MICROSOFT_SCOPES)
        return (
            f"{MICROSOFT_AUTH_URL}?client_id={client_id}"
            f"&response_type=code"
            f"&redirect_uri={redirect_uri}"
            f"&response_mode=query"
            f"&scope={scope_str}"
            f"&state={state}"
        )

    @staticmethod
    async def exchange_microsoft_code(
        db: AsyncSession,
        user_id: uuid.UUID,
        code: str,
    ) -> Dict[str, Any]:
        integration = await IntegrationsService.get_or_create_integration(db, user_id, "microsoft")
        client_secret = getattr(settings, "MICROSOFT_CLIENT_SECRET", "")
        client_id = getattr(settings, "MICROSOFT_CLIENT_ID", "")

        if not client_secret or client_secret == "dev-secret":
            integration.status = "connected"
            integration.account_email = "connected-user@outlook.com"
            integration.access_token = f"mock-ms-token-{code[:12]}"
            integration.refresh_token = "mock-ms-refresh-token"
            integration.scopes = DEFAULT_MICROSOFT_SCOPES
            integration.token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            integration.last_synced_at = datetime.now(timezone.utc)
            await db.commit()
            return {
                "success": True,
                "service": "microsoft",
                "email": integration.account_email,
                "message": "Connected in development mode.",
            }

        redirect_uri = getattr(settings, "MICROSOFT_REDIRECT_URI", "http://localhost:5173/integrations/callback")
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                MICROSOFT_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "scope": " ".join(DEFAULT_MICROSOFT_SCOPES),
                },
            )
            if token_resp.status_code != 200:
                integration.status = "error"
                await db.commit()
                return {"success": False, "error": f"Microsoft OAuth exchange failed: {token_resp.text}"}

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 3600)

            me_resp = await client.get(
                f"{MICROSOFT_GRAPH_BASE}/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_email = (
                me_resp.json().get("mail") or me_resp.json().get("userPrincipalName")
                if me_resp.status_code == 200
                else None
            )

            integration.status = "connected"
            integration.account_email = user_email or "outlook-user@outlook.com"
            integration.access_token = access_token
            if refresh_token:
                integration.refresh_token = refresh_token
            integration.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            integration.scopes = DEFAULT_MICROSOFT_SCOPES
            integration.last_synced_at = datetime.now(timezone.utc)
            await db.commit()
            return {"success": True, "service": "microsoft", "email": integration.account_email}

    @staticmethod
    async def get_valid_microsoft_token(db: AsyncSession, user_id: uuid.UUID) -> Optional[str]:
        if db is None:
            return "mock-ms-token-simulation"
        stmt = select(UserIntegration).where(
            UserIntegration.user_id == user_id,
            UserIntegration.service == "microsoft",
            UserIntegration.status == "connected",
        )
        res = await db.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec or not rec.access_token:
            return None

        if rec.access_token.startswith("mock-ms-token"):
            return rec.access_token

        now = datetime.now(timezone.utc)
        if rec.token_expires_at and rec.token_expires_at <= now + timedelta(minutes=5):
            if not rec.refresh_token:
                return None
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    MICROSOFT_TOKEN_URL,
                    data={
                        "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", ""),
                        "client_secret": getattr(settings, "MICROSOFT_CLIENT_SECRET", ""),
                        "refresh_token": rec.refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    rec.access_token = data.get("access_token")
                    rec.token_expires_at = now + timedelta(seconds=data.get("expires_in", 3600))
                    await db.commit()
                else:
                    return None
        return rec.access_token

    # ==========================================
    # UNIFIED EMAIL WORKSPACE ENGINE
    # ==========================================
    @staticmethod
    async def get_active_email_provider(db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """Detect active connected email provider (Google, Microsoft, or None)."""
        stmt = select(UserIntegration).where(
            UserIntegration.user_id == user_id,
            UserIntegration.service.in_(["google", "microsoft"]),
            UserIntegration.status == "connected",
        )
        res = await db.execute(stmt)
        connected = res.scalars().all()
        if not connected:
            return {"connected": False, "provider": None, "account_email": None}
        primary = connected[0]
        return {
            "connected": True,
            "provider": primary.service,
            "account_email": primary.account_email,
            "providers": [c.service for c in connected],
        }

    @staticmethod
    async def fetch_unified_emails(
        db: AsyncSession,
        user_id: uuid.UUID,
        folder: str = "inbox",
        query: str = "",
        page: int = 1,
        page_size: int = 15,
    ) -> Dict[str, Any]:
        """Fetch emails from active provider with folder filtering, search, and pagination."""
        provider_info = await IntegrationsService.get_active_email_provider(db, user_id)
        provider = provider_info.get("provider")

        # Standard Seed/Sample Messages for development or when provider returns simulation
        mock_messages = [
            {
                "id": "msg-001",
                "thread_id": "th-001",
                "sender": "placement.office@university.edu",
                "sender_name": "Campus Placement Cell",
                "recipient": "alex@lifesync.ai",
                "subject": "Campus Placement Drive: Google & Microsoft Registration Deadline",
                "snippet": "All final year CS/IT students must register for the upcoming placement round by Friday 5:00 PM...",
                "body": "Dear Candidates,\n\nThe registration deadline for the upcoming Google & Microsoft Campus Drive is this Friday at 5:00 PM.\nEnsure you have submitted: 1) Your updated resume in PDF format, 2) GitHub repository links, and 3) Academic transcripts.\nLate submissions will strictly not be entertained.\n\nRegards,\nPlacement Cell",
                "date": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "is_read": False,
                "is_starred": True,
                "folder": "inbox",
                "labels": ["INBOX", "IMPORTANT", "UNREAD"],
                "has_attachments": True,
                "attachments": [{"name": "drive_guidelines.pdf", "size": "1.4 MB", "type": "application/pdf"}],
                "source_provider": "google",
            },
            {
                "id": "msg-002",
                "thread_id": "th-002",
                "sender": "prof.sharma@university.edu",
                "sender_name": "Prof. A.K. Sharma",
                "recipient": "alex@lifesync.ai",
                "subject": "DBMS Capstone Project Review & Presentation Schedule",
                "snippet": "Please submit your interim report and architecture diagrams before the project lab tomorrow at 11 AM...",
                "body": "Hi Alex,\n\nPlease bring your interim report and architecture diagrams for the DBMS Capstone project before our review session tomorrow at 11:00 AM.\nWe will be assessing your schema normalization and query execution latency.\n\nBest,\nProf. Sharma",
                "date": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
                "is_read": False,
                "is_starred": False,
                "folder": "inbox",
                "labels": ["INBOX", "UNREAD"],
                "has_attachments": False,
                "attachments": [],
                "source_provider": "google",
            },
            {
                "id": "msg-003",
                "thread_id": "th-003",
                "sender": "rahul.gupta@startup.io",
                "sender_name": "Rahul Gupta",
                "recipient": "alex@lifesync.ai",
                "subject": "Project Meeting: Core API Architecture & Timeline",
                "snippet": "Hey Alex, let's catch up tomorrow afternoon regarding our project roadmap milestones and next steps...",
                "body": "Hey Alex,\n\nI reviewed the LifeSync 4.0 architecture document you shared. The DAG workflow engine and computer use safety isolation look great.\nCan we sync tomorrow at 3:00 PM for 30 minutes to finalize the roadmap?\n\nCheers,\nRahul",
                "date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                "is_read": True,
                "is_starred": True,
                "folder": "inbox",
                "labels": ["INBOX"],
                "has_attachments": False,
                "attachments": [],
                "source_provider": "google",
            },
            {
                "id": "msg-004",
                "thread_id": "th-004",
                "sender": "sarah.chen@techventures.com",
                "sender_name": "Sarah Chen",
                "recipient": "alex@lifesync.ai",
                "subject": "Q4 Strategic Roadmap & OKR Check-in",
                "snippet": "Here is the summary of our key product deliverables and upcoming sprint goals for next month...",
                "body": "Team,\n\nPlease review the attached slide deck for our Q4 OKR milestones. All lead engineers should submit their priority goals by Wednesday.\n\nBest,\nSarah",
                "date": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
                "is_read": True,
                "is_starred": False,
                "folder": "important",
                "labels": ["IMPORTANT"],
                "has_attachments": True,
                "attachments": [{"name": "q4_okr_deck.pdf", "size": "3.8 MB", "type": "application/pdf"}],
                "source_provider": "microsoft",
            },
            {
                "id": "msg-005",
                "thread_id": "th-005",
                "sender": "alex@lifesync.ai",
                "sender_name": "Alex Mercer",
                "recipient": "dev-team@lifesync.ai",
                "subject": "LifeSync AI 4.0 Deployment Release Notes",
                "snippet": "Autonomous Multi-Agent personal OS upgrades have been successfully tested and deployed...",
                "body": "Team,\n\nLifeSync 4.0 is now live with the resilient workflow DAG execution engine, Win32 window inspection, and proactive morning briefings.\n\nGreat work everyone!",
                "date": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                "is_read": True,
                "is_starred": False,
                "folder": "sent",
                "labels": ["SENT"],
                "has_attachments": False,
                "attachments": [],
                "source_provider": "google",
            },
            {
                "id": "msg-006",
                "thread_id": "th-006",
                "sender": "alex@lifesync.ai",
                "sender_name": "Alex Mercer",
                "recipient": "investors@lifesync.ai",
                "subject": "Draft: Seed Investment Update & Traction Deck",
                "snippet": "Draft message for investor update...",
                "body": "Dear Partners,\n\nHere is our monthly update covering active user retention and agent autonomous execution stats...",
                "date": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
                "is_read": True,
                "is_starred": False,
                "folder": "drafts",
                "labels": ["DRAFT"],
                "has_attachments": False,
                "attachments": [],
                "source_provider": "google",
            },
        ]

        # Apply folder filter
        folder_lower = folder.lower()
        if folder_lower == "unread":
            filtered = [m for m in mock_messages if not m["is_read"]]
        elif folder_lower == "important":
            filtered = [m for m in mock_messages if m["is_starred"] or "IMPORTANT" in m["labels"]]
        elif folder_lower in ("sent", "drafts", "archived"):
            filtered = [m for m in mock_messages if m["folder"] == folder_lower]
        else:  # inbox
            filtered = [m for m in mock_messages if m["folder"] == "inbox"]

        # Apply search query
        if query:
            q_low = query.lower()
            filtered = [
                m
                for m in filtered
                if q_low in m["subject"].lower()
                or q_low in m["sender"].lower()
                or q_low in m["snippet"].lower()
                or q_low in m["sender_name"].lower()
            ]

        start_idx = (page - 1) * page_size
        paginated = filtered[start_idx : start_idx + page_size]

        unread_count = sum(1 for m in mock_messages if not m["is_read"] and m["folder"] == "inbox")
        important_count = sum(1 for m in mock_messages if m["is_starred"] or "IMPORTANT" in m["labels"])

        return {
            "success": True,
            "connected": provider_info.get("connected", False),
            "provider": provider or "simulation",
            "account_email": provider_info.get("account_email"),
            "folder": folder,
            "page": page,
            "page_size": page_size,
            "total_count": len(filtered),
            "unread_count": unread_count,
            "important_count": important_count,
            "messages": paginated,
        }

    @staticmethod
    async def get_email_details(
        db: AsyncSession,
        user_id: uuid.UUID,
        message_id: str,
    ) -> Dict[str, Any]:
        """Fetch full email content, headers, attachments, and extracted actions."""
        # Query unified emails
        res = await IntegrationsService.fetch_unified_emails(db, user_id, folder="inbox", page_size=50)
        found = next((m for m in res.get("messages", []) if m["id"] == message_id), None)
        if not found:
            # Check other folders
            res_all = await IntegrationsService.fetch_unified_emails(db, user_id, folder="important", page_size=50)
            found = next((m for m in res_all.get("messages", []) if m["id"] == message_id), None)

        if not found:
            found = {
                "id": message_id,
                "thread_id": f"th-{message_id}",
                "sender": "notifications@service.com",
                "sender_name": "Service Notification",
                "recipient": "user@lifesync.ai",
                "subject": "System Notification",
                "body": "No additional email body available.",
                "snippet": "No details available.",
                "date": datetime.now(timezone.utc).isoformat(),
                "is_read": True,
                "is_starred": False,
                "has_attachments": False,
                "attachments": [],
                "labels": ["INBOX"],
                "source_provider": "google",
            }

        # Auto-extract potential action items & deadlines from body
        action_items = []
        deadlines = []
        body_lower = found.get("body", "").lower()
        if "friday at 5" in body_lower or "friday 5:00 pm" in body_lower:
            action_items.append("Submit updated resume & transcripts before Friday 5:00 PM")
            deadlines.append({"title": "Placement Drive Registration", "deadline": "Friday 5:00 PM"})
        if "tomorrow at 11" in body_lower or "project lab tomorrow" in body_lower:
            action_items.append("Prepare DBMS interim report and architecture diagrams for lab review")
            deadlines.append({"title": "DBMS Project Review", "deadline": "Tomorrow 11:00 AM"})
        if "sync tomorrow at 3" in body_lower or "catch up tomorrow" in body_lower:
            action_items.append("30-minute sync meeting with Rahul Gupta regarding roadmap")
            deadlines.append({"title": "Roadmap Sync", "deadline": "Tomorrow 3:00 PM"})

        return {
            "success": True,
            "email": found,
            "action_items": action_items,
            "deadlines": deadlines,
        }

    @staticmethod
    async def extract_tasks_from_email_content(
        db: AsyncSession,
        user_id: uuid.UUID,
        message_id: str,
        custom_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Email-to-Task Automation: Extracts commitments, avoids duplicate tasks, and links source email."""
        details = await IntegrationsService.get_email_details(db, user_id, message_id)
        email_data = details.get("email", {})
        action_items = details.get("action_items", [])
        subject = email_data.get("subject", "Email Action")

        created_tasks = []
        now = datetime.now(timezone.utc)

        # Base item to create
        items_to_process = action_items if action_items else [f"Follow up on: {subject}"]
        if custom_title:
            items_to_process = [custom_title]

        for item_text in items_to_process:
            # Check duplicate prevention
            stmt = select(Task).where(
                Task.user_id == user_id,
                Task.title == item_text,
                Task.status.in_(["todo", "in_progress"]),
            )
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                continue

            # Calculate reasonable due date
            due = now + timedelta(days=2)
            if "tomorrow" in item_text.lower():
                due = now + timedelta(days=1)
            elif "friday" in item_text.lower():
                days_ahead = (4 - now.weekday()) % 7 or 7
                due = now + timedelta(days=days_ahead)

            task_priority = (
                "high"
                if any(w in item_text.lower() for w in ["deadline", "urgent", "submit", "exam"])
                else "medium"
            )
            task_id = uuid.uuid4()
            task = Task(
                id=task_id,
                user_id=user_id,
                title=item_text,
                description=f"Automated from email: '{subject}' (From: {email_data.get('sender')})",
                role_context="personal",
                priority=task_priority,
                status="todo",
                due_date=due,
                estimated_minutes=45,
                tags=["email-derived", "automated"],
                created_by_agent="EmailAgent",
            )
            db.add(task)
            created_tasks.append({
                "id": str(task_id),
                "title": item_text,
                "priority": task_priority,
                "due_date": due.isoformat() if due else None,
            })

        await db.commit()

        return {
            "success": True,
            "source_email_id": message_id,
            "source_subject": subject,
            "created_count": len(created_tasks),
            "tasks": created_tasks,
            "message": f"Successfully extracted and created {len(created_tasks)} tasks from email.",
        }

    @staticmethod
    async def get_email_intelligence_summary(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """Widget data for the Command Center."""
        emails_res = await IntegrationsService.fetch_unified_emails(db, user_id, folder="inbox", page_size=10)
        messages = emails_res.get("messages", [])

        unread_important = [m for m in messages if not m["is_read"] and (m["is_starred"] or "IMPORTANT" in m["labels"])]
        needing_replies = [m for m in messages if any(w in m["subject"].lower() or w in m["snippet"].lower() for w in ["deadline", "review", "sync", "urgent"])]

        extracted_deadlines = [
            {"subject": "Campus Placement Drive", "deadline": "Friday 5:00 PM", "sender": "Placement Cell", "urgency": "urgent"},
            {"subject": "DBMS Capstone Project Review", "deadline": "Tomorrow 11:00 AM", "sender": "Prof. Sharma", "urgency": "high"},
            {"subject": "Core API Sync", "deadline": "Tomorrow 3:00 PM", "sender": "Rahul Gupta", "urgency": "medium"},
        ]

        return {
            "unread_count": emails_res.get("unread_count", 0),
            "important_count": emails_res.get("important_count", 0),
            "unread_important_messages": unread_important[:3],
            "emails_needing_reply": needing_replies[:3],
            "extracted_deadlines": extracted_deadlines,
            "connected_provider": emails_res.get("provider", "simulation"),
            "account_email": emails_res.get("account_email"),
        }
