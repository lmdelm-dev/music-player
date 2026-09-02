#!/usr/bin/env bash
# Enigmatic Player — Linux/macOS install helper
set -euo pipefail

PYTHON="${PYTHON:-python3}"
EXTRAS="${EXTRAS:-youtube,spotify,art,dev}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Python 3.10+ is required. Install it first." >&2
    exit 1
fi

if ! command -v mpv >/dev/null 2>&1; then
    echo "mpv is required ($PYTHON -c '...'):"
    echo "  Debian/Ubuntu: sudo apt install mpv"
    echo "  Fedora:        sudo dnf install mpv"
    echo "  Arch:          sudo pacman -S mpv"
    echo "  macOS:         brew install mpv"
    echo "Install mpv, then re-run this script."
    exit 1
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing Enigmatic Player from $DIR …"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install --user -e "$DIR[$EXTRAS]"

echo
echo "Done! Launch with:  enigmatic"
echo "Get help with:      enigmatic --help"