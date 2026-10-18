#!/usr/bin/env python3
"""
Inject controlled MISSING DATA into a wearable CSV and record exactly what was removed.

Examples
--------
  # defaults: 10%, 25%, 50% missing, random pattern, value set to NaN
  python inject_missing.py heartrate_seconds_merged.csv --value-cols Value --id-col Id

  # contiguous gaps (sensor off / not worn) instead of scattered samples
  python inject_missing.py minuteStepsNarrow_merged.csv --value-cols Steps --id-col Id \
      --time-col ActivityMinute --pattern block --block-min 15 --block-max 120

  # custom levels, remove the rows entirely (a real gap in the file), 7-day window
  python inject_missing.py file.csv --value-cols Value --levels 0.05 0.3 --how drop

Outputs (in --out-dir, default ./missing_out)
  <name>_missing10.csv ...      corrupted file for each level (same columns as input)
  <name>_missing10_flags.csv    ground truth: one row per ORIGINAL row, with a
                                missing_<col> True/False column for each value column
  manifest.json                 parameters, seed, and target vs realized % per level/group/column
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def pick_blocks(n, n_target, min_len, max_len, rng):
    """Non-overlapping [start, end) blocks covering ~n_target positions out of n."""
    taken = np.zeros(n, bool)
    covered, tries = 0, 0
    while covered < n_target and tries < 20000:
        tries += 1
        remaining = n_target - covered
        length = int(rng.integers(min_len, max_len + 1))
        length = min(length, remaining, n)
        start = int(rng.integers(0, n - length + 1))
        if taken[start:start + length].any():
            continue
        taken[start:start + length] = True
        covered += length
    return taken


def build_masks(n, levels, pattern, seed_key, args):
    """Return {level: boolean mask of length n (True = make missing)}."""
    rng = np.random.default_rng([args.seed, *seed_key])
    masks = {}
    if pattern == "random":
        order = rng.permutation(n)  # one shuffle -> levels are NESTED (10% subset of 25% subset of 50%)
        for f in levels:
            m = np.zeros(n, bool)
            m[order[: int(round(f * n))]] = True
            masks[f] = m
    else:  # block: contiguous gaps, drawn independently per level
        for f in levels:
            masks[f] = pick_blocks(n, int(round(f * n)), args.block_min, args.block_max, rng)
    return masks


def run(args):
    path = Path(args.input)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(path)
    for c in args.value_cols + ([args.id_col] if args.id_col else []) + ([args.time_col] if args.time_col else []):
        if c not in df.columns:
            raise SystemExit(f"Column '{c}' not in file. Available: {list(df.columns)}")
    df["_orig_idx"] = df.index
    if args.time_col:
        df[args.time_col] = pd.to_datetime(df[args.time_col])

    # optional window: keep only the first N days per subject
    if args.window_days and args.time_col:
        grp = df.groupby(args.id_col)[args.time_col] if args.id_col else df[args.time_col]
        start = grp.transform("min")
        df = df[df[args.time_col] < start + pd.Timedelta(days=args.window_days)]

    groups = list(df.groupby(args.id_col, sort=True)) if args.id_col else [("all", df)]
    levels = sorted(args.levels)
    stem = path.stem
    summary = []
    result = {f: [] for f in levels}
    flag_result = {f: [] for f in levels}

    for gi, (gid, g) in enumerate(groups):
        g = g.sort_values(args.time_col, kind="stable") if args.time_col else g
        g = g.reset_index(drop=True)
        n = len(g)
        flags = {f: pd.DataFrame({"orig_idx": g["_orig_idx"]}) for f in levels}
        if args.id_col:
            for f in levels:
                flags[f][args.id_col] = g[args.id_col].values
        dropped = {f: np.zeros(n, bool) for f in levels}
        data = {f: g.copy() for f in levels}

        for ci, col in enumerate(args.value_cols):
            already_na = g[col].isna().values
            masks = build_masks(n, levels, args.pattern, (gi, ci), args)
            for f in levels:
                m = masks[f]
                flags[f][f"missing_{col}"] = m
                if args.how == "nan":
                    data[f].loc[m, col] = np.nan
                else:
                    dropped[f] |= m  # 'drop' removes the whole row
                summary.append({
                    "level_target": f, "group": str(gid), "column": col, "pattern": args.pattern,
                    "how": args.how, "n_rows": n, "n_made_missing": int(m.sum()),
                    "realized_fraction": round(float(m.mean()), 5) if n else None,
                    "n_already_missing_in_source": int(already_na.sum()),
                })

        for f in levels:
            d = data[f]
            if args.how == "drop":
                d = d[~dropped[f]]
                flags[f]["row_removed"] = dropped[f]
            result[f].append(d)
            flag_result[f].append(flags[f])

    for f in levels:
        tag = f"missing{int(round(f * 100))}"
        out = pd.concat(result[f]).drop(columns="_orig_idx")
        out.to_csv(out_dir / f"{stem}_{tag}.csv", index=False)
        pd.concat(flag_result[f]).to_csv(out_dir / f"{stem}_{tag}_flags.csv", index=False)
        print(f"{f:>5.0%} missing -> {out_dir / (stem + '_' + tag + '.csv')}")

    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(path), "seed": args.seed, "levels": levels, "pattern": args.pattern,
        "how": args.how, "value_cols": args.value_cols, "id_col": args.id_col, "time_col": args.time_col,
        "block_min": args.block_min if args.pattern == "block" else None,
        "block_max": args.block_max if args.pattern == "block" else None,
        "window_days": args.window_days, "realized": summary,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"Manifest -> {out_dir / 'manifest.json'}")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="input CSV file")
    ap.add_argument("--value-cols", nargs="+", required=True, help="column(s) to make missing")
    ap.add_argument("--id-col", help="subject column; missingness is applied per subject")
    ap.add_argument("--time-col", help="time column (needed for --window-days; orders rows for block mode)")
    ap.add_argument("--levels", nargs="+", type=float, default=[0.10, 0.25, 0.50],
                    help="fractions of rows to make missing (default 0.10 0.25 0.50)")
    ap.add_argument("--pattern", choices=["random", "block"], default="random",
                    help="random = scattered samples; block = contiguous gaps")
    ap.add_argument("--how", choices=["nan", "drop"], default="nan",
                    help="nan = keep row, blank the value; drop = remove the row entirely")
    ap.add_argument("--block-min", type=int, default=10, help="min block length in ROWS (block pattern)")
    ap.add_argument("--block-max", type=int, default=60, help="max block length in ROWS (block pattern)")
    ap.add_argument("--window-days", type=int, help="keep only first N days per subject (needs --time-col)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", default="missing_out")
    args = ap.parse_args(argv)
    if any(not 0 < f < 1 for f in args.levels):
        ap.error("--levels must be fractions between 0 and 1, e.g. 0.10 0.25 0.50")
    if args.window_days and not args.time_col:
        ap.error("--window-days needs --time-col")
    return args


if __name__ == "__main__":
    run(parse_args())
