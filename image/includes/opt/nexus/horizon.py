#!/usr/bin/env python3
"""Native Horizon launcher with responsive cards and original vector icons."""
import subprocess
import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

BG, SURFACE, RAISED, EDGE = '#0b1220', '#151f31', '#202f46', '#2b3c55'
TEXT, MUTED, ACCENT = '#f4f7fc', '#b9c5d8', '#70dcf5'
APPLICATIONS = (
    ('Files', 'Browse your documents', ('thunar',)),
    ('Web', 'Open your browser', ('xdg-open', 'https://www.debian.org/')),
    ('Terminal', 'Work with commands', ('xfce4-terminal',)),
    ('Settings', 'Personalize your desktop', ('xfce4-settings-manager',)),
    ('Nexus Control Center', 'AI preferences and system tools', ('/usr/bin/python3', '/opt/nexus/control-center.py')),
    ('Installation Preview', 'Inspect an installation plan without writing disks', ('/usr/bin/python3', '/opt/nexus/installer-preview.py')),
    ('Nexus Agent', 'Open your AI assistant', ('x-terminal-emulator', '-e', '/usr/local/bin/nexus-agent')),
)
ICON_COLORS = ('#8abcfb', '#70dcf5', '#b9c5d8', '#b9adff', '#8fddc6', '#f3cb91', '#c2a5ff')

def matching_apps(query):
    words = query.casefold().split()
    return [app for app in APPLICATIONS if all(word in (app[0] + ' ' + app[1]).casefold() for word in words)]

def launch(command):
    return subprocess.Popen(command, stdin=subprocess.DEVNULL, close_fds=True)

def draw_icon(canvas, index):
    color = ICON_COLORS[index]
    canvas.create_oval(2, 2, 46, 46, fill=RAISED, outline=EDGE)
    def line(*points):
        canvas.create_line(*points, fill=color, width=2, capstyle='round', joinstyle='round')
    if index == 0:
        canvas.create_polygon(12, 17, 21, 17, 24, 21, 37, 21, 34, 33, 12, 33, fill='', outline=color, width=2)
    elif index == 1:
        canvas.create_oval(13, 13, 35, 35, outline=color, width=2)
        canvas.create_oval(20, 13, 28, 35, outline=color)
        line(13, 24, 35, 24)
    elif index == 2:
        line(14, 17, 21, 24, 14, 31)
        line(24, 31, 34, 31)
    elif index == 3:
        canvas.create_oval(14, 14, 34, 34, outline=color, width=2)
        canvas.create_oval(21, 21, 27, 27, outline=color, width=2)
        for segment in ((24, 10, 24, 14), (24, 34, 24, 38), (10, 24, 14, 24), (34, 24, 38, 24)):
            line(*segment)
    elif index == 4:
        for x, y in ((16, 19), (24, 28), (32, 21)):
            line(x, 13, x, 35)
            canvas.create_oval(x-3, y-3, x+3, y+3, fill=SURFACE, outline=color, width=2)
    elif index == 5:
        line(24, 12, 24, 28)
        line(18, 22, 24, 28, 30, 22)
        line(13, 29, 13, 35, 35, 35, 35, 29)
    else:
        canvas.create_polygon(24, 11, 28, 21, 38, 24, 28, 28, 24, 38, 20, 28, 10, 24, 20, 21,
                              fill='', outline=color, width=2, joinstyle='round')

