import logging
from flask import render_template, jsonify
from config.supabase_api_manager import supabase_api_manager
from datetime import datetime

logger = logging.getLogger(__name__)


def dashboard_view():
    """
    Main dashboard view. Renders the template with default/empty values.
    All dynamic data is now loaded asynchronously by dashboard.js.
    """
    try:
        template_stats = {
            "enabled_keys": 0,
            "total_keys": 0,
            "selected_key": "Loading...",
            "has_valid_selection": False,
            "system_health": 0.0,
        }

        return render_template(
            "dashboard.html", stats=template_stats, current_time=datetime.now()
        )

    except Exception as e:
        logger.error(f"❌ Error rendering dashboard template: {str(e)}")
        return render_template(
            "dashboard.html",
            stats={"total_keys": 0, "system_health": 0.0},
            error=f"Could not render dashboard template: {e}",
            current_time=datetime.now(),
        )


def api_health_check():
    """API health check endpoint with consolidated logic."""
    try:
        stats = supabase_api_manager.get_stats()
        total_keys = stats.get("total_keys", 0)

        if total_keys == 0:
            return jsonify(
                {
                    "status": "no_keys",
                    "message": "No API keys found in environment. Check Vercel environment variables.",
                    "details": {
                        "total_keys": 0,
                        "enabled_keys": 0,
                        "selected_key": None,
                        "has_valid_selection": False,
                    },
                    "timestamp": datetime.now().isoformat(),
                }
            )

        selected_key = stats.get("selected_key")
        has_valid_selection = stats.get("has_valid_selection", False)

        return jsonify(
            {
                "status": "healthy" if has_valid_selection else "no_selection",
                "message": f"{stats.get('enabled_keys', 0)}/{total_keys} keys enabled. Selected: {selected_key or 'None'}",
                "details": {
                    "total_keys": total_keys,
                    "enabled_keys": stats.get("enabled_keys", 0),
                    "selected_key": selected_key,
                    "has_valid_selection": has_valid_selection,
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Error in health check: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "Failed to retrieve health status.",
                    "details": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


def get_api_stats():
    """Get detailed API statistics directly from the manager."""
    try:
        # Use the detailed stats method
        stats = supabase_api_manager.get_detailed_stats()

        response = {
            "success": True,
            "total_keys": stats.get("total_keys", 0),
            "active_keys": stats.get("enabled_keys", 0),
            "disabled_keys": stats.get("total_keys", 0) - stats.get("enabled_keys", 0),
            "total_requests": stats.get("total_requests", 0),
            "success_rate": stats.get("success_rate", 0.0),
            "last_key_used": stats.get("last_key_used"),
            "key_details": stats.get("key_details", {}),
            "selected_key": stats.get("selected_key"),
            "has_valid_selection": stats.get("has_valid_selection", False),
        }

        if stats.get("total_keys", 0) == 0:
            response["message"] = (
                "No API keys are configured. Please add keys via Settings."
            )

        return jsonify(response)

    except Exception as e:
        logger.error(f"❌ Error getting API stats: {str(e)}")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Failed to retrieve API statistics.",
                    "details": str(e),
                }
            ),
            500,
        )
