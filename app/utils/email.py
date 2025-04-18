from flask import current_app, render_template
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body):
    """Send email wrapper"""
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    # Send asynchronously to avoid blocking the main thread
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_registration_confirmation(user, event):
    """Send event registration confirmation email"""
    send_email(
        subject=f"Registration Confirmation: {event.title}",
        recipients=[user.email],
        text_body=render_template('email/registration_confirmation.txt',
                                 user=user, event=event),
        html_body=render_template('email/registration_confirmation.html',
                                 user=user, event=event)
    )