# Enigmatic Player — Windows install helper (PowerShell)
$ErrorActionPreference = "Stop"

$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    Write-Error "Python 3.10+ is required. Install it from https://python.org/"
}

Write-Host "Checking for mpv..."
if (-not (Get-Command mpv -ErrorAction SilentlyContinue)) {
    Write-Host "mpv not found. Install it with:  winget install mpv"
    Write-Host "Then re-run this script."
    exit 1
}

$Dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Extras = "youtube,spotify,art,dev"

Write-Host "Installing Enigmatic Player from $Dir ..."
& python -m pip install --upgrade pip
& python -m pip install -e "$Dir[$Extras]"

Write-Host ""
Write-Host "Done! Launch with:  enigmatic"
Write-Host "Get help with:      enigmatic --help"
Write-Host ""
Write-Host "Note: if the TUI misrenders, enable Windows Terminal and set"
Write-Host "`TERM=xterm-256color` and a True Color / RGB color profile."