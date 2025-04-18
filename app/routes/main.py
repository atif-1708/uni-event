from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from app.models import Event
from sqlalchemy import or_
import os
from flask import current_app

main = Blueprint('main', __name__)
@main.context_processor
def inject_logo_status():
    logo_path = os.path.join(current_app.root_path, 'static', 'images', 'university_logo.png')
    logo_exists = os.path.exists(logo_path)
    return {'logo_exists': logo_exists}
# @main.route('/')
@main.route('/home')
def home():
    page = request.args.get('page', 1, type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    now = datetime.utcnow()
    query = Event.query

    # Optional filter: start date
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Event.date >= date_from_dt)
        except ValueError:
            pass

    # Optional filter: end date
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Event.date <= date_to_dt)
        except ValueError:
            pass

    # ✅ Show events that are still active (not ended)
    query = query.filter(or_(Event.end_date == None, Event.end_date >= now))

    # Sort by upcoming first
    query = query.order_by(Event.date.asc())

    # Pagination
    events = query.paginate(page=page, per_page=6)

    return render_template('index.html', events=events, title='Home')

@main.route('/about')
def about():
    return render_template('about.html', title='About')

@main.route('/contact')
def contact():
    return render_template('contact.html', title='Contact Us')

@main.route('/events/api')
def events_api():
    """API endpoint for getting events in JSON format (for AJAX filtering)"""
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    now = datetime.utcnow()
    query = Event.query

    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Event.date >= date_from_dt)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Event.date <= date_to_dt)
        except ValueError:
            pass

    # ✅ Filter for events that haven’t ended
    query = query.filter(or_(Event.end_date == None, Event.end_date >= now))
    query = query.order_by(Event.date.asc())

    events = query.all()

    # Convert to JSON serializable format
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'description': event.description[:100] + '...' if len(event.description) > 100 else event.description,
            'date': event.date.strftime('%Y-%m-%d %H:%M'),
            'end_date': event.end_date.strftime('%Y-%m-%d %H:%M') if event.end_date else 'N/A',
            'location': event.location,
            'registration_count': event.registration_count,
            'max_participants': event.max_participants,
            'is_full': event.is_full
        })

    return jsonify(events_data)
