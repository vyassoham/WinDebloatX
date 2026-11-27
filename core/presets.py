"""
WinDebloatX - Preset Profiles Orchestrator
Bundles debloating actions into 1-click profiles: Essential, Gaming, Maximum Privacy, and Full Debloat.
"""

from typing import Callable, Dict, List, Optional, Tuple
from core.appx_remover import BLOATWARE_CATALOG, batch_remove_bloatware
from core.gaming import disable_gamedvr, disable_mouse_acceleration, optimize_network_and_responsiveness
from core.logger import log_info, log_success
from core.privacy import apply_all_privacy_tweaks
from core.services import optimize_telemetry_services
from core.tasks import disable_all_telemetry_tasks
from core.win11_tweaks import set_classic_context_menu, set_copilot_state, set_edge_bloat_state, set_recall_state, set_widgets_state

PRESETS: Dict[str, Dict[str, any]] = {
    "essential": {
        "name": "Essential / Recommended",
        "description": "Safe, balanced debloat. Removes safe junk apps, disables telemetry, disables Web Search in Start, and silences ads.",
        "icon": "⚡"
    },
    "gaming": {
        "name": "Gaming Optimizer",
        "description": "Maximizes FPS and responsiveness. Removes bloat, disables GameDVR latency hooks, turns off mouse acceleration, and disables network throttling.",
        "icon": "🎮"
    },
    "privacy": {
        "name": "Maximum Privacy",
        "description": "Aggressive privacy hardening. Disables all telemetry, telemetry services, scheduled tasks, Windows Copilot, Recall AI, and Advertising ID.",
        "icon": "🛡️"
    },
    "full": {
        "name": "Extreme Full Debloat",
        "description": "Comprehensive cleanup. Applies all privacy tweaks, disables AI/Copilot/Recall, removes all non-critical bloatware, and disables telemetry tasks.",
        "icon": "🚀"
    }
}

def execute_preset(
    preset_key: str,
    progress_cb: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[bool, str]:
    """
    Executes a preset profile step-by-step.
    """
    if preset_key not in PRESETS:
        return False, f"Unknown preset: {preset_key}"

    log_info(f"Executing profile: [{PRESETS[preset_key]['name']}]...")

    # Step 1: Privacy tweaks
    if progress_cb:
        progress_cb(1, 6, "Applying privacy & telemetry hardening...")
    apply_all_privacy_tweaks()

    # Step 2: Telemetry services
    if progress_cb:
        progress_cb(2, 6, "Disabling telemetry background services...")
    optimize_telemetry_services()

    # Step 3: Telemetry tasks
    if progress_cb:
        progress_cb(3, 6, "Disabling scheduled telemetry tasks...")
    disable_all_telemetry_tasks()

    # Step 4: Win11 modern features
    if progress_cb:
        progress_cb(4, 6, "Optimizing Windows 11 features (Copilot, Recall, Widgets)...")
    set_copilot_state(True)
    set_recall_state(True)
    set_edge_bloat_state(True)
    set_widgets_state(True)

    # Step 5: Gaming specific tweaks
    if preset_key in ("gaming", "full"):
        if progress_cb:
            progress_cb(5, 6, "Applying gaming latency & performance tweaks...")
        disable_gamedvr()
        disable_mouse_acceleration()
        optimize_network_and_responsiveness()

    # Step 6: Bloatware app removal
    if progress_cb:
        progress_cb(6, 6, "Removing preinstalled bloatware packages...")
    
    # Filter default removal apps
    apps_to_remove = []
    for pkg_id, info in BLOATWARE_CATALOG.items():
        if info["default_remove"]:
            # If gaming preset, preserve Xbox overlay/identity provider
            if preset_key == "gaming" and "Xbox" in pkg_id:
                continue
            apps_to_remove.append(pkg_id)

    batch_remove_bloatware(apps_to_remove)

    msg = f"Preset '{PRESETS[preset_key]['name']}' applied successfully!"
    log_success(msg)
    return True, msg
