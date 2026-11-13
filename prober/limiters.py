from collections import deque


class FixedWindowLimiter:
    """At most `limit` requests per window. Windows start at multiples of `window`."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.window_start = None
        self.count = 0

    def request(self, t):
        if self.window_start is None or t >= self.window_start + self.window:
            self.window_start = (t // self.window) * self.window
            self.count = 0
        if self.count < self.limit:
            self.count += 1
            return True
        return False


class RollingWindowLimiter:
    """At most `limit` requests in any trailing `window` seconds."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.timestamps = deque()

    def request(self, t):
        while self.timestamps and self.timestamps[0] <= t - self.window:
            self.timestamps.popleft()
        if len(self.timestamps) < self.limit:
            self.timestamps.append(t)
            return True
        return False


LIMITERS = {
    "fixed": FixedWindowLimiter,
    "rolling": RollingWindowLimiter,
}
