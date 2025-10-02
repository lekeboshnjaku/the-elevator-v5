#!/usr/bin/env python3
import csv
import json
from pathlib import Path


def load_multipliers(jsonl_path: Path) -> dict[int, int]:
    mp = {}
    with jsonl_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            mp[int(data['id'])] = int(data['payoutMultiplier'])
    return mp


def load_weights(csv_path: Path) -> list[tuple[int, int, int]]:
    rows = []
    with csv_path.open('r', encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        for row in r:
            idx = int(row[0])
            wt = int(row[1])
            mult = int(row[2])
            rows.append((idx, wt, mult))
    return rows


def metrics(mode_name: str, cost_minor: int, jsonl_path: str, csv_path: str, scale: int = 100):
    jsonl = Path(jsonl_path)
    csvp = Path(csv_path)
    mp = load_multipliers(jsonl)
    rows = load_weights(csvp)

    total_w = 0
    total_mult = 0
    max_mult = 0
    zero_w = 0
    for idx, wt, mult in rows:
        total_w += wt
        total_mult += wt * mult
        max_mult = max(max_mult, mult)
        if wt == 0:
            zero_w += 1

    avg_mult_scaled = total_mult / total_w if total_w else 0
    avg_mult_x = avg_mult_scaled / scale
    # Expected average payout in minor units given bet=cost_minor
    avg_win_minor = cost_minor * avg_mult_x
    rtp_pct = (avg_win_minor / cost_minor) * 100 if cost_minor else 0

    print(f"Mode: {mode_name}")
    print(f"  Cost (minor): {cost_minor}")
    print(f"  Scale: x{scale}")
    print(f"  Total weight: {total_w}")
    print(f"  Zero-weight rows: {zero_w}")
    print(f"  Avg multiplier (x): {avg_mult_x:.6f}")
    print(f"  Avg win (minor): {avg_win_minor:.6f}")
    print(f"  RTP %: {rtp_pct:.4f}%")
    print(f"  Max multiplier (x): {max_mult/scale:.2f}x")


if __name__ == "__main__":
    metrics("base", 100, "math/game_logic_base.jsonl", "math/lookup_table_base.csv", scale=100)
    print()
    metrics("elevate", 300, "math/game_logic_elevate.jsonl", "math/lookup_table_elevate.csv", scale=100)
