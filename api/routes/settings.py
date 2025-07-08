"""
Settings API Routes - Corrected and Enhanced Version
Handles configuration management and API key operations with a focus on
database persistence and clear, user-authenticated logic.
"""
import os
import logging
from flask import request, jsonify
from config.simple_api_manager import api_manager
from utils.simple_api_client import simple_surfe_client
from datetime import datetime

logger = logging.getLogger(__name__)

def get_user_from_request():
    """Extract user email from request headers, form, or query args."""
    return request.headers.get('X-User-Email') or request.form.get('user_email') or request.args.get('user_email')

def add_api_key():
    """Add a new API key to a user's account in the database."""
    try:
        user_email = get_user_from_request()
        if not user_email:
            return jsonify({"success": False, "error": "User email is required to add a key."}), 401

        data = request.get_json()
        if not data or not data.get('api_key'):
            return jsonify({"success": False, "error": "API key is required."}), 400

        api_key = data['api_key'].strip()
        key_name = data.get('key_name', f"My Surfe Key {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        # Test the key's validity before adding it
        test_result = api_manager.test_surfe_key(api_key)
        if not test_result.get('valid'):
            return jsonify({"success": False, "error": f"Invalid API key: {test_result.get('message')}"}), 400

        # Add the key using the API manager
        result = api_manager.add_surfe_key(user_email, api_key, key_name)
        if result and result.get('id'):
            return jsonify({
                "success": True,
                "message": f"API key '{key_name}' was added to your account.",
                "data": {
                    "key_id": result.get('id'),
                    "key_name": result.get('key_name'),
                    "key_suffix": api_key[-4:]
                }
            }), 201
        else:
            return jsonify({"success": False, "error": "Failed to save the key to the database."}), 500

    except Exception as e:
        logger.error(f"Error in add_api_key: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

def remove_api_key():
    """Remove an API key from a user's account."""
    try:
        user_email = get_user_from_request()
        if not user_email:
            return jsonify({"success": False, "error": "User email is required to remove a key."}), 401

        data = request.get_json()
        key_id = data.get('key_id') if data else None
        if not key_id:
            return jsonify({"success": False, "error": "Key ID is required."}), 400

        if api_manager.delete_surfe_key(key_id, user_email):
            return jsonify({
                "success": True,
                "message": "API key removed from your account.",
                "data": {"key_id": key_id}
            })
        else:
            return jsonify({"success": False, "error": "Key not found or could not be removed."}), 404

    except Exception as e:
        logger.error(f"Error in remove_api_key: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

def select_api_key():
    """Select a specific API key for the user to make active."""
    try:
        user_email = get_user_from_request()
        if not user_email:
            return jsonify({"success": False, "error": "User email is required to select a key."}), 401

        data = request.get_json()
        key_id = data.get('key_id') if data else None # This can be an int (user key) or str (system key)
        if not key_id:
            return jsonify({"success": False, "error": "A key ID (for user keys) or system key name is required."}), 400

        # The manager now uses a single argument for selection
        if api_manager.select_api_key(user_email, key_id):
            return jsonify({
                "success": True,
                "message": "API key selection updated.",
                "data": {"selected_key_id": key_id}
            })
        else:
            return jsonify({"success": False, "error": "Failed to select the specified API key."}), 400

    except Exception as e:
        logger.error(f"Error in select_api_key: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

def get_available_keys():
    """Get all available API keys (user's and system-wide)."""
    try:
        user_email = get_user_from_request()
        
        # The manager handles both cases (user or no user) gracefully.
        keys_data = api_manager.get_all_available_keys(user_email)
        
        return jsonify({
            "success": True,
            "data": {
                "keys": keys_data,
                "user_context": bool(user_email)
            }
        })

    except Exception as e:
        logger.error(f"Error in get_available_keys: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

def update_key_status(is_active: bool):
    """Generic function to enable or disable a user's API key."""
    try:
        user_email = get_user_from_request()
        if not user_email:
            return jsonify({"success": False, "error": "User email is required to update a key."}), 401

        data = request.get_json()
        key_id = data.get('key_id') if data else None
        if not key_id:
            return jsonify({"success": False, "error": "Key ID is required."}), 400
        
        action = "Enabled" if is_active else "Disabled"
        
        if api_manager.update_surfe_key(key_id, {'is_active': is_active}):
            return jsonify({
                "success": True,
                "message": f"API key has been {action.lower()}.",
                "data": {"key_id": key_id, "is_active": is_active}
            })
        else:
            return jsonify({"success": False, "error": f"Failed to {action.lower()} key."}), 400

    except Exception as e:
        logger.error(f"Error in update_key_status (is_active={is_active}): {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

def enable_api_key():
    """Enable a specific API key."""
    return update_key_status(is_active=True)

def disable_api_key():
    """Disable a specific API key."""
    return update_key_status(is_active=False)

def test_api_key():
    """Test the currently selected API key for the user."""
    try:
        user_email = get_user_from_request()
        if not user_email:
            return jsonify({"success": False, "error": "User email is required to test a key."}), 401

        api_key = api_manager.get_selected_api_key(user_email)
        if not api_key:
            return jsonify({"success": False, "error": "No active API key is selected for your account."}), 404

        # Using the actual client to make a test request
        result = simple_surfe_client.make_request(
            method="GET",
            endpoint="/health", # A lightweight endpoint is best for testing
            timeout=10
        )
        
        # This assumes a successful request returns a dict-like object
        return jsonify({
            "success": True,
            "message": "API key test was successful.",
            "data": {"test_result": result}
        })

    except Exception as test_error:
        logger.error(f"API key test failed: {test_error}")
        return jsonify({"success": False, "error": "API key test failed.", "details": str(test_error)}), 400

def get_system_config():
    """Get usage stats and configuration for the user."""
    try:
        user_email = get_user_from_request()
        response_data = {
            "has_user_context": bool(user_email),
            "client_config": simple_surfe_client.get_client_stats()
        }

        if user_email:
            response_data["user_stats"] = api_manager.get_usage_stats(user_email)
            response_data["available_keys"] = api_manager.get_all_available_keys(user_email)
        
        return jsonify({
            "success": True,
            "data": response_data
        })

    except Exception as e:
        logger.error(f"Error in get_system_config: {e}")
        return jsonify({"success": False, "error": "An internal error occurred."}), 500
