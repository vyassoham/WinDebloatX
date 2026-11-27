"""
WinDebloatX - Windows Privacy & Telemetry Hardening Engine
Configures registry and policies to disable Windows telemetry, ad tracking, activity history, and cloud web searches.
Includes Windows edition awareness (Home/Pro vs Enterprise) and updated tweaks for Windows 11 24H2.
"""

import winreg
from typing import Dict, List, Tuple
from core.logger import log_debug, log_error, log_info, log_success
from core.registry import delete_reg_value, get_reg_value, set_reg_value

def get_windows_edition_info() -> Dict[str, any]:
    """
    Queries OS Edition from the registry.
    Returns edition details and whether GPO telemetry level 0 is officially supported.
    """
    path = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion"
    _, edition_id = get_reg_value(path, "EditionID")
    _, product_name = get_reg_value(path, "ProductName")

    eid = str(edition_id or "").lower()
    # Level 0 is officially respected only on Enterprise, Education, IoT, or Server
    level_0_supported = any(term in eid for term in ["enterprise", "education", "iot", "server"])

    return {
        "edition_id": edition_id or "Unknown",
        "product_name": product_name or "Windows",
        "level_0_supported": level_0_supported,
        "note": "Enterprise policy active" if level_0_supported else "Home/Pro: DiagTrack service disable is required because OS kernel coerces GPO 0 to 1"
    }

PRIVACY_TWEAKS = {
    "telemetry": {
        "title": "Windows Telemetry & Diagnostic Data",
        "description": "Sets diagnostic data submission level to Security / Minimal (Level 0).",
        "entries": [
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "AllowTelemetry", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "MaxTelemetryAllowed", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\DataCollection", "AllowTelemetry", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "LimitEnhancedDiagnosticDataWindowsAnalytics", 0, winreg.REG_DWORD),
        ],
        "default_val": 1
    },
    "bing_start_search": {
        "title": "Bing & Cloud Search in Start Menu",
        "description": "Disables web results and Bing recommendations when searching in the Start menu.",
        "entries": [
            ("HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions", 1, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search", "BingSearchEnabled", 0, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Search", "CortanaConsent", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "AllowCloudSearch", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Windows Search", "ConnectedSearchUseWeb", 0, winreg.REG_DWORD),
        ],
        "default_val": 0
    },
    "settings_ads": {
        "title": "Settings App Ads & Recommendations",
        "description": "Stops Microsoft from displaying recommended apps, tips, and promotional banners in Windows Settings.",
        "entries": [
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SubscribedContent-338388Enabled", 0, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SubscribedContent-338389Enabled", 0, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SubscribedContent-353694Enabled", 0, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SubscribedContent-353696Enabled", 0, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SystemPaneSuggestionsEnabled", 0, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager", "SoftLandingEnabled", 0, winreg.REG_DWORD),
        ],
        "default_val": 1
    },
    "advertising_id": {
        "title": "Windows Advertising ID",
        "description": "Prevents apps from using the advertising ID for relevant cross-app experiences.",
        "entries": [
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\AdvertisingInfo", "Enabled", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\AdvertisingInfo", "DisabledByGroupPolicy", 1, winreg.REG_DWORD),
        ],
        "default_val": 1
    },
    "activity_history": {
        "title": "Activity History & Timeline",
        "description": "Stops Windows from collecting activities and publishing them to the cloud.",
        "entries": [
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "EnableActivityFeed", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "PublishUserActivities", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\System", "UploadUserActivities", 0, winreg.REG_DWORD),
        ],
        "default_val": 1
    },
    "tailored_experiences": {
        "title": "Tailored Experiences & Diagnostic Tips",
        "description": "Prevents Microsoft from using diagnostic data for personalized ads and recommendations.",
        "entries": [
            ("HKCU\\Software\\Policies\\Microsoft\\Windows\\CloudContent", "DisableTailoredExperiencesWithDiagnosticData", 1, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 0, winreg.REG_DWORD),
        ],
        "default_val": 1
    },
    "feedback_frequency": {
        "title": "Windows Feedback Frequency",
        "description": "Sets Windows feedback prompt frequency to Never.",
        "entries": [
            ("HKCU\\Software\\Microsoft\\Siuf\\Rules", "NumberOfSIFInPeriod", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DataCollection", "DoNotShowFeedbackNotifications", 1, winreg.REG_DWORD),
        ],
        "default_val": 1
    },
    "typing_inking_collection": {
        "title": "Inking & Typing Personalization",
        "description": "Stops sending typing keystrokes and handwriting data to Microsoft for dictionary learning.",
        "entries": [
            ("HKCU\\Software\\Microsoft\\InputPersonalization", "RestrictImplicitInkCollection", 1, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\InputPersonalization", "RestrictImplicitTextCollection", 1, winreg.REG_DWORD),
            ("HKCU\\Software\\Microsoft\\InputPersonalization\\TrainedDataStore", "HarvestContacts", 0, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\TabletPC", "PreventHandwritingDataSharing", 1, winreg.REG_DWORD),
        ],
        "default_val": 0
    },
    "location_tracking": {
        "title": "Windows Location Tracking",
        "description": "Disables OS-level location tracking and sensor permissions.",
        "entries": [
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors", "DisableLocation", 1, winreg.REG_DWORD),
            ("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\LocationAndSensors", "DisableLocationScripting", 1, winreg.REG_DWORD),
        ],
        "default_val": 0
    }
}

def get_tweak_status(tweak_key: str) -> bool:
    """Returns True if the privacy tweak is active (applied), False otherwise."""
    tweak = PRIVACY_TWEAKS.get(tweak_key)
    if not tweak:
        return False
    path, name, expected_val, _ = tweak["entries"][0]
    ok, val = get_reg_value(path, name)
    return ok and val == expected_val

def apply_privacy_tweak(tweak_key: str) -> Tuple[bool, str]:
    """Applies a privacy tweak by key name."""
    tweak = PRIVACY_TWEAKS.get(tweak_key)
    if not tweak:
        return False, f"Unknown tweak {tweak_key}"

    log_info(f"Applying privacy tweak: {tweak['title']}...")
    all_ok = True
    for path, name, val, vtype in tweak["entries"]:
        ok = set_reg_value(path, name, val, vtype, create_backup=True)
        if not ok:
            all_ok = False

    if all_ok:
        msg = f"Successfully applied {tweak['title']}."
        log_success(msg)
        return True, msg
    else:
        msg = f"Some entries failed for {tweak['title']}."
        log_error(msg)
        return False, msg

def revert_privacy_tweak(tweak_key: str) -> Tuple[bool, str]:
    """Reverts a privacy tweak to default Windows behavior."""
    tweak = PRIVACY_TWEAKS.get(tweak_key)
    if not tweak:
        return False, f"Unknown tweak {tweak_key}"

    log_info(f"Reverting privacy tweak: {tweak['title']}...")
    for path, name, _, _ in tweak["entries"]:
        delete_reg_value(path, name)

    msg = f"Reverted {tweak['title']} to defaults."
    log_success(msg)
    return True, msg

def apply_all_privacy_tweaks() -> int:
    """Applies all privacy hardening tweaks."""
    success_count = 0
    for key in PRIVACY_TWEAKS:
        ok, _ = apply_privacy_tweak(key)
        if ok:
            success_count += 1
    return success_count
