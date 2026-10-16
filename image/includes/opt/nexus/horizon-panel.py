#!/usr/bin/env python3
"""Nexus Horizon panel: optional desktop companion, not a window manager."""
import datetime
import subprocess
import tkinter as tk

PANEL_BG = "#101827"
TEXT = "#f3f6fc"
ACCENT = "#8bd9d1"
LAUNCHER = ("/usr/local/bin/nexus-horizon",)

def start_launcher():
    return subprocess.Popen(LAUNCHER, stdin=subprocess.DEVNULL, close_fds=True)

class HorizonPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Horizon Panel")
        self.configure(bg=PANEL_BG)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._position()
        tk.Button(self, text="◈  NEXUS", bg=PANEL_BG, fg=ACCENT, activebackground="#202d41",
                  activeforeground=TEXT, relief="flat", padx=18, pady=9, font=("Sans", 11, "bold"),
                  command=self.open_launcher).pack(side="left")
        tk.Label(self, text="HORIZON  ·  DESKTOP PREVIEW", bg=PANEL_BG, fg="#a9b9d0",
                 font=("Sans", 9)).pack(side="left", padx=14)
        self.clock = tk.StringVar()
        tk.Label(self, textvariable=self.clock, bg=PANEL_BG, fg=TEXT,
                 font=("Sans", 11, "bold")).pack(side="right", padx=22)
        self._tick()

    def _position(self):
        width = min(1000, self.winfo_screenwidth())
        self.geometry(f"{width}x48+0+0")

    def _tick(self):
        self.clock.set(datetime.datetime.now().strftime("%a %d %b  %H:%M"))
        self.after(30000, self._tick)

    def open_launcher(self):
        try:
            start_launcher()
        except OSError:
            from tkinter import messagebox
            messagebox.showerror("Nexus Horizon", "The application launcher is unavailable.")

if __name__ == "__main__":
    HorizonPanel().mainloop()
