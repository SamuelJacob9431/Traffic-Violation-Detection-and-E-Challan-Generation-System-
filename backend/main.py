from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import uuid
from datetime import datetime, timezone, timedelta

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv()

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

from backend.models import SessionLocal, Violation, Vehicle, VehicleOwner, User, SystemSettings
from backend.video_stream import video_stream
from ai_engine.config import SIGNAL_STATUS, CAMERA_SOURCE
from backend.pdf_generator import generate_challan_pdf
from backend.email_service import send_violation_email, send_payment_confirmation

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Smart City Traffic Control API")

# Mount static directories
os.makedirs("data/violations", exist_ok=True)
os.makedirs("challans", exist_ok=True)
os.makedirs("evidence_images", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")
app.mount("/challans", StaticFiles(directory="challans"), name="challans")
app.mount("/evidence_images", StaticFiles(directory="evidence_images"), name="evidence_images")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# DB dependency
# ==============================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================================================================
# Mock owner data (seeded on startup)
# ==============================================================================
MOCK_OWNERS = [
    {"plate": "DEMO-001",   "name": "Nitu Prasad",    "email": "nituprasad5113@gmail.com"},
    {"plate": "DEMO-002",   "name": "Raunak Prasad",  "email": "prasadraunak644@gmail.com"},
    {"plate": "DEMO-003",   "name": "Prasad Graphics","email": "prasadgraphics3@gmail.com"},
    {"plate": "JURY-TEST",  "name": "Karan Thakur",   "email": "karanthakur.23.cse@iite.indusuni.ac.in"},
    {"plate": "VIP-007",    "name": "Sonika Rai",    "email": "sonikamajhi20@gmail.com"},
    {"plate": "GJ01AB1234", "name": "CHODU KATIK KIRAN",      "email": "kartikprasad.23.cse@iite.indusuni.ac.in"},
    {"plate": "MH12CD5678", "name": "NISHITH KUMAR",    "email": "kumarnishith.23.cse@iite.indusuni.ac.in"},
    {"plate": "DL08EF9012", "name": "Nitu Prasad",   "email": "nituprasd256@gmail.com"},
    {"plate": "DN09N8531", "name": "Adarsh Gupta",   "email": "adarshgupta202020@gmail.com"},
]

def seed_owners(db: Session):
    """UPSERT mock owners - always syncs email on every server restart."""
    for o in MOCK_OWNERS:
        existing = db.query(VehicleOwner).filter(VehicleOwner.plate_number == o["plate"]).first()
        if existing:
            existing.owner_name = o["name"]
            existing.email = o["email"]  # always sync so stale emails get fixed
        else:
            db.add(VehicleOwner(plate_number=o["plate"], owner_name=o["name"], email=o["email"]))
    db.commit()

def get_owner(plate: str, db: Session):
    # 1. Direct lookup
    owner = db.query(VehicleOwner).filter(VehicleOwner.plate_number == plate).first()
    if owner:
        return owner.owner_name, owner.email
    
    # 2. Dynamic Mapping for DEMO tags (DEMO-0173, etc.)
    # This ensures every "DEMO" car is assigned to one of our real accounts
    if plate.startswith("DEMO-"):
        try:
            # Extract number from DEMO-XXXX
            num_part = plate.split("-")[1]
            num = int(''.join(filter(str.isdigit, num_part)))
            
            # Fetch all mock owners to rotate through them
            all_owners = db.query(VehicleOwner).all()
            if all_owners:
                index = num % len(all_owners)
                return all_owners[index].owner_name, all_owners[index].email
        except:
            pass

    return "Vehicle Owner", os.environ.get("EMAIL_ADDRESS", "smarttraffic.ai.demo@gmail.com")

def _update_violation_pdf(v: Violation, db: Session) -> str:
    """Helper to generate/update PDF ensured to match CURRENT database state."""
    plate = v.vehicle.plate_number if v.vehicle else "-"
    owner_name, owner_email = get_owner(plate, db)
    
    os.makedirs("challans", exist_ok=True)
    challan_no = v.challan_number or f"CH-{v.id}"
    pdf_path = f"challans/{challan_no}.pdf"
    
    pdf_data = {
        "id": v.id,
        "challan_number": challan_no,
        "plate_number": plate,
        "owner_name": owner_name,
        "owner_email": owner_email,
        "type": v.violation_type,
        "timestamp": v.timestamp or datetime.now(),
        "fine": v.fine_amount,
        "location": v.location or "Main Junction - Signal 01",
        "image_path": v.image_path or "",
        "payment_status": v.payment_status,
        "payment_date": v.payment_date,
    }
    
    try:
        generate_challan_pdf(pdf_data, pdf_path)
    except Exception as e:
        print(f"[ERROR] PDF Generation Error: {e}")
        # Log more details for debugging
        import traceback
        traceback.print_exc()
        raise e
        
    if v.challan_pdf_path != pdf_path:
        v.challan_pdf_path = pdf_path
        db.commit()
    return pdf_path

def seed_settings(db: Session):
    """Seed default system settings if table is empty."""
    from ai_engine.config import VIDEO_PATH, INPUT_MODE, DISTANCE_METERS, SPEED_LIMIT_KMH, PRESENTATION_MODE
    existing = db.query(SystemSettings).first()
    if not existing:
        db.add(SystemSettings(
            location_name="Main Junction - Signal 01",
            camera_source=VIDEO_PATH,
            input_mode=INPUT_MODE,
            speed_limit=SPEED_LIMIT_KMH,
            distance_meters=DISTANCE_METERS,
            presentation_mode=1 if PRESENTATION_MODE else 0,
            helmet_detection=1,
            lane_detection=1
        ))
        db.commit()

# ==============================================================================
# Challan number generator
# ==============================================================================
def generate_challan_number(db: Session) -> str:
    year = datetime.now(IST).year
    count = db.query(Violation).filter(
        Violation.challan_number.like(f"CH-{year}-%")
    ).count()
    return f"CH-{year}-{count + 1:04d}"

# ==============================================================================
# HTML response helpers
# ==============================================================================
def _html_success(challan_number: str, fine: int, payment_date: datetime) -> str:
    pd_str = payment_date.strftime("%d %b %Y  %I:%M:%S %p") if payment_date else "-"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>Payment Successful</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:Arial,sans-serif;background:linear-gradient(135deg,#1b5e20,#2e7d32);
          min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .card{{background:#fff;border-radius:16px;padding:48px 40px;max-width:480px;width:100%;
           text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.3)}}
    .tick{{font-size:72px;margin-bottom:16px}}
    h1{{color:#1b5e20;font-size:26px;margin-bottom:8px}}
    p{{color:#555;font-size:14px;line-height:1.6;margin-bottom:6px}}
    .meta{{background:#f1f8e9;border-radius:10px;padding:18px;margin:24px 0;text-align:left}}
    .meta div{{display:flex;justify-content:space-between;padding:6px 0;
               border-bottom:1px solid #c8e6c9;font-size:14px}}
    .meta div:last-child{{border:none}}
    .label{{color:#888;font-weight:600}}
    .value{{color:#222;font-weight:700}}
    .green{{color:#1b5e20}}
    .btn{{display:inline-block;margin-top:20px;padding:12px 32px;
          background:#1b5e20;color:#fff;border-radius:8px;text-decoration:none;
          font-weight:700;font-size:14px}}
    .note{{font-size:12px;color:#aaa;margin-top:16px}}
  </style>
</head>
<body>
<div class="card">
  <div class="tick">OK</div>
  <h1>Payment Successful!</h1>
  <p>Your traffic challan has been paid successfully.<br/>A confirmation email with receipt has been sent to you.</p>
  <div class="meta">
    <div><span class="label">Challan No.</span><span class="value green">{challan_number}</span></div>
    <div><span class="label">Fine Paid</span><span class="value green">₹{fine}.00</span></div>
    <div><span class="label">Payment Date</span><span class="value">{pd_str}</span></div>
    <div><span class="label">Status</span><span class="value green">[OK] PAID</span></div>
  </div>
  <a class="btn" href="http://localhost:3000/violations">View Dashboard</a>
  <p class="note">Email confirmation sent. Please keep the attached PDF as receipt.</p>
</div>
</body>
</html>"""

def _html_already_paid(challan_number: str, payment_date: datetime) -> str:
    pd_str = payment_date.strftime("%d %b %Y  %I:%M:%S %p") if payment_date else "-"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/><title>Already Paid</title>
  <style>
    body{{font-family:Arial,sans-serif;background:linear-gradient(135deg,#1565c0,#0d47a1);
          min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}}
    .card{{background:#fff;border-radius:16px;padding:48px 40px;max-width:440px;
           text-align:center;box-shadow:0 20px 60px rgba(0,0,0,.3)}}
    .icon{{font-size:64px;margin-bottom:16px}}
    h1{{color:#1565c0;margin-bottom:8px}}
    p{{color:#666;font-size:14px;line-height:1.6}}
    .meta{{background:#e3f2fd;border-radius:10px;padding:16px;margin:20px 0;text-align:left;font-size:14px}}
    .meta div{{padding:6px 0;display:flex;justify-content:space-between;border-bottom:1px solid #bbdefb}}
    .meta div:last-child{{border:none}}
    .btn{{display:inline-block;margin-top:16px;padding:12px 32px;
          background:#1565c0;color:#fff;border-radius:8px;text-decoration:none;font-weight:700}}
  </style>
</head>
<body>
<div class="card">
  <div class="icon">INFO</div>
  <h1>Already Paid</h1>
  <p>This challan has already been settled. No further action needed.</p>
  <div class="meta">
    <div><span>Challan</span><strong>{challan_number}</strong></div>
    <div><span>Paid On</span><strong>{pd_str}</strong></div>
  </div>
  <a class="btn" href="http://localhost:3000/violations">View Dashboard</a>
</div>
</body>
</html>"""

def _html_not_found() -> str:
    return """<!DOCTYPE html>
<html><head><title>Not Found</title>
<style>body{{font-family:Arial;background:#f5f5f5;display:flex;align-items:center;
  justify-content:center;height:100vh}}
.card{{background:#fff;padding:40px;border-radius:12px;text-align:center;
  box-shadow:0 4px 20px rgba(0,0,0,.1)}}
h1{{color:#c62828}}p{{color:#555}}</style></head>
<body><div class="card"><h1>Challan Not Found</h1>
<p>The violation ID you used does not exist in our system.</p></div></body></html>"""

# ==============================================================================
# Startup / Shutdown
# ==============================================================================
CURRENT_SIGNAL = "GREEN"

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        seed_owners(db)
        seed_settings(db)
        print("[OK] Mock owners and system settings seeded.")
        print(f"[INFO] Email sender: {os.environ.get('EMAIL_ADDRESS', '(not set)')}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    pass

# ==============================================================================
# System status / signal
# ==============================================================================
@app.get("/status")
async def get_system_status(db: Session = Depends(get_db)):
    settings = db.query(SystemSettings).first()
    return {
        "signal": CURRENT_SIGNAL,
        "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST"),
        "settings": {
            "location_name": settings.location_name if settings else "Main Junction",
            "camera_source": settings.camera_source if settings else "videos/traffic_demo.mp4",
            "speed_limit": settings.speed_limit if settings else 50.0,
            "distance_meters": settings.distance_meters if settings else 5.0,
            "presentation_mode": settings.presentation_mode if settings else 1,
            "helmet_detection": settings.helmet_detection if settings else 1,
            "lane_detection": settings.lane_detection if settings else 1,
            "input_mode": settings.input_mode if settings else "VIDEO"
        }
    }

@app.post("/update-signal")
async def update_signal(status: str):
    global CURRENT_SIGNAL
    if status.upper() in ["RED", "GREEN", "YELLOW"]:
        CURRENT_SIGNAL = status.upper()
        return {"msg": f"Signal updated to {CURRENT_SIGNAL}"}
    raise HTTPException(status_code=400, detail="Invalid signal status")

@app.get("/settings")
async def get_settings(db: Session = Depends(get_db)):
    return db.query(SystemSettings).first()

@app.post("/settings")
async def update_settings(
    location_name: str = Form(...),
    camera_source: str = Form(...),
    speed_limit: float = Form(...),
    distance_meters: float = Form(...),
    presentation_mode: int = Form(...),
    helmet_detection: int = Form(...),
    lane_detection: int = Form(...),
    input_mode: str = Form(...),
    db: Session = Depends(get_db)
):
    settings = db.query(SystemSettings).first()
    if not settings:
        settings = SystemSettings()
        db.add(settings)
    
    settings.location_name = location_name
    settings.camera_source = camera_source
    settings.speed_limit = speed_limit
    settings.distance_meters = distance_meters
    settings.presentation_mode = presentation_mode
    settings.helmet_detection = helmet_detection
    settings.lane_detection = lane_detection
    settings.input_mode = input_mode
    
    db.commit()
    print(f"[CONFIG]  Settings updated: {location_name} | {camera_source}")
    return {"msg": "Settings updated", "settings": settings}

# ==============================================================================
# Video feed
# ==============================================================================
latest_processed_frame = None
latest_frame_id = 0

@app.post("/upload_frame")
async def upload_frame(image: UploadFile = File(...)):
    global latest_processed_frame, latest_frame_id
    contents = await image.read()
    latest_processed_frame = contents
    latest_frame_id += 1
    return {"status": "ok"}

def generate_frames():
    import time
    last_sent_id = -1
    while True:
        if latest_processed_frame is not None and latest_frame_id != last_sent_id:
            last_sent_id = latest_frame_id
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_processed_frame + b'\r\n')
        else:
            time.sleep(0.01)

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(),
                             media_type="multipart/x-mixed-replace; boundary=frame")

# ==============================================================================
# POST /violations/ - create violation + auto-generate challan + send Email #1
# ==============================================================================
@app.post("/violations/")
async def create_violation(
    plate_number: str = Form(...),
    violation_type: str = Form(...),
    value: float = Form(0.0),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Set Fine based on Type
    fine_map = {
        "Red Light Jump": 500,
        "Over Speed": 500,
        "No Helmet": 1000,
        "Wrong Lane": 2000
    }
    fine = fine_map.get(violation_type, 500)

    # Get current location from settings
    settings = db.query(SystemSettings).first()
    location = settings.location_name if settings else "Main Junction - Signal 01"

    # Ensure vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate_number).first()
    if not vehicle:
        vehicle = Vehicle(plate_number=plate_number, vehicle_type="unknown")
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

    challan_number = generate_challan_number(db)
    now_ist = datetime.now(IST).replace(tzinfo=None)

    # Create violation object (ID will be generated on commit)
    violation = Violation(
        vehicle_id=vehicle.id,
        violation_type=violation_type,
        value=value,
        image_path="", # Placeholder, update after ID is known
        fine_amount=fine,
        challan_number=challan_number,
        payment_status="Pending",
        timestamp=now_ist,
    )
    db.add(violation)
    db.commit()
    db.refresh(violation)

    # Save image using violation ID
    os.makedirs("evidence_images", exist_ok=True)
    img_filename = f"violation_{violation.id}.jpg"
    img_path = f"evidence_images/{img_filename}"
    with open(img_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    # Update violation with final path
    violation.image_path = img_path
    db.commit()


    # Owner lookup
    owner_name, owner_email = get_owner(plate_number, db)

    # Generate PDF using centralized helper
    _update_violation_pdf(violation, db)

    # == Send Email #1 - Violation Notice =====================================
    try:
        send_violation_email(
            owner_name=owner_name,
            to_email=owner_email,
            challan_number=challan_number,
            plate=plate_number,
            violation_type=violation_type,
            fine=fine,
            violation_id=violation.id,
            timestamp=violation.timestamp,
            location=location,
            image_path=violation.image_path,
        )
    except Exception as e:
        print(f"[WARN] Email #1 failed (non-fatal): {e}")

    print(f"[OK] Violation {violation.id} saved | Challan: {challan_number}")
    return {
        "msg": "Violation recorded",
        "id": violation.id,
        "challan_number": challan_number,
        "email_sent_to": owner_email,
    }

# ==============================================================================
# GET /violations/ - list all with challan info
# ==============================================================================
@app.get("/violations/", response_model=List[dict])
async def list_violations(db: Session = Depends(get_db)):
    violations = db.query(Violation).order_by(Violation.id.desc()).all()
    res = []
    for v in violations:
        plate = v.vehicle.plate_number if v.vehicle else "-"
        owner_name, owner_email = get_owner(plate, db)
        res.append({
            "id": v.id,
            "plate_number": plate,
            "type": v.violation_type,
            "timestamp": v.timestamp,
            "fine": v.fine_amount,
            "status": v.payment_status,
            "challan_number": v.challan_number,
            "payment_date": v.payment_date,
            "challan_pdf_path": v.challan_pdf_path,
            "owner_name": owner_name,
            "owner_email": owner_email,
            "location": v.location or "Main Junction - Signal 01",
        })
    return res

# ==============================================================================
# GET /pay-challan/{id} - browser payment link (from email)
# Returns HTML page; also triggers Email #2
# ==============================================================================
@app.get("/pay-challan/{violation_id}", response_class=HTMLResponse)
async def pay_challan_browser(violation_id: int, db: Session = Depends(get_db)):
    try:
        v = db.query(Violation).filter(Violation.id == violation_id).first()
        if not v:
            return HTMLResponse(content=_html_not_found(), status_code=404)

        # Already paid
        if v.payment_status == "Paid":
            return HTMLResponse(content=_html_already_paid(v.challan_number, v.payment_date))

        # Mark as paid
        payment_date = datetime.now(IST).replace(tzinfo=None)
        v.payment_status = "Paid"
        v.payment_date = payment_date
        db.commit()

        plate = v.vehicle.plate_number if v.vehicle else "-"
        owner_name, owner_email = get_owner(plate, db)

        # Regenerate PDF using helper (Always Fresh)
        pdf_path = _update_violation_pdf(v, db)

        # == Send Email #2 - Payment Confirmation =============================
        try:
            send_payment_confirmation(
                owner_name=owner_name,
                to_email=owner_email,
                challan_number=v.challan_number,
                fine=v.fine_amount,
                payment_date=payment_date,
                pdf_path=pdf_path,
                plate=plate,
                violation_type=v.violation_type,
            )
        except Exception as e:
            print(f"[WARN] Email #2 failed (non-fatal): {e}")

        print(f"[INFO] Payment confirmed: Challan {v.challan_number} | ID {violation_id}")
        return HTMLResponse(content=_html_success(v.challan_number, v.fine_amount, payment_date))

    except Exception as e:
        print(f"[ERROR] pay_challan_browser error: {e}")
        return HTMLResponse(
            content="<h2>Server Error. Please try again.</h2>",
            status_code=500
        )

# ==============================================================================
# POST /pay-challan/{id} - frontend Pay Now button (JSON API)
# ==============================================================================
@app.post("/pay-challan/{violation_id}")
async def pay_challan_api(violation_id: int, db: Session = Depends(get_db)):
    try:
        v = db.query(Violation).filter(Violation.id == violation_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Violation not found")
        if v.payment_status == "Paid":
            return {"msg": "Already paid", "challan_number": v.challan_number}

        payment_date = datetime.now(IST).replace(tzinfo=None)
        v.payment_status = "Paid"
        v.payment_date = payment_date
        db.commit()

        plate = v.vehicle.plate_number if v.vehicle else "-"
        owner_name, owner_email = get_owner(plate, db)

        # Regenerate PDF using helper (Always Fresh)
        pdf_path = _update_violation_pdf(v, db)

        # == Send Email #2 =====================================================
        try:
            send_payment_confirmation(
                owner_name=owner_name,
                to_email=owner_email,
                challan_number=v.challan_number,
                fine=v.fine_amount,
                payment_date=payment_date,
                pdf_path=pdf_path,
                plate=plate,
                violation_type=v.violation_type,
                image_path=v.image_path,
            )
        except Exception as e:
            print(f"[WARN] Email #2 failed (non-fatal): {e}")

        print(f"[INFO] Payment confirmed: Challan {v.challan_number} | ID {violation_id}")
        return {
            "msg": "Payment successful",
            "challan_number": v.challan_number,
            "payment_date": payment_date.isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] pay_challan_api error: {e}")
        raise HTTPException(status_code=500, detail="Payment processing error")

# ==============================================================================
# GET /violations/{id}/pdf - download challan PDF
# ==============================================================================
@app.get("/violations/{violation_id}/pdf")
async def get_violation_pdf(violation_id: int, db: Session = Depends(get_db)):
    try:
        v = db.query(Violation).filter(Violation.id == violation_id).first()
        if not v:
            raise HTTPException(status_code=404, detail="Violation not found")

        # Always regenerate for download to ensure latest status/watermark
        pdf_path = _update_violation_pdf(v, db)
        plate = v.vehicle.plate_number if v.vehicle else "-"

        return FileResponse(
            pdf_path,
            filename=f"Challan_{plate}_{v.challan_number}.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        print(f"[ERROR] get_violation_pdf error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Server Error")

# ==============================================================================
# GET /analytics/
# ==============================================================================
@app.get("/analytics/")
async def get_analytics(db: Session = Depends(get_db)):
    from collections import defaultdict
    violations = db.query(Violation).all()

    def to_ist(ts):
        """Convert DB timestamp (stored as naive IST) to aware IST for processing."""
        if ts is None: return datetime.now(IST)
        if ts.tzinfo is None:
            # We suspect it's already IST because we save it that way
            return ts.replace(tzinfo=IST)
        return ts.astimezone(IST)

    hourly = defaultdict(lambda: {"redLight": 0, "overSpeed": 0, "noHelmet": 0, "wrongLane": 0, "total": 0})
    for v in violations:
        h = to_ist(v.timestamp).hour
        label = f"{h:02d}:00"
        hourly[label]["total"] += 1
        if v.violation_type == "Red Light Jump":
            hourly[label]["redLight"] += 1
        elif v.violation_type == "Over Speed":
            hourly[label]["overSpeed"] += 1
        elif v.violation_type == "No Helmet":
            hourly[label]["noHelmet"] += 1
        elif v.violation_type == "Wrong Lane":
            hourly[label]["wrongLane"] += 1
        else:
            hourly[label]["overSpeed"] += 1 # Fallback
            
    # Generate full 24h slots
    hourly_data = []
    for h in range(24):
        label = f"{h:02d}:00"
        hourly_data.append({
            "hour": label,
            **hourly[label]
        })

    type_counts = defaultdict(int)
    for v in violations:
        type_counts[v.violation_type or "Unknown"] += 1

    total_fines = sum(v.fine_amount or 0 for v in violations)
    paid_count = sum(1 for v in violations if v.payment_status == "Paid")
    pending_count = len(violations) - paid_count
    avg_fine = total_fines / len(violations) if violations else 0

    plate_counts = defaultdict(int)
    for v in violations:
        plate = v.vehicle.plate_number if v.vehicle else "Unknown"
        plate_counts[plate] += 1
    top_offenders = sorted([{"plate": k, "count": cv} for k, cv in plate_counts.items()],
                           key=lambda x: x["count"], reverse=True)[:5]

    recent = sorted(violations, key=lambda v: v.timestamp or datetime.min, reverse=True)[:10]
    recent_timeline = [{
        "id": v.id,
        "plate": v.vehicle.plate_number if v.vehicle else "?",
        "type": v.violation_type,
        "fine": v.fine_amount,
        "time": to_ist(v.timestamp).strftime("%I:%M:%S %p") if v.timestamp else "-",
        "date": to_ist(v.timestamp).strftime("%d %b %Y") if v.timestamp else "-",
        "status": v.payment_status,
        "challan_number": v.challan_number,
    } for v in recent]

    daily = defaultdict(int)
    for v in violations:
        if v.timestamp:
            daily[to_ist(v.timestamp).strftime("%d %b")] += 1

    return {
        "total_violations": len(violations),
        "total_fines": total_fines,
        "avg_fine": round(avg_fine),
        "paid": paid_count,
        "pending": pending_count,
        "hourly": hourly_data,
        "type_breakdown": [{"name": k, "count": cv} for k, cv in type_counts.items()],
        "top_offenders": top_offenders,
        "recent_timeline": recent_timeline,
        "daily_trend": [{"date": k, "violations": cv} for k, cv in daily.items()],
    }

# ==============================================================================
# DEMO MODE GENERATOR
# ==============================================================================
def demo_mode_worker():
    import time, random, requests
    print("--- DEMO MODE ACTIVE: Starting Generator ---")
    time.sleep(5)
    demo_plates = ["DEMO-001", "DEMO-002", "DEMO-003", "JURY-TEST", "VIP-007"]
    while True:
        try:
            plate = random.choice(demo_plates)
            v_type = random.choice(["Over Speed", "Red Light Jump", "No Helmet", "Wrong Lane"])
            
            # Accuracy Fix: Only allow Red Light Jump if signal is RED
            if v_type == "Red Light Jump" and CURRENT_SIGNAL != "RED":
                time.sleep(5)
                continue

            value = random.randint(60, 120) if v_type == "Over Speed" else 0
            if not os.path.exists("demo.jpg"):
                with open("demo.jpg", "wb") as f:
                    f.write(b"demo_image_data")
            files = {'image': ('demo.jpg', open("demo.jpg", "rb"), 'image/jpeg')}
            data = {'plate_number': plate, 'violation_type': v_type, 'value': value}
            print(f"DEMO: Creating {v_type} for {plate}...")
            try:
                requests.post("http://127.0.0.1:8000/violations/", data=data, files=files, timeout=3)
            except Exception as e:
                print(f"DEMO INSERT FAILED: {e}")
            time.sleep(20)
        except Exception as e:
            print(f"DEMO LOOP ERROR: {e}")
            time.sleep(5)


if __name__ == "__main__":
    from ai_engine.config import DEMO_MODE
    if DEMO_MODE:
        import threading
        threading.Thread(target=demo_mode_worker, daemon=True).start()
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
