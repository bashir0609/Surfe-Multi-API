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
        user = supabase_client.get_user_profile(email)
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not check_password_hash(user.get('password_hash', ''), password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        session['user_email'] = email
        session['user_name'] = user.get('name', email)
        
        supabase_client.create_or_update_user(email, user.get('name'))
        
        return jsonify({
            "status": "success",
            "redirect_url": url_for('index'),
            "user": {
                "email": email,
                "name": user.get('name')
            }
        })
    
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
    
    if not all([email, password, name]):
        return jsonify({"error": "Name, email, and password are required"}), 400
    
    try:
        existing_user = supabase_client.get_user_profile(email)
        if existing_user:
            return jsonify({"error": "An account with this email already exists"}), 409
        
        # PERMANENT FIX: Hash the password before storing it.
        password_hash = generate_password_hash(password)
        
        # This assumes your supabase_client function can accept a password_hash.
        # You may need to adjust your Supabase client wrapper if it doesn't.
        user = supabase_client.create_or_update_user(email=email, name=name, password_hash=password_hash)
        
        if user:
            # Auto-login after registration
            session['user_email'] = email
            session['user_name'] = name
            
            return jsonify({
                "status": "success",
                "redirect_url": url_for('index'),
                "user": { "email": email, "name": name }
            })
        
        return jsonify({"error": "Registration failed"}), 500
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

# ... (The rest of the auth.py file remains the same)
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
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    try:
        user = supabase_client.get_user_profile(email)
        
        if not user:
            return jsonify({
                "status": "success",
                "message": "If the email exists, a reset link has been sent"
            })
        
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.utcnow() + timedelta(hours=1)
        
        stored = supabase_client.set_password_reset_token(email, reset_token, reset_expires)
        
        if stored:
            base_url = request.host_url.rstrip('/')
            reset_link = f"{base_url}/auth/reset-password?token={reset_token}&email={email}"
            
            return jsonify({
                "status": "success",
                "message": "Reset link generated",
                "dev_link": reset_link
            })
        else:
            return jsonify({"error": "Failed to generate reset token"}), 500
            
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to process request: {str(e)}"}), 500

def reset_password():
    """Reset password with token"""
    if request.method == 'GET':
        token = request.args.get('token')
        email = request.args.get('email')
        return render_template('reset_password.html', token=token, email=email)
    
    data = request.get_json() or request.form
    token = data.get('token')
    email = data.get('email')
    new_password = data.get('password')
    
    if not all([token, email, new_password]):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        if not supabase_client.verify_reset_token(email, token):
            return jsonify({"error": "Invalid or expired token"}), 400
        
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
        
        if not check_password_hash(user.get('password_hash', ''), current_password):
            return jsonify({"error": "Current password is incorrect"}), 401
        
        password_hash = generate_password_hash(new_password)
        
        supabase_client.update_user_password(email, password_hash)
        
        return jsonify({
            "status": "success",
            "message": "Password changed successfully"
        })
        
    except Exception as e:
        logger.error(f"Password change error: {e}")
        return jsonify({"error": "Failed to change password"}), 500
