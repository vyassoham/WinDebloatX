"""
WinDebloatX - Registry Manipulation and Safety Engine
Provides type-safe, resilient registry modification, backup, and restore capabilities.
"""

import os
import subprocess
import time
import winreg
from typing import Any, Optional, Tuple, Union
from core.logger import log_debug, log_error, log_info, log_success, log_warning

BACKUP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "WinDebloatX", "Backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

HKEY_MAP = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
    "HKCR": winreg.HKEY_CLASSES_ROOT,
    "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
    "HKU": winreg.HKEY_USERS,
    "HKEY_USERS": winreg.HKEY_USERS,
}

def parse_key_path(full_path: str) -> Tuple[int, str]:
    """Splits 'HKCU\\Software\\Policies' into (HKEY_CURRENT_USER, 'Software\\Policies')."""
    normalized = full_path.replace("/", "\\")
    parts = normalized.split("\\", 1)
    root_str = parts[0].upper()
    sub_key = parts[1] if len(parts) > 1 else ""

    if root_str not in HKEY_MAP:
        raise ValueError(f"Unknown registry root: {root_str}")
    return HKEY_MAP[root_str], sub_key

def backup_registry_key(key_path: str, backup_name: str) -> bool:
    """Exports a registry key to a .reg file for instant recovery."""
    safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in backup_name)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"{safe_name}_{timestamp}.reg")
    
    cmd = f'reg.exe export "{key_path}" "{backup_file}" /y'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            log_debug(f"Backed up registry key {key_path} -> {backup_file}")
            return True
    except Exception as e:
        log_debug(f"Backup notice for {key_path}: {e}")
    return False

def get_reg_value(full_path: str, value_name: str) -> Tuple[bool, Any]:
    """
    Reads a registry value.
    Returns (True, value) if found, (False, None) if not found or on error.
    """
    try:
        root, sub_key = parse_key_path(full_path)
        with winreg.OpenKey(root, sub_key, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            val, _ = winreg.QueryValueEx(key, value_name)
            return True, val
    except FileNotFoundError:
        return False, None
    except Exception as e:
        log_debug(f"Read error at {full_path}\\{value_name}: {e}")
        return False, None

def set_reg_value(
    full_path: str,
    value_name: str,
    value: Union[int, str, bytes],
    value_type: int = winreg.REG_DWORD,
    create_backup: bool = False
) -> bool:
    """
    Sets or creates a registry value, creating parent keys if necessary.
    """
    if create_backup:
        backup_registry_key(full_path, f"{value_name}_before_mod")

    try:
        root, sub_key = parse_key_path(full_path)
        with winreg.CreateKeyEx(root, sub_key, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
            winreg.SetValueEx(key, value_name, 0, value_type, value)
            log_debug(f"Registry Set: {full_path} [{value_name}] = {value}")
            return True
    except PermissionError:
        log_error(f"Permission denied modifying {full_path}. Run as Administrator.")
        return False
    except Exception as e:
        log_error(f"Failed to set {full_path}\\{value_name}: {e}")
        return False

def delete_reg_value(full_path: str, value_name: str) -> bool:
    """Deletes a specific value name from a key."""
    try:
        root, sub_key = parse_key_path(full_path)
        with winreg.OpenKey(root, sub_key, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as key:
            winreg.DeleteValue(key, value_name)
            log_debug(f"Registry Deleted Value: {full_path}\\{value_name}")
            return True
    except FileNotFoundError:
        return True  # Already gone
    except Exception as e:
        log_debug(f"Could not delete value {full_path}\\{value_name}: {e}")
        return False

def delete_reg_key_tree(full_path: str) -> bool:
    """Recursively deletes a registry key and all subkeys."""
    cmd = f'reg.exe delete "{full_path}" /f'
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return res.returncode == 0
    except Exception as e:
        log_debug(f"Could not delete key tree {full_path}: {e}")
        return False

def restart_explorer():
    """Restarts Windows Explorer to apply taskbar, context menu, and shell changes immediately."""
    log_info("Restarting Windows Explorer to apply changes...")
    try:
        subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
        time.sleep(1)
        subprocess.Popen("explorer.exe")
        log_success("Windows Explorer restarted successfully.")
        return True
    except Exception as e:
        log_error(f"Failed to restart explorer.exe: {e}")
        return False
