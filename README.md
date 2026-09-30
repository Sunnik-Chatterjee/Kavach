# 🛡️ Project Kavach

> **Real-Time Industrial Edge AI for Predictive Maintenance & OT Cyber Security**
> Team LastMinuteHustlers — Tata Tech Innovent

---

## What is Kavach?

Kavach is an edge-AI system that monitors industrial motors in real time, predicts mechanical faults before they cause breakdowns, and detects cyber-physical security anomalies through power side-channel analysis — all on low-cost embedded hardware.

It combines vibration sensing, power monitoring, and acoustic measurement with a Random Forest classifier to give factory operators 15–20 minutes of early warning before a fault becomes a failure.

---

## Key Features

- **Real-time fault detection** — 90Hz sensor fusion (IMU + power + audio) classified every ~1 second
- **High accuracy** — Random Forest model with cross-validated evaluation using StratifiedGroupKFold
- **Cyber-physical security** — Power side-channel monitoring to detect anomalous PLC behavior
- **Human-in-the-Loop** — AI recommends actions, but a human operator must approve before anything happens
- **Edge deployment** — Runs on a Raspberry Pi / laptop connected to STM32 hardware

---

## System Architecture

```
STM32 Transmitter (bearing + motor IMU, power sensor, mic)
        │  wireless ~90Hz
        ▼
STM32 Receiver (aggregates + forwards over USB serial)
        │  460800 baud
        ▼
Inference Engine (Python, Random Forest, ~1 prediction/sec)
        │
        ├──▶  InfluxDB  (raw time-series sensor data)
        └──▶  SQLite    (predictions, alerts, operator sign-offs)
                │
                │  REST API + WebSocket (FastAPI)
                ▼
        React Dashboard (real-time charts, alerts, approval flow)
```

---

## Repository Structure

```
Kavach/
├── EdgeAI/
│   ├── firmware/
│   │   ├── transmitter/        STM32 transmitter firmware
│   │   └── receiver/
│   │       ├── receiver_demo/  Demo mode (pre-recorded data)
│   │       └── receiver_final/ Live inference receiver
│   ├── ml/
│   │   ├── config.py           Single source of truth for ports, paths, settings
│   │   ├── features.py         Feature extraction — centralised, never copy-pasted
│   │   ├── live_inference.py   Serial reader + ML inference loop
│   │   ├── diagnose_live.py    Same as above but with debug feature printout
│   │   ├── data_logger.py      Logs raw sensor data to CSV
│   │   ├── batch_data_logger.py Batch logging utility
│   │   ├── train_model.py      Trains Random Forest with StratifiedGroupKFold CV
│   │   ├── build_features.py   Builds windowed feature CSV from raw data
│   │   ├── explore_data.py     Data exploration / sanity checks
│   │   └── requirements.txt
│   └── data/
│       ├── model.pkl           Trained Random Forest model (~790KB)
│       ├── windowed_features.csv
│       └── confusion_matrix.png
├── .gitignore
└── README.md
```

---

## Sensor Channels

| Channel | Description |
|---|---|
| `bearing_ax/ay/az` | Bearing housing accelerometer (3-axis) |
| `bearing_gx/gy/gz` | Bearing housing gyroscope (3-axis) |
| `motor_ax/ay/az` | Motor body accelerometer (3-axis) |
| `motor_gx/gy/gz` | Motor body gyroscope (3-axis) |
| `bus_voltage` | DC bus voltage (V) |
| `current_mA` | Motor current draw (mA) |
| `power_mW` | Computed power consumption (mW) |
| `audio_rms` | Microphone RMS amplitude |
| `temperature_C` | Ambient temperature (logged but excluded from model — confounded) |

---

## ML Pipeline

Every 90 samples (~1 second at 90Hz), the inference engine computes 5 statistical features (mean, std, min, max, rms) for each of the 16 sensor channels, producing an 80-feature vector fed to the Random Forest.

```bash
# Run live inference
cd EdgeAI/ml
python live_inference.py

# Train the model
python train_model.py

# Log new raw data
python data_logger.py
```

---

## Hardware Setup

1. Flash `firmware/transmitter` to the sensor node (STM32)
2. Flash `firmware/receiver/receiver_final` to the receiver node (STM32)
3. Connect receiver to host PC via USB
4. Check the port: `ls /dev/ttyUSB* /dev/ttyACM*`
5. Update `EdgeAI/ml/config.py` → `COM_PORT` if needed
6. Run `python live_inference.py`

---

## Software (Coming Soon)

The backend API (FastAPI) and frontend dashboard (React) are being built as part of the second phase.
See the [implementation guide](docs/implementation_guide.md) for full details.

---

## Team

**LastMinuteHustlers** | Tata Tech Innovent Hackathon
