"""Provider interface: a provider supplies searchable music + stream resolution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from ..core.track import Source, Track


class Provider(ABC):
    source: Source
    display_name: str = ""

    @property
    @abstractmethod
    def available(self) -> bool:
        """True if this provider is configured/usable right now."""

    @abstractmethod
    def search(self, query: str, limit: int = 30) -> List[Track]:
        """Search for tracks matching ``query``."""

    @abstractmethod
    def resolve_stream(self, track: Track) -> Optional[str]:
        """Resolve a playable audio URL/path for ``track``.

        May be slow (network); callers should run it off the UI thread and
        cache results.
        """

    def resolve_stream_with_headers(
        self, track: Track
    ) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        """Resolve a stream URL plus any HTTP headers required to fetch it.

        Some providers (YouTube) hand out URLs that are only valid when
        requested with specific headers (e.g. a client-matched User-Agent).
        Players must send them alongside the request. Default: no headers.
        """
        return self.resolve_stream(track), None

    # ---- optional rich features (implement to light up extra UI) ------------
    def browse(self, path: str = "") -> List[Track]:
        raise NotImplementedError

    def playlists(self) -> List[Track]:
        """Playlist-style collections; default drops to search."""
        raise NotImplementedError


class ProviderError(RuntimeError):
    pass


class ProviderImportError(ProviderError):
    """Raised when a provider's optional dependencies are missing."""
