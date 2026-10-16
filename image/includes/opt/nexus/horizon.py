#!/usr/bin/env python3
"""Nexus Horizon: keyboard-first application launcher prototype for XFCE."""
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# Fixed commands; search text is never interpreted as a shell command.
APPLICATIONS = (
    ("Files", "Browse your documents", ("thunar",)),
    ("Web", "Open your browser", ("xdg-open", "https://www.debian.org/")),
    ("Terminal", "Work with commands", ("xfce4-terminal",)),
    ("Settings", "Personalize your desktop", ("xfce4-settings-manager",)),
    ("Nexus Control Center", "AI preferences and system tools", ("/usr/bin/python3", "/opt/nexus/control-center.py")),
    ("Installation Preview", "Inspect an installation plan without writing disks", ("/usr/bin/python3", "/opt/nexus/installer-preview.py")),
)

def matching_apps(query):
    words = query.casefold().split()
    return [app for app in APPLICATIONS if all(word in (app[0] + " " + app[1]).casefold() for word in words)]

def launch(command):
    """Launch a vetted app without a shell or elevated privileges."""
    return subprocess.Popen(command, stdin=subprocess.DEVNULL, close_fds=True)

class Horizon(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Horizon")
        self.geometry("760x570")
        self.minsize(560, 460)
        self.configure(bg="#101827")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self.render_apps())
        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Control-f>", lambda _: self.search_entry.focus_set())
        self.bind("<Return>", self.launch_first)
        self._build()
        self.render_apps()
        self.search_entry.focus_set()

    def _build(self):
        tk.Label(self, text="NEXUS  /  HORIZON", fg="#8bd9d1", bg="#101827", font=("Sans", 11, "bold")).pack(anchor="w", padx=34, pady=(28, 3))
        tk.Label(self, text="Everything in reach.", fg="#f3f6fc", bg="#101827", font=("Sans", 26, "bold")).pack(anchor="w", padx=34)
        tk.Label(self, text="Find an app. Stay in control. Your computer works for you.", fg="#a9b9d0", bg="#101827", font=("Sans", 11)).pack(anchor="w", padx=34, pady=(4, 20))
        self.search_entry = tk.Entry(self, textvariable=self.search, font=("Sans", 15), bg="#202d41", fg="white", insertbackground="white", relief="flat")
        self.search_entry.pack(fill="x", padx=34, ipady=12)
        tk.Label(self, text="APPLICATIONS   ·   TYPE TO FILTER   ·   ENTER TO OPEN   ·   ESC TO CLOSE", fg="#8bd9d1", bg="#101827", font=("Sans", 9)).pack(anchor="w", padx=34, pady=(22, 10))
        self.list_frame = tk.Frame(self, bg="#101827")
        self.list_frame.pack(fill="both", expand=True, padx=34)
        self.feedback = tk.StringVar(value="Ready. No actions run until you select an app.")
        tk.Label(self, textvariable=self.feedback, fg="#a9b9d0", bg="#101827", anchor="w", wraplength=650).pack(fill="x", padx=34, pady=(6, 20))

    def render_apps(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        results = matching_apps(self.search.get())
        if not results:
            tk.Label(self.list_frame, text="No matching applications", bg="#101827", fg="#a9b9d0").pack(anchor="w")
        for name, description, command in results:
            button = tk.Button(self.list_frame, text=name + "    ·    " + description, command=lambda cmd=command: self.open_app(cmd),
                               bg="#202d41", fg="#f3f6fc", activebackground="#31516a", activeforeground="white",
                               relief="flat", anchor="w", padx=16, pady=11, font=("Sans", 11))
            button.pack(fill="x", pady=3)

    def open_app(self, command):
        try:
            launch(command)
            self.feedback.set("Application launch requested.")
        except OSError:
            self.feedback.set("This application is unavailable in the current environment.")

    def launch_first(self, _event=None):
        results = matching_apps(self.search.get())
        if results:
            self.open_app(results[0][2])

if __name__ == "__main__":
    Horizon().mainloop()
