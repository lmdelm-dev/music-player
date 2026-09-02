"""Playback queue with shuffle / repeat logic."""

from __future__ import annotations

import random
from typing import Callable, List, Optional

from .track import Track


class Queue:
    def __init__(self) -> None:
        self._items: List[Track] = []
        self._pos: Optional[int] = None
        self.shuffle: bool = False
        self.repeat: bool = False
        self.on_change: Optional[Callable[[], None]] = None

    # ---- state -----------------------------------------------------------
    def _notify(self) -> None:
        if self.on_change:
            self.on_change()

    @property
    def current(self) -> Optional[Track]:
        if self._items and self._pos is not None and 0 <= self._pos < len(self._items):
            return self._items[self._pos]
        return None

    @property
    def position(self) -> Optional[int]:
        return self._pos

    @property
    def length(self) -> int:
        return len(self._items)

    @property
    def items(self) -> List[Track]:
        return list(self._items)

    def clear(self) -> None:
        self._items.clear()
        self._pos = None
        self._notify()

    def set_items(self, tracks: List[Track], start: int = 0) -> None:
        """Replace contents and place the cursor at ``start`` (in original order)."""
        if not tracks:
            self.clear()
            return
        self._items = list(tracks)
        self._pos = start
        self._notify()

    def add(self, track: Track) -> None:
        self._items.append(track)
        self._notify()

    def extend(self, tracks: List[Track]) -> None:
        self._items.extend(tracks)
        self._notify()

    # ---- navigation --------------------------------------------------------
    def next(self) -> Optional[Track]:
        if not self._items:
            return None
        if self.shuffle:
            return self.shuffle_restart()
        if self._pos is None:
            self._pos = -1
        nxt = self._pos + 1
        if nxt >= len(self._items):
            if self.repeat:
                self._pos = 0
            else:
                return None
        else:
            self._pos = nxt
        self._notify()
        return self.current

    def prev(self) -> Optional[Track]:
        if not self._items:
            return None
        if self._pos is None or self._pos <= 0:
            if self.repeat or True:  # always wrap on prev is friendlier
                self._pos = len(self._items) - 1
        else:
            self._pos -= 1
        self._notify()
        return self.current

    def jump(self, index: int) -> Optional[Track]:
        if not self._items:
            return None
        self._pos = index % len(self._items)
        self._notify()
        return self.current

    # ---- shuffle -------------------------------------------------------------
    def toggle_shuffle(self) -> bool:
        self.shuffle = not self.shuffle
        self._notify()
        return self.shuffle

    def toggle_repeat(self) -> bool:
        self.repeat = not self.repeat
        self._notify()
        return self.repeat

    def _shuffled_index(self) -> int:
        if self._pos is None:
            return random.randrange(len(self._items))
        available = [i for i in range(len(self._items)) if i != self._pos]
        return random.choice(available) if available else self._pos

    def shuffle_restart(self) -> Optional[Track]:
        if not self._items:
            return None
        self._pos = self._shuffled_index()
        self._notify()
        return self.current
