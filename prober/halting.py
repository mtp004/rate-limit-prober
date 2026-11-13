from collections import deque

import numpy as np


class WindowRule:
    """Stop when, over the last `check_window` replies, the gap is flat
    (range/mean < tol), the success rate is within p_tol of target, and
    there was at least `min_failures` rejection. Must hold `patience`
    times in a row. Returns the current gap.

    min_failures should stay >= 1: from a slow start every request succeeds,
    and without it a 100% success stretch can pass as "close to 99%".
    """

    def __init__(self, target_p, check_window=50, tol=0.04, patience=3,
                 p_tol=0.015, min_failures=1):
        self.p = target_p
        self.check_window = check_window
        self.tol = tol
        self.patience = patience
        self.p_tol = p_tol
        self.min_failures = min_failures
        self.gaps = deque(maxlen=check_window)
        self.oks = deque(maxlen=check_window)
        self.streak = 0

    def observe(self, k, gap, ok):
        self.gaps.append(gap)
        self.oks.append(ok)
        if len(self.gaps) < self.check_window:
            return None

        mean = sum(self.gaps) / len(self.gaps)
        spread = (max(self.gaps) - min(self.gaps)) / mean
        n_fail = sum(1 for o in self.oks if not o)
        success = 1 - n_fail / len(self.oks)

        if (spread < self.tol and abs(success - self.p) < self.p_tol
                and n_fail >= self.min_failures):
            self.streak += 1
            if self.streak >= self.patience:
                return gap
        else:
            self.streak = 0
        return None


class CycleRule:
    """Stop when the average gap over the last `k_cycles` rejection-to-rejection
    cycles agree within `tol`. Returns their length-weighted average.

    Once settled, there is about one rejection every 1/(1-p) requests, and each
    cycle contains one full up/down swing, so its average doesn't depend on
    where in the swing you stop. Rejections closer together than
    merge_frac/(1-p) replies are treated as one event, since a burst of them
    usually comes from a single overshoot.
    """

    def __init__(self, target_p, k_cycles=2, tol=0.003, merge_frac=0.5):
        self.k_cycles = k_cycles
        self.tol = tol
        self.merge = max(1, int(merge_frac / (1 - target_p)))
        self.last_fail = None
        self.started = False
        self.cycle_sum = 0.0
        self.cycle_len = 0
        self.cycles = deque(maxlen=k_cycles)

    def observe(self, k, gap, ok):
        if self.started:
            self.cycle_sum += gap
            self.cycle_len += 1
        if ok:
            return None

        new_event = self.last_fail is None or k - self.last_fail > self.merge
        self.last_fail = k
        if not new_event:
            return None

        if self.started:
            self.cycles.append((self.cycle_sum / self.cycle_len, self.cycle_len))
        self.started = True
        self.cycle_sum, self.cycle_len = 0.0, 0

        if len(self.cycles) == self.k_cycles:
            means = np.array([m for m, _ in self.cycles])
            lens = np.array([n for _, n in self.cycles], dtype=float)
            if (means.max() - means.min()) / means.mean() < self.tol:
                return float((means * lens).sum() / lens.sum())
        return None


class NeverStop:
    def __init__(self, target_p=None):
        pass

    def observe(self, k, gap, ok):
        return None


HALT_RULES = {
    "window": WindowRule,
    "cycle": CycleRule,
    "none": NeverStop,
}
