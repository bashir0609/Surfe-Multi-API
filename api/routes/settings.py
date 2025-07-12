# api/routes/settings.py - Updated to use API ID as key identifier

"""
Settings API Routes - Supabase Version with API ID as Key Identifier
Handles configuration management and API key operations with Supabase database
Key identifier system: api_id (database id) with naming pattern SURFE_API_KEY_(1-100)
"""
import logging
from flask import request, jsonify, g
from config.supabase_api_manager import supabase_api_manager
from utils.supabase_api_client import supabase_surfe_client
from core.user_context import set_user_context, require_user_context, require_user_context, require_user_context, get_current_user_email, require_user_context
from datetime import datetime
from database.supabase_client import supabase_client

logger = logging.getLogger(__name__)

def generate_key_name(api_id: int) -> str:
    """Generate standardized key name from API ID"""
    return f"SURFE_API_KEY_{api_id}"

@require_user_context
def add_api_key():
    """Add a new API key to Supabase - user email auto-retrieved from context"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"error": "API key is required"}), 400
        
        api_key = data['api_key'].strip()
        # Automatically get user email from current context/session
        user_email = get_current_user_email()
        
        if not user_email or user_email == "system@localhost":
            return jsonify({
                "error": "User authentication required. Please set user email in session or header.",
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        if len(api_key) < 10:
            return jsonify({"error": "Invalid API key format"}), 400
        
        # Add the key to Supabase (let database generate the ID)
        key_obj = supabase_client.add_api_key(
            user_email=user_email,
            service='surfe',
            api_key=api_key,
            key_name=None  # Will be set after we get the ID
        )
        
        if key_obj and 'id' in key_obj:
            api_id = key_obj['id']
            key_name = generate_key_name(api_id)
            
            # Update the key with the proper name
            supabase_client.update_api_key(api_id, {'key_name': key_name})
            
            # Update the API manager
            success = supabase_api_manager.add_api_key(key_name, api_key, user_email)
            
            return jsonify({
                "success": True,
                "message": f"API key added successfully",
                "api_id": api_id,
                "key_name": key_name,
                "key_suffix": api_key[-10:],
                "user_email": user_email,  # Show which user the key was added for
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Failed to create API key in database",
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to add API key: {e}")
        return jsonify({
            "error": "Failed to add API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def remove_api_key():
    """Remove an API key from Supabase using API ID - user email auto-retrieved"""
    try:
        data = request.get_json()
        if not data or 'api_id' not in data:
            return jsonify({"error": "API ID is required"}), 400
        
        api_id = data['api_id']
        # Automatically get user email from current context/session
        user_email = get_current_user_email()
        
        if not user_email or user_email == "system@localhost":
            return jsonify({
                "error": "User authentication required. Please set user email in session or header.",
                "api_id": api_id,
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        # Verify the key exists and belongs to the user
        key_obj = supabase_client.client.table('api_keys').select('*').eq('id', api_id).eq('user_email', user_email).execute()
        
        if not key_obj.data:
            return jsonify({
                "error": "API key not found or access denied",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        key_name = key_obj.data[0]['key_name']
        
        # Remove from database
        success = supabase_client.delete_api_key(api_id, user_email)
        
        if success:
            # Remove from API manager
            supabase_api_manager.remove_api_key(api_id, user_email)
            
            return jsonify({
                "success": True,
                "message": f"API key removed: {key_name}",
                "api_id": api_id,
                "key_name": key_name,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key could not be removed",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to remove API key: {e}")
        return jsonify({
            "error": "Failed to remove API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def refresh_api_keys():
    """Refresh API keys from Supabase database"""
    try:
        user_email = get_current_user_email()
        supabase_api_manager.sync_from_database(user_email)
        stats = supabase_api_manager.get_stats(user_email)
        
        return jsonify({
            "success": True,
            "message": f"Loaded {stats['total_keys']} API keys from Supabase database",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to refresh API keys: {e}")
        return jsonify({
            "error": "Failed to refresh API keys",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def select_api_key():
    """Select a specific API key using API ID - user email auto-retrieved from context"""
    try:
        data = request.get_json()
        if not data or 'api_id' not in data:
            return jsonify({"error": "API ID is required"}), 400
        
        api_id = data['api_id']
        # Automatically get user email from current context/session
        user_email = get_current_user_email()
        
        if not user_email or user_email == "system@localhost":
            return jsonify({
                "error": "User authentication required. Please set user email in session or header.",
                "api_id": api_id,
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        # Verify the key exists and belongs to the current user
        key_obj = supabase_client.client.table('api_keys').select('*').eq('id', api_id).eq('user_email', user_email).execute()
        
        if not key_obj.data:
            return jsonify({
                "error": "API key not found or access denied",
                "api_id": api_id,
                "user_email": user_email,  # Show which user was checked
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        # Set as active key for this user
        success = supabase_client.set_single_active_key(api_id, user_email)
        
        if success:
            key_name = key_obj.data[0]['key_name']
            return jsonify({
                "success": True,
                "message": f"Selected API key: {key_name}",
                "api_id": api_id,
                "key_name": key_name,
                "user_email": user_email,  # Confirm which user the key belongs to
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key could not be selected",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to select API key: {e}")
        return jsonify({
            "error": "Failed to select API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def enable_api_key():
    """Enable a specific API key using API ID - user email auto-retrieved"""
    try:
        data = request.get_json()
        if not data or 'api_id' not in data:
            return jsonify({"error": "API ID is required"}), 400
        
        api_id = data['api_id']
        # Automatically get user email from current context/session
        user_email = get_current_user_email()
        
        if not user_email or user_email == "system@localhost":
            return jsonify({
                "error": "User authentication required. Please set user email in session or header.",
                "api_id": api_id,
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        # Verify the key exists and belongs to the user
        key_obj = supabase_client.client.table('api_keys').select('*').eq('id', api_id).eq('user_email', user_email).execute()
        
        if not key_obj.data:
            return jsonify({
                "error": "API key not found or access denied",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        # Enable the key
        success = supabase_client.update_api_key(api_id, {'is_active': True})
        
        if success:
            key_name = key_obj.data[0]['key_name']
            return jsonify({
                "success": True,
                "message": f"Enabled API key: {key_name}",
                "api_id": api_id,
                "key_name": key_name,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key could not be enabled",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to enable API key: {e}")
        return jsonify({
            "error": "Failed to enable API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def disable_api_key():
    """Disable a specific API key using API ID - user email auto-retrieved"""
    try:
        data = request.get_json()
        if not data or 'api_id' not in data:
            return jsonify({"error": "API ID is required"}), 400
        
        api_id = data['api_id']
        # Automatically get user email from current context/session
        user_email = get_current_user_email()
        
        if not user_email or user_email == "system@localhost":
            return jsonify({
                "error": "User authentication required. Please set user email in session or header.",
                "api_id": api_id,
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        # Verify the key exists and belongs to the user
        key_obj = supabase_client.client.table('api_keys').select('*').eq('id', api_id).eq('user_email', user_email).execute()
        
        if not key_obj.data:
            return jsonify({
                "error": "API key not found or access denied",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
        
        # Disable the key
        success = supabase_client.update_api_key(api_id, {'is_active': False})
        
        if success:
            key_name = key_obj.data[0]['key_name']
            return jsonify({
                "success": True,
                "message": f"Disabled API key: {key_name}",
                "api_id": api_id,
                "key_name": key_name,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key could not be disabled",
                "api_id": api_id,
                "user_email": user_email,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to disable API key: {e}")
        return jsonify({
            "error": "Failed to disable API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def test_api_key():
    """Test the currently selected API key"""
    try:
        user_email = get_current_user_email()
        
        # Get the currently active key
        active_key = supabase_client.get_active_api_key(user_email, 'surfe')
        
        if not active_key:
            return jsonify({
                "error": "No API key selected",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
        
        # Test with a simple API call
        try:
            result = supabase_surfe_client.make_request(
                method="GET",
                endpoint="/health",
                timeout=10,
                user_email=user_email
            )
            
            # Get the current active key info for response
            active_key_obj = supabase_client.client.table('api_keys').select('*').eq('user_email', user_email).eq('is_active', True).execute()
            selected_key_info = None
            if active_key_obj.data:
                key_data = active_key_obj.data[0]
                selected_key_info = {
                    "api_id": key_data['id'],
                    "key_name": key_data['key_name']
                }
            
            return jsonify({
                "success": True,
                "message": "API key is working",
                "selected_key": selected_key_info,
                "test_result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as test_error:
            return jsonify({
                "error": "API key test failed",
                "details": str(test_error),
                "timestamp": datetime.utcnow().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to test API key: {e}")
        return jsonify({
            "error": "Failed to test API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def list_api_keys():
    """List all API keys for the current user with API IDs"""
    try:
        user_email = get_current_user_email()
        
        keys = supabase_client.get_user_api_keys(user_email)
        
        # Format the response with API IDs as primary identifiers
        formatted_keys = []
        for key in keys:
            formatted_keys.append({
                "api_id": key['id'],
                "key_name": key['key_name'],
                "service": key['service'],
                "is_active": key['is_active'],
                "usage_count": key.get('usage_count', 0),
                "created_at": key['created_at'],
                "last_used": key.get('last_used'),
                "key_suffix": key['api_key'][-10:] if key['api_key'] else "unknown"
            })
        
        return jsonify({
            "success": True,
            "keys": formatted_keys,
            "total_keys": len(formatted_keys),
            "active_keys": len([k for k in formatted_keys if k['is_active']]),
            "user_email": user_email,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        return jsonify({
            "error": "Failed to list API keys",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def get_current_user_info():
    """Get current user information and context"""
    try:
        user_email = get_current_user_email()
        
        if not user_email or user_email == "system@localhost":
            return jsonify({
                "error": "No user context found",
                "message": "Please set user email in session, header (X-User-Email), or request body",
                "available_methods": [
                    "Set X-User-Email header",
                    "Include user_email in session",
                    "Add user_email to request body"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }), 401
        
        user_profile = supabase_client.get_user_profile(user_email)
        user_keys = supabase_client.get_user_api_keys(user_email)
        
        # Get active key info
        active_key = None
        for key in user_keys:
            if key.get('is_active'):
                active_key = {
                    "api_id": key['id'],
                    "key_name": key['key_name'],
                    "usage_count": key.get('usage_count', 0),
                    "last_used": key.get('last_used')
                }
                break
        
        return jsonify({
            "success": True,
            "user_email": user_email,
            "user_profile": user_profile,
            "total_keys": len(user_keys),
            "active_key": active_key,
            "context_source": _get_context_source(),
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get current user info: {e}")
        return jsonify({
            "error": "Failed to get current user info",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    
def get_settings_config():
    """Get settings configuration"""
    try:
        
        user_email = get_current_user_email()
        stats = supabase_api_manager.get_stats(user_email)
        
        return jsonify({
            "success": True,  # Changed from "status": "success"
            "data": {
                "api_manager": {  # Added api_manager wrapper
                    "keys": stats.get('keys', []),
                    "selected_key": stats.get('selected_key'),
                    "total_keys": stats.get('total_keys', 0),
                    "enabled_keys": stats.get('enabled_keys', 0),
                    "has_valid_selection": stats.get('has_valid_selection', False),
                    "system_health": stats.get('system_health', 0)
                },
                "user_email": user_email
            }
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def _get_context_source():
    """Helper function to determine where user email came from"""
    if request.headers.get('X-User-Email'):
        return "header"
    elif hasattr(g, 'current_user_email') and g.current_user_email:
        return "session"
    elif request.is_json:
        json_data = request.get_json(silent=True)
        if json_data and 'user_email' in json_data:
            return "request_body"
    elif request.args.get('user_email'):
        return "query_parameter"

    """Get current system configuration from Supabase"""
    try:
        user_email = get_current_user_email()
        stats = supabase_api_manager.get_stats(user_email)
        client_stats = supabase_surfe_client.get_client_stats(user_email)
        
        return jsonify({
            "success": True,
            "api_manager": stats,
            "client_config": client_stats,
            "data_source": "supabase",
            "user_email": user_email,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        return jsonify({
            "error": "Failed to get system config",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@require_user_context
def get_api_usage_stats():
    """Get API usage statistics from Supabase"""
    try:
        user_email = get_current_user_email()
        
        usage_stats = supabase_client.get_user_usage_stats(user_email)
        api_key_stats = supabase_client.get_api_key_stats(user_email)
        
        return jsonify({
            "success": True,
            "usage_stats": usage_stats,
            "api_key_stats": api_key_stats,
            "user_email": user_email,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get usage stats: {e}")
        return jsonify({
            "error": "Failed to get usage stats",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500