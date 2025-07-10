import logging
from flask import render_template, jsonify
from utils.simple_api_client import simple_surfe_client
from datetime import datetime

logger = logging.getLogger(__name__)

def dashboard_view():
    """Main dashboard view"""
    try:
        # Get client stats (simplified system)
        client_stats = simple_surfe_client.get_client_stats()
        api_manager_stats = client_stats.get("api_manager_stats", {})
        
        # Flatten the stats for the template
        stats = {
            "active_keys": api_manager_stats.get("enabled_keys", 0),
            "total_keys": api_manager_stats.get("total_keys", 0),
            "disabled_keys": api_manager_stats.get("disabled_keys", 0),
            "system_health": api_manager_stats.get("system_health", 0),
            "selected_key": api_manager_stats.get("selected_key"),
            "has_valid_selection": api_manager_stats.get("has_valid_selection", False)
        }
        
        return render_template('dashboard.html', 
                             stats=stats,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"❌ Error loading dashboard: {str(e)}")
        return render_template('dashboard.html', 
                             stats=None,
                             error=str(e),
                             current_time=datetime.now())

def api_health_check():
    """API health check endpoint"""
    try:
        from config.simple_api_manager import simple_api_manager
        
        stats = simple_api_manager.get_stats()
        
        if stats['total_keys'] == 0:
            return jsonify({
                "status": "no_keys",
                "message": "No API keys found in environment. Check Vercel environment variables.",
                "instructions": "Set SURFE_API_KEY, SURFE_API_KEY_1, etc. in Vercel environment",
                "simple_system": {
                    "total_keys": 0,
                    "enabled_keys": 0,
                    "selected_key": None,
                    "has_valid_selection": False
                },
                "total_requests": 0,
                "timestamp": datetime.now().isoformat()
            })
        
        selected_key = simple_api_manager.get_selected_key()
        
        return jsonify({
            "status": "healthy" if selected_key else "no_selection",
            "message": f"{stats['enabled_keys']}/{stats['total_keys']} API keys enabled, selected: {stats['selected_key'] or 'None'}",
            "simple_system": {
                "total_keys": stats['total_keys'],
                "enabled_keys": stats['enabled_keys'],
                "selected_key": stats['selected_key'],
                "has_valid_selection": stats['has_valid_selection']
            },
            "total_requests": sum(key['usage_count'] for key in stats['keys']),
            "timestamp": datetime.now().isoformat()
        })
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "simple_system": {
                "total_keys": stats["total_keys"],
                "enabled_keys": stats["active_keys"],
                "selected_key": stats.get("selected_key"),
                "has_valid_selection": bool(stats.get("selected_key"))
            },
            "last_key_used": stats["last_key_used"],
            "total_requests": stats["total_requests"]
        })
    except Exception as e:
        logger.error(f"❌ Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
            "instructions": "Check server logs and API key configuration"
        }), 500

def get_api_stats():
    """Get detailed API statistics"""
    try:
        client_stats = simple_surfe_client.get_client_stats()
        api_manager_stats = client_stats.get("api_manager_stats", {})
        
        # Flatten the stats for the dashboard
        stats = {
            "active_keys": api_manager_stats.get("enabled_keys", 0),
            "total_keys": api_manager_stats.get("total_keys", 0),
            "disabled_keys": api_manager_stats.get("disabled_keys", 0),
            "system_health": api_manager_stats.get("system_health", 0),
            "selected_key": api_manager_stats.get("selected_key"),
            "has_valid_selection": api_manager_stats.get("has_valid_selection", False),
            "key_details": {key["name"]: key for key in api_manager_stats.get("keys", [])},
            "last_key_used": api_manager_stats.get("selected_key"),
            "total_requests": 0,  # Simple system doesn't track this yet
            "success": True
        }
        
        if stats["active_keys"] == 0:
            stats["message"] = "No API keys configured. Add keys via Settings page."
            
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Error getting API stats: {str(e)}")
        return jsonify({
            "error": str(e),
            "message": "Failed to retrieve API statistics",
            "instructions": "Check API key configuration"
        }), 500
