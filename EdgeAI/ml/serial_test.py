# serial_test.py
# Reads live sensor CSV from the receiver over serial and parses each line
# into named, typed fields. No file logging - just prints parsed values.
# (data_logger.py / batch_data_logger.py are the versions to use for actual
# labeled data collection - this file is kept for reference/quick
# connectivity checks only.)

from features import FIELD_NAMES, parse_line
from config import COM_PORT, BAUD_RATE

import serial


def main():
    print(f"Connecting to {COM_PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print("Connected. Reading and parsing (Ctrl+C to stop)...\n")

    try:
        while True:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not raw_line:
                continue

            data = parse_line(raw_line)
            if data is None:
                print(f"[SKIPPED - malformed] {raw_line}")
                continue

            print(f"Packet #{data['packet_counter']} | "
                  f"Bearing accel: ({data['bearing_ax']:.2f}, {data['bearing_ay']:.2f}, {data['bearing_az']:.2f}) | "
                  f"Temp: {data['temperature_C']:.1f}C | "
                  f"Audio RMS: {data['audio_rms']:.0f}")

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
