import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from app.config import Config
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    # Configure login settings
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Import and register blueprints
    from app.routes.main import main
    from app.routes.auth import auth
    from app.routes.admin import admin
    from app.routes.student import student

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(student)

    # Add context processor to make 'now' available in all templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    # Add context processor for new registration count
    @app.context_processor
    def inject_new_registration_count():
        new_registration_count = 0
        if current_user.is_authenticated and hasattr(current_user, 'is_admin') and current_user.is_admin():
            # Import models here to avoid circular imports
            from app.models import Registration
            new_registration_count = Registration.query.filter_by(admin_viewed=False).count()
        return {'new_registration_count': new_registration_count}

    # Add context processor for the current year (for footer copyright)
    @app.context_processor
    def inject_year():
        return {'year': datetime.utcnow().year}

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app