from datetime import datetime
import pytz  # You'll need to install this: pip install pytz
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager

# Add this function to get the current time in your local timezone
def get_local_time():
    """Get current time in your local timezone."""
    utc_now = datetime.utcnow()
    # Replace 'Asia/Kolkata' with your actual timezone if different
    # Examples: 'Europe/London', 'America/New_York', 'Asia/Dubai'
    local_tz = pytz.timezone('Asia/Karachi')
    local_now = utc_now.replace(tzinfo=pytz.utc).astimezone(local_tz)
    # Return as naive datetime for comparison with database values
    return local_now.replace(tzinfo=None)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)  # New field for full name
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  
    student_id = db.Column(db.String(100), nullable=True)  # New field for student ID
    profile_image = db.Column(db.String(200), nullable=True)  # New field for profile picture URL
    department = db.Column(db.String(100), nullable=True)  # Department
    bio = db.Column(db.String(500), nullable=True)  # Optional bio field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship('Registration', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

   

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.role}')"



class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)  # Start Date
    end_date = db.Column(db.DateTime, nullable=True)
    registration_deadline = db.Column(db.DateTime, nullable=True)  # New Field
    location = db.Column(db.String(100), nullable=False)
    max_participants = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    registrations = db.relationship('Registration', backref='event', lazy=True, cascade="all, delete-orphan")

    @property
    def registration_count(self):
        return Registration.query.filter_by(event_id=self.id).count()

    @property
    def is_full(self):
        return self.registration_count >= self.max_participants

    @property
    def has_ended(self):
        """Determines if the event has ended based on the end_date."""
        if self.end_date is None:
            return False
        # Compare with local time (both naive datetimes)
        return self.end_date < get_local_time()

    @property
    def registration_closed(self):
        """Checks if registration has closed based on the registration_deadline."""
        if self.registration_deadline is None:
            return False
        # Compare with local time (both naive datetimes)
        return self.registration_deadline < get_local_time()

    @property
    def status(self):
        """Categorizes the event into 'Upcoming', 'Ongoing', or 'Ended'."""
        now = get_local_time()  # Use local time instead of UTC
        if self.registration_deadline and self.registration_deadline < now:
            return 'Deadline Passed'
        if self.has_ended:
            return 'Ended'
        if self.date > now:
            return 'Upcoming'
        return 'Ongoing'

    def __repr__(self):
        return f"Event('{self.title}', '{self.date}', '{self.status}')"

class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)
    admin_viewed = db.Column(db.Boolean, default=False)  # Add this line

    __table_args__ = (db.UniqueConstraint('user_id', 'event_id', name='uix_registration_user_event'),)

    def __repr__(self):
        return f"Registration(User ID: {self.user_id}, Event ID: {self.event_id})"