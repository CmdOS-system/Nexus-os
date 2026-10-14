#!/usr/bin/env python3
"""Nexus Control Center prototype using the shared validated AI settings model."""
import sys
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

CONFIG=Path.home()/".config/nexus/ai-settings.json"
MODES=("off","local","cloud","hybrid")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Control Center")
        self.geometry("560x360"); self.minsize(520,320)
        self.mode=tk.StringVar(value="off")
        self.provider=tk.StringVar(); self.model=tk.StringVar()
        self.consent=tk.BooleanVar(value=False); self.api_key=tk.StringVar()
        self._build(); self._load()

    def _build(self):
        frame=ttk.Frame(self,padding=24); frame.pack(fill="both",expand=True)
        ttk.Label(frame,text="Nexus AI",font=("",18,"bold")).pack(anchor="w")
        ttk.Label(frame,text="Choose how Nexus Agent may use AI. API keys are never stored here.").pack(anchor="w",pady=(4,20))
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
        ttk.Button(frame,text="Save",command=self._save).pack(anchor="e",pady=18)

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
            if mode in {"cloud","hybrid"} and self.api_key.get():
                LinuxSecretStore().store(provider_secret_ref(provider),self.api_key.get())
                self.api_key.set("")
            save_settings(CONFIG,settings)
        except (TypeError,ValueError,RuntimeError,OSError) as exc:
            messagebox.showerror("Nexus AI",str(exc))
            return
        messagebox.showinfo("Nexus AI","Settings saved securely.")

if __name__=="__main__":
    App().mainloop()
