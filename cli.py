"""
WinDebloatX - Command Line Interface (CLI & TUI)
Interactive Rich console interface and scriptable command-line automation.
"""

import argparse
import os
import sys
from typing import Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from core.logger import log_info, log_success, log_warning, log_error
from core.restore_point import create_restore_point, open_system_restore_gui
from core.privacy import PRIVACY_TWEAKS, apply_all_privacy_tweaks, get_tweak_status, get_windows_edition_info
from core.appx_remover import query_installed_apps, batch_remove_bloatware
from core.win11_tweaks import WIN11_TWEAKS, set_classic_context_menu, set_copilot_state, set_recall_state, set_widgets_state, set_edge_bloat_state
from core.gaming import (
    disable_gamedvr,
    disable_mouse_acceleration,
    get_mmcss_status,
    is_gamedvr_disabled,
    optimize_network_and_responsiveness,
    revert_network_and_responsiveness,
    unlock_ultimate_performance_plan
)
from core.services import BLOAT_SERVICES, get_service_status, optimize_telemetry_services
from core.tasks import disable_all_telemetry_tasks
from core.onedrive import uninstall_onedrive, reinstall_onedrive, is_onedrive_installed
from core.presets import PRESETS, execute_preset
from core.privileges import is_admin, elevate_and_relaunch
from core.backup_manager import list_backups, restore_backup
from core.persistence import install_persistence_task, remove_persistence_task, is_persistence_task_installed
from core.hardware import get_hardware_profile
from core.winget_installer import SOFTWARE_CATALOG, batch_install_software, install_single_package
from core.i18n import SUPPORTED_LANGUAGES, set_language, t

def print_banner():
    if HAS_RICH:
        console = Console()
        banner_text = """[bold cyan]╦ ╦┬┌┐┌╔╦╗┌─┐┌┐ ┬  ┌─┐┌─┐┌┬┐═╗ ╦
║║║││││ ║║├┤ ├┴┐│  │ │├─┤ │ ╔╩╦╝
╚╩╝┴┘└┘═╩╝└─┘└─┘┴─┘└─┘┴ ┴ ┴ ╩ ╚═[/bold cyan]
[bold white]Next-Generation Windows 10 & 11 Privacy Hardening, Debloater & Software Hub[/bold white]
[dim]Hardware-Intelligent • Win11 24H2 Ready • Zero-Dependency Architecture[/dim]"""
        console.print(Panel(banner_text, border_style="cyan"))
    else:
        print("=" * 60)
        print("WinDebloatX - Modern Windows 10 & 11 Debloater & Software Hub")
        print("=" * 60)

def show_hardware_report():
    """Prints a detailed hardware intelligence report."""
    console = Console() if HAS_RICH else None
    hw = get_hardware_profile()
    
    if HAS_RICH:
        table = Table(title="WinDebloatX - Hardware Intelligence Profile", header_style="bold cyan")
        table.add_column("Property", style="white")
        table.add_column("Detected Value", style="bold green")
        table.add_row("Form Factor", hw["form_factor"])
        table.add_row("Storage Medium", hw["storage_type"])
        table.add_row("Physical Memory", f"{hw['total_ram_gb']} GB")
        table.add_row("Processor Topology", f"{hw['cpu_cores']} Cores / {hw['cpu_threads']} Threads")
        console.print(table)

        console.print("\n[bold yellow]Hardware-Tailored Guidance:[/bold yellow]")
        for rec in hw["recommendations"]:
            console.print(f" • [dim]{rec}[/dim]")
        print()
    else:
        print(f"Form Factor: {hw['form_factor']}")
        print(f"Storage: {hw['storage_type']}, RAM: {hw['total_ram_gb']} GB")

