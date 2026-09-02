"""Unified track model shared by every provider."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Source(str, Enum):
    LOCAL = "local"
    YOUTUBE = "youtube"


@dataclass(frozen=True)
class Track:
    """A single playable item, provider-agnostic.

    `uri` is what a provider needs to resolve an audio stream (a file path,
    a YouTube video id, a Spotify track id, or a direct stream URL).
    """

    title: str
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    uri: str = ""
    provider: Source = Source.LOCAL
    cover_uri: Optional[str] = None
    albumart: Optional[bytes] = None
    track_id: str = field(default="", kw_only=True)

    @property
    def display(self) -> str:
        if self.artist:
            return f"{self.artist} — {self.title}"
        return self.title

    @property
    def key(self) -> str:
        return f"{self.provider.value}:{self.uri or self.track_id or self.title}"


@dataclass
class PlayableTrack:
    """A track carrying its resolved playable stream URL.

    Kept separate from :class:`Track` so that metadata (Track) is cheap to
    build while the expensive stream-resolution result is cached lazily.
    """

    track: Track
    stream_url: Optional[str] = None


def fmt_time(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"
