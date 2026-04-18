from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

def generate_challan_pdf(violation_data: dict, save_path: str):
    """
    violation_data keys:
        id, challan_number, plate_number, owner_name, owner_email,
        type, timestamp, fine, location, image_path, payment_status
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    c = canvas.Canvas(save_path, pagesize=letter)
    W, H = letter

    # ── Header bar ──────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#1a237e"))
    c.rect(0, H - 1.6 * inch, W, 1.6 * inch, fill=1, stroke=0)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(W / 2, H - 0.65 * inch, "SMART TRAFFIC VIOLATION SYSTEM")
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, H - 0.95 * inch, "Automated E-Challan System  |  www.smartcitytraffic.gov.in")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(colors.yellow)
    c.drawCentredString(W / 2, H - 1.25 * inch, "** ELECTRONIC CHALLAN NOTICE **")

    # ── Challan number band ─────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#e8eaf6"))
    c.rect(0, H - 2.15 * inch, W, 0.55 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#1a237e"))
    c.setFont("Helvetica-Bold", 14)
    challan_no = violation_data.get("challan_number", f"CH-{violation_data['id']}")
    c.drawString(1 * inch, H - 1.9 * inch, f"Challan No:  {challan_no}")
    status_color = colors.HexColor("#2e7d32") if violation_data.get("payment_status") == "Paid" else colors.HexColor("#c62828")
    c.setFillColor(status_color)
    status_label = violation_data.get("payment_status", "Pending").upper()
    c.drawRightString(W - 1 * inch, H - 1.9 * inch, f"STATUS: {status_label}")

    # ── Two-column detail section ───────────────────────────────────────────────
    c.setFillColor(colors.black)
    left_x, right_x = 1 * inch, 4.5 * inch
    y = H - 2.7 * inch
    line_h = 0.3 * inch

    def row(label, value, bold_value=True, y_pos=None):
        nonlocal y
        _y = y_pos if y_pos is not None else y
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(left_x, _y, label)
        if bold_value:
            c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(left_x + 1.5 * inch, _y, str(value))
        y -= line_h

    def right_row(label, value, y_pos=None):
        _y = y_pos if y_pos is not None else y
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(right_x, _y, label)
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.black)
        c.drawString(right_x + 1.4 * inch, _y, str(value))

    # Section title
    c.setStrokeColor(colors.HexColor("#1a237e"))
    c.setFillColor(colors.HexColor("#1a237e"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x, y + 0.05 * inch, "VEHICLE & OWNER INFORMATION")
    c.line(left_x, y - 0.05 * inch, W - 1 * inch, y - 0.05 * inch)
    y -= 0.35 * inch

    ts = violation_data.get("timestamp")
    dt_str = ts.strftime("%d %b %Y  %I:%M:%S %p") if isinstance(ts, datetime) else str(ts)

    row("Owner Name:", violation_data.get("owner_name", "Unknown"))
    right_row("Email:", violation_data.get("owner_email", "N/A"), y_pos=y + line_h)
    row("Plate Number:", violation_data.get("plate_number", "—"))
    right_row("Date/Time:", dt_str, y_pos=y + line_h)
    row("Location:", violation_data.get("location", "Main Junction - Signal 01"))

    y -= 0.2 * inch
    # Section title
    c.setFillColor(colors.HexColor("#1a237e"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x, y + 0.05 * inch, "VIOLATION DETAILS")
    c.line(left_x, y - 0.05 * inch, W - 1 * inch, y - 0.05 * inch)
    y -= 0.35 * inch

    row("Violation Type:", violation_data.get("type", "—"))
    # Fine in red
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(left_x, y + line_h, "Fine Amount:")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#c62828"))
    c.drawString(left_x + 1.5 * inch, y + line_h, f"Rs. {violation_data.get('fine', 0)}.00")
    y -= 0.1 * inch

    # ── Evidence image ──────────────────────────────────────────────────────────
    img_path = violation_data.get("image_path", "")
    y -= 0.3 * inch
    c.setFillColor(colors.HexColor("#1a237e"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(left_x, y, "EVIDENCE CAPTURE")
    c.line(left_x, y - 0.1 * inch, W - 1 * inch, y - 0.1 * inch)
    y -= 0.25 * inch

    if img_path and os.path.exists(img_path):
        img_w, img_h = 4.5 * inch, 2.8 * inch # Balanced size
        try:
            c.drawImage(img_path, left_x + 0.5 * inch, y - img_h, width=img_w, height=img_h, preserveAspectRatio=True)
        except Exception:
            c.setFont("Helvetica-Oblique", 10)
            c.setFillColor(colors.gray)
            c.drawString(left_x, y - 0.4 * inch, "[Evidence image unavailable]")
        y -= img_h + 0.15 * inch
    else:
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.gray)
        c.drawString(left_x, y - 0.3 * inch, "[No evidence image available]")
        y -= 0.55 * inch

    # ── PAID Watermark (Rotated) ────────────────────────────────────────────────
    if violation_data.get("payment_status") == "Paid":
        c.saveState()
        c.setFont("Helvetica-Bold", 100)
        c.setStrokeColor(colors.lightgreen)
        c.setFillColor(colors.lightgreen)
        c.setFillAlpha(0.15)
        c.setStrokeAlpha(0.15)
        c.translate(W/2, H/2)
        c.rotate(45)
        c.drawCentredString(0, 0, "PAID")
        c.restoreState()

        # ── Payment Receipt Section ─────────────────────────────────────────────
        y -= 0.1 * inch
        c.setFillColor(colors.HexColor("#2e7d32"))
        c.setFont("Helvetica-Bold", 12)
        c.drawString(left_x, y, "PAYMENT RECEIPT")
        c.line(left_x, y - 0.1 * inch, W - 1 * inch, y - 0.1 * inch)
        y -= 0.35 * inch

        pd = violation_data.get("payment_date")
        pd_str = pd.strftime("%d %b %Y %I:%M %p") if isinstance(pd, datetime) else str(pd or "—")
        row("Payment Status:", "COMPLETED", bold_value=True)
        right_row("Payment Date:", pd_str, y_pos=y + line_h)
        tx_id = f"TXN-{violation_data['id']}-{int(datetime.now().timestamp())}"
        row("Transaction ID:", tx_id)
        y -= 0.2 * inch

    # ── Instructions box ────────────────────────────────────────────────────────
    box_y = max(1.8 * inch, y - 0.6 * inch)
    c.setFillColor(colors.HexColor("#fff9c4"))
    c.rect(left_x, box_y, W - 2 * inch, 0.7 * inch, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#f57f17"))
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_x + 0.1 * inch, box_y + 0.45 * inch, "PAYMENT INSTRUCTIONS:")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.black)
    c.drawString(left_x + 0.1 * inch, box_y + 0.2 * inch,
                 "Pay online at www.smartcitytraffic.gov.in  or visit your nearest Traffic Police Office within 30 days.")

    # ── Footer ──────────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#1a237e"))
    c.rect(0, 0, W, 0.9 * inch, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(W / 2, 0.55 * inch, "This is a computer-generated challan. No signature is required.")
    c.drawCentredString(W / 2, 0.35 * inch, f"Generated on: {datetime.now().strftime('%d %b %Y %I:%M %p')}  |  Challan ID: {challan_no}")

    c.showPage()
    c.save()
    return save_path
