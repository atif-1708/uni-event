# Routes package initialization
from flask import Flask, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os
from datetime import datetime
from app.utils.helpers import logo_exists_helper
from app.config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    # Override database URI with environment variable if set (e.g. on Render)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
     app.config['SQLALCHEMY_DATABASE_URI'] = database_url

    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)  # Initialize Flask-Mail
    
    app.jinja_env.globals.update(logo_exists=logo_exists_helper)
    
    # Add current date to templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    @app.context_processor
    def inject_logo_status():
        logo_path = os.path.join(app.root_path, 'static', 'images', 'university_logo.png')
        logo_exists = os.path.exists(logo_path)
        return {'logo_exists': logo_exists}
    
    # Add this root route
    @app.route('/')
    def root():
        return redirect('/home')  # Redirect to your existing home page
    
    # Register blueprints
    from app.routes.admin import admin
    from app.routes.auth import auth
    from app.routes.main import main
    from app.routes.student import student
    
    app.register_blueprint(admin, url_prefix='/admin')
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(main, url_prefix='/home')
    app.register_blueprint(student, url_prefix='/student')

    return app