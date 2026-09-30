# ml/config.py
# Shared configuration for every data-collection / training / inference
# script in this project. Single source of truth so COM_PORT, file paths,
# and the baud rate can't silently drift out of sync between scripts the
# way they did before (COM_PORT and BAUD_RATE were each hardcoded
# separately in 5 different files).
#
# Update values here once; every script imports from this file.

# ---- Serial connection to the receiver ----
# Linux device path, not a Windows COM port. Find yours with:
#   python -m serial.tools.list_ports
# or check `ls /dev/ttyUSB* /dev/ttyACM*` before/after plugging the receiver in.
COM_PORT = "/dev/ttyUSB0"   # update if the receiver enumerates on a different device
BAUD_RATE = 460800      # must match Serial.begin() in firmware/receiver/receiver_final

# ---- Data paths (relative to the ml/ folder, matching how scripts are run) ----
RAW_DIR = "../data/raw"
WINDOWED_FEATURES_PATH = "../data/windowed_features.csv"
COMBINED_DATA_PATH = "../data/combined_real_data.csv"
MODEL_PATH = "../data/model.pkl"
CONFUSION_MATRIX_PATH = "../data/confusion_matrix.png"

# ---- Sampling ----
WINDOW_SIZE = 90        # ~1 second of samples at the transmitter's confirmed ~90Hz rate
