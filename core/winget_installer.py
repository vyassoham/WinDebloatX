"""
WinDebloatX - Software Package Hub (Winget Integration Engine)
Provides automated, silent batch installation of essential developer tools,
browsers, utilities, and runtimes via native Windows Package Manager (winget).
"""

import subprocess
from typing import Callable, Dict, List, Optional, Tuple
from core.logger import log_debug, log_error, log_info, log_success, log_warning

SOFTWARE_CATALOG: Dict[str, Dict[str, str]] = {
    # Web Browsers
    "Brave.Brave": {
        "name": "Brave Browser",
        "category": "Web Browsers",
        "description": "Privacy-focused browser blocking trackers and ads by default."
    },
    "Google.Chrome": {
        "name": "Google Chrome",
        "category": "Web Browsers",
        "description": "Fast, ubiquitous web browser by Google."
    },
    "Mozilla.Firefox": {
        "name": "Mozilla Firefox",
        "category": "Web Browsers",
        "description": "Open-source, highly customizable privacy browser."
    },
    "LibreWolf.LibreWolf": {
        "name": "LibreWolf",
        "category": "Web Browsers",
        "description": "Hardened, telemetry-free fork of Firefox."
    },
    # Essential Utilities
    "7zip.7zip": {
        "name": "7-Zip",
        "category": "Utilities",
        "description": "High-compression file archiver."
    },
    "M2Team.NanaZip": {
        "name": "NanaZip",
        "category": "Utilities",
        "description": "Modern 7-Zip fork integrated with Windows 11 context menus."
    },
    "Microsoft.PowerToys": {
        "name": "Microsoft PowerToys",
        "category": "Utilities",
        "description": "Productivity utilities including FancyZones and PowerToys Run."
    },
    "voidtools.Everything": {
        "name": "Everything Search",
        "category": "Utilities",
        "description": "Instant, zero-lag filename search utility for Windows."
    },
    "BleachBit.BleachBit": {
        "name": "BleachBit",
        "category": "Utilities",
        "description": "Open-source privacy cleaner and disk space shredder."
    },
    # Media & Creative
    "VideoLAN.VLC": {
        "name": "VLC Media Player",
        "category": "Media",
        "description": "Universal open-source media player supporting all codecs."
    },
    "OBSProject.OBSStudio": {
        "name": "OBS Studio",
        "category": "Media",
        "description": "Free, open-source video recording and live streaming suite."
    },
    "HandBrake.HandBrake": {
        "name": "HandBrake",
        "category": "Media",
        "description": "Open-source video transcoder and compressor."
    },
    # Developer Stack
    "Microsoft.VisualStudioCode": {
        "name": "Visual Studio Code",
        "category": "Developer Tools",
        "description": "Code editor with rich ecosystem of extensions."
    },
    "Git.Git": {
        "name": "Git for Windows",
        "category": "Developer Tools",
        "description": "Distributed version control system."
    },
    "Microsoft.WindowsTerminal": {
        "name": "Windows Terminal",
        "category": "Developer Tools",
        "description": "Modern, tabbed command-line terminal for PowerShell, CMD & WSL."
    },
    "OpenJS.NodeJS.LTS": {
        "name": "Node.js (LTS)",
        "category": "Developer Tools",
        "description": "JavaScript runtime environment."
    },
    "Python.Python.3.12": {
        "name": "Python 3.12",
        "category": "Developer Tools",
        "description": "Modern Python programming language runtime."
    },
    # Gaming & Social
    "Valve.Steam": {
        "name": "Steam",
        "category": "Gaming",
        "description": "Digital PC game distribution platform."
    },
    "EpicGames.EpicGamesLauncher": {
        "name": "Epic Games Launcher",
        "category": "Gaming",
        "description": "Store and launcher for Unreal Engine and Epic games."
    },
    "Discord.Discord": {
        "name": "Discord",
        "category": "Gaming",
        "description": "All-in-one voice and text chat for gamers and communities."
    }
}

def is_winget_available() -> bool:
    """Checks whether the winget CLI tool is installed and responsive."""
    try:
        proc = subprocess.run(["winget", "--version"], capture_output=True, text=True, timeout=5)
        return proc.returncode == 0
    except Exception:
        return False

def install_single_package(package_id: str) -> Tuple[bool, str]:
    """
    Installs a single package using winget with silent/unattended flags.
    """
    if not is_winget_available():
        return False, "Windows Package Manager (winget) is not installed."

    info = SOFTWARE_CATALOG.get(package_id, {})
    display_name = info.get("name", package_id)
    log_info(f"Installing {display_name} via winget...")

    cmd = [
        "winget", "install",
        "--id", package_id,
        "--exact",
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity"
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        out = (proc.stdout or "") + (proc.stderr or "")
        
        # Winget exit codes: 0 = success, -1978335189 (0x8A15002B) = already installed
        if proc.returncode == 0 or "Successfully installed" in out or "already installed" in out.lower():
            msg = f"Successfully installed {display_name}."
            log_success(msg)
            return True, msg
        else:
            msg = f"Failed to install {display_name}: {out.strip()}"
            log_error(msg)
            return False, msg
    except subprocess.TimeoutExpired:
        msg = f"Installation of {display_name} timed out."
        log_error(msg)
        return False, msg
    except Exception as e:
        msg = f"Exception installing {display_name}: {e}"
        log_error(msg)
        return False, msg

def batch_install_software(
    package_ids: List[str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[int, int]:
    """
    Installs a list of selected packages with progress reporting.
    Returns (success_count, fail_count).
    """
    if not is_winget_available():
        log_error("Winget is required for Software Hub operations.")
        return 0, len(package_ids)

    total = len(package_ids)
    success_count = 0
    fail_count = 0

    log_info(f"Starting batch installation of {total} packages...")
    for idx, pkg_id in enumerate(package_ids, start=1):
        info = SOFTWARE_CATALOG.get(pkg_id, {})
        dname = info.get("name", pkg_id)
        if progress_callback:
            progress_callback(idx, total, f"Installing {dname} ({idx}/{total})...")

        ok, _ = install_single_package(pkg_id)
        if ok:
            success_count += 1
        else:
            fail_count += 1

    log_success(f"Batch software installation complete: {success_count} succeeded, {fail_count} failed.")
    return success_count, fail_count
