from app.auth.rate_limit import SlidingWindowLimiter


class FakeClock:
    now = 0.0

    def __call__(self) -> float:
        return self.now


def test_blocks_at_max_hits_then_allows_after_window() -> None:
    clock = FakeClock()
    limiter = SlidingWindowLimiter(max_hits=2, window_seconds=60, clock=clock)

    assert limiter.hit("k") is None
    clock.now = 10
    assert limiter.hit("k") is None
    assert limiter.hit("k") == 50  # oldest hit (t=0) expires at t=60

    clock.now = 60
    assert limiter.hit("k") is None  # t=0 dropped; t=10 still counted
    assert limiter.hit("k") == 10


def test_keys_are_independent_and_reset_clears_one() -> None:
    limiter = SlidingWindowLimiter(max_hits=1, window_seconds=60, clock=FakeClock())
    assert limiter.hit("a") is None
    assert limiter.hit("b") is None
    assert limiter.hit("a") == 60
    limiter.reset("a")
    assert limiter.hit("a") is None
    limiter.clear()
    assert limiter.hit("b") is None
