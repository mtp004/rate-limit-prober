"""Plot the gap over time for one limiter.

    python -m experiments.plot_trace --limit 5 --window 10 --type fixed
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from prober import LIMITERS, SMOOTHERS, HALT_RULES, run_prober, solve_decrease_frac


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--window", type=float, default=10.0)
    ap.add_argument("--type", choices=LIMITERS, default="fixed")
    ap.add_argument("--i", type=float, default=0.60)
    ap.add_argument("--p", type=float, default=0.99)
    ap.add_argument("--ma", type=int, default=100)
    ap.add_argument("--start", type=float, default=0.5)
    ap.add_argument("--n", type=int, default=6000)
    ap.add_argument("--out", type=Path, default=Path("results/trace.png"))
    args = ap.parse_args()

    true_gap = args.window / args.limit
    d = solve_decrease_frac(args.i, args.p)
    res = run_prober(
        LIMITERS[args.type](args.limit, args.window),
        initial_gap=true_gap * args.start,
        decrease_frac=d, increase_frac=args.i,
        smoother=SMOOTHERS["sma"](args.ma),
        halt_rule=HALT_RULES["none"](),
        n_iters=args.n,
    )

    gaps = np.array([g for _, g, _ in res.trace])
    oks = np.array([ok for _, _, ok in res.trace])
    x = np.arange(len(gaps))
    tail = gaps[int(0.8 * len(gaps)):]
    avg = tail.mean()

    fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 8))

    top.plot(x, gaps, lw=1, label="gap")
    top.scatter(x[~oks], gaps[~oks], s=10, c="tab:red", zorder=3, label="rejected")
    top.axhline(true_gap, ls="--", c="tab:green", lw=2, label=f"true gap ({true_gap:g}s)")
    top.set_title(f"{args.type} window, {args.limit} per {args.window:g}s")
    top.set_xlabel("request #")
    top.set_ylabel("gap (s)")
    top.legend(loc="lower right")
    top.grid(alpha=0.3)

    z = slice(max(0, len(gaps) - 600), len(gaps))
    bottom.plot(x[z], gaps[z], lw=1.2)
    bottom.scatter(x[z][~oks[z]], gaps[z][~oks[z]], s=18, c="tab:red", zorder=3)
    bottom.axhline(true_gap, ls="--", c="tab:green", lw=2, label="true gap")
    bottom.axhline(avg, c="k", lw=1.5,
                   label=f"tail average {avg:.4g}s ({100 * (avg / true_gap - 1):+.2f}%)")
    bottom.set_title("last 600 requests")
    bottom.set_xlabel("request #")
    bottom.set_ylabel("gap (s)")
    bottom.legend(loc="upper left")
    bottom.grid(alpha=0.3)

    plt.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out, dpi=130)
    print(f"saved {args.out}")


if __name__ == "__main__":
    main()
