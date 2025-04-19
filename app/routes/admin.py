import io
import csv
import os
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, abort, Response, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Event, Registration, User
from flask_wtf import FlaskForm
from app.utils.helpers import admin_required
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, IntegerField, DateTimeField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from app.utils.helpers import validate_event_csv, process_event_csv
from flask import jsonify, request
from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func, desc, and_, or_, extract
from datetime import datetime, timedelta
import io
import csv
from functools import wraps
import calendar

from app import db
from app.models import Event, Registration, User
# Create the Blueprint first
admin = Blueprint('admin', __name__, url_prefix='/admin')



# Helper function to count new registrations for notifications
def get_new_registration_count():
    return Registration.query.filter_by(admin_viewed=False).count()

# Context processor to inject new registration count into all templates
@admin.context_processor
def inject_new_registration_count():
    if current_user.is_authenticated and current_user.is_admin():
        return {'new_registration_count': get_new_registration_count()}
    return {'new_registration_count': 0}

# Form classes
class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    date = DateTimeField('Start Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_date = DateTimeField('End Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    registration_deadline = DateTimeField('Registration Deadline', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    max_participants = IntegerField('Max Participants', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save Event')

class UserFilterForm(FlaskForm):
    search = StringField('Search')
    department = SelectField('Department', choices=[('', 'All Departments')], validate_choice=False)
    submit = SubmitField('Apply Filters')

class LogoUploadForm(FlaskForm):
    logo = FileField('University Logo', validators=[
        FileAllowed(['png', 'jpg', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Upload Logo')

# Routes
@admin.route('/dashboard')
@admin_required
def dashboard():
    upcoming_events_count = Event.query.filter(Event.date >= datetime.utcnow()).count()
    total_registrations = Registration.query.count()
    total_students = User.query.filter_by(role='student').count()
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow()).order_by(Event.date.asc()).limit(5).all()

    return render_template('admin/dashboard.html',
                           title='Admin Dashboard',
                           upcoming_events_count=upcoming_events_count,
                           total_registrations=total_registrations,
                           total_students=total_students,
                           recent_events=recent_events,
                           upcoming_events=upcoming_events)

@admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    
        
    logo_form = LogoUploadForm()
    
    # Check if logo exists and get last modified date
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'university_logo.png')
    logo_exists = os.path.exists(logo_path)
    logo_last_modified = None
    if logo_exists:
        # Get last modified time and format it
        mod_timestamp = os.path.getmtime(logo_path)
        logo_last_modified = datetime.fromtimestamp(mod_timestamp).strftime('%B %d, %Y at %I:%M %p')
    
    if logo_form.validate_on_submit():
        if logo_form.logo.data:
            try:
                # Ensure directory exists
                logo_dir = os.path.join(current_app.root_path, 'static', 'images')
                if not os.path.exists(logo_dir):
                    os.makedirs(logo_dir)
                
                # Save logo with a fixed name to ensure passes always use latest logo
                filename = 'university_logo.png'
                logo_form.logo.data.save(os.path.join(logo_dir, filename))
                
                flash('University logo has been updated successfully!', 'success')
                return redirect(url_for('admin.settings'))
            except Exception as e:
                flash(f'Error saving logo: {str(e)}', 'danger')
    
    return render_template(
        'admin/settings.html',
        title='System Settings',
        logo_form=logo_form,
        logo_exists=logo_exists,
        logo_last_modified=logo_last_modified
    )

@admin.route('/settings/delete-logo', methods=['POST'])
@admin_required
def delete_logo():
    # Find the logo path
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'university_logo.png')
    
    # Check if logo exists
    if os.path.exists(logo_path):
        try:
            # Delete the file
            os.remove(logo_path)
            flash('University logo has been deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error deleting logo: {str(e)}', 'danger')
    else:
        flash('No logo file found to delete.', 'warning')
    
    return redirect(url_for('admin.settings'))

@admin.route('/events')
@admin_required
def events():
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    query = Event.query.order_by(Event.date.asc())

    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Event.date >= date_from)
        except ValueError:
            pass

    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Event.date <= date_to)
        except ValueError:
            pass

    events = query.paginate(page=page, per_page=10)
    return render_template('admin/events.html', title='Manage Events', events=events)

@admin.route('/events/create', methods=['GET', 'POST'])
@admin_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            description=form.description.data,
            date=form.date.data,
            end_date=form.end_date.data,
            registration_deadline=form.registration_deadline.data,
            location=form.location.data,
            max_participants=form.max_participants.data
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('admin.events'))
    return render_template('admin/create_event.html', title='Create Event', form=form)

@admin.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_event(event_id):
    event = Event.query.get_or_404(event_id)
    form = EventForm()

    if form.validate_on_submit():
        event.title = form.title.data
        event.description = form.description.data
        event.date = form.date.data
        event.end_date = form.end_date.data
        event.registration_deadline = form.registration_deadline.data
        event.location = form.location.data
        event.max_participants = form.max_participants.data

        db.session.commit()
        flash('Event updated successfully!', 'success')
        return redirect(url_for('admin.events'))

    elif request.method == 'GET':
        form.title.data = event.title
        form.description.data = event.description
        form.date.data = event.date
        form.end_date.data = event.end_date
        form.registration_deadline.data = event.registration_deadline
        form.location.data = event.location
        form.max_participants.data = event.max_participants

    return render_template('admin/edit_event.html', title='Edit Event', form=form, event=event)

@admin.route('/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event(event_id):
    event = Event.query.get_or_404(event_id)
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully!', 'success')
    return redirect(url_for('admin.events'))

@admin.route('/events/<int:event_id>/registrations')
@admin_required
def event_registrations(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = Registration.query.filter_by(event_id=event_id).all()
    
    # Mark these registrations as viewed by admin
    for reg in registrations:
        if not reg.admin_viewed:
            reg.admin_viewed = True
    db.session.commit()
    
    registration_data = [{
        'id': r.id,
        'user_id': r.user_id,
        'username': r.user.username,
        'email': r.user.email,
        'registered_at': r.registered_at,
        'attended': r.attended
    } for r in registrations]
    return render_template('admin/registrations.html',
                           title=f'Registrations - {event.title}',
                           event=event,
                           registrations=registration_data)

@admin.route('/new_registrations')
@admin_required
def new_registrations():
    page = request.args.get('page', 1, type=int)
    new_regs = Registration.query.filter_by(admin_viewed=False).join(
        Event, Registration.event_id == Event.id
    ).join(
        User, Registration.user_id == User.id
    ).order_by(Registration.registered_at.desc()).paginate(page=page, per_page=10)
    
    # Mark registrations as viewed if requested
    if request.args.get('mark_viewed') == 'true':
        regs_to_update = Registration.query.filter_by(admin_viewed=False).all()
        for reg in regs_to_update:
            reg.admin_viewed = True
        db.session.commit()
        flash('All new registration notifications marked as viewed', 'success')
        return redirect(url_for('admin.new_registrations'))
    
    return render_template('admin/new_registrations.html', 
                          title='New Event Registrations',
                          registrations=new_regs,
                          new_count=get_new_registration_count())

@admin.route('/events/<int:event_id>/registrations/export')
@admin_required
def export_registrations(event_id):
    event = Event.query.get_or_404(event_id)
    registrations = Registration.query.filter_by(event_id=event_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Username', 'Email', 'Registration Date', 'Attended'])

    for reg in registrations:
        user = User.query.get(reg.user_id)
        writer.writerow([
            reg.id, user.username, user.email,
            reg.registered_at.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if reg.attended else 'No'
        ])

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=registrations_{event.title.replace(" ", "_")}.csv'}
    )

@admin.route('/scan-attendance', methods=['GET'])
@login_required
def scan_attendance():
    """Display the QR code scanner interface for marking attendance"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/scan_attendance.html')

@admin.route('/mark-attendance', methods=['POST'])
@login_required
def mark_attendance():
    """API endpoint to mark attendance based on scanned QR code"""
    if not current_user.is_admin():
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    
    try:
        data = request.json
        qr_content = data.get('registration_id')
        
        if not qr_content:
            return jsonify({'success': False, 'message': 'Invalid QR code content'}), 400
        
        # Debug the received content
        print(f"QR Code content: {qr_content}")
        
        # Parse the pipe-delimited format: EVENT:1|USER:4|REG:1|ID:FB23B860
        registration_id = None
        parts = qr_content.split('|')
        
        for part in parts:
            if part.startswith('REG:'):
                try:
                    registration_id = int(part.split(':')[1])
                    break
                except (ValueError, IndexError):
                    pass
        
        if not registration_id:
            return jsonify({
                'success': False, 
                'message': 'Could not find registration ID in QR code'
            }), 400
        
        # Find the registration
        registration = Registration.query.get(registration_id)
        
        if not registration:
            return jsonify({
                'success': False, 
                'message': f'Registration not found with ID: {registration_id}'
            }), 404
        
        # Check if already marked as attended
        if registration.attended:
            # Get user and event info for the response
            student = User.query.get(registration.user_id)
            event = Event.query.get(registration.event_id)
            
            return jsonify({
                'success': False, 
                'message': 'Already marked as attended',
                'student': {
                    'name': student.full_name if hasattr(student, 'full_name') and student.full_name else student.username,
                },
                'event': {
                    'title': event.title
                }
            }), 200
        
        # Mark as attended
        registration.attended = True
        db.session.commit()
        
        # Get user and event info for the response
        student = User.query.get(registration.user_id)
        event = Event.query.get(registration.event_id)
        
        return jsonify({
            'success': True, 
            'message': 'Attendance marked successfully',
            'student': {
                'name': student.full_name if hasattr(student, 'full_name') and student.full_name else student.username,
            },
            'event': {
                'title': event.title
            }
        })
    
    except Exception as e:
        # Log the error
        import traceback
        print(f"Error marking attendance: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
@admin.route('/events/<int:event_id>/registrations/<int:reg_id>/toggle-attendance', methods=['POST'])
@admin_required
def toggle_attendance(event_id, reg_id):
    registration = Registration.query.get_or_404(reg_id)
    if registration.event_id != event_id:
        abort(404)
    registration.attended = not registration.attended
    db.session.commit()
    flash(f'Attendance updated: {"Attended" if registration.attended else "Not Attended"}', 'success')
    return redirect(url_for('admin.event_registrations', event_id=event_id))

@admin.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    
    # Create filter form and populate department choices
    form = UserFilterForm()
    departments = db.session.query(User.department).filter(User.department.isnot(None)).distinct().all()
    department_choices = [('', 'All Departments')] + [(d[0], d[0]) for d in departments if d[0]]
    form.department.choices = department_choices
    
    # Apply filters
    query = User.query
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.ilike(search_term),
                User.email.ilike(search_term),
                User.full_name.ilike(search_term),
                User.student_id.ilike(search_term)
            )
        )
    
    if department:
        query = query.filter(User.department == department)
    
    # Sort and paginate
    users = query.order_by(User.username).paginate(page=page, per_page=10)
    
    return render_template('admin/users.html', 
                          title='Users',
                          users=users,
                          form=form,
                          search=search,
                          department=department)

@admin.route('/users/<int:user_id>')
@admin_required
def user_details(user_id):
    user = User.query.get_or_404(user_id)
    # Get recent registrations with event information
    registrations = Registration.query.filter_by(user_id=user_id).\
        join(Event, Registration.event_id == Event.id).\
        order_by(Registration.registered_at.desc()).limit(5).all()
    
    # Pass current time for registration status
    now = datetime.utcnow()
    
    return render_template('admin/user_details.html', 
                          title=f'User Profile: {user.username}',
                          user=user,
                          registrations=registrations,
                          now=now)

@admin.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting self
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.user_details', user_id=user_id))
    
    # Prevent deleting other admins
    if user.role == 'admin' and current_user.id != 1:  # Assuming user ID 1 is super admin
        flash('Only the super administrator can delete admin accounts!', 'danger')
        return redirect(url_for('admin.user_details', user_id=user_id))
    
    # Delete profile image if it exists
    if user.profile_image and user.profile_image != 'default.jpg':
        try:
            profile_image_path = os.path.join(current_app.root_path, 'static', 'profile_pics', user.profile_image)
            if os.path.exists(profile_image_path):
                os.remove(profile_image_path)
        except Exception as e:
            # Log the error but continue with user deletion
            print(f"Error removing profile image: {str(e)}")
    
    # First delete all registrations related to this user
    registrations = Registration.query.filter_by(user_id=user_id).all()
    for registration in registrations:
        db.session.delete(registration)
    
    # Then delete the user
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User "{username}" has been deleted successfully.', 'success')
    return redirect(url_for('admin.users'))

# Reports routes
@admin.route('/reports')
@login_required
@admin_required
def reports():
    """Generate analytics reports for events"""
    # Get filter parameters
    date_range = request.args.get('date_range', 'all')
    status = request.args.get('status', 'all')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Process date range
    start_date = None
    end_date = None
    today = datetime.utcnow().date()
    
    if date_range == 'thisMonth':
        start_date = datetime(today.year, today.month, 1)
        # Get last day of current month
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
    elif date_range == 'lastMonth':
        # Get first day of previous month
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
            end_date = datetime(today.year, 1, 1) - timedelta(seconds=1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
            last_day = calendar.monthrange(today.year, today.month - 1)[1]
            end_date = datetime(today.year, today.month - 1, last_day, 23, 59, 59)
    elif date_range == 'thisYear':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
    elif date_range == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD format.', 'warning')
    
    # Build query filters
    filters = []
    
    if start_date and end_date:
        filters.append(Event.date >= start_date)
        filters.append(Event.date <= end_date)
    
    if status != 'all':
        today_datetime = datetime.utcnow()
        if status == 'upcoming':
            filters.append(Event.date > today_datetime)
        elif status == 'ongoing':
            filters.append(Event.date <= today_datetime)
            filters.append(or_(Event.end_date == None, Event.end_date > today_datetime))
        elif status == 'ended':
            filters.append(Event.end_date <= today_datetime)
    
    # Apply filters to query
    query = Event.query
    if filters:
        query = query.filter(*filters)
    
    # Get all events based on filters
    events = query.all()
    
    # Get top events by registration count
    top_events = sorted(events, key=lambda e: e.registration_count, reverse=True)[:5]
    
    # Get top events by attendance rate (attended / registered)
    top_attendance_events = []
    for event in events:
        total_registered = event.registration_count
        if total_registered > 0:  # Avoid division by zero
            # Count attended registrations
            attended_count = Registration.query.filter_by(
                event_id=event.id, 
                attended=True
            ).count()
            
            # Add to event object for use in template
            event.attended_count = attended_count
            
            # Add to top attendance events if it has some attendance
            if attended_count > 0:
                top_attendance_events.append(event)
    
    # Sort by attendance rate
    top_attendance_events = sorted(
        top_attendance_events, 
        key=lambda e: (e.attended_count / e.registration_count), 
        reverse=True
    )[:5]
    
    # Calculate summary statistics
    total_events = len(events)
    total_registrations = sum(event.registration_count for event in events)
    total_attended = sum(getattr(event, 'attended_count', 0) for event in events)
    
    attendance_rate = 0
    if total_registrations > 0:
        attendance_rate = round((total_attended / total_registrations) * 100)
    
    avg_capacity = 0
    if total_events > 0:
        total_capacity_percentage = sum(
            min(event.registration_count / event.max_participants * 100, 100) 
            for event in events
        )
        avg_capacity = round(total_capacity_percentage / total_events)
    
    # Get registration trends data
    trend_dates = []
    registration_trends = []
    
    if start_date and end_date:
        # Group by date and count registrations for trend chart
        trend_query = db.session.query(
            func.date(Registration.registered_at).label('date'),
            func.count(Registration.id).label('count')
        ).join(Event).filter(
            Registration.event_id == Event.id
        )
        
        if filters:
            trend_query = trend_query.filter(*filters)
        
        trend_query = trend_query.group_by(
            func.date(Registration.registered_at)
        ).order_by(
            func.date(Registration.registered_at)
        ).all()
        
        # Format for chart.js
        for date, count in trend_query:
            trend_dates.append(date.strftime('%Y-%m-%d'))
            registration_trends.append(count)
    
    return render_template('admin/reports.html',
                          events=events,
                          top_events=top_events,
                          top_attendance_events=top_attendance_events,
                          total_events=total_events,
                          total_registrations=total_registrations,
                          total_attended=total_attended,
                          attendance_rate=attendance_rate,
                          avg_capacity=avg_capacity,
                          trend_dates=trend_dates,
                          registration_trends=registration_trends,
                          date_range=date_range,
                          status=status,
                          start_date=start_date_str,
                          end_date=end_date_str)

@admin.route('/reports/export-csv')
@login_required
@admin_required
def export_report_csv():
    """Export event report data as CSV"""
    # Get all events
    events = Event.query.all()
    
    if not events:
        flash('No event data available to export.', 'warning')
        return redirect(url_for('admin.reports'))
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Event ID', 'Title', 'Description', 'Date', 'End Date', 
        'Registration Deadline', 'Location', 'Max Participants',
        'Registered Count', 'Attended Count', 'Status'
    ])
    
    # Write data
    for event in events:
        # Get attended count
        attended_count = Registration.query.filter_by(
            event_id=event.id, 
            attended=True
        ).count()
        
        writer.writerow([
            event.id,
            event.title,
            event.description[:100] + '...' if len(event.description) > 100 else event.description,
            event.date.strftime('%Y-%m-%d %H:%M:%S'),
            event.end_date.strftime('%Y-%m-%d %H:%M:%S') if event.end_date else 'N/A',
            event.registration_deadline.strftime('%Y-%m-%d %H:%M:%S') if event.registration_deadline else 'N/A',
            event.location,
            event.max_participants,
            event.registration_count,
            attended_count,
            event.status
        ])
    
    # Prepare response
    output.seek(0)
    now = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"event_report_{now}.csv"
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@admin.route('/reports/export-pdf')
@login_required
@admin_required
def export_report_pdf():
    """Export event report data as PDF"""
    try:
        # Try to import PDF generation libraries
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        flash('PDF export requires ReportLab library. Please install it: pip install reportlab', 'warning')
        return redirect(url_for('admin.reports'))
    
    # Get all events
    events = Event.query.all()
    
    if not events:
        flash('No event data available to export.', 'warning')
        return redirect(url_for('admin.reports'))
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Prepare document content
    elements = []
    
    # Title
    title = Paragraph("University Event Management System - Event Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Date generated
    date_text = Paragraph(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}", styles['Normal'])
    elements.append(date_text)
    elements.append(Spacer(1, 12))
    
    # Summary statistics
    total_events = len(events)
    total_registrations = sum(event.registration_count for event in events)
    total_attended = Registration.query.filter_by(attended=True).count()
    
    summary_data = [
        ["Total Events", str(total_events)],
        ["Total Registrations", str(total_registrations)],
        ["Total Attended", str(total_attended)],
        ["Attendance Rate", f"{round((total_attended / total_registrations) * 100) if total_registrations > 0 else 0}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[200, 100])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(Paragraph("Summary Statistics", styles['Heading2']))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Top events table
    top_events = sorted(events, key=lambda e: e.registration_count, reverse=True)[:5]
    
    elements.append(Paragraph("Top 5 Events by Registration", styles['Heading2']))
    if top_events:
        top_data = [["Event Title", "Date", "Location", "Registrations", "Capacity"]]
        
        for event in top_events:
            top_data.append([
                event.title,
                event.date.strftime('%Y-%m-%d'),
                event.location,
                str(event.registration_count),
                f"{event.registration_count}/{event.max_participants}"
            ])
        
        top_table = Table(top_data, colWidths=[150, 80, 100, 80, 80])
        top_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(top_table)
    else:
        elements.append(Paragraph("No event data available", styles['Normal']))
    
    elements.append(Spacer(1, 20))
    
    # All events table
    elements.append(Paragraph("All Events", styles['Heading2']))
    
    event_data = [["Title", "Date", "Location", "Registrations", "Status"]]
    
    for event in events:
        event_data.append([
            event.title,
            event.date.strftime('%Y-%m-%d'),
            event.location,
            str(event.registration_count),
            event.status
        ])
    
    event_table = Table(event_data, colWidths=[150, 80, 100, 80, 80])
    event_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(event_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Prepare response
    now = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"event_report_{now}.pdf"
    
    return send_file(
        buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@admin.route('/api/event-stats')
@login_required
@admin_required
def event_stats_api():
    """API endpoint to get event statistics for AJAX requests"""
    # Get filter parameters
    date_range = request.args.get('date_range', 'all')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Process date range
    start_date = None
    end_date = None
    today = datetime.utcnow().date()
    
    if date_range == 'thisMonth':
        start_date = datetime(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = datetime(today.year, today.month, last_day, 23, 59, 59)
    elif date_range == 'lastMonth':
        if today.month == 1:
            start_date = datetime(today.year - 1, 12, 1)
            end_date = datetime(today.year, 1, 1) - timedelta(seconds=1)
        else:
            start_date = datetime(today.year, today.month - 1, 1)
            last_day = calendar.monthrange(today.year, today.month - 1)[1]
            end_date = datetime(today.year, today.month - 1, last_day, 23, 59, 59)
    elif date_range == 'thisYear':
        start_date = datetime(today.year, 1, 1)
        end_date = datetime(today.year, 12, 31, 23, 59, 59)
    elif date_range == 'custom' and start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    # Build query filters
    filters = []
    
    if start_date and end_date:
        filters.append(Event.date >= start_date)
        filters.append(Event.date <= end_date)
    
    # Apply filters to query
    registration_query = db.session.query(
        func.date(Registration.registered_at).label('date'),
        func.count(Registration.id).label('count')
    )
    
    if filters:
        registration_query = registration_query.join(Event).filter(*filters)
    
    registration_data = registration_query.group_by(
        func.date(Registration.registered_at)
    ).order_by(
        func.date(Registration.registered_at)
    ).all()
    
    # Format for chart.js
    dates = [date.strftime('%Y-%m-%d') for date, _ in registration_data]
    counts = [count for _, count in registration_data]
    
    return jsonify({
        'dates': dates,
        'counts': counts
    })
@admin.route('/bulk-upload', methods=['GET'])
@login_required
def bulk_upload_view():
    """Display the bulk upload page for events"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    return render_template('admin/bulk_upload.html')

@admin.route('/bulk-upload', methods=['POST'])
@login_required
def bulk_upload_events():
    """Handle the bulk upload of events via CSV"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    # Check if file was uploaded
    if 'file' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('admin.bulk_upload_view'))
    
    file = request.files['file']
    
    # Check if file is empty
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('admin.bulk_upload_view'))
    
    # Validate the CSV
    is_valid, error_message = validate_event_csv(file)
    
    if not is_valid:
        flash(error_message, 'danger')
        return redirect(url_for('admin.bulk_upload_view'))
    
    # Process the CSV
    events_data = process_event_csv(file)
    
    # Check if any events were found
    if not events_data:
        flash('No events found in the CSV file', 'warning')
        return redirect(url_for('admin.bulk_upload_view'))
    
    # Insert events into the database
    try:
        count = 0
        for event_data in events_data:
            # Skip if any required field is missing
            if not all(key in event_data and event_data[key] for key in ['title', 'description', 'date', 'end_date', 'registration_deadline', 'location', 'max_participants']):
                continue
                
            # Create new event object
            new_event = Event(
                title=event_data['title'],
                description=event_data['description'],
                date=event_data['date'],
                end_date=event_data['end_date'],
                registration_deadline=event_data['registration_deadline'],
                location=event_data['location'],
                max_participants=int(event_data['max_participants'])
            )
            
            db.session.add(new_event)
            count += 1
        
        db.session.commit()
        flash(f'Successfully imported {count} events', 'success')
        return redirect(url_for('admin.events'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error importing events: {str(e)}', 'danger')
        return redirect(url_for('admin.bulk_upload_view'))

@admin.route('/download-event-template', methods=['GET'])
@login_required
def download_event_template():
    """Provides a CSV template for event bulk upload"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))
    
    from flask import send_file
    import csv
    from io import StringIO
    
    # Create a CSV template in memory
    si = StringIO()
    writer = csv.writer(si)
    
    # Write headers
    writer.writerow(['title', 'description', 'date', 'end_date', 'registration_deadline', 
                     'location', 'max_participants'])
    
    # Write a sample row
    writer.writerow([
        'Sample Workshop',
        'This is a sample event description.',
        '2025-05-01 14:00',  # Start date
        '2025-05-01 16:00',  # End date (required)
        '2025-04-28 23:59',  # Registration deadline (required)
        'Main Campus, Room 101',
        '50'
    ])
    
    output = si.getvalue()
    si.close()
    
    # Create a response with the CSV content
    from flask import Response
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=event_template.csv"}
    )