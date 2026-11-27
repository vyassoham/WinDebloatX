"""
WinDebloatX - Windows Services Optimization Engine
Safely manages, disables, and audits Windows telemetry, diagnostic, and bloatware services.
Includes direct registry fallbacks to bypass TrustedInstaller / access denied errors.
"""

import subprocess
import winreg
from typing import Dict, List, Tuple
from core.logger import log_debug, log_error, log_info, log_success, log_warning
from core.registry import get_reg_value, set_reg_value

BLOAT_SERVICES: Dict[str, Dict[str, str]] = {
    "DiagTrack": {
        "display_name": "Connected User Experiences and Telemetry",
        "description": "Collects and uploads diagnostic and usage data to Microsoft servers.",
        "recommended_state": "disabled"
    },
    "dmwappushservice": {
        "display_name": "Device Management Wireless Application Protocol (WAP)",
        "description": "Routing service used for telemetry and push telemetry beacons.",
        "recommended_state": "disabled"
    },
    "RetailDemo": {
        "display_name": "Retail Demo Service",
        "description": "Controls retail demonstration mode used on store display machines.",
        "recommended_state": "disabled"
    },
    "diagnosticshub.standardcollector.service": {
        "display_name": "Diagnostics Hub Standard Collector Service",
        "description": "Collects real-time system events and telemetry information.",
        "recommended_state": "disabled"
    },
    "MapsBroker": {
        "display_name": "Downloaded Maps Manager",
        "description": "Background broker for offline maps. Unnecessary if not using offline maps.",
        "recommended_state": "manual"
    },
    "WMPNetworkSvc": {
        "display_name": "Windows Media Player Network Sharing Service",
        "description": "Shares Windows Media Player libraries over local network (legacy).",
        "recommended_state": "disabled"
    }
}

def get_service_status(service_name: str) -> str:
    """Queries service status via sc.exe and registry fallback."""
    reg_path = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{service_name}"
    ok, start_type = get_reg_value(reg_path, "Start")
    if ok and start_type == 4:
        return "DISABLED"

    cmd = f'sc.exe query "{service_name}"'
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
        out = proc.stdout.upper()
        if "RUNNING" in out:
            return "RUNNING"
        elif "STOPPED" in out:
            return "STOPPED"
        elif "FAILED 1060" in out or "DOES NOT EXIST" in out:
            return "NOT_FOUND"
        return "STOPPED"
    except Exception as e:
        log_debug(f"Error querying service {service_name}: {e}")
        return "UNKNOWN"

def disable_service(service_name: str) -> bool:
    """
    Stops service and sets startup type to Disabled (4) using both sc.exe
    and direct registry writes to bypass ACL locks.
    """
    log_info(f"Disabling service: {service_name}...")
    try:
        # 1. Stop service process
        subprocess.run(f'sc.exe stop "{service_name}"', shell=True, capture_output=True, timeout=10)

        # 2. Try sc config
        res = subprocess.run(f'sc.exe config "{service_name}" start=disabled', shell=True, capture_output=True, text=True, timeout=10)
        
        # 3. Direct registry guarantee: Start = 4 (Disabled)
        reg_path = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{service_name}"
        set_reg_value(reg_path, "Start", 4, winreg.REG_DWORD)

        log_success(f"Service {service_name} successfully set to Disabled.")
        return True
    except Exception as e:
        log_error(f"Exception disabling service {service_name}: {e}")
        return False

def enable_service(service_name: str, startup: str = "demand") -> bool:
    """Restores service startup type to Demand/Manual (3) or Auto (2)."""
    log_info(f"Restoring service: {service_name} (start={startup})...")
    try:
        reg_val = 3 if startup == "demand" else 2
        reg_path = f"HKLM\\SYSTEM\\CurrentControlSet\\Services\\{service_name}"
        set_reg_value(reg_path, "Start", reg_val, winreg.REG_DWORD)
        subprocess.run(f'sc.exe config "{service_name}" start={startup}', shell=True, capture_output=True, timeout=10)
        return True
    except Exception as e:
        log_error(f"Failed to enable service {service_name}: {e}")
        return False

def optimize_telemetry_services() -> Tuple[int, int]:
    """Disables all recommended bloatware and telemetry services."""
    success_count = 0
    fail_count = 0
    for s_name, info in BLOAT_SERVICES.items():
        if info["recommended_state"] == "disabled":
            ok = disable_service(s_name)
            if ok:
                success_count += 1
            else:
                fail_count += 1
    return success_count, fail_count
