import logging
from flask import jsonify
from database.supabase_client import supabase_client
from config.supabase_api_manager import supabase_api_manager
from supabase.client import Client
from typing import Optional

logger = logging.getLogger(__name__)

def get_performance_metrics():
    """
    Endpoint to get performance metrics by calling the database function.
    """
    try:
        if not supabase_client.is_available or not supabase_client: # Added check for _client
            return jsonify({"success": False, "error": "Database not available"}), 503

        response = supabase_client.client.rpc('get_performance_stats', {}).execute()

        if response.data:
            # Assuming the RPC returns a single row with statistics
            stats_data = response.data[0] 
        else:
            stats_data = {}
            logger.warning("RPC function 'get_performance_stats' returned no data.")

        return jsonify({"success": True, "data": stats_data})

    except Exception as e:
        logger.error(f"Error fetching performance metrics: {e}", exc_info=True)
        # Check for a specific "does not exist" error from Postgres
        if "function get_performance_stats() does not exist" in str(e):
             return jsonify({
                 "success": False, 
                 "error": "Database setup incomplete.",
                 "details": "The required RPC function 'get_performance_stats' was not found in the database. Please run the setup SQL."
            }), 501 # 501 Not Implemented
        
        return jsonify({"success": False, "error": f"An internal error occurred: {str(e)}"}), 500
    
def get_diagnostics_config():
    """
    Get configuration for diagnostics page
    """
    try:
        # Get current user context
        from core.user_context import get_current_user_email
        user_email = get_current_user_email()
        
        # Get API stats
        api_stats = supabase_api_manager.get_stats(user_email)
        
        config = {
            "api_configured": api_stats.get('total_keys', 0) > 0,
            "api_selected": api_stats.get('has_valid_selection', False),
            "selected_key": api_stats.get('selected_key'),
            "total_keys": api_stats.get('total_keys', 0),
            "enabled_keys": api_stats.get('enabled_keys', 0),
            "database_available": supabase_client.is_available,
            "user_email": user_email
        }
        
        return jsonify({"success": True, "config": config})
    
    except Exception as e:
        logger.error(f"Error getting diagnostics config: {e}")
        return jsonify({"success": False, "error": str(e)}), 500