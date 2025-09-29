# This script normalizes the weights in lookup_table_elevate.csv to probabilities for Stake Engine upload
import csv

input_path = 'stake_engine_upload/math/lookup_table_elevate.csv'
output_path = 'stake_engine_upload/math/lookup_table_elevate_normalized.csv'

rows = []
total_weight = 0

# Read all rows and sum weights
with open(input_path, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) < 2:
            continue
        multiplier = row[0]
        weight = float(row[1])
        extra = row[2] if len(row) > 2 else '0'
        rows.append([multiplier, weight, extra])
        total_weight += weight

# Write normalized file
with open(output_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    for multiplier, weight, extra in rows:
        prob = weight / total_weight if total_weight > 0 else 0
        writer.writerow([multiplier, f'{prob:.8f}', extra])

print(f'Normalized file written to {output_path}')
