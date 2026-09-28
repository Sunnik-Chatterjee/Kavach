# ml/features.py
# Single definition of the raw serial line format and the windowed
# feature-extraction logic. Every script that touches raw sensor rows or
# feeds the trained model MUST import from here instead of redefining its
# own copy.
#
# Why this file exists: SENSOR_COLUMNS and extract_window_features() used
# to be copy-pasted independently into build_features.py, train_model.py,
# live_inference.py and diagnose_live.py. They drifted out of sync -
# build_features.py still included temperature_C after the model was
# retrained without it (temperature was found to be confounded with
# elapsed session time, not genuinely diagnostic - see project notes,
# 31 Aug). That made data/windowed_features.csv silently inconsistent
# with the deployed model. Centralizing this here makes that class of bug
# impossible: there is exactly one place that defines "what a window
# becomes."

import numpy as np
import pandas as pd

# Full set of fields the receiver prints per raw CSV/serial line.
FIELD_NAMES = [
    "bearing_ax", "bearing_ay", "bearing_az",
    "bearing_gx", "bearing_gy", "bearing_gz",
    "motor_ax", "motor_ay", "motor_az",
    "motor_gx", "motor_gy", "motor_gz",
    "bus_voltage", "current_mA", "power_mW",
    "temperature_C", "audio_rms",
    "packet_counter",
]

# Columns actually used as model features.
#   - temperature_C is deliberately excluded: it was confounded with how
#     far into the single recording session a sample was taken, not with
#     the actual fault condition (confirmed via live diagnostic, 31 Aug).
#   - packet_counter is excluded: it's a sequence ID, not a physical
#     measurement, and would leak run-order information instead of
#     teaching the model anything about fault behavior.
SENSOR_COLUMNS = [
    "bearing_ax", "bearing_ay", "bearing_az",
    "bearing_gx", "bearing_gy", "bearing_gz",
    "motor_ax", "motor_ay", "motor_az",
    "motor_gx", "motor_gy", "motor_gz",
    "bus_voltage", "current_mA", "power_mW",
    "audio_rms",
]

WINDOW_SIZE = 90  # ~1 second at the confirmed ~90Hz transmitter rate


def parse_line(line):
    """Splits one raw CSV line from the receiver into a dict of named,
    typed values. Returns None if the line is malformed (wrong field
    count, bad number) - callers should skip it, not crash."""
    parts = line.split(",")
    if len(parts) != len(FIELD_NAMES):
        return None
    try:
        values = [float(p) for p in parts]
    except ValueError:
        return None
    values[-1] = int(values[-1])  # packet_counter is an int
    return dict(zip(FIELD_NAMES, values))


def extract_window_features(window_rows):
    """Given ~WINDOW_SIZE rows of raw sensor data (a DataFrame, or any
    iterable of dicts keyed by FIELD_NAMES), compute mean/std/min/max/rms
    for each column in SENSOR_COLUMNS. This is the ONLY place this
    computation should be implemented - build_features.py, train_model.py,
    live_inference.py and diagnose_live.py all call this function so
    training and live inference can never silently diverge again."""
    df = window_rows if hasattr(window_rows, "columns") else pd.DataFrame(window_rows)

    features = {}
    for col in SENSOR_COLUMNS:
        values = df[col].values
        features[f"{col}_mean"] = np.mean(values)
        features[f"{col}_std"] = np.std(values)
        features[f"{col}_min"] = np.min(values)
        features[f"{col}_max"] = np.max(values)
        features[f"{col}_rms"] = np.sqrt(np.mean(values ** 2))
    return features


def validate_features(feature_names, model):
    """Raise a clear, immediate error if the features just computed don't
    match what the loaded model was actually trained on - instead of
    letting pandas silently reindex missing columns to NaN and handing
    the model a meaningless input (which looks like "noisy/uncertain
    predictions" rather than the real bug it is)."""
    expected = set(model.feature_names_in_)
    got = set(feature_names)
    if got != expected:
        missing = sorted(expected - got)
        extra = sorted(got - expected)
        raise ValueError(
            "Feature mismatch between computed features and the trained model.\n"
            f"  Model expects but features.py didn't compute: {missing}\n"
            f"  features.py computed but model wasn't trained on: {extra}\n"
            "This means SENSOR_COLUMNS in features.py doesn't match the "
            "data model.pkl was trained on - retrain the model against the "
            "current features.py, or check for a stale/wrong model.pkl."
        )
