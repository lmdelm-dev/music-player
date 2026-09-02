"""Configuration and state persistence.

Config lives in a platform-appropriate directory (``platformdirs`` user
config dir). Provider credentials are stored optionally: any secrets are
best handled through OS keychains; we at least keep them in a 0600 file and
never log them.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from platformdirs import user_config_dir, user_data_dir

APP_NAME = "enigmatic-player"


def data_dir() -> Path:
    return Path(user_data_dir(APP_NAME))


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


class Config:
    def __init__(self, cfg_path: Optional[Path] = None, data_path: Optional[Path] = None) -> None:
        self._cfg_path = Path(cfg_path) if cfg_path else (config_dir() / "config.json")
        self._data_path = Path(data_path) if data_path else (data_dir() / "state.json")
        self._data: Dict[str, Any] = {}
        self.load()

    # ---- load / save --------------------------------------------------------
    def load(self) -> None:
        if self._cfg_path.exists():
            try:
                self._data = json.loads(self._cfg_path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}
        if not isinstance(self._data, dict):
            self._data = {}

    def save(self) -> None:
        self._cfg_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._cfg_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), "utf-8")
        os.replace(tmp, self._cfg_path)
        # keep any possible secrets unreadable by others
        try:
            os.chmod(self._cfg_path, 0o600)
        except OSError:
            pass

    # ---- dict-ish access ------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def update(self, mapping: Dict[str, Any]) -> None:
        self._data.update(mapping)

    @property
    def all(self) -> Dict[str, Any]:
        return dict(self._data)

    # ---- typed helpers ---------------------------------------------------------
    @property
    def library_dirs(self) -> list:
        return list(self._data.get("library_dirs", []) or [])

    def add_library_dir(self, path: str) -> None:
        path = os.path.abspath(os.path.expanduser(path))
        dirs = self.library_dirs
        if path not in dirs:
            dirs.append(path)
        self._data["library_dirs"] = dirs

    @property
    def default_provider(self) -> str:
        return self._data.get("default_provider", "local")

    @property
    def youtube_quality(self) -> str:
        """YouTube audio quality preset: 'best' (default), 'high', 'medium', 'low'."""
        return self._data.get("youtube_quality", "best")

    def set_youtube_quality(self, quality: str) -> None:
        if quality in ("best", "high", "medium", "low"):
            self._data["youtube_quality"] = quality
            self.save()

    # ---- playlists --------------------------------------------------------------
    def _playlist_list(self) -> List[Dict[str, Any]]:
        return list(self._data.get("playlists", []) or [])

    def _save_playlist_list(self, pl: List[Dict[str, Any]]) -> None:
        self._data["playlists"] = pl
        self.save()

    @property
    def playlists(self) -> List[Dict[str, Any]]:
        """Return list of playlists (each: name, tracks[], created, updated)."""
        return self._playlist_list()

    def create_playlist(self, name: str) -> Dict[str, Any]:
        pl = {
            "name": name,
            "tracks": [],
            "created": time.time(),
            "updated": time.time(),
        }
        lst = self._playlist_list()
        lst.append(pl)
        self._save_playlist_list(lst)
        return pl

    def rename_playlist(self, index: int, new_name: str) -> bool:
        lst = self._playlist_list()
        if 0 <= index < len(lst):
            lst[index]["name"] = new_name
            lst[index]["updated"] = time.time()
            self._save_playlist_list(lst)
            return True
        return False

    def delete_playlist(self, index: int) -> bool:
        lst = self._playlist_list()
        if 0 <= index < len(lst):
            lst.pop(index)
            self._save_playlist_list(lst)
            return True
        return False

    def add_track_to_playlist(self, pl_index: int, track: Dict[str, Any]) -> bool:
        lst = self._playlist_list()
        if 0 <= pl_index < len(lst):
            # avoid duplicates by uri+provider
            existing = {(t.get("uri"), t.get("provider")) for t in lst[pl_index].get("tracks", [])}
            key = (track.get("uri"), track.get("provider"))
            if key not in existing:
                lst[pl_index]["tracks"].append(track)
                lst[pl_index]["updated"] = time.time()
                self._save_playlist_list(lst)
            return True
        return False

    def remove_track_from_playlist(self, pl_index: int, track_index: int) -> bool:
        lst = self._playlist_list()
        if 0 <= pl_index < len(lst):
            tracks = lst[pl_index].get("tracks", [])
            if 0 <= track_index < len(tracks):
                tracks.pop(track_index)
                lst[pl_index]["updated"] = time.time()
                self._save_playlist_list(lst)
                return True
        return False

    def reorder_playlist_tracks(self, pl_index: int, from_idx: int, to_idx: int) -> bool:
        lst = self._playlist_list()
        if 0 <= pl_index < len(lst):
            tracks = lst[pl_index].get("tracks", [])
            if 0 <= from_idx < len(tracks) and 0 <= to_idx < len(tracks):
                tracks.insert(to_idx, tracks.pop(from_idx))
                lst[pl_index]["updated"] = time.time()
                self._save_playlist_list(lst)
                return True
        return False

    # ---- session state ----------------------------------------------------------
    def save_state(self, payload: Dict[str, Any]) -> None:
        self._data_path.parent.mkdir(parents=True, exist_ok=True)
        self._data_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), "utf-8"
        )

    def load_state(self) -> Dict[str, Any]:
        if self._data_path.exists():
            try:
                return json.loads(self._data_path.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}
