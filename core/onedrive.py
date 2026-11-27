"""
WinDebloatX - OneDrive Deep Uninstaller, Safety Auditor & Reinstaller
Terminates OneDrive, inspects Files On-Demand placeholders to prevent data loss,
removes sidebar navigation pins, and provides official reinstallation routines.
"""

import ctypes
import os
import subprocess
import time
import winreg
from typing import Optional, Tuple
from core.logger import log_debug, log_error, log_info, log_success, log_warning
from core.registry import set_reg_value, delete_reg_value, restart_explorer

FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
FILE_ATTRIBUTE_OFFLINE = 0x1000

def check_onedrive_files_on_demand() -> Tuple[bool, int, str]:
    """
    Scans %USERPROFILE%\\OneDrive for cloud-only placeholder files.
    Returns (has_cloud_only_files: bool, count: int, warning_message: str).
    """
    user_profile = os.environ.get("USERPROFILE", "")
    od_path = os.path.join(user_profile, "OneDrive")
    if not os.path.isdir(od_path):
        return False, 0, "No OneDrive folder found."

    cloud_only_count = 0
    try:
        for root, dirs, files in os.walk(od_path):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    attrs = ctypes.windll.kernel32.GetFileAttributesW(fpath)
                    if attrs != -1 and (attrs & FILE_ATTRIBUTE_REPARSE_POINT or attrs & FILE_ATTRIBUTE_OFFLINE):
                        cloud_only_count += 1
                        if cloud_only_count >= 100:  # Sample threshold
                            break
                except Exception:
                    continue
            if cloud_only_count >= 100:
                break
    except Exception as e:
        log_debug(f"Error scanning OneDrive folder attributes: {e}")

    if cloud_only_count > 0:
        msg = (
            f"Detected {cloud_only_count}+ cloud-only placeholder files in '{od_path}'. "
            "Uninstalling OneDrive now will leave these files inaccessible. "
            "Please turn off 'Files On-Demand' in OneDrive settings and allow files to download first."
        )
        return True, cloud_only_count, msg

    return False, 0, "No cloud-only placeholder files detected."

def find_onedrive_uninstaller() -> Optional[str]:
    """Locates OneDriveSetup.exe uninstaller across system paths."""
    sys_root = os.environ.get("SystemRoot", "C:\\Windows")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    candidate_paths = [
        os.path.join(sys_root, "SysWOW64", "OneDriveSetup.exe"),
        os.path.join(sys_root, "System32", "OneDriveSetup.exe"),
        os.path.join(local_app_data, "Microsoft", "OneDrive", "OneDriveSetup.exe")
    ]

    od_folder = os.path.join(local_app_data, "Microsoft", "OneDrive")
    if os.path.isdir(od_folder):
        for entry in os.listdir(od_folder):
            candidate = os.path.join(od_folder, entry, "OneDriveSetup.exe")
            if os.path.isfile(candidate):
                candidate_paths.append(candidate)

    for p in candidate_paths:
        if os.path.isfile(p):
            return p
    return None

def uninstall_onedrive(force: bool = False) -> Tuple[bool, str]:
    """
    Safely terminates and uninstalls OneDrive, removes the Explorer navigation
    sidebar link, and cleans up registry run hooks.
    """
    if not force:
        has_cloud_files, count, warn_msg = check_onedrive_files_on_demand()
        if has_cloud_files:
            log_warning(f"OneDrive safety block: {warn_msg}")
            return False, warn_msg

    log_info("Beginning Microsoft OneDrive deep removal...")

    # 1. Terminate running OneDrive processes
    subprocess.run("taskkill /f /im OneDrive.exe", shell=True, capture_output=True)
    time.sleep(1)

    # 2. Locate uninstaller
    uninstaller = find_onedrive_uninstaller()
    if uninstaller:
        log_info(f"Running OneDrive uninstaller: {uninstaller} /uninstall...")
        try:
            subprocess.run(f'"{uninstaller}" /uninstall', shell=True, capture_output=True, timeout=60)
            log_info("OneDrive native uninstaller finished.")
        except Exception as e:
            log_warning(f"Error running OneDrive uninstaller: {e}")
    else:
        log_warning("OneDrive uninstaller executable not found. Proceeding with registry cleanup.")

    # 3. Remove OneDrive from File Explorer Navigation Pane (CLSID {018D5C66-4533-4307-9B53-224DE2ED1FE6})
    clsid_keys = [
        "HKCR\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}",
        "HKCR\\Wow6432Node\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}",
        "HKCU\\Software\\Classes\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}",
        "HKCU\\Software\\Classes\\Wow6432Node\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}"
    ]
    for k in clsid_keys:
        set_reg_value(k, "System.IsPinnedToNameSpaceTree", 0, winreg.REG_DWORD)

    # 4. Disable OneDrive file sync policy
    set_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive", "DisableFileSyncNGSC", 1, winreg.REG_DWORD)

    # 5. Remove Auto-start hook
    cmd_del = 'reg.exe delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "OneDrive" /f'
    subprocess.run(cmd_del, shell=True, capture_output=True)

    restart_explorer()
    msg = "Microsoft OneDrive successfully uninstalled and removed from Explorer sidebar."
    log_success(msg)
    return True, msg

def reinstall_onedrive() -> Tuple[bool, str]:
    """
    Restores OneDrive policies, re-pins to File Explorer, and invokes installation via winget
    or official Microsoft direct download.
    """
    log_info("Re-enabling OneDrive policies and initiating installation...")

    # 1. Re-enable policy
    delete_reg_value("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\OneDrive", "DisableFileSyncNGSC")

    # 2. Re-pin to Explorer
    clsid_keys = [
        "HKCR\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}",
        "HKCR\\Wow6432Node\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}",
        "HKCU\\Software\\Classes\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}",
        "HKCU\\Software\\Classes\\Wow6432Node\\CLSID\\{018D5C66-4533-4307-9B53-224DE2ED1FE6}"
    ]
    for k in clsid_keys:
        set_reg_value(k, "System.IsPinnedToNameSpaceTree", 1, winreg.REG_DWORD)

    # 3. Try winget install
    try:
        cmd = "winget install Microsoft.OneDrive --silent --accept-package-agreements --accept-source-agreements"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if proc.returncode == 0:
            restart_explorer()
            msg = "Microsoft OneDrive successfully reinstalled via winget."
            log_success(msg)
            return True, msg
    except Exception as e:
        log_debug(f"Winget install attempt notice: {e}")

    # Fallback: Launch official Microsoft download installer URL
    url = "https://go.microsoft.com/fwlink/p/?LinkId=248256"
    subprocess.Popen(f'start "" "{url}"', shell=True)
    restart_explorer()
    msg = "Opened official Microsoft OneDrive installer download."
    log_info(msg)
    return True, msg

def is_onedrive_installed() -> bool:
    """Checks if OneDrive is installed or active."""
    uninstaller = find_onedrive_uninstaller()
    if uninstaller:
        return True
    proc = subprocess.run("tasklist /fi \"imagename eq OneDrive.exe\"", shell=True, capture_output=True, text=True)
    return "OneDrive.exe" in proc.stdout
