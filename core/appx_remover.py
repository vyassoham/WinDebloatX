"""
WinDebloatX - High-Performance UWP & Provisioned Appx Bloatware Removal Engine
Scans and uninstalls modern Windows 10 & 11 bloatware, preinstalled partner apps, and provisioned packages.
Includes process pre-termination, multi-user lock handling (0x80073D02), and native DISM fallbacks.
"""

import json
import subprocess
from typing import Callable, Dict, List, Optional, Tuple
from core.logger import log_debug, log_error, log_info, log_success, log_warning

BLOATWARE_CATALOG: Dict[str, Dict[str, any]] = {
    # Sponsored & OEM Promo Apps
    "Microsoft.BingNews": {
        "name": "Microsoft News",
        "category": "MSN & Feed",
        "default_remove": True,
        "description": "MSN News app and taskbar feed promos.",
        "store_id": "9WZDNCRFHVFW",
        "processes": []
    },
    "Microsoft.BingWeather": {
        "name": "MSN Weather",
        "category": "MSN & Feed",
        "default_remove": True,
        "description": "MSN Weather app with embedded ads.",
        "store_id": "9WZDNCRFJ3Q2",
        "processes": []
    },
    "Microsoft.BingFinance": {
        "name": "MSN Money / Finance",
        "category": "MSN & Feed",
        "default_remove": True,
        "description": "Stock tracking app with MSN news feeds.",
        "store_id": "9WZDNCRFHV4V",
        "processes": []
    },
    "Microsoft.BingSports": {
        "name": "MSN Sports",
        "category": "MSN & Feed",
        "default_remove": True,
        "description": "Sports scores and MSN feeds.",
        "store_id": "9WZDNCRFHVH4",
        "processes": []
    },
    "Microsoft.Getstarted": {
        "name": "Tips / Get Started",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Windows tips popups and feature recommendations.",
        "store_id": "9WZDNCRFJBD8",
        "processes": []
    },
    "Microsoft.GetHelp": {
        "name": "Get Help",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Microsoft support chatbot app.",
        "store_id": "9PKDZBMV1H38",
        "processes": []
    },
    "Microsoft.WindowsFeedbackHub": {
        "name": "Feedback Hub",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Diagnostic and feedback submission tool.",
        "store_id": "9NBLGGH4R32N",
        "processes": []
    },
    "Microsoft.MicrosoftSolitaireCollection": {
        "name": "Microsoft Solitaire Collection",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Ad-supported Solitaire casual game.",
        "store_id": "9WZDNCRFHWD2",
        "processes": ["Solitaire.exe"]
    },
    "Microsoft.MicrosoftOfficeHub": {
        "name": "Office (Microsoft 365 Promos)",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Promo launcher pushing Microsoft 365 subscriptions.",
        "store_id": "9WZDNCRD29V9",
        "processes": []
    },
    "Microsoft.YourPhone": {
        "name": "Phone Link",
        "category": "Consumer Promos",
        "default_remove": False,
        "description": "Syncs phone notifications, SMS, and calls.",
        "store_id": "9NMPJ99VJBWV",
        "processes": ["PhoneExperienceHost.exe", "YourPhone.exe"]
    },
    "Microsoft.People": {
        "name": "Windows People",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Deprecated Windows People contact manager.",
        "store_id": "9NBLGGH10PG8",
        "processes": ["PeopleApp.exe"]
    },
    "Microsoft.WindowsMaps": {
        "name": "Windows Maps",
        "category": "Consumer Promos",
        "default_remove": True,
        "description": "Built-in offline maps application.",
        "store_id": "9WZDNCRFJB2Z",
        "processes": ["Maps.exe"]
    },
    # Modern Windows 11 Preinstalled Bloat
    "Clipchamp.Clipchamp": {
        "name": "Clipchamp Video Editor",
        "category": "Modern Win11 Bloat",
        "default_remove": True,
        "description": "Freemium cloud-based video editing tool.",
        "store_id": "9P1J8S7CCWWT",
        "processes": ["Clipchamp.exe"]
    },
    "Microsoft.549981C3F5F10": {
        "name": "Cortana",
        "category": "Modern Win11 Bloat",
        "default_remove": True,
        "description": "Deprecated Cortana digital voice assistant.",
        "store_id": "9NBLGGH4VS18",
        "processes": ["Cortana.exe"]
    },
    "Microsoft.Windows.DevHome": {
        "name": "Dev Home",
        "category": "Modern Win11 Bloat",
        "default_remove": True,
        "description": "Developer dashboard for Git/GitHub and machine configuration.",
        "store_id": "9N8G5RF19X07",
        "processes": []
    },
    "Microsoft.PowerAutomateDesktop": {
        "name": "Power Automate Desktop",
        "category": "Modern Win11 Bloat",
        "default_remove": True,
        "description": "RPA workflow automation software.",
        "store_id": "9NFTCH6J7FHV",
        "processes": ["PAD.Console.Host.exe"]
    },
    "Microsoft.OutlookForWindows": {
        "name": "Outlook for Windows (New Web)",
        "category": "Modern Win11 Bloat",
        "default_remove": False,
        "description": "New web-based Outlook email client replacing Mail & Calendar.",
        "store_id": "9NRXDX20KLS3",
        "processes": ["olk.exe"]
    },
    "MicrosoftCorporationII.MicrosoftFamily": {
        "name": "Microsoft Family Safety",
        "category": "Modern Win11 Bloat",
        "default_remove": True,
        "description": "Parental monitoring and screen time management.",
        "store_id": "9NBLGGH51515",
        "processes": []
    },
    "MicrosoftCorporationII.QuickAssist": {
        "name": "Quick Assist",
        "category": "Modern Win11 Bloat",
        "default_remove": False,
        "description": "Remote desktop screen sharing tool.",
        "store_id": "9P7BP5VNWKX5",
        "processes": ["quickassist.exe"]
    },
    "Microsoft.Todos": {
        "name": "Microsoft To Do",
        "category": "Modern Win11 Bloat",
        "default_remove": False,
        "description": "Task management and to-do list app.",
        "store_id": "9NBLGGH5R558",
        "processes": ["Todo.exe"]
    },
    # 3D & Mixed Reality
    "Microsoft.Microsoft3DViewer": {
        "name": "3D Viewer",
        "category": "Legacy 3D Apps",
        "default_remove": True,
        "description": "3D model viewing tool.",
        "store_id": "9NBLGGH42THS",
        "processes": []
    },
    "Microsoft.Print3D": {
        "name": "Print 3D",
        "category": "Legacy 3D Apps",
        "default_remove": True,
        "description": "3D printer prep tool.",
        "store_id": "9NBLGGH513FP",
        "processes": []
    },
    "Microsoft.MixedReality.Portal": {
        "name": "Mixed Reality Portal",
        "category": "Legacy 3D Apps",
        "default_remove": True,
        "description": "VR / Mixed reality headset environment.",
        "store_id": "9NBLGGH53790",
        "processes": []
    },
    # Media & Communications
    "Microsoft.ZuneMusic": {
        "name": "Groove Music / Media Player",
        "category": "Media",
        "default_remove": False,
        "description": "Default modern Windows media player.",
        "store_id": "9WZDNCRFJ3PT",
        "processes": ["Music.UI.exe"]
    },
    "Microsoft.ZuneVideo": {
        "name": "Films & TV",
        "category": "Media",
        "default_remove": True,
        "description": "Legacy video rental and playback app.",
        "store_id": "9WZDNCRFJ3P2",
        "processes": ["Video.UI.exe"]
    },
    "Microsoft.SkypeApp": {
        "name": "Skype",
        "category": "Communications",
        "default_remove": True,
        "description": "Preinstalled Skype client.",
        "store_id": "9WZDNCRFJ364",
        "processes": ["SkypeApp.exe", "SkypeBackgroundHost.exe"]
    },
    "microsoft.windowscommunicationsapps": {
        "name": "Mail and Calendar",
        "category": "Communications",
        "default_remove": True,
        "description": "Legacy UWP Mail and Calendar client.",
        "store_id": "9WZDNCRFHVQM",
        "processes": ["HxTsr.exe", "HxOutlook.exe"]
    },
    # Third-Party Sponsored OEM Stubs
    "SpotifyAB.SpotifyMusic": {
        "name": "Spotify",
        "category": "Sponsored Third-Party",
        "default_remove": True,
        "description": "Preinstalled Spotify music stub.",
        "store_id": "9NCBCSZSJRSB",
        "processes": ["Spotify.exe"]
    },
    "BytedancePte.Ltd.TikTok": {
        "name": "TikTok",
        "category": "Sponsored Third-Party",
        "default_remove": True,
        "description": "Preinstalled TikTok social web wrapper.",
        "store_id": "9PKMS19BS320",
        "processes": []
    },
    "Disney.37853FC22B2CE": {
        "name": "Disney+",
        "category": "Sponsored Third-Party",
        "default_remove": True,
        "description": "Preinstalled Disney+ streaming app.",
        "store_id": "9NXQXX3CL2NZ",
        "processes": []
    },
    # Xbox Ecosystem (Selective)
    "Microsoft.XboxApp": {
        "name": "Xbox Console Companion",
        "category": "Xbox Ecosystem",
        "default_remove": True,
        "description": "Legacy Xbox Companion app.",
        "store_id": "9WZDNCRFJBD8",
        "processes": ["XboxApp.exe"]
    },
    "Microsoft.XboxGamingOverlay": {
        "name": "Xbox Game Bar",
        "category": "Xbox Ecosystem",
        "default_remove": False,
        "description": "In-game overlay, FPS counter, and capture.",
        "store_id": "9NZKPSTSNW4P",
        "processes": ["GameBar.exe", "GameBarFTServer.exe"]
    },
    "Microsoft.XboxSpeechToTextOverlay": {
        "name": "Xbox Speech-to-Text",
        "category": "Xbox Ecosystem",
        "default_remove": True,
        "description": "Game voice transcription overlay.",
        "store_id": "9WZDNCRFJBD8",
        "processes": []
    },
    "Microsoft.XboxIdentityProvider": {
        "name": "Xbox Identity Provider",
        "category": "Xbox Ecosystem",
        "default_remove": False,
        "description": "Authentication library required for Microsoft Store game logins.",
        "store_id": "9WZDNCRD1HKW",
        "processes": []
    }
}

