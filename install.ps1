# WinDebloatX - One-Liner Web Bootstrapper & Zero-Install Launcher
# Usage: irm https://raw.githubusercontent.com/vyassoham/WinDebloatX/main/install.ps1 | iex

[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

Write-Host @"
============================================================
              WinDebloatX Bootstrapper v2.2                 
  Modern Windows 10 & 11 Optimizer, Hardener & Software Hub 
============================================================
"@ -ForegroundColor Cyan

# 1. Require Administrator Privileges
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] Administrator privileges required. Spawning elevated session..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command `"irm https://raw.githubusercontent.com/vyassoham/WinDebloatX/main/install.ps1 | iex`"" -Verb RunAs
    exit
}

# 2. Setup Working Directory
$appDir = Join-Path $env:LOCALAPPDATA "WinDebloatX\App"
if (-not (Test-Path $appDir)) {
    New-Item -ItemType Directory -Path $appDir -Force | Out-Null
}

# 3. Check for Python or Embedded Runtime
$pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)?.Source

if (-not $pythonCmd) {
    Write-Host "[*] Python not detected on host. Downloading portable embedded runtime..." -ForegroundColor Green
    $embedUrl = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-embed-amd64.zip"
    $embedZip = Join-Path $appDir "python-embed.zip"
    $pythonDir = Join-Path $appDir "python"
    
    if (-not (Test-Path $pythonDir)) {
        Invoke-WebRequest -Uri $embedUrl -OutFile $embedZip
        Expand-Archive -Path $embedZip -DestinationPath $pythonDir -Force
        Remove-Item $embedZip -Force
    }
    $pythonCmd = Join-Path $pythonDir "python.exe"
}

# 4. Pull / Clone / Update Source Code
Write-Host "[*] Synchronizing WinDebloatX latest release..." -ForegroundColor Green
$repoZipUrl = "https://github.com/vyassoham/WinDebloatX/archive/refs/heads/main.zip"
$zipFile = Join-Path $appDir "windebloatx.zip"
$srcDir = Join-Path $appDir "src"

try {
    Invoke-WebRequest -Uri $repoZipUrl -OutFile $zipFile
    Expand-Archive -Path $zipFile -DestinationPath $srcDir -Force
    Remove-Item $zipFile -Force
    $entryPoint = Get-ChildItem -Path $srcDir -Filter "main.py" -Recurse | Select-Object -ExpandProperty FullName -First 1
} catch {
    Write-Host "[!] Note: Using local development entry point if available..." -ForegroundColor Yellow
    $entryPoint = Join-Path $PSScriptRoot "main.py"
}

# 5. Launch WinDebloatX
Write-Host "[+] Launching WinDebloatX..." -ForegroundColor Cyan
if (Test-Path $entryPoint) {
    Start-Process -FilePath $pythonCmd -ArgumentList "`"$entryPoint`"" -Wait
} else {
    Write-Host "[!] Could not locate main.py. Please verify repository connection." -ForegroundColor Red
}
