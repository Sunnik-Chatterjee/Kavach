# ml/diagnose_live.py
# Same as live_inference.py, but also prints the raw feature values used
# for each prediction - specifically bearing accel and bus voltage - so we
# can directly compare live values against known per-class training averages.

import serial
import pandas as pd
import joblib
import time

from features import extract_window_features, parse_line, validate_features, WINDOW_SIZE
from config import COM_PORT, BAUD_RATE, MODEL_PATH


def main():
    print("Loading trained model...")
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded. Classes: {list(model.classes_)}\n")

    print(f"Connecting to {COM_PORT} at {BAUD_RATE} baud...")
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    print("Connected. Starting diagnostic (Ctrl+C to stop)...\n")

    window_buffer = []

    try:
        while True:
            raw_line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not raw_line:
                continue

            data = parse_line(raw_line)
            if data is None:
                continue

            window_buffer.append(data)

            if len(window_buffer) >= WINDOW_SIZE:
                features = extract_window_features(window_buffer)
                validate_features(list(features.keys()), model)

                feature_df = pd.DataFrame([features])
                feature_df = feature_df.reindex(columns=model.feature_names_in_)

                prediction = model.predict(feature_df)[0]
                probabilities = model.predict_proba(feature_df)[0]
                confidence = max(probabilities)

                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Prediction: {prediction:20s} | Confidence: {confidence:.1%}")
                print(f"    bearing_ax_mean     = {features['bearing_ax_mean']:.2f}")
                print(f"    bearing_ay_mean     = {features['bearing_ay_mean']:.2f}")
                print(f"    bus_voltage_mean    = {features['bus_voltage_mean']:.2f}")
                print()

                window_buffer = []

    except ValueError as e:
        print(f"\nStopped - feature mismatch: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
