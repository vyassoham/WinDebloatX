"""
WinDebloatX - Ultimate Windows 10 & 11 Debloater, Privacy Hardener & Software Hub
Modernized for Windows 10 & 11 (24H2+) | Open Source Flagship
"""

import sys
from cli import parse_cli_args, run_interactive_cli, show_status_audit, show_backups_table, show_hardware_report
from core.appx_remover import batch_remove_bloatware, query_installed_apps
from core.backup_manager import restore_backup
from core.gaming import (
    disable_gamedvr,
    disable_mouse_acceleration,
    optimize_network_and_responsiveness,
    revert_network_and_responsiveness,
    unlock_ultimate_performance_plan
)
from core.i18n import set_language
from core.logger import log_error, log_info, log_success
from core.onedrive import uninstall_onedrive, reinstall_onedrive
from core.persistence import install_persistence_task, remove_persistence_task
from core.presets import execute_preset
from core.privacy import apply_all_privacy_tweaks
from core.privileges import elevate_and_relaunch, is_admin
from core.restore_point import create_restore_point, open_system_restore_gui
from core.services import optimize_telemetry_services
from core.tasks import disable_all_telemetry_tasks
from core.win11_tweaks import (
    set_classic_context_menu,
    set_copilot_state,
    set_edge_bloat_state,
    set_recall_state,
    set_widgets_state
)
from core.winget_installer import SOFTWARE_CATALOG, batch_install_software

def main():
    args = parse_cli_args()

    if args.lang:
        set_language(args.lang)

    # Informational flags (no elevation required)
    if args.hardware:
        show_hardware_report()
        return

    if args.status:
        show_status_audit()
        return

    if args.list_backups:
        show_backups_table()
        return

    if args.open_restore_gui:
        open_system_restore_gui()
        return

    if args.restore_backup:
        restore_backup(args.restore_backup)
        return

    # Action flags (require administrator privileges)
    has_action_flags = any([
        args.preset,
        args.create_restore_point,
        args.remove_bloatware,
        args.disable_telemetry,
        args.classic_context_menu,
        args.disable_copilot,
        args.disable_recall,
        args.disable_widgets,
        args.optimize_gaming,
        args.mmcss,
        args.install_software,
        args.install_dev,
        args.uninstall_onedrive,
        args.reinstall_onedrive,
        args.install_guard,
        args.remove_guard
    ])

    if has_action_flags:
        if not is_admin():
            log_error("Administrator privileges are required for system modifications.")
            if not args.silent:
                elevate_and_relaunch()
                return
            sys.exit(1)

        if args.create_restore_point:
            create_restore_point()

        if args.preset:
            execute_preset(args.preset)

        if args.disable_telemetry:
            apply_all_privacy_tweaks()
            optimize_telemetry_services()
            disable_all_telemetry_tasks()

        if args.remove_bloatware:
            apps = query_installed_apps()
            to_remove = [a["id"] for a in apps if a["default_remove"]]
            batch_remove_bloatware(to_remove)

        if args.classic_context_menu:
            set_classic_context_menu(True)

        if args.disable_copilot:
            set_copilot_state(True)

        if args.disable_recall:
            set_recall_state(True)

        if args.disable_widgets:
            set_widgets_state(True)

        if args.optimize_gaming:
            disable_gamedvr()
            disable_mouse_acceleration()
            optimize_network_and_responsiveness("balanced")
            unlock_ultimate_performance_plan()

        if args.mmcss:
            if args.mmcss == "default":
                revert_network_and_responsiveness()
            else:
                optimize_network_and_responsiveness(args.mmcss)

        if args.install_software:
            batch_install_software(args.install_software)

        if args.install_dev:
            dev_ids = [k for k, v in SOFTWARE_CATALOG.items() if v["category"] == "Developer Tools"]
            batch_install_software(dev_ids)

        if args.uninstall_onedrive:
            uninstall_onedrive(force=True)

        if args.reinstall_onedrive:
            reinstall_onedrive()

        if args.install_guard:
            install_persistence_task()

        if args.remove_guard:
            remove_persistence_task()

        log_success("All requested command-line operations completed.")
        return

    if args.cli:
        run_interactive_cli()
        return

    # Default to modern GUI
    try:
        from gui.app import launch_gui
        launch_gui()
    except Exception as e:
        log_error(f"Could not launch graphical user interface: {e}")
        log_info("Falling back to interactive console interface (CLI)...")
        run_interactive_cli()

if __name__ == "__main__":
    main()