def show_status_audit():
    """Prints a structured table showing the live state of all system tweaks, edition info, and services."""
    console = Console() if HAS_RICH else None
    if not HAS_RICH:
        print("Status Audit requires 'rich' package.")
        return

    ed_info = get_windows_edition_info()
    console.print(f"\n[bold cyan]Detected OS:[/bold cyan] {ed_info['product_name']} ({ed_info['edition_id']})")
    console.print(f"[dim]Edition Telemetry Capability: {ed_info['note']}[/dim]\n")

    table = Table(title="WinDebloatX - System State Audit", header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Feature / Component", style="white")
    table.add_column("Current State", style="bold")

    # Privacy Tweaks
    for k, v in PRIVACY_TWEAKS.items():
        active = get_tweak_status(k)
        state_str = "[green]Hardened (Active)[/green]" if active else "[yellow]Default (Unprotected)[/yellow]"
        table.add_row("Privacy", v["title"], state_str)

    # Win11 Tweaks
    for k, v in WIN11_TWEAKS.items():
        active = v["check"]()
        state_str = "[green]Active / Disabled[/green]" if active else "[dim]Default[/dim]"
        table.add_row("Windows 11", v["title"], state_str)

    # Services
    for s_name, s_info in BLOAT_SERVICES.items():
        status = get_service_status(s_name)
        color = "green" if status == "DISABLED" else ("red" if status == "RUNNING" else "yellow")
        table.add_row("Service", s_info["display_name"], f"[{color}]{status}[/{color}]")

    # Gaming & MMCSS
    dvr_state = "[green]Disabled (Optimized)[/green]" if is_gamedvr_disabled() else "[yellow]Enabled (Default)[/yellow]"
    table.add_row("Gaming", "GameDVR Background Capture", dvr_state)
    
    mmcss = get_mmcss_status()
    mmcss_state = f"[green]Optimized (Resp={mmcss['system_responsiveness']})[/green]" if mmcss["is_optimized"] else "[dim]Windows Default[/dim]"
    table.add_row("Gaming", "MMCSS Network & Responsiveness", mmcss_state)

    # Components
    od_state = "[yellow]Installed[/yellow]" if is_onedrive_installed() else "[green]Not Found / Removed[/green]"
    table.add_row("Components", "Microsoft OneDrive", od_state)

    guard_state = "[green]Active (Installed)[/green]" if is_persistence_task_installed() else "[dim]Disabled[/dim]"
    table.add_row("Protection", "Update Persistence Guard Task", guard_state)

    console.print(table)

def show_backups_table():
    """Lists available backups."""
    console = Console() if HAS_RICH else None
    backups = list_backups()
    if not backups:
        print("No registry backups found.")
        return

    if HAS_RICH:
        table = Table(title="Saved Registry Backups", header_style="bold yellow")
        table.add_column("Filename", style="cyan")
        table.add_column("Created", style="white")
        table.add_column("Size", style="dim")
        for b in backups:
            table.add_row(b["filename"], b["created_at"], f"{b['size_kb']} KB")
        console.print(table)
    else:
        for b in backups:
            print(f"- {b['filename']} ({b['created_at']}, {b['size_kb']} KB)")

def run_interactive_cli():
    """Interactive text user interface using Rich."""
    console = Console() if HAS_RICH else None

    while True:
        print_banner()
        if not is_admin():
            if HAS_RICH:
                console.print("[bold red]WARNING: Running without Administrator privileges. Some operations may fail.[/bold red]")
                if Confirm.ask("Would you like to elevate to Administrator now?"):
                    elevate_and_relaunch()
                    return
            else:
                print("WARNING: Not running as Administrator.")

        if HAS_RICH:
            table = Table(title="WinDebloatX Main Menu", show_header=True, header_style="bold magenta")
            table.add_column("Option", style="cyan", width=8)
            table.add_column("Category / Action", style="white")
            table.add_column("Description", style="dim")

            table.add_row("1", "Apply 1-Click Preset", "Essential, Gaming, Max Privacy, or Full Debloat")
            table.add_row("2", "Create System Restore Point", "Safe Windows checkpoint with disk pre-flight check")
            table.add_row("3", "System State Audit", "Inspect live protection, edition, and tweak status")
            table.add_row("4", "Hardware Intelligence", "View detected chassis, storage, and recommendations")
            table.add_row("5", "Debloat UWP Packages", "Scan and remove preinstalled bloat apps (fast batch)")
            table.add_row("6", "Software Package Hub", "Install developer tools, browsers, and utilities via winget")
            table.add_row("7", "Privacy & Telemetry Hardening", "Disable telemetry, diagnostic data, and web start search")
            table.add_row("8", "Windows 11 & AI Optimizations", "Classic context menu, disable Copilot, Recall & Widgets")
            table.add_row("9", "Gaming & Latency Tweaks", "Disable GameDVR, mouse acceleration & MMCSS profiles")
            table.add_row("10", "OneDrive Management", "Uninstall or reinstall Microsoft OneDrive")
            table.add_row("11", "Persistence Guard Task", "Install scheduled task to guard against Windows Updates")
            table.add_row("12", "Manage Backups & Rollback", "View and restore registry snapshots")
            table.add_row("13", "Launch Graphical UI (GUI)", "Switch to modern CustomTkinter interface")
            table.add_row("0", "Exit", "Close WinDebloatX")

            console.print(table)
            choice = Prompt.ask("\n[bold green]Select an option[/bold green]", choices=[str(i) for i in range(14)], default="1")
        else:
            print("\n1. Apply Preset\n2. Create Restore Point\n3. Audit\n4. Hardware\n5. Debloat Apps\n6. Software Hub\n7. Privacy\n8. Win11 Tweaks\n9. Gaming\n10. OneDrive\n11. Guard\n12. Backups\n13. Launch GUI\n0. Exit")
            choice = input("Select: ").strip()

        if choice == "0":
            break
        elif choice == "1":
            menu_presets()
        elif choice == "2":
            create_restore_point()
        elif choice == "3":
            show_status_audit()
        elif choice == "4":
            show_hardware_report()
        elif choice == "5":
            menu_apps()
        elif choice == "6":
            menu_software()
        elif choice == "7":
            menu_privacy()
        elif choice == "8":
            menu_win11()
        elif choice == "9":
            menu_gaming()
        elif choice == "10":
            menu_onedrive()
        elif choice == "11":
            menu_guard()
        elif choice == "12":
            menu_backups()
        elif choice == "13":
            from gui.app import launch_gui
            launch_gui()
            break

        input("\nPress Enter to return to main menu...")

def menu_presets():
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        table = Table(title="1-Click Optimization Presets", header_style="bold yellow")
        table.add_column("Key", style="cyan")
        table.add_column("Preset Name", style="bold white")
        table.add_column("Summary", style="dim")
        for k, v in PRESETS.items():
            table.add_row(k, f"{v['icon']} {v['name']}", v["description"])
        console.print(table)
        preset_choice = Prompt.ask("Choose preset", choices=list(PRESETS.keys()) + ["back"], default="essential")
        if preset_choice != "back":
            execute_preset(preset_choice)

def menu_apps():
    apps = query_installed_apps()
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        table = Table(title="Detected Bloatware Apps", header_style="bold green")
        table.add_column("ID", style="cyan")
        table.add_column("App Name", style="white")
        table.add_column("Category", style="yellow")
        table.add_column("Status", style="magenta")
        for a in apps:
            status = "[green]Installed[/green]" if a["is_installed"] else "[dim]Not Found[/dim]"
            table.add_row(a["id"], a["name"], a["category"], status)
        console.print(table)

        if Confirm.ask("Uninstall all default recommended bloatware apps now?"):
            to_remove = [a["id"] for a in apps if a["default_remove"] and a["is_installed"]]
            if to_remove:
                batch_remove_bloatware(to_remove)
            else:
                console.print("[green]No installed default bloatware found.[/green]")

def menu_software():
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        table = Table(title="Software Package Hub (Winget)", header_style="bold cyan")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Category", style="yellow")
        for pid, info in SOFTWARE_CATALOG.items():
            table.add_row(pid, info["name"], info["category"])
        console.print(table)

        action = Prompt.ask("Install options", choices=["dev-stack", "browsers", "custom-id", "back"], default="dev-stack")
        if action == "dev-stack":
            dev_ids = [k for k, v in SOFTWARE_CATALOG.items() if v["category"] == "Developer Tools"]
            batch_install_software(dev_ids)
        elif action == "browsers":
            browser_ids = [k for k, v in SOFTWARE_CATALOG.items() if v["category"] == "Web Browsers"]
            batch_install_software(browser_ids)
        elif action == "custom-id":
            cid = Prompt.ask("Enter exact Winget Package ID (e.g. Git.Git)")
            install_single_package(cid)

def menu_privacy():
    apply_all_privacy_tweaks()
    optimize_telemetry_services()
    disable_all_telemetry_tasks()

def menu_win11():
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        console.print("1. Enable Classic Context Menu\n2. Disable Windows Copilot\n3. Disable Windows Recall\n4. Disable Widgets\n5. Disable Edge Background Bloat")
        c = Prompt.ask("Select Win11 tweak", choices=["1", "2", "3", "4", "5", "back"])
        if c == "1":
            set_classic_context_menu(True)
        elif c == "2":
            set_copilot_state(True)
        elif c == "3":
            set_recall_state(True)
        elif c == "4":
            set_widgets_state(True)
        elif c == "5":
            set_edge_bloat_state(True)

def menu_gaming():
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        console.print("1. Disable GameDVR\n2. Disable Mouse Acceleration\n3. Set MMCSS to Balanced (Streaming Safe)\n4. Set MMCSS to Extreme (0% Background Reserved)\n5. Revert MMCSS to Default\n6. Unlock Ultimate Performance Plan")
        c = Prompt.ask("Select gaming option", choices=["1", "2", "3", "4", "5", "6", "back"])
        if c == "1":
            disable_gamedvr()
        elif c == "2":
            disable_mouse_acceleration()
        elif c == "3":
            optimize_network_and_responsiveness("balanced")
        elif c == "4":
            optimize_network_and_responsiveness("extreme")
        elif c == "5":
            revert_network_and_responsiveness()
        elif c == "6":
            unlock_ultimate_performance_plan()

def menu_onedrive():
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        console.print("1. Uninstall OneDrive (with Files-On-Demand check)\n2. Reinstall OneDrive")
        c = Prompt.ask("Select OneDrive action", choices=["1", "2", "back"])
        if c == "1":
            if Confirm.ask("Completely uninstall OneDrive and remove from Explorer sidebar?"):
                uninstall_onedrive(force=True)
        elif c == "2":
            reinstall_onedrive()

def menu_guard():
    installed = is_persistence_task_installed()
    console = Console() if HAS_RICH else None
    if HAS_RICH:
        console.print(f"Update Persistence Guard is currently: {'[green]Active[/green]' if installed else '[yellow]Inactive[/yellow]'}")
        if not installed and Confirm.ask("Install Persistence Guard scheduled task?"):
            install_persistence_task()
        elif installed and Confirm.ask("Remove Persistence Guard scheduled task?"):
            remove_persistence_task()

def menu_backups():
    show_backups_table()
    backups = list_backups()
    if backups and Confirm.ask("Would you like to restore a backup?"):
        fname = Prompt.ask("Enter the filename of the backup to restore")
        target = [b for b in backups if b["filename"].lower() == fname.lower()]
        if target:
            restore_backup(target[0]["filepath"])
        else:
            print("Backup filename not found.")

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="WinDebloatX - Ultimate Windows 10 & 11 Debloater, Privacy Hardener & Software Hub"
    )
    parser.add_argument("--cli", action="store_true", help="Launch interactive CLI menu instead of GUI")
    parser.add_argument("--status", action="store_true", help="Audit and display live state of all system tweaks")
    parser.add_argument("--hardware", action="store_true", help="Display hardware intelligence report and recommendations")
    parser.add_argument("--lang", choices=["en", "es", "de", "zh"], help="Set application language")
    parser.add_argument("--list-backups", action="store_true", help="List all saved registry backups")
    parser.add_argument("--restore-backup", type=str, help="Restore a specific registry backup file")
    parser.add_argument("--open-restore-gui", action="store_true", help="Launch native Windows System Restore wizard")
    parser.add_argument("--preset", choices=["essential", "gaming", "privacy", "full"], help="Execute a predefined optimization profile")
    parser.add_argument("--create-restore-point", action="store_true", help="Create a Windows System Restore Point")
    parser.add_argument("--remove-bloatware", action="store_true", help="Remove all recommended bloatware packages")
    parser.add_argument("--disable-telemetry", action="store_true", help="Apply all telemetry & privacy hardening tweaks")
    parser.add_argument("--classic-context-menu", action="store_true", help="Enable Windows 11 classic context menu")
    parser.add_argument("--disable-copilot", action="store_true", help="Disable Windows Copilot AI")
    parser.add_argument("--disable-recall", action="store_true", help="Disable Windows Recall AI snapshots")
    parser.add_argument("--disable-widgets", action="store_true", help="Disable Windows 11 taskbar widgets")
    parser.add_argument("--optimize-gaming", action="store_true", help="Apply GameDVR, mouse acceleration, and latency tweaks")
    parser.add_argument("--mmcss", choices=["balanced", "extreme", "default"], help="Configure MMCSS latency and CPU responsiveness profile")
    parser.add_argument("--install-software", nargs="+", help="Install software packages by winget ID (e.g. Brave.Brave Git.Git)")
    parser.add_argument("--install-dev", action="store_true", help="Install full developer software stack via winget")
    parser.add_argument("--uninstall-onedrive", action="store_true", help="Completely uninstall OneDrive and clean explorer sidebar")
    parser.add_argument("--reinstall-onedrive", action="store_true", help="Reinstall OneDrive and restore explorer pins")
    parser.add_argument("--install-guard", action="store_true", help="Register update persistence scheduled task")
    parser.add_argument("--remove-guard", action="store_true", help="Remove update persistence scheduled task")
    parser.add_argument("--silent", "-s", action="store_true", help="Silent non-interactive execution")

    return parser.parse_args()
