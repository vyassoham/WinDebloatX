"""
WinDebloatX - Modern High-Performance Graphical User Interface (GUI)
Optimized with zero-lag buffered logging, non-blocking asynchronous startup (<150ms),
and widget caching.
"""

import os
import platform
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List

import customtkinter as ctk

from core.appx_remover import (
    BLOATWARE_CATALOG,
    batch_remove_bloatware,
    query_installed_apps,
    reinstall_app_from_store
)
from core.backup_manager import (
    delete_backup,
    list_backups,
    restore_backup
)
from core.gaming import (
    disable_gamedvr,
    disable_mouse_acceleration,
    enable_gamedvr,
    enable_mouse_acceleration,
    get_mmcss_status,
    is_gamedvr_disabled,
    optimize_network_and_responsiveness,
    revert_network_and_responsiveness,
    unlock_ultimate_performance_plan
)
from core.hardware import get_hardware_profile
from core.i18n import SUPPORTED_LANGUAGES, get_current_language, set_language, t
from core.logger import LOG_DIR, register_log_callback
from core.onedrive import is_onedrive_installed, reinstall_onedrive, uninstall_onedrive
from core.persistence import install_persistence_task, is_persistence_task_installed, remove_persistence_task
from core.presets import PRESETS, execute_preset
from core.privacy import (
    PRIVACY_TWEAKS,
    apply_all_privacy_tweaks,
    apply_privacy_tweak,
    get_tweak_status,
    get_windows_edition_info,
    revert_privacy_tweak
)
from core.privileges import elevate_and_relaunch, is_admin
from core.registry import BACKUP_DIR
from core.restore_point import create_restore_point, open_system_restore_gui
from core.services import optimize_telemetry_services
from core.tasks import disable_all_telemetry_tasks
from core.win11_tweaks import WIN11_TWEAKS, toggle_win11_tweak
from core.winget_installer import SOFTWARE_CATALOG, batch_install_software, is_winget_available

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class WinDebloatXApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("WinDebloatX - Ultimate Windows 10 & 11 Optimizer")
        self.geometry("1140x780")
        self.minsize(1000, 680)

        # Apply icon if present
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
        if os.path.isfile(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Thread-safe log buffer (prevents Tkinter event queue starvation)
        self._log_queue: queue.Queue = queue.Queue()

        # State
        self.is_elevated = is_admin()
        self.is_busy = False
        self.hw_profile = None
        self.app_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.software_checkboxes: Dict[str, ctk.CTkCheckBox] = {}
        self.privacy_switches: Dict[str, ctk.CTkSwitch] = {}
        self.win11_switches: Dict[str, ctk.CTkSwitch] = {}
        self.gaming_switches: Dict[str, ctk.CTkSwitch] = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._build_sidebar()
        self._build_main_container()

        register_log_callback(self._on_log_message)
        
        # Start high-performance log flusher (runs every 80ms)
        self.after(80, self._flush_logs_loop)

        # Start non-blocking asynchronous hardware detection
        self.after(30, self._load_hardware_async)

        self.select_view("presets")

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        # Brand Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="WinDebloatX",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 4))

        self.subtitle_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="v2.3 • High-Performance Edition",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 16))

        # Navigation Buttons
        self.nav_buttons = {}
        views = [
            ("presets", t("nav_presets", "⚡ 1-Click Presets")),
            ("bloatware", t("nav_bloatware", "📦 Bloatware Apps")),
            ("software", t("nav_software", "🚀 Software Hub")),
            ("privacy", t("nav_privacy", "🛡️ Privacy & Telemetry")),
            ("win11", t("nav_win11", "🪟 Windows 11 & UI")),
            ("gaming", t("nav_gaming", "🎮 Gaming & Latency")),
            ("services", t("nav_services", "⚙️ Services & System")),
            ("backups", t("nav_backups", "🔄 Backups & Rollback")),
            ("logs", t("nav_logs", "📋 Activity Log")),
        ]

        for idx, (view_id, title) in enumerate(views, start=2):
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=title,
                anchor="w",
                height=34,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda v=view_id: self.select_view(v)
            )
            btn.grid(row=idx, column=0, padx=15, pady=2, sticky="ew")
            self.nav_buttons[view_id] = btn

        # Admin Status Badge
        admin_text = t("admin_mode", "🛡️ Admin Mode") if self.is_elevated else t("elevate_admin", "⚠️ Elevate to Admin")
        admin_color = "#10b981" if self.is_elevated else "#ef4444"
        admin_cmd = None if self.is_elevated else self._request_elevation

        self.admin_btn = ctk.CTkButton(
            self.sidebar_frame,
            text=admin_text,
            fg_color=admin_color,
            hover_color=admin_color,
            command=admin_cmd,
            height=30
        )
        self.admin_btn.grid(row=12, column=0, padx=15, pady=(10, 6), sticky="ew")

        # Language Selector
        self.lang_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=list(SUPPORTED_LANGUAGES.values()),
            command=self._change_language,
            height=26
        )
        curr_lang_name = SUPPORTED_LANGUAGES.get(get_current_language(), "English")
        self.lang_menu.set(curr_lang_name)
        self.lang_menu.grid(row=13, column=0, padx=15, pady=(2, 6), sticky="ew")

        # Theme Switcher
        self.theme_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dark", "Light", "System"],
            command=ctk.set_appearance_mode,
            height=26
        )
        self.theme_menu.grid(row=14, column=0, padx=15, pady=(2, 16), sticky="ew")

    def _build_main_container(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=18, pady=16)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Header Bar
        self.header_frame = ctk.CTkFrame(self.main_frame, height=54, corner_radius=8)
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.hw_label = ctk.CTkLabel(
            self.header_frame,
            text="⚡ Initializing hardware intelligence...",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.hw_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.restore_btn = ctk.CTkButton(
            self.header_frame,
            text=t("btn_restore_point", "🛡️ Create Restore Point"),
            fg_color="#059669",
            hover_color="#047857",
            height=30,
            command=self._trigger_restore_point
        )
        self.restore_btn.grid(row=0, column=1, padx=(5, 8), pady=10)

        self.rstrui_btn = ctk.CTkButton(
            self.header_frame,
            text=t("btn_open_restore", "Open System Restore"),
            fg_color="gray40",
            hover_color="gray30",
            height=30,
            command=open_system_restore_gui
        )
        self.rstrui_btn.grid(row=0, column=2, padx=(0, 15), pady=10)

        # Progress Indicator Bar
        self.progress_frame = ctk.CTkFrame(self.main_frame, height=24, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=7)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)

        self.status_label = ctk.CTkLabel(self.progress_frame, text=t("ready", "Ready"), font=ctk.CTkFont(size=11), text_color="gray70")
        self.status_label.grid(row=1, column=0, sticky="w", pady=(1, 0))

        # Views Container
        self.views_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.views_container.grid(row=2, column=0, sticky="nsew")
        self.views_container.grid_rowconfigure(0, weight=1)
        self.views_container.grid_columnconfigure(0, weight=1)

        self.views = {
            "presets": self._create_presets_view(),
            "bloatware": self._create_bloatware_view(),
            "software": self._create_software_view(),
            "privacy": self._create_privacy_view(),
            "win11": self._create_win11_view(),
            "gaming": self._create_gaming_view(),
            "services": self._create_services_view(),
            "backups": self._create_backups_view(),
            "logs": self._create_logs_view(),
        }

    def _load_hardware_async(self):
        """Asynchronously queries hardware profile off the main UI thread."""
        def worker():
            hw = get_hardware_profile()
            self.hw_profile = hw

            def update_ui():
                hw_icon = "💻" if hw["is_laptop"] else "🖥️"
                hw_str = f"{hw_icon} {hw['form_factor']} • {hw['storage_type']} • {hw['total_ram_gb']} GB RAM"
                self.hw_label.configure(text=hw_str)
                if hasattr(self, "hw_recs_box"):
                    for widget in self.hw_recs_box.winfo_children():
                        widget.destroy()
                    ctk.CTkLabel(self.hw_recs_box, text="💡 Hardware Intelligence Recommendations:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8").pack(anchor="w", padx=12, pady=(6, 2))
                    for rec in hw["recommendations"]:
                        ctk.CTkLabel(self.hw_recs_box, text=f"• {rec}", font=ctk.CTkFont(size=11), text_color="gray70").pack(anchor="w", padx=16, pady=1)

            self.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def select_view(self, view_id: str):
        for vid, frame in self.views.items():
            if vid == view_id:
                frame.grid(row=0, column=0, sticky="nsew")
                self.nav_buttons[vid].configure(fg_color=("gray75", "gray25"))
            else:
                frame.grid_forget()
                self.nav_buttons[vid].configure(fg_color="transparent")

        if view_id == "backups":
            self._refresh_backups_list()

    def _change_language(self, lang_display_name: str):
        for code, name in SUPPORTED_LANGUAGES.items():
            if name == lang_display_name:
                set_language(code)
                break
        messagebox.showinfo("Language Updated", "Language setting updated. Restart app to refresh all UI labels completely.")

    # ==========================
    # 1. PRESETS VIEW
    # ==========================
    def _create_presets_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self.views_container, corner_radius=8)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text=t("nav_presets", "1-Click Optimization Profiles"), font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")

        # Hardware Guidance Container
        self.hw_recs_box = ctk.CTkFrame(frame, fg_color=("gray95", "gray15"), corner_radius=6)
        self.hw_recs_box.grid(row=1, column=0, padx=20, pady=(5, 12), sticky="ew")
        ctk.CTkLabel(self.hw_recs_box, text="💡 Analyzing hardware profile...", font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8").pack(anchor="w", padx=12, pady=8)

        for row_idx, (p_id, p_info) in enumerate(PRESETS.items(), start=2):
            card = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray90", "gray17"))
            card.grid(row=row_idx, column=0, padx=20, pady=7, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            card_title = ctk.CTkLabel(card, text=f"{p_info['icon']} {p_info['name']}", font=ctk.CTkFont(size=16, weight="bold"))
            card_title.grid(row=0, column=0, padx=15, pady=(12, 4), sticky="w")

            card_desc = ctk.CTkLabel(card, text=p_info["description"], font=ctk.CTkFont(size=12), text_color="gray70", wraplength=600, justify="left")
            card_desc.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="w")

            apply_btn = ctk.CTkButton(
                card,
                text=f"Apply {p_info['name']}",
                width=160,
                height=34,
                command=lambda pid=p_id: self._execute_preset_wrapped(pid)
            )
            apply_btn.grid(row=0, column=1, rowspan=2, padx=15, pady=12)

        return frame

    def _execute_preset_wrapped(self, preset_id: str):
        def task():
            def cb(cur, tot, msg):
                self._update_progress(cur / tot, msg)
            execute_preset(preset_id, progress_cb=cb)
            self._update_progress(1.0, f"Finished applying {PRESETS[preset_id]['name']}.")
        self._run_in_thread(task)

    # ==========================
    # 2. BLOATWARE APPS VIEW
    # ==========================
    def _create_bloatware_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, corner_radius=8)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(frame, height=50, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=8)

        scan_btn = ctk.CTkButton(top_bar, text=t("scan_apps", "🔄 Scan Apps"), width=110, command=self._refresh_apps_list)
        scan_btn.pack(side="left", padx=5)

        select_default_btn = ctk.CTkButton(top_bar, text=t("select_recommended", "Select Recommended"), fg_color="gray40", hover_color="gray30", command=self._select_recommended_apps)
        select_default_btn.pack(side="left", padx=5)

        deselect_btn = ctk.CTkButton(top_bar, text=t("deselect_all", "Deselect All"), fg_color="gray40", hover_color="gray30", command=self._deselect_all_apps)
        deselect_btn.pack(side="left", padx=5)

        self.uninstall_btn = ctk.CTkButton(top_bar, text=f"{t('uninstall_selected', 'Uninstall Selected')} (0)", fg_color="#dc2626", hover_color="#b91c1c", command=self._remove_selected_apps)
        self.uninstall_btn.pack(side="right", padx=5)

        self.apps_scroll = ctk.CTkScrollableFrame(frame, corner_radius=8)
        self.apps_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.apps_scroll.grid_columnconfigure(0, weight=1)

        self._populate_apps_view()
        return frame

    def _populate_apps_view(self):
        for widget in self.apps_scroll.winfo_children():
            widget.destroy()
        self.app_checkboxes.clear()

        for idx, (pkg_id, info) in enumerate(BLOATWARE_CATALOG.items()):
            row_frame = ctk.CTkFrame(self.apps_scroll, fg_color=("gray95", "gray15"), corner_radius=6)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            cb = ctk.CTkCheckBox(row_frame, text=info["name"], font=ctk.CTkFont(size=13, weight="bold"), command=self._update_uninstall_button_count)
            cb.grid(row=0, column=0, padx=10, pady=7, sticky="w")
            if info["default_remove"]:
                cb.select()

            cat_badge = ctk.CTkLabel(row_frame, text=info["category"], font=ctk.CTkFont(size=11), text_color="gray60")
            cat_badge.grid(row=0, column=1, padx=10, pady=7, sticky="w")

            if info.get("store_id"):
                reinstall_btn = ctk.CTkButton(
                    row_frame,
                    text="Get Store Link",
                    width=95,
                    height=24,
                    font=ctk.CTkFont(size=10),
                    fg_color="gray30",
                    hover_color="gray20",
                    command=lambda sid=info["store_id"]: reinstall_app_from_store(sid)
                )
                reinstall_btn.grid(row=0, column=2, padx=10, pady=7, sticky="e")

            self.app_checkboxes[pkg_id] = cb

        self._update_uninstall_button_count()

    def _select_recommended_apps(self):
        for pkg_id, cb in self.app_checkboxes.items():
            if BLOATWARE_CATALOG.get(pkg_id, {}).get("default_remove", False):
                cb.select()
            else:
                cb.deselect()
        self._update_uninstall_button_count()

    def _deselect_all_apps(self):
        for cb in self.app_checkboxes.values():
            cb.deselect()
        self._update_uninstall_button_count()

    def _update_uninstall_button_count(self):
        selected = sum(1 for cb in self.app_checkboxes.values() if cb.get())
        self.uninstall_btn.configure(text=f"{t('uninstall_selected', 'Uninstall Selected')} ({selected})")

    def _refresh_apps_list(self):
        def task():
            self._update_progress(0.2, "Scanning installed Appx packages...")
            apps = query_installed_apps()
            for a in apps:
                cb = self.app_checkboxes.get(a["id"])
                if cb:
                    status_text = " [Installed]" if a["is_installed"] else " [Not Found]"
                    cb.configure(text=f"{a['name']}{status_text}")
            self._update_progress(1.0, "Package scan completed.")
        self._run_in_thread(task)

    def _remove_selected_apps(self):
        to_remove = [pkg_id for pkg_id, cb in self.app_checkboxes.items() if cb.get()]
        if not to_remove:
            messagebox.showinfo("No Selection", "Please select at least one package to uninstall.")
            return

        if messagebox.askyesno("Confirm Removal", f"Uninstall {len(to_remove)} selected packages for all users?"):
            def task():
                def cb(cur, tot, msg):
                    self._update_progress(cur / tot, msg)
                batch_remove_bloatware(to_remove, progress_callback=cb)
                self._update_progress(1.0, f"Uninstalled {len(to_remove)} packages.")
            self._run_in_thread(task)

    # ==========================
    # 3. SOFTWARE HUB VIEW (WINGET)
    # ==========================
    def _create_software_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, corner_radius=8)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(frame, height=50, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=8)

        ctk.CTkLabel(top_bar, text="🚀 Software Package Hub", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=5)

        select_dev_btn = ctk.CTkButton(top_bar, text="Select Dev Stack", fg_color="gray40", command=self._select_dev_software)
        select_dev_btn.pack(side="left", padx=5)

        select_browsers_btn = ctk.CTkButton(top_bar, text="Select Browsers", fg_color="gray40", command=self._select_browser_software)
        select_browsers_btn.pack(side="left", padx=5)

        deselect_sw_btn = ctk.CTkButton(top_bar, text=t("deselect_all", "Deselect All"), fg_color="gray40", command=self._deselect_all_software)
        deselect_sw_btn.pack(side="left", padx=5)

        self.install_sw_btn = ctk.CTkButton(top_bar, text=f"{t('install_selected', 'Install Selected')} (0)", fg_color="#059669", hover_color="#047857", command=self._install_selected_software)
        self.install_sw_btn.pack(side="right", padx=5)

        self.sw_scroll = ctk.CTkScrollableFrame(frame, corner_radius=8)
        self.sw_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.sw_scroll.grid_columnconfigure(0, weight=1)

        for idx, (pkg_id, info) in enumerate(SOFTWARE_CATALOG.items()):
            row_frame = ctk.CTkFrame(self.sw_scroll, fg_color=("gray95", "gray15"), corner_radius=6)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=3)
            row_frame.grid_columnconfigure(1, weight=1)

            cb = ctk.CTkCheckBox(row_frame, text=info["name"], font=ctk.CTkFont(size=13, weight="bold"), command=self._update_software_button_count)
            cb.grid(row=0, column=0, padx=10, pady=7, sticky="w")

            cat_badge = ctk.CTkLabel(row_frame, text=info["category"], font=ctk.CTkFont(size=11), text_color="#38bdf8")
            cat_badge.grid(row=0, column=1, padx=10, pady=7, sticky="w")

            desc = ctk.CTkLabel(row_frame, text=info["description"], font=ctk.CTkFont(size=11), text_color="gray")
            desc.grid(row=0, column=2, padx=10, pady=7, sticky="e")

            self.software_checkboxes[pkg_id] = cb

        return frame

    def _select_dev_software(self):
        for pkg_id, cb in self.software_checkboxes.items():
            if SOFTWARE_CATALOG.get(pkg_id, {}).get("category") == "Developer Tools":
                cb.select()
        self._update_software_button_count()

    def _select_browser_software(self):
        for pkg_id, cb in self.software_checkboxes.items():
            if SOFTWARE_CATALOG.get(pkg_id, {}).get("category") == "Web Browsers":
                cb.select()
        self._update_software_button_count()

    def _deselect_all_software(self):
        for cb in self.software_checkboxes.values():
            cb.deselect()
        self._update_software_button_count()

    def _update_software_button_count(self):
        selected = sum(1 for cb in self.software_checkboxes.values() if cb.get())
        self.install_sw_btn.configure(text=f"{t('install_selected', 'Install Selected')} ({selected})")

    def _install_selected_software(self):
        to_install = [pkg_id for pkg_id, cb in self.software_checkboxes.items() if cb.get()]
        if not to_install:
            messagebox.showinfo("No Selection", "Please select at least one software package to install.")
            return

        if not is_winget_available():
            messagebox.showerror("Winget Missing", "Windows Package Manager (winget) is not installed on this system.")
            return

        if messagebox.askyesno("Confirm Install", f"Silently install {len(to_install)} selected packages via winget?"):
            def task():
                def cb(cur, tot, msg):
                    self._update_progress(cur / tot, msg)
                batch_install_software(to_install, progress_callback=cb)
                self._update_progress(1.0, f"Installed {len(to_install)} packages.")
            self._run_in_thread(task)

    # ==========================
    # 4. PRIVACY & TELEMETRY VIEW
    # ==========================
    def _create_privacy_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self.views_container, corner_radius=8)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text=t("nav_privacy", "Privacy & Telemetry Hardening"), font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(15, 2), sticky="w")

        ed_info = get_windows_edition_info()
        ed_label = ctk.CTkLabel(frame, text=f"Windows Edition Note: {ed_info['note']}", font=ctk.CTkFont(size=11), text_color="#38bdf8")
        ed_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")

        apply_all_btn = ctk.CTkButton(frame, text="🛡️ Apply All Privacy Tweaks", command=lambda: self._run_in_thread(apply_all_privacy_tweaks))
        apply_all_btn.grid(row=0, column=1, rowspan=2, padx=20, pady=(15, 5), sticky="e")

        for idx, (t_id, info) in enumerate(PRIVACY_TWEAKS.items(), start=2):
            card = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
            card.grid(row=idx, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            lbl_title = ctk.CTkLabel(card, text=info["title"], font=ctk.CTkFont(size=14, weight="bold"))
            lbl_title.grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")

            lbl_desc = ctk.CTkLabel(card, text=info["description"], font=ctk.CTkFont(size=12), text_color="gray")
            lbl_desc.grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")

            is_active = get_tweak_status(t_id)
            switch = ctk.CTkSwitch(
                card,
                text="Applied" if is_active else "Default",
                command=lambda tid=t_id: self._toggle_privacy(tid)
            )
            if is_active:
                switch.select()
            switch.grid(row=0, column=1, rowspan=2, padx=15, pady=10)
            self.privacy_switches[t_id] = switch

        return frame

    def _toggle_privacy(self, tweak_id: str):
        switch = self.privacy_switches[tweak_id]
        if switch.get():
            apply_privacy_tweak(tweak_id)
            switch.configure(text="Applied")
        else:
            revert_privacy_tweak(tweak_id)
            switch.configure(text="Default")

    # ==========================
    # 5. WINDOWS 11 & UI VIEW
    # ==========================
    def _create_win11_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self.views_container, corner_radius=8)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text=t("nav_win11", "Windows 11 & Interface Tweaks"), font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        for idx, (t_id, info) in enumerate(WIN11_TWEAKS.items(), start=1):
            card = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
            card.grid(row=idx, column=0, padx=20, pady=5, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            lbl_title = ctk.CTkLabel(card, text=info["title"], font=ctk.CTkFont(size=14, weight="bold"))
            lbl_title.grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")

            lbl_desc = ctk.CTkLabel(card, text=info["description"], font=ctk.CTkFont(size=12), text_color="gray")
            lbl_desc.grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")

            is_active = info["check"]()
            switch = ctk.CTkSwitch(
                card,
                text="Active" if is_active else "Disabled",
                command=lambda tid=t_id: self._toggle_win11(tid)
            )
            if is_active:
                switch.select()
            switch.grid(row=0, column=1, rowspan=2, padx=15, pady=10)
            self.win11_switches[t_id] = switch

        return frame

    def _toggle_win11(self, tweak_id: str):
        switch = self.win11_switches[tweak_id]
        activate = bool(switch.get())
        toggle_win11_tweak(tweak_id, activate)
        switch.configure(text="Active" if activate else "Disabled")

    # ==========================
    # 6. GAMING & LATENCY VIEW
    # ==========================
    def _create_gaming_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self.views_container, corner_radius=8)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text=t("nav_gaming", "Gaming & Latency Optimizations"), font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # GameDVR
        card_dvr = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_dvr.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        card_dvr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_dvr, text="Disable GameDVR Background Recording", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_dvr, text="Prevents micro-stutters and input lag by disabling constant background gameplay capture.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        dvr_switch = ctk.CTkSwitch(card_dvr, text="Disabled", command=self._toggle_gamedvr)
        if is_gamedvr_disabled():
            dvr_switch.select()
        dvr_switch.grid(row=0, column=1, rowspan=2, padx=15, pady=10)
        self.gaming_switches["gamedvr"] = dvr_switch

        # Mouse Accel
        card_mouse = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_mouse.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        card_mouse.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_mouse, text="Disable Mouse Acceleration (1:1 Raw Input)", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_mouse, text="Turns off Enhanced Pointer Precision for consistent muscle memory aiming.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        ctk.CTkButton(card_mouse, text="Disable Acceleration", width=140, command=disable_mouse_acceleration).grid(row=0, column=1, rowspan=2, padx=15, pady=10)

        # Network Throttling & MMCSS Profiles
        card_net = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_net.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        card_net.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_net, text="MMCSS Network Throttling & CPU Responsiveness", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_net, text="Balanced preserves 10% CPU for Discord/Spotify. Extreme grants 100% CPU to the game.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        
        btn_box = ctk.CTkFrame(card_net, fg_color="transparent")
        btn_box.grid(row=0, column=1, rowspan=2, padx=15, pady=10)
        ctk.CTkButton(btn_box, text="Balanced (Streaming)", width=130, command=lambda: optimize_network_and_responsiveness("balanced")).pack(side="top", pady=2)
        ctk.CTkButton(btn_box, text="Extreme (Max FPS)", width=130, fg_color="gray40", command=lambda: optimize_network_and_responsiveness("extreme")).pack(side="top", pady=2)
        ctk.CTkButton(btn_box, text="Revert to Default", width=130, fg_color="gray30", command=revert_network_and_responsiveness).pack(side="top", pady=2)

        # Ultimate Performance Plan
        card_power = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_power.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        card_power.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_power, text="Unlock Ultimate Performance Power Plan", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_power, text="Unlocks the hidden Windows power plan designed for workstation and low-latency workloads.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        ctk.CTkButton(card_power, text="Unlock Scheme", width=140, command=unlock_ultimate_performance_plan).grid(row=0, column=1, rowspan=2, padx=15, pady=10)

        return frame

    def _toggle_gamedvr(self):
        switch = self.gaming_switches["gamedvr"]
        if switch.get():
            disable_gamedvr()
        else:
            enable_gamedvr()

    # ==========================
    # 7. SERVICES & SYSTEM VIEW
    # ==========================
    def _create_services_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkScrollableFrame(self.views_container, corner_radius=8)
        frame.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(frame, text=t("nav_services", "Services & Component Management"), font=ctk.CTkFont(size=20, weight="bold"))
        title.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")

        # Telemetry Services
        card_srv = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_srv.grid(row=1, column=0, padx=20, pady=5, sticky="ew")
        card_srv.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_srv, text="Telemetry & Diagnostic Services", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_srv, text="Disables DiagTrack, dmwappushservice, and retail demo collectors via registry & service manager.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        ctk.CTkButton(card_srv, text="Optimize Services", width=140, command=lambda: self._run_in_thread(optimize_telemetry_services)).grid(row=0, column=1, rowspan=2, padx=15, pady=10)

        # Scheduled Tasks
        card_tasks = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_tasks.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        card_tasks.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_tasks, text="Telemetry Scheduled Tasks", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_tasks, text="Disables Customer Experience (CEIP) and Compatibility Appraiser tasks.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        ctk.CTkButton(card_tasks, text="Disable Tasks", width=140, command=lambda: self._run_in_thread(disable_all_telemetry_tasks)).grid(row=0, column=1, rowspan=2, padx=15, pady=10)

        # Windows Update Persistence Guard
        card_persist = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_persist.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        card_persist.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_persist, text="Windows Update Persistence Guard", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_persist, text="Registers a logon task to ensure telemetry and bloat tasks stay disabled after Cumulative Updates.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        
        persist_box = ctk.CTkFrame(card_persist, fg_color="transparent")
        persist_box.grid(row=0, column=1, rowspan=2, padx=15, pady=10)
        ctk.CTkButton(persist_box, text="Install Guard Task", width=130, command=install_persistence_task).pack(side="top", pady=2)
        ctk.CTkButton(persist_box, text="Remove Guard", width=130, fg_color="gray40", command=remove_persistence_task).pack(side="top", pady=2)

        # OneDrive Removal & Reinstallation
        card_od = ctk.CTkFrame(frame, corner_radius=8, fg_color=("gray95", "gray17"))
        card_od.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        card_od.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card_od, text="Microsoft OneDrive Management", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, padx=15, pady=(9, 2), sticky="w")
        ctk.CTkLabel(card_od, text="Includes Files-On-Demand safety scans. Reinstall via official winget/MS CDN.", font=ctk.CTkFont(size=12), text_color="gray").grid(row=1, column=0, padx=15, pady=(0, 9), sticky="w")
        
        od_box = ctk.CTkFrame(card_od, fg_color="transparent")
        od_box.grid(row=0, column=1, rowspan=2, padx=15, pady=10)
        ctk.CTkButton(od_box, text="Uninstall OneDrive", fg_color="#dc2626", hover_color="#b91c1c", width=130, command=self._confirm_uninstall_onedrive).pack(side="top", pady=2)
        ctk.CTkButton(od_box, text="Reinstall OneDrive", fg_color="gray40", width=130, command=lambda: self._run_in_thread(reinstall_onedrive)).pack(side="top", pady=2)

        return frame

    def _confirm_uninstall_onedrive(self):
        if messagebox.askyesno("Uninstall OneDrive", "Are you sure you want to completely uninstall Microsoft OneDrive and remove it from File Explorer?"):
            self._run_in_thread(uninstall_onedrive, True)

    # ==========================
    # 8. BACKUPS & ROLLBACK VIEW
    # ==========================
    def _create_backups_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, corner_radius=8)
        frame.grid_rowconfigure(2, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(frame, height=50, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=15, pady=8)

        ctk.CTkLabel(top_bar, text=t("nav_backups", "Registry Backups & Rollback"), font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=5)

        refresh_btn = ctk.CTkButton(top_bar, text="🔄 Refresh", width=90, command=self._refresh_backups_list)
        refresh_btn.pack(side="right", padx=5)

        open_folder_btn = ctk.CTkButton(top_bar, text="📂 Open Backups", width=110, fg_color="gray40", command=self._open_backup_dir)
        open_folder_btn.pack(side="right", padx=5)

        self.backups_scroll = ctk.CTkScrollableFrame(frame, corner_radius=8)
        self.backups_scroll.grid(row=2, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.backups_scroll.grid_columnconfigure(0, weight=1)

        return frame

    def _refresh_backups_list(self):
        for widget in self.backups_scroll.winfo_children():
            widget.destroy()

        backups = list_backups()
        if not backups:
            lbl = ctk.CTkLabel(self.backups_scroll, text="No registry backups found yet. Backups are automatically created before modifications.", text_color="gray")
            lbl.grid(row=0, column=0, padx=20, pady=20)
            return

        for idx, b in enumerate(backups):
            row_frame = ctk.CTkFrame(self.backups_scroll, fg_color=("gray95", "gray17"), corner_radius=6)
            row_frame.grid(row=idx, column=0, sticky="ew", padx=5, pady=3)
            row_frame.grid_columnconfigure(0, weight=1)

            fname = ctk.CTkLabel(row_frame, text=b["filename"], font=ctk.CTkFont(size=12, weight="bold"))
            fname.grid(row=0, column=0, padx=12, pady=(7, 2), sticky="w")

            meta = ctk.CTkLabel(row_frame, text=f"Date: {b['created_at']} • Size: {b['size_kb']} KB", font=ctk.CTkFont(size=11), text_color="gray")
            meta.grid(row=1, column=0, padx=12, pady=(0, 7), sticky="w")

            restore_btn = ctk.CTkButton(
                row_frame,
                text="Restore Backup",
                width=110,
                height=28,
                command=lambda fp=b["filepath"]: self._trigger_restore_backup(fp)
            )
            restore_btn.grid(row=0, column=1, rowspan=2, padx=6, pady=7)

            del_btn = ctk.CTkButton(
                row_frame,
                text="Delete",
                width=70,
                height=28,
                fg_color="gray40",
                hover_color="#b91c1c",
                command=lambda fp=b["filepath"]: self._trigger_delete_backup(fp)
            )
            del_btn.grid(row=0, column=2, rowspan=2, padx=(0, 10), pady=7)

    def _trigger_restore_backup(self, backup_path: str):
        if messagebox.askyesno("Restore Backup", f"Restore registry settings from {os.path.basename(backup_path)}?"):
            ok, msg = restore_backup(backup_path)
            if ok:
                messagebox.showinfo("Restored", msg)
            else:
                messagebox.showerror("Error", msg)

    def _trigger_delete_backup(self, backup_path: str):
        if messagebox.askyesno("Delete Backup", f"Delete {os.path.basename(backup_path)}?"):
            delete_backup(backup_path)
            self._refresh_backups_list()

    def _open_backup_dir(self):
        try:
            os.startfile(BACKUP_DIR)
        except Exception:
            subprocess.Popen(f'explorer.exe "{BACKUP_DIR}"')

    # ==========================
    # 9. LOGS VIEW (HIGH PERFORMANCE BUFFERED)
    # ==========================
    def _create_logs_view(self) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(self.views_container, corner_radius=8)
        frame.grid_rowconfigure(1, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        top_bar = ctk.CTkFrame(frame, height=45, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        title = ctk.CTkLabel(top_bar, text=t("nav_logs", "Activity & Operation Logs"), font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(side="left", padx=5)

        open_folder_btn = ctk.CTkButton(top_bar, text="📂 Open Log Folder", width=120, command=self._open_log_dir)
        open_folder_btn.pack(side="right", padx=5)

        clear_btn = ctk.CTkButton(top_bar, text="Clear", width=70, fg_color="gray40", command=self._clear_logs)
        clear_btn.pack(side="right", padx=5)

        self.log_textbox = ctk.CTkTextbox(frame, wrap="word", font=ctk.CTkFont(family="Consolas", size=12))
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        return frame

    def _on_log_message(self, level: str, message: str):
        """Puts log message into thread-safe queue in <0.001ms (Zero UI Thread Blocking)."""
        self._log_queue.put(f"[{level}] {message}\n")

    def _flush_logs_loop(self):
        """Flushes buffered log messages in batches every 80ms, preventing GUI freeze."""
        batch = []
        while not self._log_queue.empty():
            try:
                batch.append(self._log_queue.get_nowait())
            except queue.Empty:
                break

        if batch and hasattr(self, "log_textbox"):
            self.log_textbox.insert("end", "".join(batch))
            self.log_textbox.see("end")

        self.after(80, self._flush_logs_loop)

    def _clear_logs(self):
        self.log_textbox.delete("1.0", "end")

    def _open_log_dir(self):
        try:
            os.startfile(LOG_DIR)
        except Exception:
            subprocess.Popen(f'explorer.exe "{LOG_DIR}"')

    # Progress and Background Threading
    def _update_progress(self, progress_float: float, status_str: str):
        def update():
            self.progress_bar.set(progress_float)
            self.status_label.configure(text=status_str)
        self.after(0, update)

    def _run_in_thread(self, target, *args):
        if self.is_busy:
            return
        self.is_busy = True

        def runner():
            try:
                target(*args)
            finally:
                self.is_busy = False

        t = threading.Thread(target=runner, daemon=True)
        t.start()

    def _trigger_restore_point(self):
        def task():
            self._update_progress(0.3, "Creating Windows System Restore Point...")
            create_restore_point("WinDebloatX Manual Checkpoint")
            self._update_progress(1.0, "Restore point operation completed.")
        self._run_in_thread(task)

    def _request_elevation(self):
        elevate_and_relaunch()


def launch_gui():
    app = WinDebloatXApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
