#!/usr/bin/env python3
"""Nexus Control Center prototype: safe AI mode configuration UI."""
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox

CONFIG = Path.home() / ".config/nexus/ai-settings.json"
MODES = ("off", "local", "cloud", "hybrid")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Nexus Control Center")
        self.geometry("560x360")
        self.minsize(520, 320)
        self.mode = tk.StringVar(value="off")
        self.provider = tk.StringVar()
        self.model = tk.StringVar()
        self.consent = tk.BooleanVar(value=False)
        self._build()
        self._load()

    def _build(self):
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Nexus AI", font=("", 18, "bold")).pack(anchor="w")
        ttk.Label(frame, text="Choose how Nexus Agent may use AI. API keys are never stored here.").pack(anchor="w", pady=(4,20))
        form = ttk.Frame(frame); form.pack(fill="x")
        ttk.Label(form, text="Mode").grid(row=0,column=0,sticky="w",pady=6)
        ttk.Combobox(form,textvariable=self.mode,values=MODES,state="readonly").grid(row=0,column=1,sticky="ew",pady=6)
        ttk.Label(form,text="Provider").grid(row=1,column=0,sticky="w",pady=6)
        ttk.Entry(form,textvariable=self.provider).grid(row=1,column=1,sticky="ew",pady=6)
        ttk.Label(form,text="Model").grid(row=2,column=0,sticky="w",pady=6)
        ttk.Entry(form,textvariable=self.model).grid(row=2,column=1,sticky="ew",pady=6)
        ttk.Checkbutton(form,text="Allow cloud AI for this configuration",variable=self.consent).grid(row=3,column=1,sticky="w",pady=8)
        form.columnconfigure(1,weight=1)
        ttk.Button(frame,text="Save",command=self._save).pack(anchor="e",pady=18)

    def _load(self):
        try:
            data=json.loads(CONFIG.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return
        except (OSError,json.JSONDecodeError):
            messagebox.showwarning("Nexus AI","Existing settings could not be read.")
            return
        self.mode.set(data.get("mode","off"))
        self.provider.set(data.get("provider") or "")
        self.model.set(data.get("model") or "")
        self.consent.set(bool(data.get("cloud_consent",False)))

    def _save(self):
        mode=self.mode.get()
        provider=self.provider.get().strip() or None
        model=self.model.get().strip() or None
        consent=bool(self.consent.get())
        if mode=="off":
            provider=model=None; consent=False
        elif not provider or not model:
            messagebox.showerror("Nexus AI","Provider and model are required.")
            return
        if mode in {"cloud","hybrid"} and not consent:
            messagebox.showerror("Nexus AI","Cloud mode requires explicit consent.")
            return
        if mode=="local" and consent:
            messagebox.showerror("Nexus AI","Local mode cannot enable cloud consent.")
            return
        data={"mode":mode,"provider":provider,"model":model,"cloud_consent":consent}
        CONFIG.parent.mkdir(parents=True,exist_ok=True)
        CONFIG.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8")
        messagebox.showinfo("Nexus AI","Settings saved.")

if __name__=="__main__":
    App().mainloop()
