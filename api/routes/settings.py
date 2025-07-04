"""
Settings API Routes - Simplified Version
Handles configuration management and API key operations with simple selection
"""
import os
import logging
from flask import request, jsonify
from config.simple_api_manager import simple_api_manager
from utils.simple_api_client import simple_surfe_client
from datetime import datetime

logger = logging.getLogger(__name__)

def add_api_key():
    """Add a new API key dynamically"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"error": "API key is required"}), 400
        
        api_key = data['api_key'].strip()
        key_name = data.get('key_name', f"DYNAMIC_KEY_{len(simple_api_manager.dynamic_keys) + 1}")
        
        if len(api_key) < 10:
            return jsonify({"error": "Invalid API key format"}), 400
        
        # Add the key
        if simple_api_manager.add_dynamic_key(key_name, api_key):
            return jsonify({
                "success": True,
                "message": f"API key added successfully: {key_name}",
                "key_name": key_name,
                "key_suffix": api_key[-10:],
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key already exists or could not be added",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            }), 400
            
    except Exception as e:
        logger.error(f"Failed to add API key: {e}")
        return jsonify({
            "error": "Failed to add API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def remove_api_key():
    """Remove a dynamically added API key"""
    try:
        data = request.get_json()
        if not data or 'key_name' not in data:
            return jsonify({"error": "Key name is required"}), 400
        
        key_name = data['key_name']
        
        if simple_api_manager.remove_dynamic_key(key_name):
            return jsonify({
                "success": True,
                "message": f"API key removed: {key_name}",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key not found or could not be removed",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to remove API key: {e}")
        return jsonify({
            "error": "Failed to remove API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def refresh_api_keys():
    """Refresh API keys from Vercel environment variables"""
    try:
        simple_api_manager.load_keys_from_env()
        stats = simple_api_manager.get_stats()
        
        return jsonify({
            "success": True,
            "message": f"Loaded {stats['total_keys']} API keys from environment",
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

def select_api_key():
    """Select a specific API key"""
    try:
        data = request.get_json()
        if not data or 'key_name' not in data:
            return jsonify({"error": "Key name is required"}), 400
        
        key_name = data['key_name']
        
        if simple_api_manager.select_key(key_name):
            return jsonify({
                "success": True,
                "message": f"Selected API key: {key_name}",
                "selected_key": key_name,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key not found or disabled",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to select API key: {e}")
        return jsonify({
            "error": "Failed to select API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def enable_api_key():
    """Enable a specific API key"""
    try:
        data = request.get_json()
        if not data or 'key_name' not in data:
            return jsonify({"error": "Key name is required"}), 400
        
        key_name = data['key_name']
        
        if simple_api_manager.enable_key(key_name):
            return jsonify({
                "success": True,
                "message": f"Enabled API key: {key_name}",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key not found",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to enable API key: {e}")
        return jsonify({
            "error": "Failed to enable API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def disable_api_key():
    """Disable a specific API key"""
    try:
        data = request.get_json()
        if not data or 'key_name' not in data:
            return jsonify({"error": "Key name is required"}), 400
        
        key_name = data['key_name']
        
        if simple_api_manager.disable_key(key_name):
            return jsonify({
                "success": True,
                "message": f"Disabled API key: {key_name}",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                "error": "Key not found",
                "key_name": key_name,
                "timestamp": datetime.utcnow().isoformat()
            }), 404
            
    except Exception as e:
        logger.error(f"Failed to disable API key: {e}")
        return jsonify({
            "error": "Failed to disable API key",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

def test_api_key():
    """Test the currently selected API key"""
    try:
        api_key = simple_api_manager.get_selected_key()
        if not api_key:
            return jsonify({
                "error": "No API key selected",
                "timestamp": datetime.utcnow().isoformat()
            }), 400
        
        # Test with a simple API call
        try:
            result = simple_surfe_client.make_request(
                method="GET",
                endpoint="/health",
                timeout=10
            )
            
            return jsonify({
                "success": True,
                "message": "API key is working",
                "selected_key": simple_api_manager.selected_key,
                "test_result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except Exception as test_error:
            return jsonify({
                "error": "API key test failed",
                "details": str(test_error),
                "selected_key": simple_api_manager.selected_key,
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
    """Get current system configuration"""
    try:
        stats = simple_api_manager.get_stats()
        client_stats = simple_surfe_client.get_client_stats()
        
        return jsonify({
            "success": True,
            "api_manager": stats,
            "client_config": client_stats,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to get system config: {e}")
        return jsonify({
            "error": "Failed to get system config",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500