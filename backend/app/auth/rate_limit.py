import math
import threading
import time
from collections import deque
from collections.abc import Callable

_PRUNE_ABOVE_KEYS = 10_000


# ponytail: in-memory, single process/machine ceiling; move to Postgres/Redis if scaled out.
class SlidingWindowLimiter:
    def __init__(
        self,
        max_hits: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_hits = max_hits
        self._window = window_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._hits: dict[str, deque[float]] = {}

    def _expire(self, key: str, now: float) -> deque[float]:
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= now - self._window:
            hits.popleft()
        return hits

    def hit(self, key: str) -> int | None:
        """Record a hit. Return seconds until allowed (>= 1) if over the limit, else None."""
        with self._lock:
            now = self._clock()
            if len(self._hits) > _PRUNE_ABOVE_KEYS:
                for k in list(self._hits):
                    if not self._expire(k, now):
                        del self._hits[k]
            hits = self._expire(key, now)
            if len(hits) >= self._max_hits:
                return max(1, math.ceil(hits[0] + self._window - now))
            hits.append(now)
            return None

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


# No per-username key: there is one teacher, so a per-username lock would let anyone lock her out.
pair_limiter = SlidingWindowLimiter(max_hits=10, window_seconds=15 * 60)
ip_limiter = SlidingWindowLimiter(max_hits=50, window_seconds=15 * 60)
