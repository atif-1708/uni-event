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

@admin.route('/reports')
@admin_required
def reports():
    events = Event.query.order_by(Event.date.desc()).all()
    top_events = sorted(events, key=lambda e: e.registration_count, reverse=True)[:3]
    now = datetime.utcnow() 
     # Make sure each event has a title and registration_count
    for event in events:
        if not hasattr(event, 'registration_count') or event.registration_count is None:
            event.registration_count = 0
    return render_template('admin/reports.html', title='Reports', events=events, top_events=top_events)

@admin.route('/reports/export')
@admin_required
def export_report_csv():
    events = Event.query.order_by(Event.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Event Title', 'Start Date', 'End Date', 'Reg Deadline', 'Location', 'Registered', 'Capacity'])

    for event in events:
        writer.writerow([
            event.title,
            event.date.strftime('%Y-%m-%d %H:%M'),
            event.end_date.strftime('%Y-%m-%d %H:%M') if event.end_date else 'N/A',
            event.registration_deadline.strftime('%Y-%m-%d %H:%M') if event.registration_deadline else 'N/A',
            event.location,
            event.registration_count,
            event.max_participants
        ])

    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=event_report.csv'}
    )