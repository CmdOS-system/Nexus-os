#!/usr/bin/env python3
"""Nexus OS installer preview: read-only inspection, never installs or writes disks."""
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

sys.path.insert(0, str(Path("/opt/nexus/agent")))
from installer_inventory import capture_inventory
from installer_plan import plan_install, UnsafeTarget


class Preview(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus OS — Installation Preview (Read Only)")
        self.geometry("680x420")
        self.inventory = None
        self.devices = []
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Installation preview", font=("", 18, "bold")).pack(anchor="w")
        ttk.Label(frame, text="READ ONLY — this application cannot install, format or erase disks.").pack(anchor="w", pady=(6, 16))
        self.target = tk.StringVar()
        self.choice = ttk.Combobox(frame, textvariable=self.target, state="readonly", width=72)
        self.choice.pack(fill="x")
        ttk.Button(frame, text="Refresh disk inventory", command=self.refresh).pack(anchor="w", pady=8)
        ttk.Button(frame, text="Review installation plan", command=self.review).pack(anchor="w", pady=8)
        self.result = tk.Text(frame, height=9, wrap="word", state="disabled")
        self.result.pack(fill="both", expand=True)
        self.refresh()

    def show(self, value):
        self.result.configure(state="normal")
        self.result.delete("1.0", "end")
        self.result.insert("end", value)
        self.result.configure(state="disabled")

    def refresh(self):
        self.inventory = None
        self.devices = []
        self.target.set("")
        self.choice.configure(values=[])
        self.show("Scanning read-only inventory…")
        try:
            inventory = capture_inventory()
            devices = [d for d in inventory["blockdevices"] if isinstance(d, dict) and d.get("type") == "disk"]
            self.devices = [d.get("path") for d in devices if isinstance(d.get("path"), str)]
            self.inventory = inventory
            self.choice.configure(values=self.devices)
            self.show("Select a disk and review its safety checks. No changes will be made.")
        except UnsafeTarget as exc:
            self.show(f"Disk inventory unavailable: {exc}")

    def review(self):
        if self.inventory is None or not self.target.get():
            messagebox.showwarning("Nexus OS", "Refresh inventory and select a disk first.")
            return
        try:
            plan = plan_install(self.inventory, self.target.get())
            self.show(f"Disk: {plan.path}\nModel: {plan.model}\nSerial: {plan.serial}\nSize: {plan.size_bytes:,} bytes\n\n{plan.warning}\n\nInstallation is DISABLED in this preview.")
        except UnsafeTarget as exc:
            self.show(f"Target rejected: {exc}\n\nNo disk changes were made.")


if __name__ == "__main__":
    Preview().mainloop()
