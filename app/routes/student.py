from datetime import datetime
import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Event, Registration, get_local_time
from app.utils.email import send_registration_confirmation

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

student = Blueprint('student', __name__, url_prefix='/student')

# In app/routes/student.py

@student.route('/registrations/<int:registration_id>/pass')
@login_required
def event_pass(registration_id):
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    registration = Registration.query.get_or_404(registration_id)
    
    # Ensure the user owns this registration
    if registration.user_id != current_user.id:
        abort(403)
    
    event = Event.query.get_or_404(registration.event_id)
    
    # Generate the pass
    try:
        from app.utils.helpers import generate_event_pass
        pass_data = generate_event_pass(current_user, event, registration)
        
        return render_template(
            'student/event_pass.html',
            title=f"Event Pass - {event.title}",
            registration=registration,
            event=event,
            pass_data=pass_data
        )
    except Exception as e:
        flash(f"Error generating event pass: {str(e)}", "danger")
        return redirect(url_for('student.dashboard'))
# Dashboard to display events categorized
@student.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    user_registrations = Registration.query.filter_by(user_id=current_user.id).all()
    registered_event_ids = [reg.event_id for reg in user_registrations]

    registered_events = []
    for reg in user_registrations:
        event = Event.query.get(reg.event_id)
        if event:
            registered_events.append({
                'registration_id': reg.id,
                'event': event,
                'registered_at': reg.registered_at,
                'attended': reg.attended
            })

    # Get current local time for comparisons (naive datetime)
    now = get_local_time()

    # We can't directly filter with local time in the query
    # So we'll filter in memory after fetching events
    all_events = Event.query.order_by(Event.date.asc()).all()
    
    upcoming_events = []
    ongoing_events = []
    ended_events = []
    deadline_passed_events = []
    
    for event in all_events:
        if event.end_date and event.end_date < now:
            ended_events.append(event)
        elif event.registration_deadline and event.registration_deadline < now and event.end_date and event.end_date >= now:
            deadline_passed_events.append(event)
        elif event.date > now and (not event.registration_deadline or event.registration_deadline >= now):
            upcoming_events.append(event)
        elif event.date <= now and event.end_date and event.end_date >= now and (not event.registration_deadline or event.registration_deadline >= now):
            ongoing_events.append(event)

    return render_template('student/dashboard.html',
                           title='Student Dashboard',
                           registered_events=registered_events,
                           upcoming_events=upcoming_events,
                           ongoing_events=ongoing_events,
                           ended_events=ended_events,
                           deadline_passed_events=deadline_passed_events)

# Display events with filtering options
@student.route('/events')
@login_required
def events():
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    # We can't directly use local time in the query, so we'll start with all events
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

    # Get all matching events and filter in memory
    all_events = query.all()
    now = get_local_time()
    
    # Filter for events that haven't started yet and registration is still open
    filtered_events = [e for e in all_events if e.date >= now and (not e.registration_deadline or e.registration_deadline >= now)]
    
    # Calculate total pages and current page data
    per_page = 6
    total = len(filtered_events)
    total_pages = (total + per_page - 1) // per_page  # ceiling division
    current_page = min(max(1, page), max(1, total_pages))
    
    start_idx = (current_page - 1) * per_page
    end_idx = min(start_idx + per_page, total)
    current_page_data = filtered_events[start_idx:end_idx]
    
    # Create a simple pagination object
    class SimplePagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
        
        def iter_pages(self, left_edge=2, left_current=2, right_current=3, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                   (num > self.page - left_current - 1 and num < self.page + right_current) or \
                   num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num
        
        @property
        def pages(self):
            return (self.total + self.per_page - 1) // self.per_page
        
        @property
        def has_prev(self):
            return self.page > 1
        
        @property
        def has_next(self):
            return self.page < self.pages
        
        @property
        def prev_num(self):
            return self.page - 1 if self.has_prev else None
        
        @property
        def next_num(self):
            return self.page + 1 if self.has_next else None
    
    # Create pagination object
    pagination = SimplePagination(current_page_data, current_page, per_page, total)
    
    user_registrations = Registration.query.filter_by(user_id=current_user.id).all()
    registered_event_ids = [reg.event_id for reg in user_registrations]

    return render_template('student/events.html',
                           title='Events',
                           events=pagination,
                           registered_event_ids=registered_event_ids)

# Display event details with registration options
@student.route('/events/<int:event_id>')
@login_required
def event_details(event_id):
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    event = Event.query.get_or_404(event_id)

    registration = Registration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()

    registration_count = Registration.query.filter_by(event_id=event_id).count()

    return render_template('student/event_details.html',
                           title=event.title,
                           event=event,
                           is_registered=registration is not None,
                           registration=registration,
                           registration_count=registration_count,
                           now=get_local_time())

# Register for the event
@student.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_for_event(event_id):
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    event = Event.query.get_or_404(event_id)
    
    # Debug logging
    now = get_local_time()
    logger.info(f"Current local time: {now}")
    logger.info(f"Event registration deadline: {event.registration_deadline}")
    logger.info(f"Is deadline passed? {event.registration_closed}")
    logger.info(f"Has event ended? {event.has_ended}")
    
    # Disable registration if event ended
    if event.has_ended:
        flash("This event has already ended. Registration is closed.", "warning")
        return redirect(url_for('student.event_details', event_id=event_id))

    # Disable registration if deadline passed
    if event.registration_closed:
        flash("The registration deadline for this event has passed.", "warning")
        return redirect(url_for('student.event_details', event_id=event_id))

    # Prevent registration if already registered
    existing_registration = Registration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id
    ).first()

    if existing_registration:
        flash('You are already registered for this event!', 'info')
        return redirect(url_for('student.event_details', event_id=event_id))

    # Prevent registration if the event is full
    if event.is_full:
        flash('This event is already at maximum capacity!', 'danger')
        return redirect(url_for('student.event_details', event_id=event_id))

    # All checks passed, create a new registration
    registration = Registration(
        user_id=current_user.id,
        event_id=event_id,
        admin_viewed=False  # Set as unviewed for admin notifications
    )

    db.session.add(registration)
    db.session.commit()

    send_registration_confirmation(current_user, event)

    flash('You have successfully registered for this event!', 'success')
    return redirect(url_for('student.dashboard'))

# Cancel registration for event
@student.route('/registrations/<int:registration_id>/cancel', methods=['POST'])
@login_required
def cancel_registration(registration_id):
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))

    registration = Registration.query.get_or_404(registration_id)

    if registration.user_id != current_user.id:
        abort(403)

    event = Event.query.get_or_404(registration.event_id)

    db.session.delete(registration)
    db.session.commit()

    flash(f'Your registration for "{event.title}" has been cancelled.', 'info')
    return redirect(url_for('student.dashboard'))