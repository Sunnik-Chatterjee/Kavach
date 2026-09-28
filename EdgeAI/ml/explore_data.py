# ml/explore_data.py
# Combines all labeled CSV runs from data/raw/ into one dataset and
# does a first-pass sanity check before we train anything on it.
# (Operates on raw, per-sample rows - not windowed features - so it's
# fine that this still looks at temperature_C directly here: that's raw
# sensor data, not a model feature.)

import pandas as pd
import glob
import os

from config import RAW_DIR, COMBINED_DATA_PATH

DATA_DIR = RAW_DIR
OUTPUT_FILE = COMBINED_DATA_PATH


def main():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    print(f"Found {len(csv_files)} CSV files in {DATA_DIR}\n")

    if not csv_files:
        print("No CSV files found - check the path.")
        return

    dataframes = []
    for filepath in csv_files:
        df = pd.read_csv(filepath)
        dataframes.append(df)

    combined = pd.concat(dataframes, ignore_index=True)

    print(f"Combined dataset: {len(combined)} total rows, {len(combined.columns)} columns\n")

    print("=== Rows per class (fault_label) ===")
    print(combined["fault_label"].value_counts())
    print()

    print("=== Class balance check ===")
    counts = combined["fault_label"].value_counts()
    max_count = counts.max()
    min_count = counts.min()
    ratio = max_count / min_count
    print(f"Largest class: {counts.idxmax()} ({max_count} rows)")
    print(f"Smallest class: {counts.idxmin()} ({min_count} rows)")
    print(f"Imbalance ratio: {ratio:.2f}x")
    if ratio > 1.5:
        print("NOTE: Some imbalance present - worth keeping in mind for training, not urgent yet.")
    else:
        print("Classes are well balanced.")
    print()

    print("=== Quick sanity check: mean values per class (selected features) ===")
    key_features = ["bearing_ax", "bearing_ay", "bearing_az",
                     "current_mA", "temperature_C", "audio_rms"]
    print(combined.groupby("fault_label")[key_features].mean().round(2))
    print()

    print("=== Missing values check ===")
    missing = combined.isnull().sum()
    if missing.sum() == 0:
        print("No missing values - clean dataset.")
    else:
        print(missing[missing > 0])
    print()

    combined.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved combined dataset to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
