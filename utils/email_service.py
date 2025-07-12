from flask_mail import Mail, Message
from flask import current_app, render_template_string
import logging
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

mail = Mail()

def init_mail(app):
    """Initialize Flask-Mail with app"""
    mail.init_app(app)

def send_email(
    subject: str,
    recipient: str,
    body: str,
    html_body: Optional[str] = None,
    cc: Optional[List[str]] = None,
    bcc: Optional[List[str]] = None
):
    """Send an email"""
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body,
            html=html_body,
            cc=cc,
            bcc=bcc
        )
        
        mail.send(msg)
        logger.info(f"Email sent to {recipient}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        return False

def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email"""
    reset_link = f"{current_app.config.get('APP_URL', 'http://localhost:5000')}/auth/reset-password?token={reset_token}&email={email}"
    
    subject = "Password Reset Request - Surfe Multi API"
    
    # Plain text version
    body = f"""
Hello,

You have requested to reset your password for Surfe Multi API.

Please click the following link to reset your password:
{reset_link}

This link will expire in 1 hour.

If you did not request this password reset, please ignore this email.

Best regards,
Surfe Multi API Team
    """
    
    # HTML version
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #007bff;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .button {{
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            font-size: 0.8em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hello,</p>
            <p>You have requested to reset your password for Surfe Multi API.</p>
            <p>Please click the button below to reset your password:</p>
            <center>
                <a href="{reset_link}" class="button">Reset Password</a>
            </center>
            <p>Or copy and paste this link into your browser:</p>
            <p style="word-break: break-all;">{reset_link}</p>
            <p><strong>This link will expire in 1 hour.</strong></p>
            <p>If you did not request this password reset, please ignore this email.</p>
        </div>
        <div class="footer">
            <p>Best regards,<br>Surfe Multi API Team</p>
        </div>
    </div>
</body>
</html>
    """
    
    return send_email(subject, email, body, html_body)

def send_welcome_email(email: str, name: str):
    """Send welcome email to new user"""
    subject = "Welcome to Surfe Multi API"
    
    body = f"""
Hello {name},

Welcome to Surfe Multi API! Your account has been successfully created.

You can now log in and start using our API services to search and enrich people and company data.

If you have any questions, please don't hesitate to contact us.

Best regards,
Surfe Multi API Team
    """
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background-color: #28a745;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .features {{
            list-style-type: none;
            padding: 0;
        }}
        .features li {{
            padding: 10px 0;
            border-bottom: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to Surfe Multi API!</h1>
        </div>
        <div class="content">
            <p>Hello {name},</p>
            <p>Your account has been successfully created. You now have access to:</p>
            <ul class="features">
                <li>✓ People Search & Enrichment</li>
                <li>✓ Company Search & Enrichment</li>
                <li>✓ Bulk Operations</li>
                <li>✓ API Key Management</li>
                <li>✓ Usage Analytics</li>
            </ul>
            <p>Login to your account to get started!</p>
        </div>
    </div>
</body>
</html>
    """
    
    return send_email(subject, email, body, html_body)

def send_api_key_alert(email: str, key_name: str, action: str):
    """Send alert when API key is added/removed/changed"""
    subject = f"API Key {action} - Surfe Multi API"
    
    body = f"""
Hello,

This is to notify you that an API key has been {action}:

Key Name: {key_name}
Action: {action}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

If you did not perform this action, please contact us immediately.

Best regards,
Surfe Multi API Team
    """
    
    return send_email(subject, email, body)