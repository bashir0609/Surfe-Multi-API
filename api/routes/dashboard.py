import logging
from flask import render_template, jsonify
from config.simple_api_manager import simple_api_manager
from datetime import datetime

logger = logging.getLogger(__name__)

def dashboard_view():
    """Main dashboard view, pulling stats directly from the API manager."""
    try:
        # Using the direct stats source for consistency.
        stats = simple_api_manager.get_stats()

        # Prepare a clean, safe dictionary for the template.
        template_stats = {
            "enabled_keys": stats.get("enabled_keys", 0),
            "total_keys": stats.get("total_keys", 0),
            "selected_key": stats.get("selected_key"),
            "has_valid_selection": stats.get("has_valid_selection", False)
        }

        return render_template('dashboard.html',
                             stats=template_stats,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"❌ Error loading dashboard: {str(e)}")
        # Provide a default structure for the template on error.
        return render_template('dashboard.html',
                             stats={"total_keys": 0},
                             error=f"Could not load API manager stats: {e}",
                             current_time=datetime.now())

def api_health_check():
    """API health check endpoint with consolidated logic."""
    try:
        stats = simple_api_manager.get_stats()
        total_keys = stats.get("total_keys", 0)

        if total_keys == 0:
            return jsonify({
                "status": "no_keys",
                "message": "No API keys found in environment. Check Vercel environment variables.",
                "details": {
                    "total_keys": 0,
                    "enabled_keys": 0,
                    "selected_key": None,
                    "has_valid_selection": False
                },
                "timestamp": datetime.now().isoformat()
            })

        # Consolidated logic for a healthy response.
        selected_key = stats.get("selected_key")
        has_valid_selection = stats.get("has_valid_selection", False)

        return jsonify({
            "status": "healthy" if has_valid_selection else "no_selection",
            "message": f"{stats.get('enabled_keys', 0)}/{total_keys} keys enabled. Selected: {selected_key or 'None'}",
            "details": {
                "total_keys": total_keys,
                "enabled_keys": stats.get("enabled_keys", 0),
                "selected_key": selected_key,
                "has_valid_selection": has_valid_selection
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"❌ Error in health check: {str(e)}")
        return jsonify({
            "status": "error",
            "error": "Failed to retrieve health status.",
            "details": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def get_api_stats():
    """Get detailed API statistics directly from the manager."""
    try:
        # Use the single source of truth for stats.
        stats = simple_api_manager.get_stats()
        
        # Add a success flag and ensure all keys are safely accessed.
        stats["success"] = True
        stats.setdefault("enabled_keys", 0)
        stats.setdefault("total_keys", 0)
        
        if stats["total_keys"] > 0 and stats["enabled_keys"] == 0:
            stats["message"] = "All API keys are currently disabled."
        elif stats["total_keys"] == 0:
            stats["message"] = "No API keys are configured. Please add keys via environment variables."

        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"❌ Error getting API stats: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to retrieve API statistics.",
            "details": str(e)
        }), 500
