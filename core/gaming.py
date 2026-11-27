"""
WinDebloatX - Gaming & Latency Optimization Subsystem
Disables background game DVR recording, micro-stutter hooks, mouse acceleration,
and provides granular MMCSS network throttling profiles with balanced audio preservation.
"""

import subprocess
import winreg
from typing import Dict, Tuple
from core.logger import log_debug, log_error, log_info, log_success
from core.registry import get_reg_value, set_reg_value

def disable_gamedvr() -> Tuple[bool, str]:
    """
    Disables Windows GameDVR background video recording and capture hooks.
    This eliminates FPS drops, input lag, and micro-stutters during gaming.
    """
    log_info("Optimizing GameDVR & background capture settings...")
    set_reg_value("HKCU\\System\\GameConfigStore", "GameDVR_Enabled", 0, winreg.REG_DWORD)
    set_reg_value("HKCU\\System\\GameConfigStore", "GameDVR_FSEBehaviorMode", 2, winreg.REG_DWORD)
    set_reg_value("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR", "AppCaptureEnabled", 0, winreg.REG_DWORD)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR", "AllowGameDVR", 0, winreg.REG_DWORD)
    
    msg = "GameDVR background capture disabled. Input latency and FPS stutters reduced."
    log_success(msg)
    return True, msg

def enable_gamedvr() -> Tuple[bool, str]:
    """Re-enables GameDVR background capture."""
    log_info("Restoring GameDVR default settings...")
    set_reg_value("HKCU\\System\\GameConfigStore", "GameDVR_Enabled", 1, winreg.REG_DWORD)
    set_reg_value("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR", "AppCaptureEnabled", 1, winreg.REG_DWORD)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR", "AllowGameDVR", 1, winreg.REG_DWORD)
    msg = "GameDVR settings restored to default."
    log_success(msg)
    return True, msg

def is_gamedvr_disabled() -> bool:
    """Checks if GameDVR background recording is currently disabled."""
    ok, val = get_reg_value("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR", "AppCaptureEnabled")
    return ok and val == 0

def disable_mouse_acceleration() -> Tuple[bool, str]:
    """
    Disables Windows Enhanced Pointer Precision (mouse acceleration)
    to provide true 1:1 raw mouse tracking for competitive gaming.
    """
    log_info("Disabling mouse acceleration (Enhanced Pointer Precision)...")
    set_reg_value("HKCU\\Control Panel\\Mouse", "MouseSpeed", "0", winreg.REG_SZ)
    set_reg_value("HKCU\\Control Panel\\Mouse", "MouseThreshold1", "0", winreg.REG_SZ)
    set_reg_value("HKCU\\Control Panel\\Mouse", "MouseThreshold2", "0", winreg.REG_SZ)
    msg = "Mouse acceleration disabled. True 1:1 raw input enabled."
    log_success(msg)
    return True, msg

def enable_mouse_acceleration() -> Tuple[bool, str]:
    """Restores default Windows mouse acceleration."""
    log_info("Restoring default mouse acceleration...")
    set_reg_value("HKCU\\Control Panel\\Mouse", "MouseSpeed", "1", winreg.REG_SZ)
    set_reg_value("HKCU\\Control Panel\\Mouse", "MouseThreshold1", "6", winreg.REG_SZ)
    set_reg_value("HKCU\\Control Panel\\Mouse", "MouseThreshold2", "10", winreg.REG_SZ)
    msg = "Default mouse acceleration restored."
    log_success(msg)
    return True, msg

def optimize_network_and_responsiveness(profile: str = "balanced") -> Tuple[bool, str]:
    """
    Configures Multimedia Class Scheduler Service (MMCSS).
    Profiles:
    - 'balanced' (Recommended): NetworkThrottlingIndex=0xFFFFFFFF, SystemResponsiveness=10.
      Eliminates network latency while preserving 10% CPU priority for Discord/Spotify voice audio.
    - 'extreme': NetworkThrottlingIndex=0xFFFFFFFF, SystemResponsiveness=0.
      100% CPU priority dedicated to foreground games.
    """
    path = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile"
    if profile == "extreme":
        resp_val = 0
        desc = "Extreme (0% reserved background priority)"
    else:
        resp_val = 10
        desc = "Balanced (10% reserved for Discord/voice streaming)"

    log_info(f"Setting MMCSS responsiveness profile: {desc}...")
    set_reg_value(path, "NetworkThrottlingIndex", 0xFFFFFFFF, winreg.REG_DWORD)
    set_reg_value(path, "SystemResponsiveness", resp_val, winreg.REG_DWORD)
    msg = f"MMCSS optimized: Network throttling disabled, responsiveness set to {desc}."
    log_success(msg)
    return True, msg

def revert_network_and_responsiveness() -> Tuple[bool, str]:
    """Restores Windows default MMCSS scheduling."""
    log_info("Restoring Windows default MMCSS values...")
    path = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile"
    set_reg_value(path, "NetworkThrottlingIndex", 10, winreg.REG_DWORD)
    set_reg_value(path, "SystemResponsiveness", 20, winreg.REG_DWORD)
    msg = "MMCSS network throttling and responsiveness restored to Windows defaults (10, 20)."
    log_success(msg)
    return True, msg

def get_mmcss_status() -> Dict[str, any]:
    """Queries current MMCSS registry values."""
    path = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile"
    _, net_val = get_reg_value(path, "NetworkThrottlingIndex")
    _, resp_val = get_reg_value(path, "SystemResponsiveness")
    return {
        "network_throttling_index": net_val,
        "system_responsiveness": resp_val,
        "is_optimized": net_val == 0xFFFFFFFF
    }

def unlock_ultimate_performance_plan() -> Tuple[bool, str]:
    """Unlocks Windows 'Ultimate Performance' power plan scheme via powercfg."""
    log_info("Unlocking Windows Ultimate Performance Power Plan...")
    cmd = "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61"
    try:
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            msg = "Ultimate Performance power plan scheme unlocked in Windows Power Options."
            log_success(msg)
            return True, msg
        else:
            return False, proc.stderr.strip()
    except Exception as e:
        return False, str(e)
