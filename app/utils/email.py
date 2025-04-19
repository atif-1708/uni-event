from flask import current_app, render_template
from flask_mail import Message
from app import mail
from threading import Thread
def send_registration_confirmation(user, event):
    """
    Compatibility function for existing code - Sends event registration confirmation
    
    Args:
        user: The user model object
        event: The event model object
    """
    return send_registration_confirmation_email(user, event)
def send_async_email(app, msg):
    """Send email asynchronously to avoid blocking the main thread"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None):
    """Send an email with both plain text and HTML versions"""
    msg = Message(subject, 
                  sender=current_app.config['MAIL_DEFAULT_SENDER'],
                  recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # Send email in a background thread to not block the request
    Thread(target=send_async_email, 
           args=(current_app._get_current_object(), msg)).start()

def send_registration_confirmation_email(user, event):
    """
    Send a confirmation email when a user registers for an event
    
    Args:
        user: The user model object
        event: The event model object
    """
    subject = f"Registration Confirmation: {event.title}"
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/confirmation_registration.txt', 
                               user=user, 
                               event=event)
    html_body = render_template('email/confirmation_registration.html', 
                               user=user, 
                               event=event)
    
    # Send the email
    send_email(subject, recipients, text_body, html_body)

def send_account_registration_email(user):
    """
    Send a welcome email when a user creates a new account
    
    Args:
        user: The user model object
    """
    subject = "Welcome to University Event Management System"
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/account_registration.txt', user=user)
    html_body = render_template('email/account_registration.html', user=user)
    
    # Send the email
    send_email(subject, recipients, text_body, html_body)

def send_event_update_email(users, event, update_message):
    """
    Send an email to notify registered users about event updates
    
    Args:
        users: List of user model objects
        event: The event model object
        update_message: Message explaining the update
    """
    subject = f"Event Update: {event.title}"
    
    for user in users:
        recipients = [user.email]
        
        # Render email templates
        text_body = render_template('email/event_update.txt',
                                  user=user,
                                  event=event,
                                  message=update_message)
        html_body = render_template('email/event_update.html',
                                  user=user,
                                  event=event,
                                  message=update_message)
        
        # Send the email
        send_email(subject, recipients, text_body, html_body)

def send_event_reminder_email(user, event, hours_remaining):
    """
    Send a reminder email before an event starts
    
    Args:
        user: The user model object
        event: The event model object
        hours_remaining: Hours remaining until event starts
    """
    subject = f"Reminder: {event.title} starts in {hours_remaining} hours"
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/event_reminder.txt',
                               user=user,
                               event=event,
                               hours=hours_remaining)
    html_body = render_template('email/event_reminder.html',
                               user=user,
                               event=event,
                               hours=hours_remaining)
    
    # Send the email
    send_email(subject, recipients, text_body, html_body)

def send_registration_cancel_email(user, event):
    """
    Send confirmation when a user cancels event registration
    
    Args:
        user: The user model object
        event: The event model object
    """
    subject = f"Registration Canceled: {event.title}"
    recipients = [user.email]
    
    # Render email templates
    text_body = render_template('email/registration_canceled.txt',
                               user=user,
                               event=event)
    html_body = render_template('email/registration_canceled.html',
                               user=user,
                               event=event)
    
    # Send the email
    send_email(subject, recipients, text_body, html_body)