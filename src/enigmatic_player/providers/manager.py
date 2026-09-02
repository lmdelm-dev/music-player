"""Builds and exposes the active provider set."""

from __future__ import annotations

from typing import Dict, List, Optional

from ..config import Config
from ..core.track import Source
from .base import Provider
from .local import LocalProvider
from .youtube import YoutubeProvider


class ProviderManager:
    def __init__(self, config: Optional[Config] = None, premium_spotify: bool = False) -> None:
        self._config = config or Config()
        self._local = LocalProvider(self._config)
        self._youtube = YoutubeProvider(quality=self._config.youtube_quality)

    @property
    def local(self) -> LocalProvider:
        return self._local

    @property
    def youtube(self) -> YoutubeProvider:
        return self._youtube

    def all(self) -> List[Provider]:
        return [self._local, self._youtube]

    def by_source(self, source: Source) -> Provider:
        for p in self.all():
            if p.source is source:
                return p
        return self._local

    def available(self) -> Dict[Source, Provider]:
        return {p.source: p for p in self.all() if p.available}
