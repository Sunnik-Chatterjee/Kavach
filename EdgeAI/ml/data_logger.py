# FINAL DATA LOGGER
# Reads live sensor CSV from the receiver over serial, prompts for a fault
# label and duration, and saves a labeled CSV file into data/raw/
#
# Run from: C:\Users\sujal\Documents\EdgeAI\ml>  python data_logger.py
#
# NOTE: batch_data_logger.py is the version actually used for the real
# data-collection sessions (auto-repeats runs per class). This single-run
# version is kept for quick one-off tests.

import serial
import csv
import time
import os

from features import FIELD_NAMES, parse_line
from config import COM_PORT, BAUD_RATE, RAW_DIR

OUTPUT_DIR = RAW_DIR


def main():
    label = input("Fault label for this run (e.g. healthy, bearing_fault): ").strip()
    duration_sec = float(input("Duration in seconds: ").strip())

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"\nConnecting to {COM_PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"Logging '{label}' for {duration_sec} seconds -> {filepath}\n")

    rows_written = 0
    skipped = 0
    start_time = time.time()

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES + ["fault_label"])
        writer.writeheader()

        try:
            while (time.time() - start_time) < duration_sec:
                raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not raw_line:
                    continue

                data = parse_line(raw_line)
                if data is None:
                    skipped += 1
                    continue

                data["fault_label"] = label
                writer.writerow(data)
                rows_written += 1

                if rows_written % 100 == 0:
                    elapsed = time.time() - start_time
                    print(f"  {rows_written} rows written | {elapsed:.1f}s elapsed")

        except KeyboardInterrupt:
            print("\nStopped early by user.")
        finally:
            ser.close()

    print(f"\nDone. {rows_written} rows written, {skipped} lines skipped (malformed).")
    print(f"Saved to: {filepath}")


if __name__ == "__main__":
    main()