SYSTEM_WHITELIST = {
    "Microsoft.WindowsStore",
    "Microsoft.DesktopAppInstaller",
    "Microsoft.WindowsTerminal",
    "Microsoft.WindowsCalculator",
    "Microsoft.ScreenSketch",
    "Microsoft.Paint",
    "Microsoft.WindowsNotepad",
    "Microsoft.SecHealthUI",
    "Microsoft.Windows.ShellExperienceHost",
    "Microsoft.Windows.StartMenuExperienceHost"
}

def terminate_package_processes(package_ids: List[str]):
    """Kills active processes associated with packages to prevent 0x80073D02 in-use locks."""
    for pkg_id in package_ids:
        info = BLOATWARE_CATALOG.get(pkg_id, {})
        for proc in info.get("processes", []):
            try:
                subprocess.run(f'taskkill /f /im "{proc}"', shell=True, capture_output=True, timeout=3)
            except Exception:
                pass

def dism_remove_provisioned_package(package_id: str) -> bool:
    """
    Fallback using native DISM.exe. Useful in WDAC / AppLocker constrained environments
    where PowerShell scripting or JSON conversion is restricted.
    """
    try:
        # Query package name
        cmd_list = "dism.exe /Online /Get-ProvisionedAppxPackages"
        res = subprocess.run(cmd_list, shell=True, capture_output=True, text=True, timeout=20)
        pkg_full_name = None
        for line in res.stdout.splitlines():
            if package_id.lower() in line.lower() and "PackageName :" in line:
                pkg_full_name = line.split(":", 1)[1].strip()
                break

        if pkg_full_name:
            del_cmd = f'dism.exe /Online /Remove-ProvisionedAppxPackage /PackageName:"{pkg_full_name}"'
            del_res = subprocess.run(del_cmd, shell=True, capture_output=True, text=True, timeout=30)
            return del_res.returncode == 0
    except Exception as e:
        log_debug(f"DISM fallback error: {e}")
    return False

