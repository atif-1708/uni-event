import os
from datetime import timedelta

class Config:
    # General Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_for_development_only')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://event_db_mmjn_user:zZpdPTQRAakpQ9O0FG02nTFsa5YBYUPx@dpg-d01tkqngi27c73f15610-a/event_db_mmjn')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Mail configuration
    # For development with debugging server
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 1025
    MAIL_USE_TLS = False
    MAIL_USE_SSL = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@university.edu')
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)