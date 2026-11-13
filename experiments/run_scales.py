"""Compare halting rules across limiter types, scales, and latency settings.

    python -m experiments.run_scales
    python -m experiments.run_scales --start 3.0 --rtt 0.3 --jitter 0.1
"""
import argparse
import csv
from pathlib import Path

from prober import LIMITERS, SMOOTHERS, HALT_RULES, run_prober, solve_decrease_frac

SCALES = [
    # name, limit, window (s)
    ("5 per 10s", 5, 10.0),
    ("Strict API", 20, 5.0),
    ("Burst-friendly", 100, 1.0),
    ("Very slow/daily", 50, 3600.0),
    ("Tiny/fast", 3, 0.3),
]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--i", type=float, default=0.60, help="increase fraction")
    ap.add_argument("--p", type=float, default=0.99, help="target success rate")
    ap.add_argument("--ma", type=int, default=100, help="smoothing window")
    ap.add_argument("--smoother", choices=SMOOTHERS, default="sma")
    ap.add_argument("--start", type=float, default=0.5, help="initial gap as a multiple of the true gap")
    ap.add_argument("--rtt", type=float, default=0.0)
    ap.add_argument("--jitter", type=float, default=0.0)
    ap.add_argument("--rules", nargs="+", default=["window", "cycle"], choices=HALT_RULES)
    ap.add_argument("--n", type=int, default=30000, help="max replies per run")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--csv", type=Path, default=None, help="also write results to this file")
    return ap.parse_args()


def main():
    args = parse_args()
    d = solve_decrease_frac(args.i, args.p)
    print(f"i={args.i}  p={args.p}  d={d:.6f}  ma={args.ma}  smoother={args.smoother}  "
          f"start={args.start}x  rtt={args.rtt}s  jitter={args.jitter}s\n")

    rows = []
    header = f"{'scale':16s} {'limiter':8s}" + "".join(f" | {r:>20s}" for r in args.rules)
    print(header)
    print("-" * len(header))

    for name, limit, window in SCALES:
        true_gap = window / limit
        for lim_name, lim_cls in LIMITERS.items():
            line = f"{name:16s} {lim_name:8s}"
            for rule in args.rules:
                res = run_prober(
                    lim_cls(limit, window),
                    initial_gap=true_gap * args.start,
                    decrease_frac=d,
                    increase_frac=args.i,
                    smoother=SMOOTHERS[args.smoother](args.ma),
                    halt_rule=HALT_RULES[rule](args.p),
                    rtt=args.rtt, jitter=args.jitter,
                    n_iters=args.n, seed=args.seed,
                )
                err = 100 * (res.estimate - true_gap) / true_gap
                cell = f"#{res.stopped_at} {err:+.2f}%" if res.converged else f"none {err:+.2f}%"
                line += f" | {cell:>20s}"
                rows.append(dict(scale=name, limit=limit, window=window, limiter=lim_name,
                                 rule=rule, stopped_at=res.stopped_at,
                                 estimate=res.estimate, true_gap=true_gap, err_pct=err,
                                 max_in_flight=res.max_in_flight))
            print(line)

    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {args.csv}")


if __name__ == "__main__":
    main()
