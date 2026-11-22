import uuid
import pytest
from unittest.mock import patch

from app.core.config import settings
from app.services.integrations_service import IntegrationsService
from app.api.v1.integrations import KNOWN_INTEGRATIONS
from app.api.v1.router import api_router
from app.ai.tools import ALL_TOOLS, get_tool
from app.ai.tools.workspace_tools import (
    SearchEmailsTool,
    ReadEmailThreadTool,
    ReplyEmailTool,
    ArchiveEmailTool,
)


def test_microsoft_oauth_url_generation():
    """Verify Microsoft OAuth authorization URL contains proper client_id, scopes, and response_type."""
    with patch.object(settings, "MICROSOFT_CLIENT_ID", "test-ms-client-id"), \
         patch.object(settings, "MICROSOFT_REDIRECT_URI", "http://localhost:5173/auth/microsoft/callback"):
        url = IntegrationsService.get_microsoft_auth_url(state="test-state-123")
        assert "login.microsoftonline.com/common/oauth2/v2.0/authorize" in url
        assert "client_id=test-ms-client-id" in url
        assert "response_type=code" in url
        assert "state=test-state-123" in url
        assert "Mail.ReadWrite" in url
        assert "Mail.Send" in url
        assert "offline_access" in url


def test_known_integrations_catalog_contains_microsoft_and_google():
    """Verify KNOWN_INTEGRATIONS catalog contains both Microsoft Outlook and Google Workspace."""
    services = [item["service"] for item in KNOWN_INTEGRATIONS]
    assert "microsoft" in services, "Missing microsoft in KNOWN_INTEGRATIONS"
    assert "google" in services, "Missing google in KNOWN_INTEGRATIONS"

    outlook = next(item for item in KNOWN_INTEGRATIONS if item["service"] == "microsoft")
    assert "Microsoft" in outlook["name"]
    assert outlook["category"] == "Communication & Calendar"
    assert "Mail.ReadWrite" in outlook["details"]


def test_email_workspace_tools_registration():
    """Verify all 4 core email workspace tools are registered with appropriate approvals."""
    email_tools = [
        ("search_emails", SearchEmailsTool, False, "low"),
        ("read_email_thread", ReadEmailThreadTool, False, "low"),
        ("reply_email", ReplyEmailTool, True, "high"),
        ("archive_email", ArchiveEmailTool, False, "low"),
    ]
    for tool_name, tool_cls, req_approval, risk in email_tools:
        assert tool_name in ALL_TOOLS, f"Missing {tool_name} in ALL_TOOLS"
        tool = get_tool(tool_name)
        assert isinstance(tool, tool_cls)
        assert tool.requires_approval is req_approval
        assert tool.risk_level == risk


def test_email_router_endpoints_registered():
    """Verify dedicated email router endpoints are mounted on the v1 API router."""
    routes = [r.path for r in api_router.routes]

    # Email router endpoints
    assert "/email/messages" in routes
    assert "/email/messages/{message_id}" in routes
    assert "/email/send" in routes
    assert "/email/reply" in routes
    assert "/email/forward" in routes
    assert "/email/extract-tasks" in routes
    assert "/email/intelligence-summary" in routes


def test_microsoft_integration_oauth_endpoints_registered():
    """Verify Microsoft Outlook OAuth endpoints are mounted on the v1 API router."""
    routes = [r.path for r in api_router.routes]

    assert "/integrations/microsoft/auth-url" in routes
    assert "/integrations/microsoft/callback" in routes
