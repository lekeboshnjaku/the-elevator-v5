#!/usr/bin/env python3
import csv
from pathlib import Path

"""
Adjust lookup_table_elevate.csv by replacing zero weights with 1.
Keeps row order and multiplier values unchanged.
"""

CSV_PATH = Path('math/lookup_table_elevate.csv')

def main():
    if not CSV_PATH.exists():
        print(f"ERROR: {CSV_PATH} not found")
        return 1

    rows = []
    zeros = 0
    total_before = 0
    with CSV_PATH.open('r', encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        for row in r:
            if not row:
                continue
            idx, w, mult = row[0], row[1], row[2]
            w_int = int(w)
            total_before += w_int
            if w_int == 0:
                zeros += 1
                w_int = 1
            rows.append((idx, str(w_int), mult))

    total_after = sum(int(w) for _, w, _ in rows)

    with CSV_PATH.open('w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)

    print(f"Processed: {CSV_PATH}")
    print(f"  Zero weights replaced: {zeros}")
    print(f"  Total weight before:   {total_before}")
    print(f"  Total weight after:    {total_after}")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
