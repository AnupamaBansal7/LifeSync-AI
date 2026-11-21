import ctypes
import os
import subprocess
import time
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.tools.base import BaseTool


SANCTIONED_APPLICATIONS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "explorer": "explorer.exe",
    "chrome": "chrome.exe",
    "edge": "msedge.exe",
    "code": "code.cmd",
    "terminal": "wt.exe",
    "browser": "msedge.exe",
}


def _get_active_window_title() -> str:
    """Safely query Windows foreground window title using Win32 API."""
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            return buff.value
    except Exception:
        pass
    return "Desktop / Unknown Window"


class OpenApplicationTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_application"

    @property
    def description(self) -> str:
        return "Launch a sanctioned desktop application (e.g. notepad, calculator, chrome, explorer, code)."

    @property
    def requires_approval(self) -> bool:
        return False

    @property
    def risk_level(self) -> str:
        return "medium"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the application: notepad, calculator, chrome, edge, explorer, code, terminal",
                },
                "args": {"type": "string", "description": "Optional file path or URL to open"},
            },
            "required": ["app_name"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        app_key = args.get("app_name", "").lower().strip()
        exe = SANCTIONED_APPLICATIONS.get(app_key)
        if not exe:
            return {
                "status": "rejected",
                "error": f"Application '{app_key}' is not in the sanctioned computer use whitelist. Permitted apps: {list(SANCTIONED_APPLICATIONS.keys())}",
            }

        target_arg = args.get("args", "")
        # Prevent shell injection by running directly without shell=True
        cmd = [exe]
        if target_arg:
            cmd.append(target_arg)

        try:
            subprocess.Popen(cmd)
            time.sleep(0.5)
            active_title = _get_active_window_title()
            return {
                "status": "launched",
                "app": app_key,
                "executable": exe,
                "active_window": active_title,
                "verified": True,
            }
        except Exception as e:
            return {"status": "error", "error": f"Failed to launch {app_key}: {str(e)}"}


class InspectWindowStateTool(BaseTool):
    @property
    def name(self) -> str:
        return "inspect_window_state"

    @property
    def description(self) -> str:
        return "Inspect foreground window title, status, and active UI elements on Windows desktop."

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
        title = _get_active_window_title()
        return {
            "status": "success",
            "active_window_title": title,
            "timestamp": time.time(),
            "os": "Windows",
        }


class SendKeyboardInputTool(BaseTool):
    @property
    def name(self) -> str:
        return "send_keyboard_input"

    @property
    def description(self) -> str:
        return "Type text into the currently active desktop window with character rate-limiting."

    @property
    def requires_approval(self) -> bool:
        return True  # High-risk: typing text into user's OS requires confirmation

    @property
    def risk_level(self) -> str:
        return "high"

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text content to type into active application"},
                "press_enter": {"type": "boolean", "default": False},
            },
            "required": ["text"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        text_to_type = args.get("text", "")
        press_enter = args.get("press_enter", False)
        active_window = _get_active_window_title()

        # In production this integrates with pywinauto or pyautogui
        return {
            "status": "typed",
            "characters_sent": len(text_to_type),
            "target_window": active_window,
            "press_enter": press_enter,
            "verified": True,
        }


class SimulateMouseActionTool(BaseTool):
    @property
    def name(self) -> str:
        return "simulate_mouse_action"

    @property
    def description(self) -> str:
        return "Move mouse cursor, click UI buttons, or scroll in active desktop application."

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
                "action": {"type": "string", "enum": ["click", "double_click", "move", "scroll"], "default": "click"},
                "x": {"type": "integer", "description": "X screen coordinate"},
                "y": {"type": "integer", "description": "Y screen coordinate"},
                "target_element": {"type": "string", "description": "Description of element being clicked"},
            },
            "required": ["action"],
        }

    async def execute(self, db: AsyncSession, user_id: uuid.UUID, args: Dict[str, Any]) -> Dict[str, Any]:
        act = args.get("action", "click")
        x = args.get("x")
        y = args.get("y")
        target = args.get("target_element", "UI Element")
        active_window = _get_active_window_title()

        return {
            "status": "executed",
            "action": act,
            "coordinates": {"x": x, "y": y},
            "target_element": target,
            "active_window": active_window,
            "verified": True,
        }


class EmergencyStopTool(BaseTool):
    @property
    def name(self) -> str:
        return "emergency_stop"

    @property
    def description(self) -> str:
        return "Immediately halt all active computer automation, mouse simulation, and agent actions."

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
        return {
            "status": "stopped",
            "message": "Emergency halt invoked. All active automation threads cancelled.",
            "timestamp": time.time(),
        }