def query_installed_apps() -> List[Dict[str, any]]:
    """Scans for installed Appx packages and correlates them with the catalog."""
    log_info("Scanning installed UWP and provisioned bloatware packages...")
    ps_cmd = """
    $apps = Get-AppxPackage -AllUsers | Select-Object -Property Name, PackageFullName
    $apps | ConvertTo-Json -Compress
    """
    installed_names = set()
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=30
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw = proc.stdout.strip()
            data = json.loads(raw)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "Name" in item:
                        installed_names.add(item["Name"])
            elif isinstance(data, dict) and "Name" in data:
                installed_names.add(data["Name"])
    except Exception as e:
        log_debug(f"Error scanning Appx packages: {e}")

    results = []
    for pkg_id, info in BLOATWARE_CATALOG.items():
        is_installed = any(pkg_id.lower() in name.lower() for name in installed_names)
        results.append({
            "id": pkg_id,
            "name": info["name"],
            "category": info["category"],
            "description": info["description"],
            "default_remove": info["default_remove"],
            "is_installed": is_installed,
            "store_id": info.get("store_id", "")
        })
    return results

def batch_remove_bloatware(
    package_ids: List[str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Tuple[int, int]:
    """
    High-Performance single-pass uninstaller for Appx packages.
    Pre-terminates running processes, handles 0x80073D02 locks, and provides DISM fallback.
    """
    filtered_ids = [p for p in package_ids if p not in SYSTEM_WHITELIST]
    total = len(filtered_ids)
    if total == 0:
        log_info("No non-whitelisted packages to remove.")
        return 0, 0

    log_info(f"Terminating active background app processes before removal...")
    terminate_package_processes(filtered_ids)

    log_info(f"Initiating single-pass removal of {total} packages...")
    pkg_json = json.dumps(filtered_ids)

    ps_script = f"""
    $ErrorActionPreference = 'SilentlyContinue'
    $targets = ConvertFrom-Json @'
{pkg_json}
'@

    $total = $targets.Count
    $current = 0

    foreach ($pkgId in $targets) {{
        $current++
        Write-Output "PROGRESS:$current:$total:$pkgId:START"

        $found = $false
        $locked = $false

        $pkgs = Get-AppxPackage -AllUsers -Name "*$pkgId*"
        foreach ($p in $pkgs) {{
            try {{
                Remove-AppxPackage -Package $p.PackageFullName -AllUsers -ErrorAction Stop
                $found = $true
            }} catch {{
                if ($_.Exception.Message -like "*0x80073D02*" -or $_.Exception.Message -like "*in use*") {{
                    $locked = $true
                }}
            }}
        }}

        $prov = Get-AppxProvisionedPackage -Online | Where-Object {{ $_.DisplayName -like "*$pkgId*" }}
        foreach ($pr in $prov) {{
            try {{
                Remove-AppxProvisionedPackage -Online -PackageName $pr.PackageName -ErrorAction SilentlyContinue
                $found = $true
            }} catch {{}}
        }}

        if ($locked) {{
            Write-Output "PROGRESS:$current:$total:$pkgId:LOCKED"
        }} elseif ($found) {{
            Write-Output "PROGRESS:$current:$total:$pkgId:REMOVED"
        }} else {{
            Write-Output "PROGRESS:$current:$total:$pkgId:NOT_FOUND"
        }}
    }}
    Write-Output "COMPLETED"
    """

    success_count = 0
    fail_count = 0

    try:
        proc = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        for line in iter(proc.stdout.readline, ""):
            line = line.strip()
            if line.startswith("PROGRESS:"):
                parts = line.split(":")
                if len(parts) >= 5:
                    cur_idx = int(parts[1])
                    tot_idx = int(parts[2])
                    pkg = parts[3]
                    status = parts[4]

                    if status == "START":
                        if progress_callback:
                            progress_callback(cur_idx, tot_idx, f"Removing {pkg}...")
                    elif status == "REMOVED":
                        log_success(f"Removed package: {pkg}")
                        success_count += 1
                    elif status == "LOCKED":
                        log_warning(f"Package {pkg} is locked by another logged-in user session (0x80073D02). Attempting DISM de-provisioning...")
                        if dism_remove_provisioned_package(pkg):
                            success_count += 1
                        else:
                            fail_count += 1
                    elif status == "NOT_FOUND":
                        log_debug(f"Package not currently present: {pkg}")
                        success_count += 1
            elif line == "COMPLETED":
                break

        proc.stdout.close()
        proc.wait(timeout=180)
    except Exception as e:
        log_error(f"PowerShell batch failure ({e}). Engaging DISM fallback...")
        for pkg in filtered_ids:
            if dism_remove_provisioned_package(pkg):
                success_count += 1
            else:
                fail_count += 1

    log_success(f"Batch uninstallation complete. {success_count} processed.")
    return success_count, fail_count

def reinstall_app_from_store(store_id: str) -> bool:
    """Launches Microsoft Store page for an app using store protocol URI."""
    if not store_id:
        return False
    try:
        url = f"ms-windows-store://pdp/?ProductId={store_id}"
        subprocess.Popen(f'start "" "{url}"', shell=True)
        log_info(f"Opened Microsoft Store page for Product ID: {store_id}")
        return True
    except Exception as e:
        log_error(f"Failed to open Microsoft Store: {e}")
        return False
