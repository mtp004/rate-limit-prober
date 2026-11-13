import heapq
import random
from dataclasses import dataclass, field


@dataclass
class ProbeResult:
    stopped_at: int | None      # reply index where the halting rule fired, or None
    estimate: float             # gap estimate (seconds)
    trace: list = field(default_factory=list)   # (reply_time, gap, ok)
    max_in_flight: int = 0

    @property
    def converged(self):
        return self.stopped_at is not None


SEND, ARRIVE, REPLY = 0, 1, 2


def run_prober(limiter, initial_gap, decrease_frac, increase_frac, smoother,
               halt_rule, rtt=0.0, jitter=0.0, n_iters=30000, min_gap=1e-6,
               seed=None):
    """Run the prober against a simulated limiter.

    Each request goes send -> arrive -> reply. The limiter sees the arrival
    time, and the prober only updates its gap when the reply comes back.
    Requests keep going out on the current schedule in the meantime, so with
    gap < rtt several are in flight at once.

    One-way delay is rtt/2 plus Gaussian noise with std jitter/2, floored at 0.
    With rtt = jitter = 0 this reduces to the plain synchronous loop.
    """
    rng = random.Random(seed)

    def one_way():
        if rtt == 0 and jitter == 0:
            return 0.0
        return max(0.0, rng.gauss(rtt / 2, jitter / 2))

    events = []
    seq = 0

    def push(t, kind, payload=None):
        nonlocal seq
        heapq.heappush(events, (t, seq, kind, payload))
        seq += 1

    gap = initial_gap
    in_flight = max_in_flight = 0
    k = 0
    trace = []
    push(0.0, SEND)

    while events and k < n_iters:
        t, _, kind, ok = heapq.heappop(events)

        if kind == SEND:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            push(t + one_way(), ARRIVE)
            push(t + gap, SEND)

        elif kind == ARRIVE:
            push(t + one_way(), REPLY, limiter.request(t))

        else:
            in_flight -= 1
            if ok:
                candidate = max(gap * (1 - decrease_frac), min_gap)
            else:
                candidate = gap * (1 + increase_frac)
            gap = smoother.update(candidate)
            trace.append((t, gap, ok))

            est = halt_rule.observe(k, gap, ok)
            if est is not None:
                return ProbeResult(k, est, trace, max_in_flight)
            k += 1

    return ProbeResult(None, gap, trace, max_in_flight)
