# WinDebloatX

WinDebloatX is an open-source Windows 10 & 11 optimization, privacy hardening, and software deployment platform. Engineered with zero-install bootstrapping, hardware intelligence, and an integrated Winget software hub.

---

## ⚡ 1-Liner Quick Launch (No Python Required)

Run PowerShell as Administrator and paste:

```powershell
irm https://raw.githubusercontent.com/vyassoham/WinDebloatX/main/install.ps1 | iex
```

*Automatically bootstraps the environment, checks administrator privileges, and launches the graphical interface with zero manual installation.*

---

## Flagship Capabilities

### 1. 🧠 Hardware Intelligence Engine
- **Form Factor Aware**: Auto-detects Laptops vs Desktops. On laptops, automatically preserves Location services for automatic timezone updates and *Find My Device*, while keeping Bluetooth device brokers intact.
- **Storage & RAM Profiling**: Identifies NVMe/SSD vs HDD and evaluates RAM capacity to make intelligent decisions regarding SysMain (Superfetch) and indexing.
- **CPU Topology Scheduling**: Tunes MMCSS network throttling and thread responsiveness based on core and thread counts.

### 2. 🚀 Winget Software Package Hub
- Install full developer stacks, privacy browsers, media suites, and gaming launchers silently in one click:
  - **Browsers**: Brave, Firefox, LibreWolf, Chrome
  - **Dev Stack**: VS Code, Git, Windows Terminal, Node.js LTS, Python 3.12, Docker
  - **Utilities**: NanaZip, 7-Zip, PowerToys, Everything Search, BleachBit
  - **Media & Gaming**: VLC, OBS Studio, HandBrake, Steam, Discord

### 3. 🛡️ Privacy Hardening & Modern Win11 24H2 Controls
- **Edition-Aware Telemetry Defense**: Recognizes that Windows Home and Pro kernel-coerce GPO telemetry level 0 to 1, enforcing primary protection through service-level disabling (`DiagTrack`).
- **24H2 Settings & App Promos**: Eliminates injected recommendations inside Windows Settings, Explorer, and Lock Screen tips.
- **Modern AI Toggles**: One-click toggles for Windows Copilot, Recall AI screen snapshots, taskbar widgets, and Edge sidebar analysis.
- **Classic Context Menu**: Restores the responsive Windows 10 right-click menu with zero-latency Explorer restarting.

### 4. 🔄 Safety Architecture & Rollback Manager
- **VSS & Storage Pre-Flight**: Verifies free disk space (> 4 GB) and shadow copy configuration before creating System Restore points.
- **In-App Rollback Manager**: View, manage, and restore timestamped `.reg` snapshots directly within the UI.
- **OneDrive Protection**: Scans for cloud-only placeholder files (Files On-Demand) to prevent accidental data loss before uninstallation.
- **Store Reinstall Links**: Re-download any uninstalled UWP app via 1-click Microsoft Store protocol handlers (`ms-windows-store://`).

### 5. 🌐 Internationalization (i18n)
- Native multi-language support:
  - 🇺🇸 English (`en`)
  - 🇪🇸 Español (`es`)
  - 🇩🇪 Deutsch (`de`)
  - 🇨🇳 简体中文 (`zh`)

---

## Command Line & Automation

```bash
# Print live hardware intelligence profile
python main.py --hardware

# Audit live system protection and component states
python main.py --status

# Create restore point and apply gaming preset silently
python main.py --create-restore-point --preset gaming --silent

# Install full developer stack via winget
python main.py --install-dev --silent

# Register Windows Update persistence task
python main.py --install-guard --silent

# Restore a saved registry snapshot
python main.py --restore-backup <filename>
```

---

## Automated GitHub Release CI/CD

This repository includes a production GitHub Actions workflow ([.github/workflows/build-release.yml](.github/workflows/build-release.yml)):
- Automatically compiles standalone binaries on `windows-latest`.
- Computes SHA-256 hashes (`SHA256SUMS.txt`).
- Generates GitHub Releases on tag push (`git tag v2.3.0 && git push --tags`).

---

## License

Released under the terms of the [MIT License](LICENSE).
