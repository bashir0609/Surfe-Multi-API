# core/user_context.py - Fixed version

import logging
from functools import wraps
from flask import request, session, g
from typing import Optional

logger = logging.getLogger(__name__)

def get_current_user_email() -> str:
    """
    Get current user email from various sources
    Priority: request header > session > query param > default
    """
    # Try to get from request header (for API calls)
    user_email = request.headers.get('X-User-Email')
    if user_email:
        return user_email.strip()
    
    # Try to get from session (for web interface)
    user_email = session.get('user_email')
    if user_email:
        return user_email.strip()
    
    # Try to get from query parameter
    user_email = request.args.get('user_email')
    if user_email:
        return user_email.strip()
    
    # Try to get from JSON body
    if request.is_json:
        json_data = request.get_json(silent=True) or {}
        if 'user_email' in json_data:
            return json_data['user_email'].strip()
    
    # Default system user for backward compatibility
    return "system@localhost"

def set_user_context(func):
    """
    Decorator to set user context for Supabase RLS (Row Level Security)
    This sets the current_setting('app.current_user_email') that RLS policies use
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Get current user email
            user_email = get_current_user_email()
            
            # Store in Flask's g object for the request
            g.current_user_email = user_email
            
            # Set Supabase context for RLS (if available)
            try:
                # Import here to avoid circular imports
                from database.supabase_client import supabase_client
                
                # Only try to set context if client is available
                if hasattr(supabase_client, 'is_available') and supabase_client.is_available:
                    # Try to set user context using our custom function
                    supabase_client.set_user_context(user_email)
                
            except Exception as context_error:
                logger.debug(f"Could not set Supabase user context: {context_error}")
                # Continue anyway - the decorator shouldn't break the request
            
            logger.debug(f"Set user context: {user_email}")
            
            # Call the original function
            return func(*args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in set_user_context decorator: {e}")
            # Still call the function even if context setting fails
            return func(*args, **kwargs)
    
    return wrapper

def require_user_context(func):
    """
    Decorator that requires a valid user context to be set
    Returns 401 if no valid user is found
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_email = get_current_user_email()
        
        # Don't allow default system user for user-required endpoints
        if user_email == "system@localhost":
            from flask import jsonify
            return jsonify({
                "error": "User authentication required",
                "message": "Please provide user_email in header, session, or request body"
            }), 401
        
        # Validate user exists in database (if database is available)
        try:
            from database.supabase_client import supabase_client
            
            if hasattr(supabase_client, 'is_available') and supabase_client.is_available:
                user_profile = supabase_client.get_user_profile(user_email)
                if not user_profile:
                    # Create user if doesn't exist
                    supabase_client.create_or_update_user(user_email)
        except Exception as e:
            logger.debug(f"Could not validate user in database: {e}")
            # Continue anyway - don't break the request
        
        return set_user_context(func)(*args, **kwargs)
    
    return wrapper

def get_current_user() -> Optional[dict]:
    """Get current user from context"""
    if hasattr(g, 'current_user_email'):
        try:
            from database.supabase_client import supabase_client
            
            if hasattr(supabase_client, 'is_available') and supabase_client.is_available:
                return supabase_client.get_user_profile(g.current_user_email)
        except Exception as e:
            logger.debug(f"Error getting current user: {e}")
    return None

def get_user_context_info() -> dict:
    """Get information about current user context (for debugging)"""
    user_email = get_current_user_email()
    
    context_info = {
        'user_email': user_email,
        'source': 'unknown',
        'is_system_user': user_email == "system@localhost",
        'flask_g_context': hasattr(g, 'current_user_email')
    }
    
    # Determine source
    if request.headers.get('X-User-Email'):
        context_info['source'] = 'header'
    elif session.get('user_email'):
        context_info['source'] = 'session'
    elif request.args.get('user_email'):
        context_info['source'] = 'query_param'
    elif request.is_json:
        json_data = request.get_json(silent=True) or {}
        if 'user_email' in json_data:
            context_info['source'] = 'json_body'
    else:
        context_info['source'] = 'default'
    
    return context_info