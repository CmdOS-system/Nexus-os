#!/usr/bin/env python3
"""Nexus Horizon panel: optional desktop companion, not a window manager."""
import datetime
import subprocess
import tkinter as tk

PANEL_BG = "#101827"
TEXT = "#f3f6fc"
ACCENT = "#8bd9d1"
LAUNCHER = ("/usr/local/bin/nexus-horizon",)
QUICK_APPS = (
    ("Files", ("thunar",)),
    ("Terminal", ("xfce4-terminal",)),
    ("Settings", ("xfce4-settings-manager",)),
)

def start_app(command):
    return subprocess.Popen(command, stdin=subprocess.DEVNULL, close_fds=True)

def start_launcher():
    return subprocess.Popen(LAUNCHER, stdin=subprocess.DEVNULL, close_fds=True)

class HorizonPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Horizon Panel")
        self.configure(bg=PANEL_BG)
        self.resizable(False, False)
        # Floating dock at the bottom of the screen
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.95)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._position()
        tk.Button(self, text="◈  NEXUS", bg=PANEL_BG, fg=ACCENT, activebackground="#202d41",
                  activeforeground=TEXT, relief="flat", padx=18, pady=9, font=("Sans", 11, "bold"),
                  command=self.open_launcher).pack(side="left")
        for name, command in QUICK_APPS:
            tk.Button(self, text=name, bg=PANEL_BG, fg=TEXT,
                      activebackground="#202d41", activeforeground=ACCENT,
                      relief="flat", padx=12, pady=9, font=("Sans", 10),
                      command=lambda cmd=command: self.open_quick_app(cmd)).pack(side="left")
        self.clock = tk.StringVar()
        tk.Label(self, textvariable=self.clock, bg=PANEL_BG, fg=TEXT,
                 font=("Sans", 11, "bold")).pack(side="right", padx=22)
        self._tick()

    def _position(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(720, screen_width - 48)
        height = 48
        x = (screen_width - width) // 2
        y = screen_height - height - 12
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _tick(self):
        self.clock.set(datetime.datetime.now().strftime("%a %d %b  %H:%M"))
        self.after(30000, self._tick)

    def open_quick_app(self, command):
        try:
            start_app(command)
        except OSError:
            from tkinter import messagebox
            messagebox.showerror("Nexus Horizon", "The selected application is unavailable.")

    def open_launcher(self):
        try:
            start_launcher()
        except OSError:
            from tkinter import messagebox
            messagebox.showerror("Nexus Horizon", "The application launcher is unavailable.")

if __name__ == "__main__":
    HorizonPanel().mainloop()
