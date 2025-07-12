from flask import request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from database.supabase_client import supabase_client
import secrets
from datetime import datetime, timedelta
import logging
from utils.email_service import send_password_reset_email, send_welcome_email
from flask import request, jsonify, session, redirect, url_for, render_template, current_app

logger = logging.getLogger(__name__)

def login():
    """Handle user login"""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() or request.form
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    try:
        # Get user from database
        user = supabase_client.get_user_profile(email)
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Check password (you'll need to add password_hash to users table)
        if not check_password_hash(user.get('password_hash', ''), password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Set session
        session['user_email'] = email
        session['user_name'] = user.get('name', email)
        session.permanent = True
        
        # Update last login
        supabase_client.create_or_update_user(email, user.get('name'))
        
        return jsonify({
            "status": "success",
            "user": {
                "email": email,
                "name": user.get('name')
            }
        })
            
        if user:
            # Send welcome email
            send_welcome_email(email, name)

            # Auto-login after registration
            session['user_email'] = email
            session['user_name'] = name
            session.permanent = True
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

def logout():
    """Handle user logout"""
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})

def register():
    """Handle user registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() or request.form
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', email.split('@')[0])
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    try:
        # Check if user exists
        existing_user = supabase_client.get_user_profile(email)
        if existing_user:
            return jsonify({"error": "User already exists"}), 409
        
        # Create user (you'll need to modify create_or_update_user to handle passwords)
        password_hash = generate_password_hash(password)
        
        # For now, just create the user without password
        # You'll need to add password_hash column to users table
        user = supabase_client.create_or_update_user(email, name)
        
        if user:
            # Auto-login after registration
            session['user_email'] = email
            session['user_name'] = name
            session.permanent = True
            
            return jsonify({
                "status": "success",
                "user": {
                    "email": email,
                    "name": name
                }
            })
        
        return jsonify({"error": "Registration failed"}), 500
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

def get_current_user():
    """Get current logged-in user info"""
    if 'user_email' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    return jsonify({
        "email": session.get('user_email'),
        "name": session.get('user_name')
    })

def require_auth(f):
    """Decorator to require authentication"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            if request.is_json:
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    
    return decorated_function

def request_password_reset():
    """Send password reset email"""
    data = request.get_json() or request.form
    email = data.get('email')
    
    logger.info(f"Password reset requested for email: {email}")
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    try:
        # Check if user exists
        logger.info(f"Checking if user exists: {email}")
        user = supabase_client.get_user_profile(email)
        
        if not user:
            logger.info(f"User not found: {email}")
            # Don't reveal if user exists or not
            return jsonify({
                "status": "success",
                "message": "If the email exists, a reset link has been sent"
            })
        
        logger.info(f"User found, generating reset token")
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        logger.info(f"Attempting to store reset token in database")
        
        # Store reset token in database
        stored = supabase_client.set_password_reset_token(email, reset_token, reset_expires)
        
        if stored:
            logger.info(f"Reset token stored successfully")
            
            # Generate reset link
            reset_link = f"http://localhost:5000/auth/reset-password?token={reset_token}&email={email}"
            
            logger.info(f"Reset link generated: {reset_link[:50]}...")
            
            # Always return the link in development for testing
            return jsonify({
                "status": "success",
                "message": "Reset link generated",
                "dev_link": reset_link
            })
        else:
            logger.error("Failed to store reset token in database")
            return jsonify({"error": "Failed to generate reset token"}), 500
            
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

def reset_password():
    """Reset password with token"""
    if request.method == 'GET':
        # Show reset form
        token = request.args.get('token')
        email = request.args.get('email')
        return render_template('reset_password.html', token=token, email=email)
    
    # Handle POST
    data = request.get_json() or request.form
    token = data.get('token')
    email = data.get('email')
    new_password = data.get('password')
    
    if not all([token, email, new_password]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Verify token
        if not supabase_client.verify_reset_token(email, token):
            return jsonify({"error": "Invalid or expired token"}), 400
        
        # Update password
        password_hash = generate_password_hash(new_password)
        
        if supabase_client.update_user_password(email, password_hash):
            return jsonify({
                "status": "success",
                "message": "Password has been reset successfully"
            })
        else:
            return jsonify({"error": "Failed to update password"}), 500
            
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        return jsonify({"error": "Failed to reset password"}), 500

def change_password():
    """Change password for logged-in user"""
    if 'user_email' not in session:
        return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json() or request.form
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not all([current_password, new_password]):
        return jsonify({"error": "Current and new password required"}), 400
    
    try:
        email = session.get('user_email')
        user = supabase_client.get_user_profile(email)
        
        # Verify current password
        if not check_password_hash(user.get('password_hash', ''), current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update password
        password_hash = generate_password_hash(new_password)
        
        # Update in database (you'll need to implement this)
        # supabase_client.update_user_password(email, password_hash)
        
        return jsonify({
            "status": "success",
            "message": "Password changed successfully"
        })
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({"error": "Failed to change password"}), 500