import os
import csv

def inspect_datasets():
    dataset_dir = 'Dataset'
    files = sorted([f for f in os.listdir(dataset_dir) if f.endswith('.csv')])
    for filename in files:
        filepath = os.path.join(dataset_dir, filename)
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            first_row = next(reader, None)
            print(f"=== File: {filename} ===")
            print("Headers:", headers)
            print("Sample Row:", first_row)
            print("-" * 50)

if __name__ == "__main__":
    inspect_datasets()
