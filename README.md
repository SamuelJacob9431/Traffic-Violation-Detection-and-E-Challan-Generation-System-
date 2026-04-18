# Smart Traffic Violation Detection & E-Challan System

This system uses AI (YOLOv8 + EasyOCR) to detect traffic violations and generate automated e-challans.

## Prerequisites
- Python 3.9+
- Node.js & npm
- C++ Build Tools (for EasyOCR/PyTorch if not using pre-built binaries)

## Setup
1. **Install Python Dependencies**
   ```bash
   pip install fastapi uvicorn sqlalchemy sqlalchemy-utils opencv-python ultralytics easyocr reportlab python-multipart requests jinja2 pyyaml
   ```

2. **Install Frontend Dependencies**
   ```bash
   cd frontend
   npm install
   ```

## Running the System
Run the integrated startup script from the root directory:
```bash
python start_system.py
```

## Manual Mode / Demo
- **Signal Control**: Use the dashboard to manually toggle the signal (RED/GREEN).
- **Speed Limit**: Adjust the speed limit in the dashboard control panel.
- **RTSP Input**: Update line `CAMERA_SOURCE` in `ai_engine/config.py` to your IP Webcam URL.

## Project Structure
- `/ai_engine`: YOLOv8 detection, Tracking, and OCR logic.
- `/backend`: FastAPI server, SQLite database, and PDF generation.
- `/frontend`: React Dashboard with real-time logs and controls.
- `/data`: Storage for violation images and generated PDFs.
