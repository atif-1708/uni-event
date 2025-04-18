# Routes package initialization
from flask import Flask, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
import os
from app.utils.helpers import logo_exists_helper

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'
    db.init_app(app)
    app.jinja_env.globals.update(logo_exists=logo_exists_helper)

    @app.context_processor
    def inject_logo_status():
        logo_path = os.path.join(app.root_path, 'static', 'images', 'university_logo.png')
        logo_exists = os.path.exists(logo_path)
        return {'logo_exists': logo_exists}
    
    # Add this root route
    @app.route('/')
    def root():
        return redirect('/home')  # Redirect to your existing home page
    
    # Make sure your blueprints are registered here
    # The exact import will depend on your project structure
    
    return app