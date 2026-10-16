#!/usr/bin/env python3
"""Nexus OS installer preview: read-only inspection, never installs or writes disks."""
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

sys.path.insert(0, str(Path("/opt/nexus/agent")))
from installer_inventory import capture_inventory, require_unchanged_inventory
from installer_plan import plan_install, UnsafeTarget
from installer_preflight import inspect


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
            report = inspect(inventory)
            eligible = [item["path"] for item in report["disks"] if item["eligible"]]
            self.devices = eligible
            self.inventory = inventory
            self.choice.configure(values=eligible)
            eligible_count = len(self.devices)
            rejected_count = len(report["disks"]) - eligible_count
            lines = [f"Disk readiness (read-only): {eligible_count} eligible, {rejected_count} rejected."]
            for item in report["disks"]:
                status = "READY FOR PREVIEW" if item["eligible"] else "REJECTED"
                detail = "" if item["eligible"] else f" — {item['reason']}"
                lines.append(f"{item['path']}: {status}{detail}")
            if not self.devices:
                lines.append("\nNo eligible disks found. Selection is unavailable.")
            else:
                lines.append("\nOnly eligible disks are selectable. Review is read-only; no changes will be made.")
            self.show("\n".join(lines))
        except (UnsafeTarget, KeyError, TypeError, ValueError) as exc:
            self.inventory = None
            self.devices = []
            self.target.set("")
            self.choice.configure(values=[])
            self.show(f"Disk inventory unavailable: {exc}")

    def review(self):
        if self.inventory is None or not self.target.get():
            messagebox.showwarning("Nexus OS", "Refresh inventory and select a disk first.")
            return
        if self.target.get() not in self.devices:
            self.target.set("")
            self.show("Target rejected: disk is not eligible in the current inventory. No disk changes were made.")
            return
        try:
            # Re-enumerate before previewing: disk topology may have changed since Refresh.
            current_inventory = capture_inventory()
            require_unchanged_inventory(self.inventory, current_inventory)
            plan = plan_install(current_inventory, self.target.get())
            self.show(f"Disk: {plan.path}\nModel: {plan.model}\nSerial: {plan.serial}\nSize: {plan.size_bytes:,} bytes\n\n{plan.warning}\n\nInstallation is DISABLED in this preview.")
        except UnsafeTarget as exc:
            self.inventory = None
            self.devices = []
            self.target.set("")
            self.choice.configure(values=[])
            self.show(f"Target rejected: {exc}\n\nNo disk changes were made.")


if __name__ == "__main__":
    Preview().mainloop()
