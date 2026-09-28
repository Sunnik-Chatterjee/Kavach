# BATCH DATA LOGGER
# Same as data_logger.py, but runs multiple repeats automatically per label
# and prompts you between classes (since rig changes are physical/manual).
# This is the version actually used for real data-collection sessions.

import serial
import csv
import time
import os

from features import FIELD_NAMES, parse_line
from config import COM_PORT, BAUD_RATE, RAW_DIR

OUTPUT_DIR = RAW_DIR


def log_one_run(ser, label, duration_sec, run_number):
    ser.reset_input_buffer()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{label}_{timestamp}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"\n--- Run {run_number}: '{label}' for {duration_sec}s -> {filepath} ---")

    rows_written = 0
    skipped = 0
    start_time = time.time()

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES + ["fault_label"])
        writer.writeheader()

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

    print(f"    Done: {rows_written} rows, {skipped} skipped -> {filename}")


def main():
    print("=== Batch Data Logger ===")
    print("Ctrl+C at any point to stop the current run or the whole batch.\n")

    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.\n")

    try:
        while True:
            label = input("Fault label for this batch (or 'quit' to stop): ").strip()
            if label.lower() == "quit":
                break

            num_runs = int(input("Number of runs: ").strip())
            duration_sec = float(input("Duration per run (seconds): ").strip())
            gap_sec = 5  # brief pause between repeat runs of the same label

            input(f"\nMake sure the rig is set up for '{label}', motor running steadily, then press Enter to start...")

            for run_number in range(1, num_runs + 1):
                log_one_run(ser, label, duration_sec, run_number)
                if run_number < num_runs:
                    print(f"Waiting {gap_sec}s before next run...")
                    time.sleep(gap_sec)

            print(f"\nBatch complete for '{label}'. {num_runs} runs saved.\n")
            print("=" * 50)

    except KeyboardInterrupt:
        print("\nBatch stopped by user.")
    finally:
        ser.close()
        print("Serial connection closed.")


if __name__ == "__main__":
    main()
