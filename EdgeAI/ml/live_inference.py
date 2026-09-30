# ml/live_inference.py
# Reads live sensor data from the receiver over serial, buffers it into
# 1-second (90-sample) windows, extracts features, runs the trained model,
# and sends the prediction BACK to the receiver so it can drive the
# OLED/RGB LED/buzzer. Same serial connection used both ways.
#
# Requires firmware/receiver/receiver_final (the real live-inference
# receiver, NOT receiver_demo) to be flashed and listening for
# "PRED,<label>,<confidence>" lines on serial.

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
    print("Connected. Starting live inference (Ctrl+C to stop)...\n")

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

                # Fail loudly on a feature/model mismatch instead of letting
                # pandas silently fill missing columns with NaN and handing
                # the model garbage (which just looks like "uncertain
                # predictions" rather than the real bug it is).
                validate_features(list(features.keys()), model)

                feature_df = pd.DataFrame([features])
                feature_df = feature_df.reindex(columns=model.feature_names_in_)

                prediction = model.predict(feature_df)[0]
                probabilities = model.predict_proba(feature_df)[0]
                confidence = max(probabilities)

                timestamp = time.strftime("%H:%M:%S")
                print(f"[{timestamp}] Prediction: {prediction:25s} | Confidence: {confidence:.1%}")

                # Send prediction back to the receiver for OLED/LED/buzzer
                message = f"PRED,{prediction},{confidence:.3f}\n"
                ser.write(message.encode('utf-8'))

                window_buffer = []

    except ValueError as e:
        # Raised by validate_features() on a real feature/model mismatch -
        # stop instead of continuing to send meaningless predictions.
        print(f"\nStopped - feature mismatch: {e}")
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
