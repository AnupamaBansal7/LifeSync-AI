"""
LifeSync AI 3.0 — Autonomous Desktop Companion ("Sync")
Always-on-top, draggable, intelligent OS-level floating AI companion that interacts
directly with the LifeSync AI multi-agent orchestrator, Google Workspace integrations,
and background automation engine.
"""

import base64
import io
import json
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import urllib.error
import urllib.request
import webbrowser

# Optional imports for Windows integration
try:
    import winreg
    HAS_WINREG = True
except ImportError:
    HAS_WINREG = False

try:
    from PIL import ImageGrab
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


BACKEND_API_BASE = os.environ.get("LIFESYNC_API_URL", "http://localhost:8000/api/v1")
WEB_DASHBOARD_URL = os.environ.get("LIFESYNC_WEB_URL", "http://localhost:5173")
ACCESS_TOKEN = os.environ.get("LIFESYNC_ACCESS_TOKEN", "")
RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "LifeSyncCompanion"


class DesktopAIPet:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LifeSync Companion")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        # Transparent background for orb effect
        self.transparent_color = "#030712"
        try:
            self.root.wm_attributes("-transparentcolor", self.transparent_color)
        except Exception:
            pass

        # Window dimensions & positioning (bottom-right of screen)
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.orb_size = 64
        self.chat_w = 400
        self.chat_h = 520

        self.is_expanded = False
        self.pos_x = screen_w - self.orb_size - 30
        self.pos_y = screen_h - self.orb_size - 80
        self.root.geometry(f"{self.orb_size}x{self.orb_size}+{self.pos_x}+{self.pos_y}")

        self.active_role = "personal"
        self.conversation_id = None
        self.is_busy = False
        self.backend_online = False
        self.pending_approvals = 0

        # Build Canvas Orb
        self.canvas = tk.Canvas(
            self.root,
            width=self.orb_size,
            height=self.orb_size,
            bg=self.transparent_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Draw glowing orb layers
        self.outer_ring = self.canvas.create_oval(4, 4, 60, 60, outline="#6366f1", width=2, fill="#1e1b4b")
        self.inner_orb = self.canvas.create_oval(12, 12, 52, 52, fill="#4f46e5", outline="#818cf8", width=1)
        self.core = self.canvas.create_oval(22, 22, 42, 42, fill="#c7d2fe", outline="")
        self.label = self.canvas.create_text(32, 32, text="SYNC", fill="#ffffff", font=("Segoe UI", 8, "bold"))

        # Dragging events
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        # Pulse animation state
        self.pulse_phase = 0
        self.animate_pulse()

        # Chat Drawer Window
        self.chat_win = None

        # Start Heartbeat in background daemon thread
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def is_autostart_enabled(self) -> bool:
        if not HAS_WINREG:
            return False
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_READ)
            val, _ = winreg.QueryValueEx(key, APP_REG_NAME)
            winreg.CloseKey(key)
            return bool(val)
        except Exception:
            return False

    def set_autostart(self, enable: bool):
        if not HAS_WINREG:
            return
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY_PATH, 0, winreg.KEY_SET_VALUE)
            if enable:
                script_path = os.path.abspath(__file__)
                python_exe = sys.executable
                cmd = f'"{python_exe}" "{script_path}"'
                winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_REG_NAME)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"[Autostart Error] {e}")

    def _heartbeat_loop(self):
        """Periodically pings the LifeSync backend to check connectivity and pending approvals."""
        while True:
            try:
                url = f"{BACKEND_API_BASE}/roles/default"
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status == 200:
                        self.backend_online = True
            except Exception:
                self.backend_online = False

            time.sleep(10)

    def animate_pulse(self):
        self.pulse_phase = (self.pulse_phase + 1) % 20

        if not self.backend_online:
            ring_color = "#f43f5e" if self.pulse_phase < 10 else "#9f1239"
            core_color = "#fda4af"
        elif self.is_busy:
            ring_color = "#38bdf8"
            core_color = "#e0f2fe"
        else:
            ring_color = "#818cf8" if self.pulse_phase < 10 else "#6366f1"
            core_color = "#e0e7ff" if self.pulse_phase < 10 else "#c7d2fe"

        self.canvas.itemconfig(self.outer_ring, outline=ring_color)
        self.canvas.itemconfig(self.core, fill=core_color)
        self.root.after(100, self.animate_pulse)

    def on_press(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.has_moved = False

    def on_drag(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        if abs(dx) > 3 or abs(dy) > 3:
            self.has_moved = True
            self.pos_x += dx
            self.pos_y += dy
            self.root.geometry(f"+{self.pos_x}+{self.pos_y}")
            if self.chat_win and self.chat_win.winfo_exists():
                self.update_chat_pos()

    def on_release(self, event):
        if not self.has_moved:
            self.toggle_chat()

    def toggle_chat(self):
        if self.chat_win and self.chat_win.winfo_exists():
            self.chat_win.destroy()
            self.chat_win = None
            return

        self.chat_win = tk.Toplevel(self.root)
        self.chat_win.overrideredirect(True)
        self.chat_win.wm_attributes("-topmost", True)
        self.chat_win.configure(bg="#0f172a")

        self.update_chat_pos()

        # Header Frame
        hdr = tk.Frame(self.chat_win, bg="#020617", padx=10, pady=8)
        hdr.pack(fill=tk.X)

        title_frame = tk.Frame(hdr, bg="#020617")
        title_frame.pack(side=tk.LEFT)

        lbl = tk.Label(title_frame, text="Sync AI 3.0", font=("Segoe UI", 10, "bold"), fg="#e2e8f0", bg="#020617")
        lbl.pack(side=tk.LEFT)

        status_text = " ● Live" if self.backend_online else " ● Reconnecting"
        status_color = "#10b981" if self.backend_online else "#f43f5e"
        self.status_lbl = tk.Label(title_frame, text=status_text, font=("Segoe UI", 8), fg=status_color, bg="#020617")
        self.status_lbl.pack(side=tk.LEFT, padx=6)

        # Action Buttons in Header
        btn_frame = tk.Frame(hdr, bg="#020617")
        btn_frame.pack(side=tk.RIGHT)

        web_btn = tk.Button(
            btn_frame,
            text="🌐 Web",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#1e293b",
            bd=0,
            padx=6,
            cursor="hand2",
            command=lambda: webbrowser.open(WEB_DASHBOARD_URL),
        )
        web_btn.pack(side=tk.LEFT, padx=3)

        screen_btn = tk.Button(
            btn_frame,
            text="👁 Screen",
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#1e293b",
            bd=0,
            padx=6,
            cursor="hand2",
            command=self.capture_and_analyze_screen,
        )
        screen_btn.pack(side=tk.LEFT, padx=3)

        close_btn = tk.Button(
            btn_frame,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            fg="#94a3b8",
            bg="#020617",
            bd=0,
            activeforeground="#f43f5e",
            activebackground="#020617",
            cursor="hand2",
            command=self.toggle_chat,
        )
        close_btn.pack(side=tk.LEFT, padx=3)

        # Context & Autostart Selector Bar
        ctx_frame = tk.Frame(self.chat_win, bg="#0f172a", padx=10, pady=4)
        ctx_frame.pack(fill=tk.X)

        tk.Label(ctx_frame, text="Role:", font=("Segoe UI", 8), fg="#94a3b8", bg="#0f172a").pack(side=tk.LEFT)
        self.role_var = tk.StringVar(value=self.active_role)
        role_menu = ttk.Combobox(
            ctx_frame,
            textvariable=self.role_var,
            values=["personal", "student", "professional", "entrepreneur"],
            width=11,
            state="readonly",
            font=("Segoe UI", 8),
        )
        role_menu.pack(side=tk.LEFT, padx=4)
        role_menu.bind("<<ComboboxSelected>>", lambda e: setattr(self, "active_role", self.role_var.get()))

        # Autostart checkbox
        self.autostart_var = tk.BooleanVar(value=self.is_autostart_enabled())
        autostart_cb = tk.Checkbutton(
            ctx_frame,
            text="Start with Windows",
            variable=self.autostart_var,
            font=("Segoe UI", 8),
            fg="#94a3b8",
            bg="#0f172a",
            selectcolor="#1e293b",
            activebackground="#0f172a",
            command=lambda: self.set_autostart(self.autostart_var.get()),
        )
        autostart_cb.pack(side=tk.RIGHT)

        # Chat Message History Text Widget
        self.msg_area = tk.Text(
            self.chat_win,
            bg="#020617",
            fg="#cbd5e1",
            font=("Segoe UI", 9),
            wrap=tk.WORD,
            bd=0,
            padx=10,
            pady=8,
        )
        self.msg_area.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.msg_area.insert(
            tk.END,
            "Sync: Hello! I am your LifeSync AI 3.0 desktop companion.\n"
            "• Ask me to plan your day, schedule study sessions, or create tasks.\n"
            "• Click '👁 Screen' to analyze whatever is currently on your display.\n"
            "• Google Workspace, Smart Calendar & Gmail tools are active.\n\n",
        )
        self.msg_area.config(state=tk.DISABLED)

        # Input Frame
        in_frame = tk.Frame(self.chat_win, bg="#0f172a", padx=8, pady=8)
        in_frame.pack(fill=tk.X)

        self.input_entry = tk.Entry(
            in_frame,
            bg="#1e293b",
            fg="#ffffff",
            font=("Segoe UI", 9),
            insertbackground="#ffffff",
            bd=0,
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 6))
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        self.input_entry.focus_set()

        send_btn = tk.Button(
            in_frame,
            text="Send",
            font=("Segoe UI", 9, "bold"),
            fg="#ffffff",
            bg="#4f46e5",
            activebackground="#4338ca",
            bd=0,
            padx=12,
            cursor="hand2",
            command=self.send_message,
        )
        send_btn.pack(side=tk.RIGHT, ipady=4)

    def update_chat_pos(self):
        if not self.chat_win:
            return
        cx = max(10, self.pos_x - self.chat_w + self.orb_size)
        cy = max(10, self.pos_y - self.chat_h - 10)
        self.chat_win.geometry(f"{self.chat_w}x{self.chat_h}+{cx}+{cy}")

    def append_message(self, sender: str, text: str):
        if not self.chat_win or not self.chat_win.winfo_exists():
            return
        self.msg_area.config(state=tk.NORMAL)
        self.msg_area.insert(tk.END, f"{sender}: {text}\n\n")
        self.msg_area.see(tk.END)
        self.msg_area.config(state=tk.DISABLED)

    def capture_and_analyze_screen(self):
        """Grabs display frame and queries ScreenAssistanceAgent."""
        if self.is_busy:
            return
        self.append_message("You", "[Shared Active Screen Frame for AI Inspection]")
        self.is_busy = True

        threading.Thread(target=self._capture_and_send, daemon=True).start()

    def _capture_and_send(self):
        img_b64 = ""
        if HAS_PIL:
            try:
                # Capture primary monitor
                snapshot = ImageGrab.grab()
                # Downsample to 1280x720 for fast transport
                snapshot.thumbnail((1280, 720))
                buffer = io.BytesIO()
                snapshot.save(buffer, format="JPEG", quality=70)
                img_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")
            except Exception as e:
                print(f"[Screen Capture Warning] {e}")

        prompt = "Inspect what is on my screen right now. Identify active apps, detect errors or actionable tasks, and suggest immediate next steps."
        self._query_backend(prompt, screen_data=img_b64)

    def send_message(self):
        text = self.input_entry.get().strip()
        if not text or self.is_busy:
            return
        self.input_entry.delete(0, tk.END)
        self.append_message("You", text)
        self.is_busy = True

        threading.Thread(target=self._query_backend, args=(text,), daemon=True).start()

    def _query_backend(self, prompt: str, screen_data: str = ""):
        url = f"{BACKEND_API_BASE}/agents/chat"
        headers = {"Content-Type": "application/json"}
        if ACCESS_TOKEN:
            headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"

        payload = {
            "message": prompt,
            "conversation_id": self.conversation_id,
            "active_role": self.active_role,
        }
        if screen_data:
            payload["screen_context"] = {"image_data": screen_data}

        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.conversation_id = data.get("conversation_id")
                reply = data.get("reply", "No response from orchestrator.")
                approvals = data.get("approvals", [])
                if approvals:
                    reply += f"\n\n⚠️ Action Approval Card staged ({len(approvals)} pending). Review on Web Dashboard."

                self.root.after(0, lambda: self.append_message("Sync", reply))
        except urllib.error.URLError:
            reply = (
                "Local LifeSync backend is offline.\n"
                "Please start the backend service at http://localhost:8000 to interact with autonomous agents."
            )
            self.root.after(0, lambda: self.append_message("System", reply))
        except Exception as e:
            self.root.after(0, lambda: self.append_message("Error", str(e)))
        finally:
            self.is_busy = False


def main():
    root = tk.Tk()
    app = DesktopAIPet(root)
    root.mainloop()


if __name__ == "__main__":
    main()
