#!/usr/bin/env python3
"""Nexus Control Center prototype using the shared validated AI settings model."""
import sys
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

AGENT_DIR=Path("/opt/nexus/agent")
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0,str(AGENT_DIR))
from settings import AISettings
from settings_store import load_settings, save_settings
from config import provider_secret_ref
from linux_secret_store import LinuxSecretStore
from local_model_diagnostics import check_local_model

CONFIG=Path.home()/".config/nexus/ai-settings.json"
MODES=("off","local","cloud","hybrid")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Control Center")
        self.geometry("640x500"); self.minsize(580,440)
        self.mode=tk.StringVar(value="off")
        self.provider=tk.StringVar(); self.model=tk.StringVar()
        self.consent=tk.BooleanVar(value=False); self.api_key=tk.StringVar()
        self.status=tk.StringVar(value="AI configuration: Off")
        self._probe_generation=0
        self.mode.trace_add("write",self._update_status)
        self.provider.trace_add("write",self._invalidate_probe)
        self.model.trace_add("write",self._invalidate_probe)
        self._build(); self._load()
        self._update_status()

    def _build(self):
        frame=ttk.Frame(self,padding=24); frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="Nexus Control Center",font=("",20,"bold")).pack(anchor="w")
        ttk.Label(frame,text="Your system, your choices — local controls first.",font=("",10)).pack(anchor="w",pady=(2,14))
        ttk.Separator(frame,orient="horizontal").pack(fill="x",pady=(0,12))
        ttk.Label(frame,text="Nexus AI",font=("",15,"bold")).pack(anchor="w")
        ttk.Label(frame,text="Choose how Nexus Agent may use AI. API keys are never stored here.").pack(anchor="w",pady=(4,8))
        ttk.Label(frame,textvariable=self.status).pack(anchor="w",pady=(0,4))
        ttk.Label(frame,text="This describes settings only; it does not verify connectivity.",font=("",9)).pack(anchor="w",pady=(0,6))
        self.probe_result=tk.StringVar(value="Local model check has not run.")
        ttk.Label(frame,textvariable=self.probe_result,wraplength=540).pack(anchor="w",pady=(0,6))
        ttk.Button(frame,text="Check local Ollama model",command=self._check_local_model).pack(anchor="w",pady=(0,10))
        form=ttk.Frame(frame); form.pack(fill="x")
        ttk.Label(form,text="Mode").grid(row=0,column=0,sticky="w",pady=6)
        ttk.Combobox(form,textvariable=self.mode,values=MODES,state="readonly").grid(row=0,column=1,sticky="ew",pady=6)
        ttk.Label(form,text="Provider").grid(row=1,column=0,sticky="w",pady=6)
        ttk.Entry(form,textvariable=self.provider).grid(row=1,column=1,sticky="ew",pady=6)
        ttk.Label(form,text="Model").grid(row=2,column=0,sticky="w",pady=6)
        ttk.Entry(form,textvariable=self.model).grid(row=2,column=1,sticky="ew",pady=6)
        ttk.Label(form,text="API key").grid(row=3,column=0,sticky="w",pady=6)
        ttk.Entry(form,textvariable=self.api_key,show="•").grid(row=3,column=1,sticky="ew",pady=6)
        ttk.Checkbutton(form,text="Allow cloud AI for this configuration",variable=self.consent).grid(row=4,column=1,sticky="w",pady=8)
        form.columnconfigure(1,weight=1)
        ttk.Button(frame,text="Save AI settings",command=self._save).pack(anchor="e",pady=14)
        ttk.Separator(frame,orient="horizontal").pack(fill="x",pady=(2,12))
        ttk.Label(frame,text="System tools",font=("",15,"bold")).pack(anchor="w")
        ttk.Label(frame,text="Installation is disabled. You can inspect disks and review a plan safely.").pack(anchor="w",pady=(4,8))
        ttk.Button(frame,text="Open installation preview (read-only)",command=self._open_installer_preview).pack(anchor="w")

    def _invalidate_probe(self, *_):
        self._probe_generation += 1
        if hasattr(self, "probe_result"):
            self.probe_result.set("Model selection changed. Run the local check again.")

    def _update_status(self, *_):
        self._invalidate_probe()
        descriptions = {
            "off": "AI configuration: Off — AI requests disabled by configuration",
            "local": "AI configuration: Local — model availability not verified",
            "cloud": "AI configuration: Cloud — connection not verified",
            "hybrid": "AI configuration: Hybrid — connection not verified",
        }
        self.status.set(descriptions.get(self.mode.get(), "AI configuration: Invalid mode"))

    def _check_local_model(self):
        if self.mode.get() != "local" or self.provider.get().strip().lower() != "ollama":
            self.probe_result.set("Select Local mode and Ollama provider to run this check.")
            return
        model = self.model.get().strip()
        self._probe_generation += 1
        generation = self._probe_generation
        self.probe_result.set("Checking local Ollama service (no prompts sent)…")
        def worker():
            available, detail = check_local_model(model)
            try:
                self.after(0, lambda: self._display_probe_result(generation, available, detail))
            except RuntimeError:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def _display_probe_result(self, generation, available, detail):
        if generation != self._probe_generation:
            return
        self.probe_result.set(("Ready: " if available else "Not ready: ") + detail)

    def _open_installer_preview(self):
        preview = Path("/opt/nexus/installer-preview.py")
        if not preview.is_file():
            messagebox.showerror("Nexus OS", "Installation preview is not available in this system.")
            return
        try:
            subprocess.Popen(["/usr/bin/python3", str(preview)], stdin=subprocess.DEVNULL, close_fds=True)
        except OSError as exc:
            messagebox.showerror("Nexus OS", f"Could not open installation preview: {exc}")

    def _load(self):
        try:
            s=load_settings(CONFIG)
        except (RuntimeError,ValueError):
            messagebox.showwarning("Nexus AI","Existing settings are invalid or cannot be read.")
            return
        self.mode.set(s.mode); self.provider.set(s.provider or "")
        self.model.set(s.model or ""); self.consent.set(s.cloud_consent)

    def _save(self):
        mode=self.mode.get()
        provider=self.provider.get().strip() or None
        model=self.model.get().strip() or None
        consent=bool(self.consent.get())
        if mode=="off":
            provider=model=None; consent=False
        try:
            settings=AISettings(mode,provider,model,consent).validate()
            if mode in {"cloud","hybrid"}:
                store=LinuxSecretStore(); ref=provider_secret_ref(provider)
                if self.api_key.get():
                    store.store(ref,self.api_key.get()); self.api_key.set("")
                elif not store.has(ref):
                    raise ValueError("API key is required for this cloud provider")
            save_settings(CONFIG,settings)
        except (TypeError,ValueError,RuntimeError,OSError) as exc:
            messagebox.showerror("Nexus AI",str(exc))
            return
        messagebox.showinfo("Nexus AI","Settings saved securely.")

if __name__=="__main__":
    App().mainloop()
