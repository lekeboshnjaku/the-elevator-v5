import json
from pathlib import Path

MATH = Path(__file__).resolve().parents[1] / 'math'

def write_jsonl(csv_path: Path, jsonl_out: Path):
    payouts = []
    with csv_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) != 3:
                continue
            try:
                payouts.append(int(parts[2]))
            except ValueError:
                continue
    uniq = sorted(set(payouts))
    with jsonl_out.open('w', encoding='utf-8', newline='\n') as out:
        for i, p in enumerate(uniq, start=1):
            out.write(json.dumps({'id': i, 'events': [{}], 'payoutMultiplier': p}, separators=(',', ':')) + '\n')


def main():
    write_jsonl(MATH / 'lookup_table_base.csv', MATH / 'game_logic_base.jsonl')
    write_jsonl(MATH / 'lookup_table_elevate.csv', MATH / 'game_logic_elevate.jsonl')
    print('Wrote JSONL files to', MATH)


if __name__ == '__main__':
    main()
