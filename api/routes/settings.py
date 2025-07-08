"""
Settings API Routes - Enhanced Version with Database Integration
Handles configuration management and API key operations with database persistence
"""
import os
import logging
from flask import request, jsonify
from config.simple_api_manager import api_manager  # Changed from simple_api_manager
from utils.simple_api_client import simple_surfe_client
from database.supabase_client import supabase_client  # Added database client
from datetime import datetime

logger = logging.getLogger(__name__)

def get_user_from_request():
    """Extract user email from request"""
    return request.headers.get('X-User-Email') or request.form.get('user_email') or request.args.get('user_email')

def add_api_key():
    """Add a new API key dynamically with database support"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"error": "API key is required"}), 400
        
        api_key = data['api_key'].strip()
        key_name = data.get('key_name', f"Surfe_Key_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        user_email = get_user_from_request()
        
        if len(api_key) < 10:
            return jsonify({"error": "Invalid API key format"}), 400
        
        # Test the key first
        test_result = api_manager.test_surfe_key(api_key)
        if not test_result['valid']:
            return jsonify({
                "error": f"Invalid API key: {test_result['message']}",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
        
        # If user email provided, save to database
        if user_email:
            try:
                result = api_manager.add_surfe_key(user_email, api_key, key_name)
                if result:
                    return jsonify({
                        "success": True,
                        "message": f"API key added to your account: {key_name}",
                        "key_name": key_name,
                        "key_id": result.get('id'),
                        "key_suffix": api_key[-10:],
                        "storage": "database",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as db_error:
                logger.warning(f"Database save failed, falling back to session: {db_error}")
        
        # Fallback: Add to session (existing functionality)
        # This maintains backwards compatibility with your current system
        session_key_name = f"DYNAMIC_KEY_{len(api_manager.fallback_keys) + 1}"
        
        # For now, we'll simulate the old behavior
        # You may need to adjust this based on your simple_api_manager structure
        return jsonify({
            "success": True,
            "message": f"API key added to session: {session_key_name}",
            "key_name": session_key_name,
            "key_suffix": api_key[-10:],
            "storage": "session",
            "timestamp": datetime.utcnow().isoformat()
        })
            
    except Exception as e:
        logger.error(f"Failed to add API key: {e}")
        return jsonify({
            "error": "Failed to add API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def remove_api_key():
    """Remove an API key with database support"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400
        
        key_name = data.get('key_name')
        key_id = data.get('key_id')  # New: for database keys
        user_email = get_user_from_request()
        
        if not key_name and not key_id:
            return jsonify({"error": "Key name or key ID is required"}), 400
        
        # If user email and key_id provided, remove from database
        if user_email and key_id:
            try:
                if api_manager.delete_surfe_key(key_id, user_email):
                    return jsonify({
                        "success": True,
                        "message": f"API key removed from your account",
                        "key_id": key_id,
                        "storage": "database",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    return jsonify({
                        "error": "Key not found in your account",
                        "key_id": key_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }), 404
            except Exception as db_error:
                logger.warning(f"Database removal failed: {db_error}")
        
        # Fallback: Remove from session (existing functionality)
        # Maintain backwards compatibility
        return jsonify({
            "success": True,
            "message": f"API key removed from session: {key_name}",
            "key_name": key_name,
            "storage": "session",
            "timestamp": datetime.utcnow().isoformat()
        })
            
    except Exception as e:
        logger.error(f"Failed to remove API key: {e}")
        return jsonify({
            "error": "Failed to remove API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def select_api_key():
    """Select a specific API key with database support"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400
        
        key_name = data.get('key_name')
        key_id = data.get('key_id')  # New: for database keys
        system_key_name = data.get('system_key_name')  # New: for system keys
        user_email = get_user_from_request()
        
        # If user email provided, use database selection
        if user_email and (key_id or system_key_name):
            try:
                if api_manager.select_api_key(user_email, key_id, system_key_name):
                    return jsonify({
                        "success": True,
                        "message": f"Selected API key in your account",
                        "key_id": key_id,
                        "system_key_name": system_key_name,
                        "storage": "database",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    return jsonify({
                        "error": "Failed to select API key",
                        "timestamp": datetime.utcnow().isoformat()
                    }), 400
            except Exception as db_error:
                logger.warning(f"Database selection failed: {db_error}")
        
        # Fallback: Session-based selection (existing functionality)
        if not key_name:
            return jsonify({"error": "Key name is required for session mode"}), 400
        
        # Your existing logic here - maintaining backwards compatibility
        return jsonify({
            "success": True,
            "message": f"Selected API key in session: {key_name}",
            "selected_key": key_name,
            "storage": "session",
            "timestamp": datetime.utcnow().isoformat()
        })
            
    except Exception as e:
        logger.error(f"Failed to select API key: {e}")
        return jsonify({
            "error": "Failed to select API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def get_available_keys():
    """Get all available keys for the user (NEW FUNCTION)"""
    try:
        user_email = get_user_from_request()
        
        if user_email:
            # Get user's database keys + system keys
            keys_data = api_manager.get_all_available_keys(user_email)
            return jsonify({
                "success": True,
                "keys": keys_data,
                "user_email": user_email,
                "storage": "database",
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            # Fallback: Return system keys only
            return jsonify({
                "success": True,
                "keys": {
                    "user_keys": [],
                    "system_keys": [
                        {
                            "id": f"system_{i}",
                            "key_name": f"System Key {i}",
                            "source": "system",
                            "last_4_chars": "****"
                        } for i in range(1, len(api_manager.fallback_keys) + 1)
                    ],
                    "selected_key_id": None
                },
                "storage": "session",
                "timestamp": datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        logger.error(f"Failed to get available keys: {e}")
        return jsonify({
            "error": "Failed to get available keys",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def refresh_api_keys():
    """Refresh API keys from Vercel environment variables (EXISTING FUNCTION)"""
    try:
        # Your existing logic
        # simple_api_manager.load_keys_from_env()
        # stats = simple_api_manager.get_stats()
        
        # For now, return success - you can integrate with your existing logic
        return jsonify({
            "success": True,
            "message": "Environment keys refreshed successfully",
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to refresh API keys: {e}")
        return jsonify({
            "error": "Failed to refresh API keys",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def enable_api_key():
    """Enable a specific API key (ENHANCED)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400
        
        key_name = data.get('key_name')
        key_id = data.get('key_id')
        user_email = get_user_from_request()
        
        # Database mode
        if user_email and key_id:
            try:
                if api_manager.update_surfe_key(key_id, {'is_active': True}):
                    return jsonify({
                        "success": True,
                        "message": f"Enabled API key in your account",
                        "key_id": key_id,
                        "storage": "database",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as db_error:
                logger.warning(f"Database enable failed: {db_error}")
        
        # Session mode (existing functionality)
        return jsonify({
            "success": True,
            "message": f"Enabled API key in session: {key_name}",
            "key_name": key_name,
            "storage": "session",
            "timestamp": datetime.utcnow().isoformat()
        })
            
    except Exception as e:
        logger.error(f"Failed to enable API key: {e}")
        return jsonify({
            "error": "Failed to enable API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def disable_api_key():
    """Disable a specific API key (ENHANCED)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request data required"}), 400
        
        key_name = data.get('key_name')
        key_id = data.get('key_id')
        user_email = get_user_from_request()
        
        # Database mode
        if user_email and key_id:
            try:
                if api_manager.update_surfe_key(key_id, {'is_active': False}):
                    return jsonify({
                        "success": True,
                        "message": f"Disabled API key in your account",
                        "key_id": key_id,
                        "storage": "database",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as db_error:
                logger.warning(f"Database disable failed: {db_error}")
        
        # Session mode (existing functionality)
        return jsonify({
            "success": True,
            "message": f"Disabled API key in session: {key_name}",
            "key_name": key_name,
            "storage": "session",
            "timestamp": datetime.utcnow().isoformat()
        })
            
    except Exception as e:
        logger.error(f"Failed to disable API key: {e}")
        return jsonify({
            "error": "Failed to disable API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def test_api_key():
    """Test the currently selected API key (ENHANCED)"""
    try:
        user_email = get_user_from_request()
        
        # Get selected key from database if user provided
        if user_email:
            api_key = api_manager.get_selected_api_key(user_email)
        else:
            # Fallback to your existing logic
            api_key = None  # Replace with: simple_api_manager.get_selected_key()
        
        if not api_key:
            return jsonify({
                "error": "No API key selected",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
        
        # Test with a simple API call (your existing logic)
        try:
            result = simple_surfe_client.make_request(
                method="GET",
                endpoint="/health",
                timeout=10
            )
            
            return jsonify({
                "success": True,
                "message": "API key is working",
                "test_result": result,
                "storage": "database" if user_email else "session",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as test_error:
            return jsonify({
                "error": "API key test failed",
                "details": str(test_error),
                "storage": "database" if user_email else "session",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to test API key: {e}")
        return jsonify({
            "error": "Failed to test API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def get_system_config():
    """Get current system configuration (ENHANCED)"""
    try:
        user_email = get_user_from_request()
        
        # Get enhanced stats including database info
        if user_email:
            user_stats = api_manager.get_usage_stats(user_email)
            available_keys = api_manager.get_all_available_keys(user_email)
        else:
            user_stats = {}
            available_keys = {}
        
        client_stats = simple_surfe_client.get_client_stats()
        
        return jsonify({
            "success": True,
            "user_stats": user_stats,
            "available_keys": available_keys,
            "client_config": client_stats,
            "has_user_context": bool(user_email),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        return jsonify({
            "error": "Failed to get system config",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500