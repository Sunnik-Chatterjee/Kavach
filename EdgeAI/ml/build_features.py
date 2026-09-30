# ml/build_features.py
# Converts raw per-sample sensor CSVs into windowed statistical features
# and saves them to data/windowed_features.csv.
#
# NOTE: this is an EXPLORATION / dataset-inspection tool only.
# train_model.py rebuilds features itself directly from data/raw (with
# per-run group tracking for cross-validation) and does NOT read
# data/windowed_features.csv - so this script's output is useful for
# eyeballing the feature table, but it is not what the deployed model
# was trained on. Don't assume windowed_features.csv reflects model.pkl;
# re-run train_model.py if you need the authoritative training data.

import pandas as pd
import glob
import os

from features import extract_window_features, WINDOW_SIZE
from config import RAW_DIR, WINDOWED_FEATURES_PATH

DATA_DIR = RAW_DIR
OUTPUT_FILE = WINDOWED_FEATURES_PATH


def process_file(filepath):
    """Splits one raw CSV file into non-overlapping windows and extracts
       features from each. Returns a list of feature dicts."""
    df = pd.read_csv(filepath)
    fault_label = df["fault_label"].iloc[0]  # same label for the whole file

    rows = []
    num_windows = len(df) // WINDOW_SIZE  # drop incomplete trailing window

    for i in range(num_windows):
        start = i * WINDOW_SIZE
        end = start + WINDOW_SIZE
        window_df = df.iloc[start:end]

        features = extract_window_features(window_df)
        features["fault_label"] = fault_label
        rows.append(features)

    return rows


def main():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    print(f"Found {len(csv_files)} raw CSV files\n")

    all_rows = []
    for filepath in csv_files:
        rows = process_file(filepath)
        all_rows.extend(rows)
        print(f"  {os.path.basename(filepath)}: {len(rows)} windows")

    result_df = pd.DataFrame(all_rows)

    print(f"\nTotal windows (feature rows): {len(result_df)}")
    print(f"Total features per row: {len(result_df.columns) - 1}")  # -1 for fault_label
    print(f"\nWindows per class:")
    print(result_df["fault_label"].value_counts())

    result_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
