"""Allow `python -m enigmatic_player` to launch the TUI."""

from enigmatic_player.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