class Horizon(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Nexus Horizon')
        self.geometry(f'{min(880, self.winfo_screenwidth()-48)}x{min(720, self.winfo_screenheight()-80)}')
        self.minsize(540, 440)
        self.configure(bg=BG)
        self.family = 'Inter' if 'Inter' in tkfont.families(self) else tkfont.nametofont('TkDefaultFont').actual('family')
        self.search = tk.StringVar()
        self.feedback = tk.StringVar(value='Choose an application to get started.')
        self._app_buttons, self._columns = [], 2
        self._build()
        self.search.trace_add('write', lambda *_: self.render_apps())
        self.bind('<Escape>', lambda _: self.destroy())
        self.bind('<Control-f>', lambda _: self.search_entry.focus_set())
        self.bind('<Return>', self.launch_first)
        self.search_entry.bind('<Down>', self.focus_first)
        self.bind('<MouseWheel>', lambda e: self.scroll.yview_scroll(-1 if e.delta > 0 else 1, 'units'))
        self.bind('<Button-4>', lambda _: self.scroll.yview_scroll(-1, 'units'))
        self.bind('<Button-5>', lambda _: self.scroll.yview_scroll(1, 'units'))
        self.render_apps()
        self.search_entry.focus_set()

    def _label(self, parent, text, size=11, color=MUTED, bold=False):
        return tk.Label(parent, text=text, font=(self.family, size, 'bold' if bold else 'normal'),
                        fg=color, bg=parent.cget('bg'), anchor='w')

    def _build(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill='x', padx=30, pady=(24, 16))
        self._label(header, '◈  Nexus', 13, ACCENT, True).pack(side='left')
        self._label(header, 'Horizon', 11).pack(side='left', padx=12)
        tk.Button(header, text='Esc  ×', command=self.destroy, font=(self.family, 10), fg=MUTED, bg=SURFACE,
                  activebackground=RAISED, activeforeground=TEXT, relief='flat', bd=0, padx=12, pady=6,
                  highlightthickness=1, highlightbackground=EDGE, highlightcolor=ACCENT).pack(side='right')
        self._label(self, 'A little more space to think.', 25, TEXT, True).pack(fill='x', padx=30)
        self._label(self, 'Your apps and tools, thoughtfully within reach.').pack(fill='x', padx=30, pady=(6, 20))
        search_box = tk.Frame(self, bg=SURFACE, highlightthickness=1, highlightbackground=EDGE)
        search_box.pack(fill='x', padx=30)
        self._label(search_box, '⌕', 22, ACCENT).pack(side='left', padx=(14, 8))
        self.search_entry = tk.Entry(search_box, textvariable=self.search, font=(self.family, 14), bg=SURFACE,
                                     fg=TEXT, insertbackground=ACCENT, relief='flat', bd=0, highlightthickness=0)
        self.search_entry.pack(side='left', fill='x', expand=True, ipady=14)
        self._label(search_box, 'Ctrl F', 9).pack(side='right', padx=16)
        self.search_entry.bind('<FocusIn>', lambda _: search_box.configure(highlightbackground=ACCENT))
        self.search_entry.bind('<FocusOut>', lambda _: search_box.configure(highlightbackground=EDGE))
        section = tk.Frame(self, bg=BG)
        section.pack(fill='x', padx=30, pady=(20, 10))
        self._label(section, 'Applications', 12, TEXT, True).pack(side='left')
        self.count = self._label(section, '', 10)
        self.count.pack(side='right')
        area = tk.Frame(self, bg=BG)
        area.pack(fill='both', expand=True, padx=24)
        self.scroll = tk.Canvas(area, bg=BG, bd=0, highlightthickness=0, yscrollincrement=28)
        self.scroll.pack(side='left', fill='both', expand=True)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Horizon.Vertical.TScrollbar', background=EDGE, troughcolor=BG,
                        bordercolor=BG, arrowcolor=MUTED, lightcolor=EDGE, darkcolor=EDGE, arrowsize=10)
        style.map('Horizon.Vertical.TScrollbar', background=[('active', RAISED)])
        scrollbar = ttk.Scrollbar(area, orient='vertical', command=self.scroll.yview,
                                  style='Horizon.Vertical.TScrollbar')
        scrollbar.pack(side='right', fill='y')
        self.scroll.configure(yscrollcommand=scrollbar.set)
        self.list_frame = tk.Frame(self.scroll, bg=BG)
        self._list_window = self.scroll.create_window((0, 0), window=self.list_frame, anchor='nw')
        self.list_frame.bind('<Configure>', lambda _: self.scroll.configure(scrollregion=self.scroll.bbox('all')))
        self.scroll.bind('<Configure>', self._resize)
        footer = tk.Frame(self, bg=BG)
        footer.pack(fill='x', padx=30, pady=(14, 18))
        tk.Label(footer, textvariable=self.feedback, font=(self.family, 10), fg=MUTED, bg=BG,
                 wraplength=450, anchor='w', justify='left').pack(side='left', fill='x', expand=True)
        self._label(footer, '↵  Open', 10, ACCENT).pack(side='right', padx=(12, 0))

    def _resize(self, event):
        self.scroll.itemconfigure(self._list_window, width=event.width)
        columns = 2 if event.width >= 640 else 1
        if columns != self._columns:
            self._columns = columns
            self.render_apps()

    def render_apps(self):
        for child in self.list_frame.winfo_children():
            child.destroy()
        results = matching_apps(self.search.get())
        self.count.configure(text=f'{len(results)} available' if not self.search.get() else f'{len(results)} found')
        self._app_buttons = []
        for column in range(2):
            self.list_frame.columnconfigure(column, weight=1 if column < self._columns else 0, uniform='cards')
        if not results:
            self._label(self.list_frame, 'No matching applications. Try another name.').grid(padx=6, pady=24, sticky='w')
        for index, (name, description, command) in enumerate(results):
            card = tk.Frame(self.list_frame, bg=SURFACE, highlightthickness=1, highlightbackground=EDGE)
            card.grid(row=index // self._columns, column=index % self._columns, sticky='nsew', padx=6, pady=6)
            icon = tk.Canvas(card, width=48, height=48, bg=SURFACE, highlightthickness=0)
            icon.pack(side='left', padx=(12, 8), pady=12)
            draw_icon(icon, next(i for i, app in enumerate(APPLICATIONS) if app[0] == name))
            icon.bind('<Button-1>', lambda _, cmd=command: self.open_app(cmd))
            button = tk.Button(card, text=name + '\n' + description, command=lambda cmd=command: self.open_app(cmd),
                               bg=SURFACE, fg=TEXT, activebackground=RAISED, activeforeground=TEXT,
                               relief='flat', bd=0, anchor='w', justify='left', wraplength=235,
                               font=(self.family, 10), padx=8, pady=12, highlightthickness=2,
                               highlightbackground=SURFACE, highlightcolor=ACCENT)
            button.pack(side='left', fill='both', expand=True, padx=(0, 6), pady=4)
            button.bind('<Enter>', lambda _, b=button: b.configure(bg=RAISED))
            button.bind('<Leave>', lambda _, b=button: b.configure(bg=SURFACE))
            self._app_buttons.append(button)
        self.scroll.yview_moveto(0)

    def focus_first(self, _event=None):
        if self._app_buttons:
            self._app_buttons[0].focus_set()
        return 'break'

    def open_app(self, command):
        try:
            launch(command)
            self.feedback.set('Application launch requested.')
        except OSError:
            self.feedback.set('This application is unavailable in the current environment.')

    def launch_first(self, _event=None):
        focused = self.focus_get()
        if focused in self._app_buttons:
            focused.invoke()
        else:
            results = matching_apps(self.search.get())
            if results:
                self.open_app(results[0][2])
        return 'break'

if __name__ == '__main__':
    Horizon().mainloop()
