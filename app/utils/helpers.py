from flask import request, redirect, url_for
from flask import request, redirect, url_for
from urllib.parse import urlparse  # ✅ correct built-in replacement
# In app/utils/helpers.py
import io
import qrcode
import uuid
import base64
import os
from datetime import datetime
from flask import current_app
from reportlab.lib.pagesizes import A6, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Line
from reportlab.lib.colors import HexColor
# app/utils/helpers.py

from flask_login import current_user
from flask import abort
from functools import wraps
def admin_required(f):
    """
    Decorator to ensure that the current user is an admin.
    If not, it will abort with a 403 status.
    """
    @wraps(f)  # Add this line to preserve the original function name

    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)  # Forbidden if not an admin
        return f(*args, **kwargs)
    return decorated_function

def logo_exists_helper():
    import os
    from flask import current_app
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'university_logo.png')
    return os.path.exists(logo_path)
def generate_event_pass(user, event, registration):
    """
    Generate a beautiful event pass/voucher for the registered user
    Returns the PDF as a base64 encoded string
    """
    # Create a unique pass ID
    pass_id = str(uuid.uuid4())[:8].upper()
    
    # Generate QR code with registration info
    qr_data = f"EVENT:{event.id}|USER:{user.id}|REG:{registration.id}|ID:{pass_id}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert QR to reportlab image
    qr_byte_io = io.BytesIO()
    qr_img.save(qr_byte_io)
    qr_byte_io.seek(0)
    
    # Create PDF buffer with landscape orientation
    buffer = io.BytesIO()
    
    # Use a custom drawing function for more control
    width, height = landscape(A6)
    c = canvas.Canvas(buffer, pagesize=landscape(A6))
    
    # Check if university logo exists
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'university_logo.png')
    has_logo = os.path.exists(logo_path)
    
    # Set background color for the entire pass
    c.setFillColor(HexColor('#f0f8ff'))  # Light blue background
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Add decorative header
    c.setFillColor(HexColor('#FFFFFF'))  # Darker blue for header
    c.rect(0, height-17*mm, width, 25*mm, fill=1, stroke=0)
    
    # Add decorative footer
    c.setFillColor(HexColor('#1a75ff'))  # Darker blue for footer
    c.rect(0, 0, width, 10*mm, fill=1, stroke=0)
    
    # Add logo if it exists
    if has_logo:
        
        c.drawImage(logo_path, 10*mm, height-20*mm, width=25*mm, height=18.75*mm, preserveAspectRatio=True,mask='auto')
    
    # Add title
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 16)
    title_text = "EVENT PASS"
    title_width = c.stringWidth(title_text, "Helvetica-Bold", 16)
    c.drawString((width - title_width) / 2, height-15*mm, title_text)
    
    # Add event details
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(10*mm, height-30*mm, event.title)
    
    c.setFont("Helvetica", 10)
    c.drawString(10*mm, height-35*mm, f"Date: {event.date.strftime('%B %d, %Y')}")
    c.drawString(10*mm, height-40*mm, f"Time: {event.date.strftime('%I:%M %p')} - {event.end_date.strftime('%I:%M %p')}")
    c.drawString(10*mm, height-45*mm, f"Location: {event.location}")
    
    # Calculate QR code position - move it a bit higher to avoid the line
    qr_width = 30*mm
    qr_height = 30*mm
    qr_x = width-40*mm  # Position from right
    qr_y = height-70*mm  # Position from bottom
    
    # Add attendee details
    c.setFont("Helvetica-Bold", 10)
    c.drawString(10*mm, height-55*mm, "ATTENDEE:")
    c.setFont("Helvetica", 10)
    c.drawString(15*mm, height-60*mm, f"Name: {user.full_name or user.username}")
    c.drawString(15*mm, height-65*mm, f"Department: {user.department or 'N/A'}")
    c.drawString(15*mm, height-70*mm, f"Student ID: {user.student_id or 'N/A'}")

    
    # Add registration details
    c.setFont("Helvetica-Bold", 8)
    c.drawString(10*mm, 20*mm, f"Pass ID: {pass_id}")
    c.drawString(10*mm, 16*mm, f"Registered: {registration.registered_at.strftime('%Y-%m-%d')}")
    
    # Add QR code
    qr_img = Image(qr_byte_io)
    qr_img.drawHeight = qr_height
    qr_img.drawWidth = qr_width
    qr_img.wrapOn(c, width, height)
    qr_img.drawOn(c, qr_x, qr_y)
    
    # Add decorative line - FIXED: Stop the line before the QR code
    c.setStrokeColor(HexColor('#1a75ff'))
    c.setLineWidth(1)
    # Calculate where QR code begins to avoid drawing the line through it
    line_end_x = qr_x - 5*mm  # 5mm margin before QR code
    c.line(10*mm, height-50*mm, line_end_x, height-50*mm)
    
    # Validation text
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(colors.white)
    c.drawCentredString(width/2, 5*mm, "This pass must be presented at the event entrance for verification")
    
    c.save()
    
    # Get PDF and encode as base64
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return base64.b64encode(pdf_data).decode('utf-8')
def redirect_to_next_page(default='index'):
    next_page = request.args.get('next')
    # Make sure the next page is relative, not a full domain (to prevent open redirect attack)
    if not next_page or urlparse(next_page).netloc != '':
        return redirect(url_for(default))
    return redirect(next_page)


def format_datetime(value, format='%B %d, %Y at %I:%M %p'):
    """Format a datetime object to a string"""
    if value is None:
        return ""
    return value.strftime(format)

def get_event_status(event):
    """Get event status based on capacity"""
    registration_count = event.registration_count
    max_participants = event.max_participants
    
    if registration_count >= max_participants:
        return 'Full'
    elif registration_count >= max_participants * 0.8:
        return 'Almost Full'
    elif registration_count >= max_participants * 0.5:
        return 'Half Full'
    else:
        return 'Open'