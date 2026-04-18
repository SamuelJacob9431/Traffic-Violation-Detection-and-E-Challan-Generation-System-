# iTUB (Intelligent Traffic Urban Bureau) 🚦

![iTUB Banner](https://img.shields.io/badge/AI-Traffic_Detection-blue?style=for-the-badge&logo=ai)
![Version](https://img.shields.io/badge/Version-1.0.0-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)

iTUB is a state-of-the-art **Smart Traffic Violation Detection & E-Challan System**. Leveraging the power of Computer Vision (YOLOv8) and Optical Character Recognition (EasyOCR), iTUB automates the monitoring of road safety and the enforcement of traffic laws in real-time.

---

## 🌟 Key Features

- **Real-time Detection**: Seamlessly detects vehicles (cars, motorcycles, buses, trucks) using YOLOv8.
- **Multimodal Violation Detection**:
    - 🔴 **Red Light Jump**: Automatically detects vehicles crossing the stop line during a red signal.
    - ⚡ **Over Speeding**: Calculates vehicle speed using time-distance tracking and flags offenders.
    - ⛑️ **Helmet Enforcement**: Deep learning model to identify riders without helmets.
    - 🛣️ **Wrong Lane Detection**: Identifies vehicles moving in restricted or incorrect lanes.
- **Automated E-Challan System**:
    - Extracts license plate numbers using EasyOCR.
    - Generates professional PDF challans with evidence images.
    - Automated email notifications to vehicle owners.
- **Interactive Dashboard**:
    - Real-time video feed with AI overlays.
    - Comprehensive analytics and violation logs.
    - Remote signal control and system configuration.
- **Resilient AI Engine**: Automatic fallback to recorded video if the live camera stream is interrupted.

---

## 🛠️ Technology Stack

| Component | Technology |
| :--- | :--- |
| **Logic/AI** | Python 3.9+, OpenCV, Ultralytics YOLOv8, EasyOCR |
| **Backend** | FastAPI, SQLAlchemy (SQLite), Uvicorn |
| **Frontend** | React, Vite, TailwindCSS, Framer Motion, Recharts |
| **Database** | SQLite (Production-ready abstraction available) |
| **Notification** | SMTP Email Integration |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** & **npm**
- **C++ Build Tools** (Required for processing libraries like EasyOCR)

### 1. Installation

Clone the repository and install the backend dependencies:

```bash
pip install -r requirements.txt
```

*(Note: If requirements.txt is missing, install manually: `pip install fastapi uvicorn sqlalchemy sqlalchemy-utils opencv-python ultralytics easyocr reportlab python-multipart requests jinja2 pyyaml`)*

Install the frontend dependencies:

```bash
cd frontend
npm install
```

### 2. Configuration

Adjust the system settings in `ai_engine/config.py`:
- `CAMERA_SOURCE`: Update to your RTSP/IP camera URL.
- `SPEED_LIMIT_KMH`: Set the threshold for speeding violations.
- `PROJECT_MODE`: Switch between `REAL` and `TOY` (for laboratory/demo setups).

### 3. Launching the System

Run the integrated startup script from the root directory:

```bash
python start_system.py
```

Access the interfaces:
- **Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 Project Structure

```text
├── ai_engine/          # YOLOv8 Detection, Tracking, and OCR logic
├── backend/            # FastAPI Server, Database models, and PDF engine
├── frontend/           # React Dashboard (Vite + Tailwind)
├── database/           # SQLite data storage
├── challans/           # Generated PDF evidence
├── evidence_images/    # Snapshots of detected violations
├── videos/             # Demo/Fallback video files
└── start_system.py     # Integrated system launcher
```

---

## 📊 Analytics & Reporting

iTUB provides a robust analytics suite that tracks:
- **Daily Trends**: Violation frequency over time.
- **Type Breakdown**: Distribution of violation types (Speeding vs Red Light, etc.).
- **Top Offenders**: Identification of recurring violators.
- **Revenue tracking**: Real-time status of pending and paid fines.

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.

---

## 👥 Contributors

- **Team SCP** - *Deep Learning & System Architecture*

---

*Built with ❤️ for a safer urban future.*
