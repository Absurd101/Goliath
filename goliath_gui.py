# -*- coding: utf-8 -*-
#!/usr/bin/env python3
#
# Goliath - D2R Terror Zone + Diablo Clone Notifier
# Full GUI Dashboard with system tray support
#
# SETUP
# -----
# 1. Install Python from https://python.org/downloads
#    (tick "Add Python to PATH" during install)
#
# 2. Open Command Prompt and run:
#    pip install requests pystray pillow
#
# 3. Run:
#    python goliath_gui.py
#
# AUTO-START ON WINDOWS BOOT
# ---------------------------
# Add goliath_gui.py to your Startup folder shortcut as before,
# or simply run it manually. It will minimize to tray automatically.
#

import threading
import time
import logging
import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime, timezone
from PIL import Image, ImageDraw
import pystray
import winreg
import sys
import os
import json

# -----------------------------------------------
#  CONFIGURATION (editable in the GUI Settings tab)
# -----------------------------------------------

DEFAULT_CONFIG = {
    "webhook": "https://discord.com/api/webhooks/1507676709774954668/naiVpgRanu3tx6EXoFxjEdiJMovahkw2PqHhzYjdqNWdAcKUCs6YxK0xXkSX-A5lUZ4I",
    "poll_interval": 300,
    "dclone_threshold": 5,
    "dclone_server": "nonLadderSoftcoreEurope",
    "watchlist": [
        "Cathedral and Catacombs",
        "The Pit",
        "Moo Moo Farm",
        "Tal Rasha's Tombs and Tal Rasha's Chamber",
        "Ancient Tunnels",
        "Arcane Sanctuary",
        "Travincal",
        "Durance of Hate",
        "River of Flame and City of the Damned",
        "The Chaos Sanctuary",
        "Worldstone Keep, Throne of Destruction, and Worldstone Chamber",
    ],
}

ALL_ZONES = [
    "Blood Moor and Den of Evil",
    "Cold Plains and The Cave",
    "Burial Grounds, Crypt, and Mausoleum",
    "Stony Field",
    "Tristram",
    "Dark Wood and Underground Passage",
    "Black Marsh and The Hole",
    "The Forgotten Tower",
    "The Pit",
    "Jail and Barracks",
    "Cathedral and Catacombs",
    "Moo Moo Farm",
    "Lut Gholein Sewers",
    "Rocky Waste and Stony Tomb",
    "Dry Hills and Halls of the Dead",
    "Far Oasis",
    "Lost City, Valley of Snakes, and Claw Viper Temple",
    "Ancient Tunnels",
    "Arcane Sanctuary",
    "Tal Rasha's Tombs and Tal Rasha's Chamber",
    "Spider Forest and Spider Cavern",
    "Great Marsh",
    "Flayer Jungle and Flayer Dungeon",
    "Kurast Bazaar, Ruined Temple, and Disused Fane",
    "Travincal",
    "Durance of Hate",
    "Outer Steppes and Plains of Despair",
    "River of Flame and City of the Damned",
    "The Chaos Sanctuary",
    "Bloody Foothills, Frigid Highlands, and Abaddon",
    "Glacial Trail and Drifter Cavern",
    "Crystalline Passage and Frozen River",
    "Arreat Plateau and Pit of Acheron",
    "Nihlathak's Temple, Halls of Anguish, and Halls of Pain",
    "Worldstone Keep, Throne of Destruction, and Worldstone Chamber",
]

DCLONE_LEVELS = {
    1: "1/6 - Terror gazes upon Sanctuary",
    2: "2/6 - Terror approaches Sanctuary",
    3: "3/6 - Terror begins to form within Sanctuary",
    4: "4/6 - Terror spreads across Sanctuary",
    5: "5/6 - Terror is about to be unleashed!",
    6: "6/6 - DIABLO WALKS THE EARTH",
}

TZ_API_URL = "https://d2runewizard.com/api/trackers/terror-zone"
DCLONE_API_URL = "https://d2runewizard.com/api/diablo-clone-progress/all"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "D2R-Contact": "goliath-notifier",
    "D2R-Platform": "Discord",
    "D2R-Repo": "Personal private bot, local PC use only",
}

# Diablo theme colors
BG       = "#0a0a0a"
BG2      = "#120808"
BG3      = "#1a0a0a"
GOLD     = "#c8972a"
GOLD2    = "#e8b84b"
RED      = "#8b1a1a"
RED2     = "#c0392b"
RED3     = "#ff4444"
TEXT     = "#d4c5a9"
TEXT2    = "#8a7a6a"
GREEN    = "#4a7c4a"
GREEN2   = "#6abf6a"
BORDER   = "#3a1a0a"


STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Goliath"
def get_app_dir():
    """Return the folder where the exe or script lives."""
    if getattr(sys, "frozen", False):
        # Running as compiled .exe
        return os.path.dirname(sys.executable)
    else:
        # Running as .py script
        return os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(get_app_dir(), "goliath_config.json")


def load_config():
    """Load saved config from disk, falling back to defaults."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Merge with defaults so new keys always exist
            merged = dict(DEFAULT_CONFIG)
            merged["watchlist"] = list(DEFAULT_CONFIG["watchlist"])
            merged.update(saved)
            return merged
        except Exception:
            pass
    cfg = dict(DEFAULT_CONFIG)
    cfg["watchlist"] = list(DEFAULT_CONFIG["watchlist"])
    return cfg


def save_config(cfg):
    """Persist config to disk."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def get_exe_path():
    """Return the path to the running executable or script."""
    if getattr(sys, "frozen", False):
        # Running as compiled .exe
        return sys.executable
    else:
        # Running as .py script
        return sys.executable + ' "' + os.path.abspath(__file__) + '"'


def is_startup_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def enable_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_exe_path())
        winreg.CloseKey(key)
        return True
    except Exception as exc:
        return False


def disable_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


class GoliathApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Goliath - D2R Notifier")
        self.root.geometry("780x620")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # Set window icon
        import os
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "goliath.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self.config = load_config()

        self.running = False
        self.monitor_thread = None
        self.tray_icon = None
        self.last_alerted_tz = None
        self.last_dclone_progress = 0

        self._setup_styles()
        self._build_ui()
        self._build_tray()

        self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=BG3, foreground=GOLD,
                        padding=[16, 6], font=("Georgia", 10, "bold"),
                        borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", RED), ("active", BG3)],
                  foreground=[("selected", GOLD2)])
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=TEXT)
        style.configure("TCheckbutton", background=BG, foreground=TEXT,
                        selectcolor=RED, font=("Georgia", 9))

    def _build_ui(self):
        # Header
        header = tk.Frame(self.root, bg=BG, pady=10)
        header.pack(fill="x", padx=20)

        tk.Label(header, text="GOLIATH",
                 font=("Georgia", 28, "bold"), fg=GOLD2, bg=BG).pack(side="left")
        tk.Label(header, text=" D2R NOTIFIER",
                 font=("Georgia", 14), fg=RED2, bg=BG).pack(side="left", padx=(4,0), pady=8)

        self.status_dot = tk.Label(header, text="  OFFLINE",
                                   font=("Georgia", 10, "bold"), fg=TEXT2, bg=BG)
        self.status_dot.pack(side="right", padx=10)

        # Divider
        tk.Frame(self.root, bg=GOLD, height=1).pack(fill="x", padx=20)
        tk.Frame(self.root, bg=RED, height=1).pack(fill="x", padx=20)

        # Tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)

        self._build_dashboard_tab()
        self._build_watchlist_tab()
        self._build_settings_tab()
        self._build_log_tab()

        # Bottom controls
        ctrl = tk.Frame(self.root, bg=BG, pady=8)
        ctrl.pack(fill="x", padx=20)

        self.start_btn = tk.Button(ctrl, text="START MONITORING",
                                   font=("Georgia", 11, "bold"),
                                   bg=RED, fg=GOLD2, activebackground=RED2,
                                   activeforeground=GOLD2, relief="flat",
                                   padx=20, pady=6, cursor="hand2",
                                   command=self._toggle_monitoring)
        self.start_btn.pack(side="left")

        tk.Button(ctrl, text="HIDE TO TRAY",
                  font=("Georgia", 10), bg=BG3, fg=TEXT,
                  activebackground=BORDER, relief="flat",
                  padx=14, pady=6, cursor="hand2",
                  command=self._hide_to_tray).pack(side="left", padx=10)

        tk.Label(ctrl, text="Source: d2runewizard.com",
                 font=("Georgia", 8), fg=TEXT2, bg=BG).pack(side="right")

    def _build_dashboard_tab(self):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text="  Dashboard  ")

        # Current TZ
        tz_frame = tk.LabelFrame(frame, text=" Terror Zone ",
                                  font=("Georgia", 10, "bold"),
                                  fg=GOLD, bg=BG, bd=1,
                                  highlightbackground=BORDER)
        tz_frame.pack(fill="x", padx=16, pady=(14,6))

        row1 = tk.Frame(tz_frame, bg=BG)
        row1.pack(fill="x", padx=10, pady=6)
        tk.Label(row1, text="CURRENT", font=("Georgia", 8), fg=TEXT2, bg=BG, width=10, anchor="w").pack(side="left")
        self.current_tz_label = tk.Label(row1, text="---", font=("Georgia", 11, "bold"), fg=TEXT, bg=BG, anchor="w")
        self.current_tz_label.pack(side="left", padx=6)

        row2 = tk.Frame(tz_frame, bg=BG)
        row2.pack(fill="x", padx=10, pady=(0,6))
        tk.Label(row2, text="NEXT (~30m)", font=("Georgia", 8), fg=TEXT2, bg=BG, width=10, anchor="w").pack(side="left")
        self.next_tz_label = tk.Label(row2, text="---", font=("Georgia", 11, "bold"), fg=GOLD, bg=BG, anchor="w")
        self.next_tz_label.pack(side="left", padx=6)

        self.tz_watchlist_badge = tk.Label(tz_frame, text="",
                                            font=("Georgia", 9, "bold"),
                                            fg=GREEN2, bg=BG)
        self.tz_watchlist_badge.pack(anchor="w", padx=10, pady=(0,6))

        # Dclone
        dc_frame = tk.LabelFrame(frame, text=" Diablo Clone - Ladder SC Europe ",
                                   font=("Georgia", 10, "bold"),
                                   fg=GOLD, bg=BG, bd=1,
                                   highlightbackground=BORDER)
        dc_frame.pack(fill="x", padx=16, pady=6)

        dc_inner = tk.Frame(dc_frame, bg=BG)
        dc_inner.pack(fill="x", padx=10, pady=8)

        tk.Label(dc_inner, text="PROGRESS", font=("Georgia", 8), fg=TEXT2, bg=BG, width=10, anchor="w").pack(side="left")
        self.dclone_label = tk.Label(dc_inner, text="---", font=("Georgia", 11, "bold"), fg=TEXT, bg=BG, anchor="w")
        self.dclone_label.pack(side="left", padx=6)

        # Progress bar
        pb_frame = tk.Frame(dc_frame, bg=BG)
        pb_frame.pack(fill="x", padx=10, pady=(0,8))
        tk.Label(pb_frame, text="", font=("Georgia", 8), fg=TEXT2, bg=BG, width=10).pack(side="left")
        self.progress_canvas = tk.Canvas(pb_frame, width=300, height=16, bg=BG3,
                                          highlightthickness=1, highlightbackground=BORDER)
        self.progress_canvas.pack(side="left", padx=6)
        self._draw_progress(0)

        # Last alert
        alert_frame = tk.LabelFrame(frame, text=" Last Alert ",
                                     font=("Georgia", 10, "bold"),
                                     fg=GOLD, bg=BG, bd=1)
        alert_frame.pack(fill="x", padx=16, pady=6)
        self.last_alert_label = tk.Label(alert_frame, text="No alerts sent yet.",
                                          font=("Georgia", 9, "italic"),
                                          fg=TEXT2, bg=BG, anchor="w")
        self.last_alert_label.pack(fill="x", padx=10, pady=8)

        # Last checked
        self.last_checked_label = tk.Label(frame, text="Last checked: never",
                                            font=("Georgia", 8), fg=TEXT2, bg=BG)
        self.last_checked_label.pack(anchor="e", padx=16, pady=4)

    def _draw_progress(self, level):
        self.progress_canvas.delete("all")
        total = 6
        w, h = 300, 16
        seg_w = w // total
        for i in range(total):
            filled = i < level
            color = RED2 if filled else BG3
            if level == 6 and filled:
                color = RED3
            self.progress_canvas.create_rectangle(
                i * seg_w + 1, 1,
                (i + 1) * seg_w - 1, h - 1,
                fill=color, outline=""
            )
        self.progress_canvas.create_text(
            w // 2, h // 2,
            text=str(level) + "/6",
            fill=GOLD if level > 0 else TEXT2,
            font=("Georgia", 8, "bold")
        )

    def _build_watchlist_tab(self):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text="  Watchlist  ")

        tk.Label(frame, text="Select zones to receive alerts for:",
                 font=("Georgia", 10), fg=TEXT2, bg=BG).pack(anchor="w", padx=16, pady=(12,4))

        scroll_frame = tk.Frame(frame, bg=BG)
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=4)

        canvas = tk.Canvas(scroll_frame, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        self.zones_frame = tk.Frame(canvas, bg=BG)

        self.zones_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.zones_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mousewheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        self.zones_frame.bind("<MouseWheel>", _on_mousewheel)

        self.zone_vars = {}
        for zone in ALL_ZONES:
            var = tk.BooleanVar(value=zone in self.config["watchlist"])
            self.zone_vars[zone] = var
            cb = tk.Checkbutton(self.zones_frame, text=zone, variable=var,
                                 bg=BG, fg=TEXT, selectcolor=RED,
                                 activebackground=BG, activeforeground=GOLD,
                                 font=("Georgia", 9),
                                 command=self._update_watchlist)
            cb.pack(anchor="w", padx=8, pady=1)
            cb.bind("<MouseWheel>", lambda e, c=canvas: c.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        btn_row = tk.Frame(frame, bg=BG)
        btn_row.pack(fill="x", padx=16, pady=6)
        tk.Button(btn_row, text="Select All", font=("Georgia", 9),
                  bg=BG3, fg=TEXT, relief="flat", padx=10, pady=4,
                  command=self._select_all_zones).pack(side="left", padx=(0,6))
        tk.Button(btn_row, text="Clear All", font=("Georgia", 9),
                  bg=BG3, fg=TEXT, relief="flat", padx=10, pady=4,
                  command=self._clear_all_zones).pack(side="left")
        self.wl_count = tk.Label(btn_row, text=str(len(self.config["watchlist"])) + " zones selected",
                                  font=("Georgia", 9), fg=TEXT2, bg=BG)
        self.wl_count.pack(side="right")

    def _update_watchlist(self):
        self.config["watchlist"] = [z for z, v in self.zone_vars.items() if v.get()]
        self.wl_count.config(text=str(len(self.config["watchlist"])) + " zones selected")
        save_config(self.config)

    def _select_all_zones(self):
        for var in self.zone_vars.values():
            var.set(True)
        self._update_watchlist()

    def _clear_all_zones(self):
        for var in self.zone_vars.values():
            var.set(False)
        self._update_watchlist()

    def _build_settings_tab(self):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text="  Settings  ")

        def labeled_entry(parent, label, default, row):
            tk.Label(parent, text=label, font=("Georgia", 9), fg=TEXT2, bg=BG,
                     anchor="w", width=22).grid(row=row, column=0, sticky="w", padx=10, pady=6)
            var = tk.StringVar(value=str(default))
            entry = tk.Entry(parent, textvariable=var, font=("Georgia", 9),
                             bg=BG3, fg=TEXT, insertbackground=GOLD,
                             relief="flat", bd=4, width=50)
            entry.grid(row=row, column=1, sticky="ew", padx=10, pady=6)
            return var

        grid = tk.Frame(frame, bg=BG)
        grid.pack(fill="x", padx=10, pady=14)
        grid.columnconfigure(1, weight=1)

        self.webhook_var = labeled_entry(grid, "Discord Webhook URL", self.config["webhook"], 0)
        self.interval_var = labeled_entry(grid, "Poll Interval (seconds)", self.config["poll_interval"], 1)
        self.threshold_var = labeled_entry(grid, "Dclone Alert Threshold", self.config["dclone_threshold"], 2)
        self.server_var = labeled_entry(grid, "Dclone Server", self.config["dclone_server"], 3)

        tk.Button(frame, text="SAVE SETTINGS",
                  font=("Georgia", 10, "bold"),
                  bg=RED, fg=GOLD2, activebackground=RED2,
                  relief="flat", padx=16, pady=6, cursor="hand2",
                  command=self._save_settings).pack(anchor="w", padx=20, pady=8)

        self.settings_status = tk.Label(frame, text="", font=("Georgia", 9), fg=GREEN2, bg=BG)
        self.settings_status.pack(anchor="w", padx=20)

        # Startup on boot option
        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", padx=20, pady=16)

        self.startup_var = tk.BooleanVar(value=is_startup_enabled())
        startup_cb = tk.Checkbutton(
            frame,
            text="  Run Goliath automatically when Windows starts",
            variable=self.startup_var,
            font=("Georgia", 10),
            bg=BG, fg=TEXT,
            selectcolor=RED,
            activebackground=BG,
            activeforeground=GOLD,
            cursor="hand2",
            command=self._toggle_startup,
        )
        startup_cb.pack(anchor="w", padx=20)

        self.startup_status = tk.Label(frame, text="", font=("Georgia", 9), fg=GREEN2, bg=BG)
        self.startup_status.pack(anchor="w", padx=20, pady=4)

    def _save_settings(self):
        try:
            self.config["webhook"] = self.webhook_var.get().strip()
            self.config["poll_interval"] = int(self.interval_var.get().strip())
            self.config["dclone_threshold"] = int(self.threshold_var.get().strip())
            self.config["dclone_server"] = self.server_var.get().strip()
            save_config(self.config)
            self.settings_status.config(text="Settings saved.", fg=GREEN2)
        except ValueError:
            self.settings_status.config(text="Invalid value - check interval and threshold.", fg=RED3)

    def _toggle_startup(self):
        if self.startup_var.get():
            if enable_startup():
                self.startup_status.config(
                    text="Goliath will now start automatically with Windows.", fg=GREEN2)
            else:
                self.startup_var.set(False)
                self.startup_status.config(
                    text="Failed to enable startup. Try running as administrator.", fg=RED3)
        else:
            if disable_startup():
                self.startup_status.config(
                    text="Startup on boot disabled.", fg=TEXT2)
            else:
                self.startup_var.set(True)
                self.startup_status.config(
                    text="Failed to disable startup.", fg=RED3)

    def _build_log_tab(self):
        frame = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(frame, text="  Log  ")

        self.log_box = scrolledtext.ScrolledText(
            frame, font=("Courier New", 8),
            bg=BG2, fg=TEXT, insertbackground=GOLD,
            relief="flat", bd=0, state="disabled"
        )
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(frame, text="Clear Log", font=("Georgia", 9),
                  bg=BG3, fg=TEXT, relief="flat", padx=10, pady=4,
                  command=self._clear_log).pack(anchor="e", padx=10, pady=(0,8))

    def _log(self, message):
        now = datetime.now().strftime("%H:%M:%S")
        line = "[" + now + "] " + message + "\n"
        self.log_box.config(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.config(state="disabled")

    def _clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.config(state="disabled")

    def _build_tray(self):
        import os
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "goliath.ico")
        if os.path.exists(icon_path):
            img = Image.open(icon_path).resize((64, 64), Image.NEAREST).convert("RGB")
        else:
            img = Image.new("RGB", (64, 64), color=BG)
            draw = ImageDraw.Draw(img)
            draw.ellipse([8, 8, 56, 56], fill=RED)
            draw.ellipse([20, 20, 44, 44], fill=GOLD)

        menu = pystray.Menu(
            pystray.MenuItem("Show Goliath", self._show_window, default=True),
            pystray.MenuItem("Start Monitoring", self._tray_start),
            pystray.MenuItem("Stop Monitoring", self._tray_stop),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", self._quit_app),
        )
        self.tray_icon = pystray.Icon("Goliath", img, "Goliath - D2R Notifier", menu)

    def _show_window(self, icon=None, item=None):
        self.root.after(0, self.root.deiconify)
        self.root.after(0, self.root.lift)

    def _hide_to_tray(self):
        self.root.withdraw()
        if not self.tray_icon._running:
            threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _tray_start(self, icon=None, item=None):
        self.root.after(0, self._start_monitoring)

    def _tray_stop(self, icon=None, item=None):
        self.root.after(0, self._stop_monitoring)

    def _quit_app(self, icon=None, item=None):
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def _toggle_monitoring(self):
        if self.running:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(text="STOP MONITORING", bg=BG3, fg=RED3)
        self.status_dot.config(text="  ONLINE", fg=GREEN2)
        self._log("Goliath started.")
        self._send_startup_message()
        self.last_alerted_tz = None
        self.last_dclone_progress = 0
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _stop_monitoring(self):
        self.running = False
        self.start_btn.config(text="START MONITORING", bg=RED, fg=GOLD2)
        self.status_dot.config(text="  OFFLINE", fg=TEXT2)
        self._log("Goliath stopped.")

    def _send_startup_message(self):
        msg = (
            "==============================\n"
            "**GOLIATH ONLINE**\n"
            "==============================\n"
            "```\n"
            "TZ Watchlist : " + str(len(self.config["watchlist"])) + " zones active\n"
            "Dclone Watch : Ladder SC Europe - alerting at " + str(self.config["dclone_threshold"]) + "/6+\n"
            "Status       : Monitoring...\n"
            "```"
        )
        try:
            requests.post(self.config["webhook"], json={"content": msg}, timeout=10)
            self._log("Startup message sent to Discord.")
        except Exception as exc:
            self._log("Failed to send startup message: " + str(exc))

    def _monitor_loop(self):
        while self.running:
            self._check_tz()
            self._check_dclone()
            now = datetime.now().strftime("%H:%M:%S")
            self.root.after(0, self.last_checked_label.config,
                            {"text": "Last checked: " + now})
            interval = self.config["poll_interval"]
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_tz(self):
        try:
            resp = requests.get(TZ_API_URL, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", "unknown")
            next_zone = data.get("next", "unknown")

            self.root.after(0, self.current_tz_label.config, {"text": current})
            self.root.after(0, self.next_tz_label.config, {"text": next_zone})

            watchlist_lower = {z.lower() for z in self.config["watchlist"]}
            if next_zone and next_zone.lower() in watchlist_lower:
                self.root.after(0, self.tz_watchlist_badge.config,
                                {"text": "  [!] Next zone is on your watchlist!"})
            else:
                self.root.after(0, self.tz_watchlist_badge.config, {"text": ""})

            self._log("TZ Current: " + current + " | Next: " + next_zone)

            if next_zone and next_zone.lower() in watchlist_lower:
                if next_zone != self.last_alerted_tz:
                    self._send_tz_alert(current, next_zone)
                    self.last_alerted_tz = next_zone
                    self.root.after(0, self.last_alert_label.config,
                                    {"text": "[TZ] " + next_zone + " - " + datetime.now().strftime("%H:%M")})
            else:
                if next_zone and next_zone != self.last_alerted_tz:
                    self.last_alerted_tz = None

        except Exception as exc:
            self._log("TZ error: " + str(exc))

    def _check_dclone(self):
        try:
            resp = requests.get(DCLONE_API_URL, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            progress = None
            message = ""
            for server in data.get("servers", []):
                if server.get("server") == self.config["dclone_server"]:
                    progress = server.get("progress")
                    message = server.get("message", "")
                    break



            if progress is not None:
                # Always update display regardless of threshold
                self.root.after(0, self.dclone_label.config,
                                {"text": DCLONE_LEVELS.get(progress, str(progress) + "/6")})
                self.root.after(0, self._draw_progress, progress)
                self._log("Dclone: " + str(progress) + "/6 - " + message)

                threshold = self.config["dclone_threshold"]

                # Reset dedup if progress dropped (new spawn cycle started)
                if progress < self.last_dclone_progress:
                    self._log("Dclone reset detected - new cycle started.")
                    self.last_dclone_progress = 0

                # Alert if threshold reached and not already alerted this level
                if progress >= threshold and progress != self.last_dclone_progress:
                    self._send_dclone_alert(progress)
                    self.last_dclone_progress = progress
                    self.root.after(0, self.last_alert_label.config,
                                    {"text": "[DCLONE] " + str(progress) + "/6 - " + datetime.now().strftime("%H:%M")})

        except Exception as exc:
            self._log("Dclone error: " + str(exc))

    def _send_tz_alert(self, current, next_zone):
        now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")
        lines = [
            "** D2R Terror Zone Alert **",
            "==============================",
            "[NEXT in ~30 min]  " + next_zone,
            "[CURRENT]          " + current,
            "[DETECTED]         " + now_utc,
            "==============================",
            "Get to your PC - time to farm!",
            "Source: d2runewizard.com",
        ]
        try:
            requests.post(self.config["webhook"],
                          json={"content": "\n".join(lines)}, timeout=10)
            self._log("[OK] TZ alert sent: " + next_zone)
        except Exception as exc:
            self._log("Failed to send TZ alert: " + str(exc))

    def _send_dclone_alert(self, progress):
        now_utc = datetime.now(timezone.utc).strftime("%H:%M UTC")
        action = "DIABLO IS WALKING - get in game RIGHT NOW!" if progress == 6 else "Get ready - Diablo Clone is close!"
        lines = [
            "** DIABLO CLONE ALERT **",
            "==============================",
            "[PROGRESS]  " + DCLONE_LEVELS.get(progress, str(progress) + "/6"),
            "[SERVER]    Ladder Softcore Europe",
            "[DETECTED]  " + now_utc,
            "==============================",
            action,
            "Source: d2runewizard.com",
        ]
        try:
            requests.post(self.config["webhook"],
                          json={"content": "\n".join(lines)}, timeout=10)
            self._log("[OK] Dclone alert sent: " + str(progress) + "/6")
        except Exception as exc:
            self._log("Failed to send dclone alert: " + str(exc))


def main():
    root = tk.Tk()
    app = GoliathApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
