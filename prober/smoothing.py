import math
from collections import deque

import numpy as np


class SMA:
    def __init__(self, n):
        self.buf = deque(maxlen=n)

    def update(self, x):
        self.buf.append(x)
        return sum(self.buf) / len(self.buf)


class WindowedEMA:
    """Exponential weights over the last n values, renormalized.

    alpha = 2/(n+1) gives the same mean lag as an n-sample SMA.
    """

    def __init__(self, n):
        a = 2 / (n + 1)
        self.weights = np.array([a * (1 - a) ** k for k in range(n)])
        self.buf = deque(maxlen=n)

    def update(self, x):
        self.buf.append(x)
        w = self.weights[: len(self.buf)]
        vals = np.array(self.buf)[::-1]  # newest first
        return float(np.dot(w, vals) / w.sum())


class GeoSMA:
    """SMA in log space (geometric mean)."""

    def __init__(self, n):
        self.buf = deque(maxlen=n)

    def update(self, x):
        self.buf.append(math.log(x))
        return math.exp(sum(self.buf) / len(self.buf))


SMOOTHERS = {
    "sma": SMA,
    "ema": WindowedEMA,
    "geo": GeoSMA,
}
