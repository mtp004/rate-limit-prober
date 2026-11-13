# Adaptive Rate-Limit Prober

CS 5151/6051 Database Theory, group project (research project track).

Many APIs enforce a rate limit (e.g. 20 requests per 5 seconds) but don't say what it is. This project finds the smallest safe spacing between requests, `window / limit`, without knowing either value, using only whether each request was accepted or rejected.

## Method

The prober adjusts its request gap multiplicatively after every response:

- accepted: `gap *= (1 - d)` (small step faster)
- rejected: `gap *= (1 + i)` (large step slower)

The new value is passed through a moving average (SMA by default) and fed back as the next gap.

`d` is not tuned by hand. Given `i` and a target success rate `p`, it is solved so that the up and down steps cancel exactly at success rate `p`:

```
d = 1 - (1 + i) ^ (-(1 - p) / p)
```

Below the true gap a windowed limiter accepts roughly `gap / true_gap` of requests, so with `p = 0.99` the prober settles within about 1% of the true gap.

### Halting

Two stopping rules are implemented in `prober/halting.py`:

- **window**: the gap is flat over the last 50 replies, the success rate is near `p`, and at least one rejection was seen.
- **cycle**: averages the gap over each stretch between rejections and stops when the last two of these averages agree within 0.3%. Clustered rejections count as one event.

The cycle rule takes somewhat longer, but its estimate is much closer to the value the prober actually settles at, and it does not stop early when many requests are in flight.

### Latency

`run_prober` simulates network delay. The limiter sees each request's arrival time, and the prober only learns the result one round trip later. Constant latency has no effect on spacing, but jitter does, and with high jitter relative to the gap the prober settles at a slower (safer) rate.

## Layout

```
prober/
  limiters.py     fixed-window and rolling-window simulators
  tuning.py       d/i/p formula
  smoothing.py    SMA, windowed EMA, geometric SMA
  halting.py      stopping rules
  core.py         event-driven prober loop with latency
experiments/
  run_scales.py   compare rules across limiter types and scales
  plot_trace.py   plot one run
tests/
results/          output plots and CSVs (not tracked)
```

## Running

Requires Python 3.10+.

```
pip install -r requirements.txt

python -m pytest
python -m experiments.run_scales
python -m experiments.run_scales --rtt 0.3 --jitter 0.1 --csv results/latency.csv
python -m experiments.plot_trace --limit 5 --window 10 --type fixed
```

Run `python -m experiments.run_scales --help` for all options (step size, target rate, smoothing window, starting gap, latency).

## Results (no latency, start at 0.5x true gap)

Replies until stop and error vs. true gap:

| Scale | Limiter | window rule | cycle rule |
|---|---|---|---|
| 5 per 10s | fixed | #204, -2.77% | #482, -0.92% |
| 5 per 10s | rolling | #172, +2.39% | #722, +0.48% |
| 20 per 5s | fixed | #275, -1.33% | #547, -0.80% |
| 20 per 5s | rolling | #277, +1.39% | #673, +0.38% |
| 100 per 1s | fixed | #1632, -0.93% | #1731, -0.79% |
| 100 per 1s | rolling | #1273, +0.11% | #1522, +0.02% |
| 50 per hour | fixed | #463, -0.46% | #713, -0.72% |
| 50 per hour | rolling | #299, +2.06% | #762, +0.16% |
| 3 per 0.3s | fixed | #199, -2.23% | #518, -0.87% |
| 3 per 0.3s | rolling | #516, +0.56% | #628, +0.26% |

These are single runs. Fixed windows settle about 0.8% below the true gap and rolling windows slightly above it.

## Known issues

- With large limits (several hundred or more per window), the first burst of `limit` successes drives the gap far too low, and the rejections that follow push it far too high. Shrinking `i` as the limit grows helps but slows settling.
- Starting from a gap that is too slow (above the true gap) takes much longer to settle than starting too fast.
- Results above come from one run per configuration; they should be repeated across seeds.
