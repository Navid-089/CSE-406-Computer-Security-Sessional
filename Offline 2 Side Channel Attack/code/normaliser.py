import os
import json
from tqdm import tqdm  # Progress bar

BASE_DIR = "offline-2-datasets-security"
INPUT_FILENAME = "dataset.json"
OUTPUT_FILENAME = "dataset_normalised.json"

def normalize_dataset_globally(data):
    # Flatten all values from all traces to get global min and max
    all_values = [val for record in data for val in record['trace_data']]
    min_val = min(all_values)
    max_val = max(all_values)
    if max_val == min_val:
        return [ [0.0] * len(record['trace_data']) for record in data ]

    # Normalize each trace using global min and max
    normalized_traces = [
        [(x - min_val) / (max_val - min_val + 1e-8) for x in record['trace_data']]
        for record in data
    ]
    return normalized_traces

def process_folder(folder_path):
    input_path = os.path.join(folder_path, INPUT_FILENAME)
    output_path = os.path.join(folder_path, OUTPUT_FILENAME)

    if not os.path.exists(input_path):
        print(f"Skipping {folder_path}, no {INPUT_FILENAME} found.")
        return

    with open(input_path, 'r') as f:
        data = json.load(f)

    # Normalize all traces using a global min/max for this folder
    normalized_traces = normalize_dataset_globally(data)

    for record, norm_trace in zip(data, normalized_traces):
        record['trace_data'] = norm_trace

    with open(output_path, 'w') as f:
        json.dump(data, f)

    print(f"✔ Normalized and saved: {output_path}")

def main():
    for folder_name in tqdm(os.listdir(BASE_DIR)):
        folder_path = os.path.join(BASE_DIR, folder_name)
        if os.path.isdir(folder_path):
            process_folder(folder_path)

if __name__ == "__main__":
    main()
