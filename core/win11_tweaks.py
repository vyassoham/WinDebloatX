"""
WinDebloatX - Windows 11 Specific Tweaks & Modern AI Bloatware Engine
Manages modern Windows 11 features: Classic Context Menu, Windows Copilot, Windows Recall, Widgets, and Edge.
"""

import winreg
from typing import Dict, Tuple
from core.logger import log_debug, log_error, log_info, log_success
from core.registry import (
    delete_reg_key_tree,
    delete_reg_value,
    get_reg_value,
    restart_explorer,
    set_reg_value
)

WIN11_TWEAKS = {
    "classic_context_menu": {
        "title": "Windows 11 Classic Context Menu",
        "description": "Restores the responsive, full right-click context menu (bypasses 'Show more options').",
        "check": lambda: get_reg_value(
            "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32", ""
        )[0]
    },
    "disable_copilot": {
        "title": "Windows Copilot AI",
        "description": "Disables the built-in Windows Copilot sidebar and taskbar integration.",
        "check": lambda: get_reg_value(
            "HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot"
        )[1] == 1
    },
    "disable_recall": {
        "title": "Windows Recall (AI Screen Snapshots)",
        "description": "Disables Windows Recall AI background screenshot tracking and data analysis.",
        "check": lambda: get_reg_value(
            "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis"
        )[1] == 1
    },
    "disable_widgets": {
        "title": "Taskbar Widgets & News Feed",
        "description": "Disables Windows 11 Widgets board / News and Interests icon from the taskbar.",
        "check": lambda: get_reg_value(
            "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarDa"
        )[1] == 0
    },
    "disable_edge_bloat": {
        "title": "Edge Startup Boost & Background Pre-launch",
        "description": "Stops Microsoft Edge from running silent background processes and pre-launching on boot.",
        "check": lambda: get_reg_value(
            "HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge", "StartupBoostEnabled"
        )[1] == 0
    }
}

def set_classic_context_menu(enable_classic: bool = True) -> Tuple[bool, str]:
    """Enables or disables the Windows 11 Classic Context Menu."""
    clsid_path = "HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32"
    if enable_classic:
        log_info("Enabling Windows 11 Classic Context Menu...")
        ok = set_reg_value(clsid_path, "", "", winreg.REG_SZ)
        if ok:
            restart_explorer()
            msg = "Classic Context Menu enabled successfully."
            log_success(msg)
            return True, msg
        return False, "Failed to write CLSID key."
    else:
        log_info("Restoring Windows 11 Modern Context Menu...")
        delete_reg_key_tree("HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}")
        restart_explorer()
        msg = "Modern Context Menu restored."
        log_success(msg)
        return True, msg

def set_copilot_state(disable: bool = True) -> Tuple[bool, str]:
    """Enables or disables Windows Copilot."""
    val = 1 if disable else 0
    log_info(f"{'Disabling' if disable else 'Enabling'} Windows Copilot...")
    set_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", val)
    set_reg_value("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "ShowCopilotButton", 0 if disable else 1)
    
    if disable:
        msg = "Windows Copilot has been disabled."
        log_success(msg)
    else:
        delete_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot")
        delete_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot")
        msg = "Windows Copilot has been re-enabled."
        log_success(msg)
    return True, msg

def set_recall_state(disable: bool = True) -> Tuple[bool, str]:
    """Enables or disables Windows Recall AI data analysis and screen tracking."""
    val = 1 if disable else 0
    log_info(f"{'Disabling' if disable else 'Enabling'} Windows Recall AI Snapshots...")
    set_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis", val)
    set_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsAI", "TurnOffRecall", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "TurnOffRecall", val)
    
    if disable:
        msg = "Windows Recall AI Snapshots disabled."
        log_success(msg)
    else:
        delete_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis")
        delete_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "DisableAIDataAnalysis")
        delete_reg_value("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsAI", "TurnOffRecall")
        delete_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsAI", "TurnOffRecall")
        msg = "Windows Recall AI restored to system defaults."
        log_success(msg)
    return True, msg

def set_widgets_state(disable: bool = True) -> Tuple[bool, str]:
    """Enables or disables Taskbar Widgets."""
    log_info(f"{'Disabling' if disable else 'Enabling'} Windows Widgets...")
    set_reg_value("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced", "TaskbarDa", 0 if disable else 1)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Dsh", "AllowNewsAndInterests", 0 if disable else 1)
    msg = f"Windows Widgets {'disabled' if disable else 'enabled'}."
    log_success(msg)
    return True, msg

def set_edge_bloat_state(disable: bool = True) -> Tuple[bool, str]:
    """Disables Edge startup boost, background extension execution, and Copilot sidebar."""
    val = 0 if disable else 1
    log_info(f"{'Disabling' if disable else 'Enabling'} Microsoft Edge background bloat & Copilot...")
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge", "StartupBoostEnabled", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge", "BackgroundModeEnabled", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge", "HubsSidebarEnabled", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge", "ShowCopilotButton", val)
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Edge", "DiscoverPageContextEnabled", val)
    msg = f"Edge background bloat {'disabled' if disable else 'restored'}."
    log_success(msg)
    return True, msg

def toggle_win11_tweak(tweak_key: str, activate: bool) -> Tuple[bool, str]:
    """Dispatches toggle for a named Win11 tweak."""
    if tweak_key == "classic_context_menu":
        return set_classic_context_menu(activate)
    elif tweak_key == "disable_copilot":
        return set_copilot_state(activate)
    elif tweak_key == "disable_recall":
        return set_recall_state(activate)
    elif tweak_key == "disable_widgets":
        return set_widgets_state(activate)
    elif tweak_key == "disable_edge_bloat":
        return set_edge_bloat_state(activate)
    return False, f"Unknown tweak: {tweak_key}"
