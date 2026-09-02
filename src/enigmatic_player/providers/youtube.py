"""YouTube Music provider — metadata from ytmusicapi, audio from yt-dlp."""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from ..core.track import Source, Track
from .base import Provider

log = logging.getLogger(__name__)


class YoutubeProvider(Provider):
    source = Source.YOUTUBE
    display_name = "YouTube"

    def __init__(self, quality: str = "best") -> None:
        self._ym = None  # ytmusicapi.YTMusic
        self._resolver = None  # yt_dlp.YoutubeDL
        self._cache: Dict[str, Optional[str]] = {}
        self._headers_cache: Dict[str, Dict[str, str]] = {}
        self._quality = quality

    @property
    def _format_selector(self) -> str:
        """Return yt-dlp format selector based on quality setting."""
        if self._quality == "high":
            # Try for 251 (opus ~128k) or 140 (m4a ~128k) - best free tier
            return "bestaudio[ext=webm][acodec^=opus]/bestaudio[ext=m4a]/bestaudio/best"
        elif self._quality == "medium":
            # Explicitly target medium quality (128k)
            return "bestaudio[abr>=128][ext=webm]/bestaudio[abr>=128][ext=m4a]/bestaudio/best"
        elif self._quality == "low":
            # Lowest bandwidth
            return "worstaudio/worst"
        else:  # "best" - default, highest available
            return (
                "bestaudio[ext=webm][acodec^=opus]/"
                "bestaudio[ext=m4a]/"
                "bestaudio/best"
            )

    @property
    def available(self) -> bool:
        try:
            import yt_dlp  # noqa: F401
            import ytmusicapi  # noqa: F401
            return True
        except ImportError:
            return False

    def _client(self):
        if self._ym is None:
            from ytmusicapi import YTMusic

            self._ym = YTMusic()
        return self._ym

    # ---- search --------------------------------------------------------------------
    def search(self, query: str, limit: int = 30) -> List[Track]:
        client = self._client()
        try:
            results = client.search(query, filter="songs", limit=limit)
        except Exception:
            results = client.search(query, limit=limit)
        out: List[Track] = []
        for r in results:
            if r.get("videoId") is None:
                continue
            out.append(
                Track(
                    title=str(r.get("title") or "unknown"),
                    artist=_artists(r),
                    album=str(r.get("album") or ""),
                    duration=_duration(r),
                    uri=str(r["videoId"]),
                    provider=self.source,
                    track_id=str(r["videoId"]),
                    cover_uri=r.get("thumbnails", [{}])[-1].get("url"),
                )
            )
        return out[:limit]

    # ---- browse: playlists / albums -------------------------------------------------
    def playlists(self, query: str, limit: int = 12) -> List[Track]:
        """Return playlists as fake 'tracks' whose albums act as playlist owners."""
        client = self._client()
        results = client.search(query, filter="playlists", limit=limit)
        return [
            Track(
                title=str(r.get("title") or ""),
                artist="Playlist",
                uri=str(r.get("browseId") or ""),
                provider=self.source,
                track_id="playlist:" + str(r.get("browseId") or ""),
                cover_uri=r.get("thumbnails", [{}])[-1].get("url"),
            )
            for r in results
            if r.get("browseId")
        ]

    def album_tracks(self, browse_id: str) -> Optional[List[Track]]:
        client = self._client()
        try:
            data = client.get_album(browse_id)
        except Exception:  # noqa: BLE001
            return None
        meta = data.get("tracks", [])
        album = str(data.get("title") or "")
        artist = str(data.get("artists", [{}])[0].get("name") or "")
        tracks = []
        for r in meta:
            video_id = r.get("videoId")
            if not video_id:
                continue
            tracks.append(
                Track(
                    title=str(r.get("title") or ""),
                    artist=artist,
                    album=album,
                    duration=float(r.get("duration_seconds") or 0),
                    uri=str(video_id),
                    provider=self.source,
                    track_id=str(video_id),
                    cover_uri=data.get("thumbnails", [{}])[-1].get("url"),
                )
            )
        return tracks

    # ---- audio resolution -------------------------------------------------------------
    def resolve_stream_with_headers(
        self, track: Track
    ) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
        """Resolve the stream URL *and* the HTTP headers required to fetch it.

        YouTube now mints stream URLs for a specific internal client (e.g.
        ``ANDROID_VR``) and rejects requests whose User-Agent doesn't match
        that client with HTTP 403. yt-dlp returns the correct per-format
        ``http_headers`` — we must hand them to the player alongside the URL.
        """
        vid = track.uri
        if not vid:
            return None, None
        if vid in self._cache:
            return self._cache[vid], self._headers_cache.get(vid)
        if self._resolver is None:
            import yt_dlp

            self._resolver = yt_dlp.YoutubeDL(
                {
                    "format": self._format_selector,
                    "format_sort": ["abr", "ext:webm:m4a", "acodec:opus:aac"],
                    "quiet": True,
                    "no_warnings": True,
                    "noplaylist": True,
                }
            )
        try:
            info = self._resolver.extract_info(
                f"https://www.youtube.com/watch?v={vid}", download=False
            )
        except Exception as exc:  # noqa: BLE001 - surfaced via log + None return
            # Don't cache failures: a yt-dlp update (or transient block) should
            # let the next attempt succeed without restarting the app.
            log.warning("yt-dlp failed to resolve %s: %s", vid, exc)
            return None, None

        url = info.get("url")
        fmt = None
        formats = info.get("formats") or []
        if not url and formats:
            fmt = formats[-1]
            url = fmt.get("url")
        elif info.get("format_id"):
            # prefer the headers of the format that was actually selected
            fmt = next((f for f in formats if f.get("format_id") == info["format_id"]), None)

        # Format-level headers carry the client-matched User-Agent; fall back
        # to top-level ones only if missing.
        headers: Dict[str, str] = {}
        if fmt and fmt.get("http_headers"):
            headers.update(fmt["http_headers"])
        elif info.get("http_headers"):
            headers.update(info["http_headers"])

        self._cache[vid] = url
        self._headers_cache[vid] = headers or {}
        return url, headers or {}

    def resolve_stream(self, track: Track) -> Optional[str]:
        url, _headers = self.resolve_stream_with_headers(track)
        return url


def _artists(result: dict) -> str:
    artists = result.get("artists")
    if isinstance(artists, list):
        return ", ".join(str(a.get("name") or "") for a in artists if a.get("name"))
    return str(artists or "")


def _duration(result: dict) -> float:
    try:
        return float(result.get("duration_seconds") or 0)
    except (TypeError, ValueError):  # noqa: PERF203
        return 0.0
