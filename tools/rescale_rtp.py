#!/usr/bin/env python3
import csv
import json
from pathlib import Path
from typing import Tuple


def compute_avg_multiplier(csv_path: Path) -> Tuple[float, int]:
    total_w = 0
    total_mult = 0
    max_mult = 0
    with csv_path.open('r', encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        for row in r:
            idx = int(row[0])
            w = int(row[1])
            m = int(row[2])
            total_w += w
            total_mult += w * m
            if m > max_mult:
                max_mult = m
    avg = total_mult / total_w if total_w else 0.0
    return avg, max_mult


def rescale_csv(csv_in: Path, csv_out: Path, scale: float):
    rows = []
    with csv_in.open('r', encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        for row in r:
            idx = int(row[0])
            w = int(row[1])
            m = int(row[2])
            if idx == 1:
                new_m = 0
            else:
                new_m = int(round(m / scale))
                if new_m < 0:
                    new_m = 0
            rows.append((idx, w, new_m))
    with csv_out.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)


def rescale_jsonl(jsonl_in: Path, jsonl_out: Path, scale: float):
    lines = []
    with jsonl_in.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if int(obj.get('id')) == 1:
                obj['payoutMultiplier'] = 0
            else:
                m = int(obj['payoutMultiplier'])
                m2 = int(round(m / scale))
                if m2 < 0:
                    m2 = 0
                obj['payoutMultiplier'] = m2
            # Ensure consistent minimal events representation
            obj['events'] = [{}]
            lines.append(json.dumps(obj, separators=(',', ':')))
    with jsonl_out.open('w', encoding='utf-8', newline='\n') as f:
        for ln in lines:
            f.write(ln + '\n')


def run(mode_name: str, target_rtp: float, jsonl_path: str, csv_path: str, scale_factor: int = 100):
    jsonl = Path(jsonl_path)
    csvp = Path(csv_path)

    avg_scaled, max_mult = compute_avg_multiplier(csvp)
    current_avg_x = avg_scaled / scale_factor
    target_avg_x = target_rtp / 100.0
    scale = current_avg_x / target_avg_x if target_avg_x > 0 else 1.0

    print(f"[{mode_name}] current_avg_x={current_avg_x:.6f}, target_avg_x={target_avg_x:.6f}, scale={scale:.6f}")

    # Write back in-place
    rescale_csv(csvp, csvp, scale)
    rescale_jsonl(jsonl, jsonl, scale)


if __name__ == '__main__':
    # Base and Elevate to 98.0% RTP
    run('base', 98.0, 'math/game_logic_base.jsonl', 'math/lookup_table_base.csv', 100)
    run('elevate', 98.0, 'math/game_logic_elevate.jsonl', 'math/lookup_table_elevate.csv', 100)
