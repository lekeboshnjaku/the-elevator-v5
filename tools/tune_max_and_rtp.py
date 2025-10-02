#!/usr/bin/env python3
import csv
import json
from pathlib import Path


def read_csv(path: Path):
    rows = []
    with path.open('r', encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        for row in r:
            rows.append([int(row[0]), int(row[1]), int(row[2])])
    return rows


def write_csv(path: Path, rows):
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)


def read_jsonl(path: Path):
    items = []
    with path.open('r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            items.append(obj)
    return items


def write_jsonl(path: Path, items):
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for obj in items:
            obj['events'] = [{}]
            f.write(json.dumps(obj, separators=(',', ':')) + '\n')


def compute_totals(rows):
    total_w = 0
    total_mult = 0
    max_m = -1
    max_row_index = -1
    for i, (idx, w, m) in enumerate(rows):
        total_w += w
        total_mult += w * m
        if m > max_m:
            max_m = m
            max_row_index = i
    return total_w, total_mult, max_row_index, max_m


def tune_mode(name: str, csv_path: str, jsonl_path: str, target_max: int, target_avg_x: float, scale: int = 100):
    csvp = Path(csv_path)
    jsonp = Path(jsonl_path)
    rows = read_csv(csvp)
    items = read_jsonl(jsonp)

    total_w, total_mult, max_row_idx, current_max = compute_totals(rows)
    current_avg_x = (total_mult / total_w) / scale
    target_total_mult = int(round(target_avg_x * scale * total_w))

    # Step 1: force the maximum payout to target_max
    # Find index in CSV and JSONL
    # Ensure id=1 remains 0
    assert items[0]['id'] == 1 and items[0]['payoutMultiplier'] == rows[0][2] == 0

    # ensure we know the max row by payout (not necessarily last id)
    max_id_csv = rows[max_row_idx][0]
    # Set both CSV and JSONL for that id to target_max
    delta_max = target_max - rows[max_row_idx][2]
    rows[max_row_idx][2] = target_max
    # Update JSONL item with same id
    for obj in items:
        if int(obj['id']) == max_id_csv:
            obj['payoutMultiplier'] = target_max
            break

    # Step 2: scale all other multipliers by a common factor k to hit the target
    # Compute S_target and S after applying max change
    S_after_max = total_mult + rows[max_row_idx][1] * delta_max
    # Contribution of others (exclude max row and also zero payout rows contribute 0 regardless)
    S_others_old = 0
    for i, (idx, w, m) in enumerate(rows):
        if i == max_row_idx:
            continue
        S_others_old += w * m

    # Desired contribution from others
    S_others_target = target_total_mult - rows[max_row_idx][1] * target_max

    # If S_others_target < 0, clamp to 0 (others cannot be negative)
    S_others_target = max(0, S_others_target)

    # Compute scaling factor k
    k = 0.0
    if S_others_old > 0:
        k = S_others_target / S_others_old

    # Apply scaling to others with rounding
    for i, (idx, w, m) in enumerate(rows):
        if i == max_row_idx:
            continue
        if m == 0:
            rows[i][2] = 0
        else:
            rows[i][2] = max(0, int(round(m * k)))

    # Recompute total and fix residual with greedy ±1 adjustments
    def current_sum():
        return sum(w * m for _, w, m in rows)

    S_now = current_sum()
    delta = S_now - target_total_mult

    if delta != 0:
        # Exclude zero-payout row (id=1) and max row from residual fixing
        candidates = [
            i for i in range(len(rows))
            if i not in (0, max_row_idx) and rows[i][1] > 0
        ]
        if delta > 0:
            # Need to reduce sum: decrement high-weight rows first
            candidates.sort(key=lambda i: (rows[i][1], rows[i][2]), reverse=True)
            for i in candidates:
                if delta <= 0:
                    break
                w = rows[i][1]
                m = rows[i][2]
                if m <= 0:
                    continue
                drop_units = min(m, (delta + w - 1) // w)
                if drop_units > 0:
                    rows[i][2] = m - drop_units
                    delta -= drop_units * w
        else:
            # Need to increase sum: increment low-weight rows first, and cap below max
            delta = -delta
            candidates.sort(key=lambda i: (rows[i][1], rows[i][2]))
            # Each increment of 1 on row i adds rows[i][1] to the sum
            for i in candidates:
                if delta <= 0:
                    break
                w = rows[i][1]
                m = rows[i][2]
                cap = max(0, target_max - 1 - m)
                if cap <= 0:
                    continue
                inc_units = min(cap, (delta + w - 1) // w)
                if inc_units > 0:
                    rows[i][2] = m + inc_units
                    delta -= inc_units * w

    # Reflect CSV multipliers back into JSONL items by id map
    mp = {idx: m for idx, _, m in rows}
    for obj in items:
        idx = int(obj['id'])
        obj['payoutMultiplier'] = int(mp[idx])

    # Write files back
    write_csv(csvp, rows)
    write_jsonl(jsonp, items)

    # Report
    final_total_w, final_total_mult, _, final_max = compute_totals(rows)
    final_avg_x = (final_total_mult / final_total_w) / scale
    print(f"[{name}] final_avg_x={final_avg_x:.6f}, final_max={final_max}")


if __name__ == '__main__':
    # Base: max 1,000,000 (x100), nudge target avg slightly above to counter rounding
    tune_mode('base', 'math/lookup_table_base.csv', 'math/game_logic_base.jsonl', 1_000_000, 0.985, 100)
    # Elevate: max 10,000,000 (x100), target avg 0.98x
    tune_mode('elevate', 'math/lookup_table_elevate.csv', 'math/game_logic_elevate.jsonl', 10_000_000, 0.98, 100)
