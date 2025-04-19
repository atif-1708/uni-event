from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Registration  # Added Registration model import
from app.utils.helpers import redirect_to_next_page
from urllib.parse import urlparse
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length, Optional
import os
import secrets
from app.utils.email import send_account_registration_email

auth = Blueprint('auth', __name__)

# Forms
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('admin', 'Admin')], validators=[DataRequired()])
    admin_code = StringField('Admin Registration Code (only for admin registration)', validators=[Optional()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')
    
    def validate_role(self, role):
        if role.data == 'admin':
            admin_code = self.admin_code.data
            if admin_code != '1708':  # You can replace this with logic to check the actual passcode
                raise ValidationError('Invalid admin registration code')


# New Form for Profile Editing
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Full Name', validators=[Optional(), Length(max=100)])
    bio = TextAreaField('Bio', validators=[Optional(), Length(max=500)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    student_id = StringField('Student ID', validators=[Optional(), Length(max=20)])
    profile_image = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    current_password = PasswordField('Current Password (required for password change)')
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', 
                                    validators=[EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Update Profile')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is already registered. Please use a different one.')
    
    def validate_new_password(self, new_password):
        if new_password.data and not self.current_password.data:
            raise ValidationError('Current password is required to set a new password')

# Helper function for saving profile pictures
def save_profile_picture(form_picture):
    # Generate a random hex to use as filename to avoid conflicts
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/profile_pics', picture_fn)
    
    # Save the picture
    form_picture.save(picture_path)
    
    return picture_fn

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                if user.is_admin():
                    next_page = url_for('admin.dashboard')
                else:
                    next_page = url_for('student.dashboard')
            
            return redirect(next_page)
        else:
            flash('Login unsuccessful. Please check email and password.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
     # Send account registration email
        try:
            send_account_registration_email(user)
            flash('Your account has been created! A confirmation email has been sent to your email address.', 'success')
        except Exception as e:
            # Log the error but don't prevent registration
            print(f"Failed to send registration email: {str(e)}")
            flash('Your account has been created! You can now log in.', 'success')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

# New routes for profile
@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', title='My Profile')

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    if form.validate_on_submit():
        # Check if current password is correct for password change
        if form.new_password.data and not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('auth.edit_profile'))
        
        # Update profile info
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.full_name = form.full_name.data
        current_user.bio = form.bio.data
        current_user.department = form.department.data
        current_user.student_id = form.student_id.data
        
        # Handle password change if provided
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
        
        # Handle profile picture upload
        if form.profile_image.data:
            try:
                # Make sure the profile_pics directory exists
                profile_pics_dir = os.path.join(current_app.root_path, 'static/profile_pics')
                if not os.path.exists(profile_pics_dir):
                    os.makedirs(profile_pics_dir)
                
                picture_file = save_profile_picture(form.profile_image.data)
                
                # Delete old profile picture if it exists and isn't the default
                if current_user.profile_image and current_user.profile_image != 'default.jpg':
                    old_picture_path = os.path.join(current_app.root_path, 'static/profile_pics', current_user.profile_image)
                    if os.path.exists(old_picture_path):
                        os.remove(old_picture_path)
                
                current_user.profile_image = picture_file
            except Exception as e:
                flash(f'Error saving profile picture: {str(e)}', 'danger')
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('auth.profile'))
    
    elif request.method == 'GET':
        # Pre-populate form fields with current user data
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.full_name.data = current_user.full_name or ""
        form.bio.data = current_user.bio or ""
        form.department.data = current_user.department or ""
        form.student_id.data = current_user.student_id or ""
    
    return render_template('auth/edit_profile.html', title='Edit Profile', form=form)

@auth.route('/delete_account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        # Check password confirmation for security
        if not current_user.check_password(request.form.get('password')):
            flash('Password is incorrect. Account deletion canceled.', 'danger')
            return redirect(url_for('auth.delete_account'))
        
        # Delete profile image if it exists
        if current_user.profile_image and current_user.profile_image != 'default.jpg':
            try:
                profile_image_path = os.path.join(current_app.root_path, 'static/profile_pics', current_user.profile_image)
                if os.path.exists(profile_image_path):
                    os.remove(profile_image_path)
            except Exception as e:
                # Log the error but continue with user deletion
                print(f"Error removing profile image: {str(e)}")
        
        # Delete all registrations
        registrations = Registration.query.filter_by(user_id=current_user.id).all()
        for registration in registrations:
            db.session.delete(registration)
        
        # Get username for flash message
        username = current_user.username
        
        # Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        # Log the user out
        logout_user()
        
        flash(f'Your account has been permanently deleted. Goodbye, {username}!', 'info')
        return redirect(url_for('main.home'))
    
    return render_template('auth/delete_account.html', title='Delete Account')