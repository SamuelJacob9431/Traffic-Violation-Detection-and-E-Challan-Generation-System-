"""
email_service.py - Real Gmail SMTP email notifications for E-Challan system.

Reads credentials from environment variables:
    EMAIL_ADDRESS       - sender Gmail address
    EMAIL_APP_PASSWORD  - Gmail App Password (not your regular password)

Sends:
    Email #1 -> Violation Notice  (on violation detected)
    Email #2 -> Payment Receipt   (on payment confirmed, with PDF attachment)
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime

# Load from environment (set via .env loaded in main.py)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _get_credentials():
    addr = os.environ.get("EMAIL_ADDRESS", "")
    pwd  = os.environ.get("EMAIL_APP_PASSWORD", "")
    return addr, pwd


def _send_in_background(msg: MIMEMultipart, to_email: str):
    """Dispatch SMTP in a daemon thread - API responds immediately."""
    import threading
    threading.Thread(target=_do_send, args=(msg, to_email), daemon=True).start()

def _do_send(msg: MIMEMultipart, to_email: str) -> bool:
    """Actual SMTP work - runs in background thread, never blocks main server."""
    sender, password = _get_credentials()
    if not sender or not password:
        print("[WARN]  [EMAIL] Credentials not set in .env - skipping.")
        return False
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        print(f"[OK]  [EMAIL] Sent successfully -> {to_email}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[ERROR]  [EMAIL] Auth failed (535) - update EMAIL_APP_PASSWORD in .env")
        print("   ?  Go to: myaccount.google.com -> Security -> App Passwords -> Generate")
        return False
    except Exception as e:
        print(f"[ERROR]  [EMAIL] Send failed: {e}")
        return False




# == Email #1 - Violation Notice ===============================================
def send_violation_email(
    owner_name: str,
    to_email: str,
    challan_number: str,
    plate: str,
    violation_type: str,
    fine: int,
    violation_id: int,
    timestamp: datetime = None,
    location: str = "Main Junction - Signal 01",
    image_path: str = None,
) -> bool:
    sender, _ = _get_credentials()
    ts_str = (timestamp or datetime.now()).strftime("%d %b %Y  %I:%M:%S %p")
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:8000")
    payment_link = f"{base_url}/pay-challan/{violation_id}"

    # Image Evidence Tag
    evidence_html = ""
    if image_path and os.path.exists(image_path):
        evidence_html = """
        <div style="margin-top:25px; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
            <div style="background:#f8f9fa; padding:10px; font-size:12px; font-weight:700; color:#1a237e; border-bottom:1px solid #ddd;">
                [PHOTO] AI EVIDENCE CAPTURE
            </div>
            <img src="cid:evidence_image" style="width:100%; display:block;" />
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body      {{ font-family: Arial, sans-serif; background:#f0f2f5; margin:0; padding:20px; }}
    .card     {{ max-width:600px; margin:auto; background:#ffffff; border-radius:12px;
                overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.12); }}
    .header   {{ background:#1a237e; color:#fff; padding:28px 32px; }}
    .header h1{{ margin:0 0 6px; font-size:22px; }}
    .header p {{ margin:0; font-size:13px; opacity:.8; }}
    .body     {{ padding:28px 32px; }}
    .row      {{ display:flex; justify-content:space-between; padding:10px 0;
                border-bottom:1px solid #eee; font-size:14px; }}
    .label    {{ color:#666; font-weight:600; }}
    .value    {{ color:#222; }}
    .fine     {{ color:#c62828; font-size:20px; font-weight:700; }}
    .challan  {{ color:#1a237e; font-weight:700; }}
    .btn      {{ display:block; margin:28px auto 0; width:fit-content; padding:14px 36px;
                background:#1b5e20; color:#fff; border-radius:8px; text-decoration:none;
                font-size:15px; font-weight:700; letter-spacing:.5px; }}
    .footer   {{ background:#f8f9fa; padding:18px 32px; font-size:11px; color:#999;
                text-align:center; border-top:1px solid #eee; }}
    .badge    {{ display:inline-block; background:#fff3e0; color:#e65100;
                padding:4px 12px; border-radius:20px; font-size:12px;
                font-weight:700; margin-top:6px; }}
  </style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>Traffic Violation Detected</h1>
    <p>Smart City Traffic Police - Automated E-Challan System</p>
  </div>
  <div class="body">
    <p>Dear <strong>{owner_name}</strong>,</p>
    <p>A traffic violation has been recorded against your vehicle.
       Please review the details below and complete payment at your earliest convenience.</p>

    <div class="row"><span class="label">Challan Number</span><span class="value challan">{challan_number}</span></div>
    <div class="row"><span class="label">Vehicle Plate</span><span class="value">{plate}</span></div>
    <div class="row"><span class="label">Violation Type</span><span class="value">{violation_type}</span></div>
    <div class="row"><span class="label">Date &amp; Time</span><span class="value">{ts_str}</span></div>
    <div class="row"><span class="label">Location</span><span class="value">{location}</span></div>
    <div class="row"><span class="label">Fine Amount</span><span class="value fine">₹{fine}.00</span></div>
    <div class="row"><span class="label">Payment Status</span>
        <span class="value"><span class="badge">PENDING</span></span></div>

    {evidence_html}

    <a class="btn" href="{payment_link}">PAY NOW - ₹{fine}.00</a>

    <p style="margin-top:24px;font-size:12px;color:#888;text-align:center;">
      Payment link valid for 30 days. Late payment attracts ₹100/day penalty.
    </p>
  </div>
  <div class="footer">
    Smart City Traffic Police &nbsp;|&nbsp; Do not reply to this email<br/>
    This is an automated message generated by the AI Traffic Violation Detection System.
  </div>
</div>
</body>
</html>
"""

    msg = MIMEMultipart("related") # "related" for CID inline
    msg["Subject"] = f"[ALERT] Traffic Violation Notice - Challan {challan_number}"
    msg["From"]    = sender
    msg["To"]      = to_email

    msg_alt = MIMEMultipart("alternative")
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html, "html"))

    # Attach CID Image
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<evidence_image>')
                msg.attach(img)
        except Exception as e:
            print(f"[WARN]  [EMAIL #1] Failed to embed image CID: {e}")

    print(f"[EMAIL]  [EMAIL #1] Queued violation notice -> {to_email} | Challan: {challan_number}")
    _send_in_background(msg, to_email)
    return True


# == Email #2 - Payment Confirmation ==========================================
def send_payment_confirmation(
    owner_name: str,
    to_email: str,
    challan_number: str,
    fine: int,
    payment_date: datetime,
    pdf_path: str = None,
    plate: str = "",
    violation_type: str = "",
    image_path: str = None,
) -> bool:
    sender, _ = _get_credentials()
    pd_str = (payment_date or datetime.now()).strftime("%d %b %Y  %I:%M:%S %p")

    # Image Evidence Tag
    evidence_html = ""
    if image_path and os.path.exists(image_path):
        evidence_html = """
        <div style="margin-top:25px; border:1px solid #ddd; border-radius:8px; overflow:hidden;">
            <div style="background:#f8f9fa; padding:10px; font-size:12px; font-weight:700; color:#1b5e20; border-bottom:1px solid #ddd;">
                [PHOTO] ATTACHED EVIDENCE RECEIPT
            </div>
            <img src="cid:evidence_image" style="width:100%; display:block;" />
        </div>
        """

    html = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8"/>
  <style>
    body      {{ font-family: Arial, sans-serif; background:#f0f2f5; margin:0; padding:20px; }}
    .card     {{ max-width:600px; margin:auto; background:#ffffff; border-radius:12px;
                overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,.12); }}
    .header   {{ background:#1b5e20; color:#fff; padding:28px 32px; }}
    .header h1{{ margin:0 0 6px; font-size:22px; }}
    .header p {{ margin:0; font-size:13px; opacity:.8; }}
    .body     {{ padding:28px 32px; }}
    .row      {{ display:flex; justify-content:space-between; padding:10px 0;
                border-bottom:1px solid #eee; font-size:14px; }}
    .label    {{ color:#666; font-weight:600; }}
    .value    {{ color:#222; }}
    .challan  {{ color:#1b5e20; font-weight:700; }}
    .paid-badge{{ display:inline-block; background:#e8f5e9; color:#1b5e20;
                  padding:6px 18px; border-radius:20px; font-size:14px;
                  font-weight:700; border:2px solid #a5d6a7; }}
    .footer   {{ background:#f8f9fa; padding:18px 32px; font-size:11px; color:#999;
                text-align:center; border-top:1px solid #eee; }}
    .tick     {{ font-size:60px; text-align:center; margin:16px 0 8px; }}
  </style>
</head>
<body>
<div class="card">
  <div class="header">
    <h1>Payment Confirmed</h1>
    <p>Smart City Traffic Police - E-Challan Payment Receipt</p>
  </div>
  <div class="body">
    <div class="tick">OK</div>
    <p style="text-align:center">Dear <strong>{owner_name}</strong>, your payment has been received successfully.</p>

    <div class="row"><span class="label">Challan Number</span><span class="value challan">{challan_number}</span></div>
    <div class="row"><span class="label">Vehicle Plate</span><span class="value">{plate or '-'}</span></div>
    <div class="row"><span class="label">Violation Type</span><span class="value">{violation_type or '-'}</span></div>
    <div class="row"><span class="label">Fine Paid</span><span class="value" style="color:#1b5e20;font-weight:700">₹{fine}.00</span></div>
    <div class="row"><span class="label">Payment Date</span><span class="value">{pd_str}</span></div>
    <div class="row"><span class="label">Status</span>
        <span class="value"><span class="paid-badge">[OK] PAID</span></span></div>

    {evidence_html}

    <p style="margin-top:20px;font-size:13px;color:#555;">
      Your challan PDF receipt is attached to this email. Please keep it for your records.
    </p>
  </div>
  <div class="footer">
    Smart City Traffic Police &nbsp;|&nbsp; No further action required<br/>
    This is an automated receipt - do not reply.
  </div>
</div>
</body>
</html>
"""

    msg = MIMEMultipart("mixed") # Mixed because we have attachment
    msg["Subject"] = f"Payment Confirmed - Challan {challan_number}"
    msg["From"]    = sender
    msg["To"]      = to_email

    # Inline Related body
    msg_related = MIMEMultipart("related")
    msg.attach(msg_related)

    msg_alt = MIMEMultipart("alternative")
    msg_related.attach(msg_alt)
    msg_alt.attach(MIMEText(html, "html"))

    # Attach CID Image for inline display
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<evidence_image>')
                msg_related.attach(img)
        except Exception as e:
            print(f"[WARN] [EMAIL #2] Failed to embed image CID: {e}")

    # Attach PDF Receipt
    if pdf_path and os.path.exists(pdf_path):
        try:
            with open(pdf_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{challan_number}_receipt.pdf"'
            )
            msg.attach(part)
            print(f"[ATTACH] [EMAIL #2] PDF attached: {pdf_path}")
        except Exception as e:
            print(f"[WARN] [EMAIL #2] PDF attach failed: {e}")

    print(f"[QUEUED] [EMAIL #2] Queued payment confirmation -> {to_email} | Challan: {challan_number}")
    _send_in_background(msg, to_email)
    return True
