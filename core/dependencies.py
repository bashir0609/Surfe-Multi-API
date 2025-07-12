import os
import logging
from typing import Optional
from functools import wraps
from flask import request, session, jsonify

# Import the global API manager instance
from config.supabase_api_manager import supabase_api_manager

logger = logging.getLogger(__name__)


def get_api_key() -> str:
    """
    Dependency function to get API key for endpoints.
    In Flask, this is simpler since we handle rotation in the client.
    """
    # Return a placeholder since we handle rotation in the client
    api_key = os.getenv("SURFE_API_KEY", "default_key")
    return api_key


def validate_request_data(data: dict) -> bool:
    """Validate common request data structure"""
    if not isinstance(data, dict):
        return False

    # Basic validation for people search
    has_company_filters = bool(data.get("companies"))
    has_people_filters = bool(data.get("people"))

    return has_company_filters or has_people_filters


# --- NEWLY ADDED DECORATOR ---
def set_user_context_old(f):
    """
    A decorator to extract user ID from session and set it in the API manager.
    Requires authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if 'user_email' not in session:
            return jsonify({"error": "Authentication required"}), 401
        
        user_email = session.get('user_email')
        
        # Set the user context in the singleton API manager instance
        supabase_api_manager.set_current_user(user_email)
        logger.debug(f"User context set to '{user_email}' for endpoint '{f.__name__}'")
        
        # Proceed to execute the original endpoint function
        return f(*args, **kwargs)
    
    return decorated_function