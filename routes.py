from flask import render_template, jsonify, session, request
from datetime import datetime
import logging
from functools import wraps
from core.user_context import set_user_context, get_current_user_email, require_user_context
from config.supabase_api_manager import supabase_api_manager
from supabase.client import create_client, Client
from database.supabase_client import supabase_client

try:
    from core.user_context import get_current_user_email

    ENHANCED_USER_CONTEXT = True
except ImportError:
    ENHANCED_USER_CONTEXT = False


# Import route handlers
from api.routes import (
    people_search,
    company_search,
    dashboard,
    people_enrichment,
    company_enrichment,
    settings,
    diagnostics,
    auth,
)

# Check for database availability
try:
    from database.supabase_client import supabase_client

    DATABASE_AVAILABLE = supabase_client and supabase_client.is_available
except:
    DATABASE_AVAILABLE = False

# Check for database config availability
try:
    from config.database_config import db_config

    DATABASE_CONFIG_AVAILABLE = True
except ImportError:
    DATABASE_CONFIG_AVAILABLE = False

PUBLIC_PAGES = [
    'login_page',
    'register_page',
    'forgot_password_page',
    'reset_password_page',
    'health_check'
    ]

def register_routes(app):
    """Register all routes with the Flask app"""

    # --- HTML Page Routes ---
    @app.route("/")
    def index():
        # If user is logged in, show dashboard
        if "user_email" in session:
            return dashboard.dashboard_view()
        # Otherwise show the homepage
        return render_template("homepage.html")
    
    # --- Favicon Route ---
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

    @app.route("/people-search")
    def people_search_page():
        return render_template("people_search.html")

    @app.route("/company-search")
    def company_search_page():
        return render_template("company_search.html")

    @app.route("/people-enrichment")
    def people_enrichment_page():
        return render_template("people_enrichment.html")

    @app.route("/company-enrichment")
    def company_enrichment_page():
        return render_template("company_enrichment.html")

    @app.route("/diagnostics")
    def diagnostics_page():
        return render_template("diagnostics.html")

    @app.route("/settings")
    def settings_page():
        return render_template("settings.html")

    # --- Health Check Routes (both /health and /api/health) ---
    @app.route("/health")
    @app.route("/api/health")
    def health_check():
        """Enhanced health check with database connectivity test"""
        try:
            db_status = "not_configured"
            if DATABASE_AVAILABLE:
                try:
                    response = (
                        supabase_client.client.table("users")
                        .select("count")
                        .limit(1)
                        .execute()
                    )
                    db_status = "connected" if response else "disconnected"
                except Exception as e:
                    db_status = f"error: {str(e)[:100]}"

            return jsonify(
                {
                    "status": "healthy",
                    "environment": app.config.get("ENVIRONMENT", "unknown"),
                    "database": db_status,
                    "database_config_available": DATABASE_CONFIG_AVAILABLE,
                    "enhanced_user_context": ENHANCED_USER_CONTEXT,
                    "supabase_url": (
                        app.config.get("SUPABASE_URL", "")[:50] + "..."
                        if app.config.get("SUPABASE_URL")
                        else "not_configured"
                    ),
                    "max_keys_per_user": app.config.get("MAX_API_KEYS_PER_USER", 100),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    # --- Configuration Info Endpoint ---
    @app.route("/config-info")
    @require_user_context
    def config_info():
        """Get current configuration information (development only)"""
        if app.config.get("ENVIRONMENT") != "development":
            return jsonify({"error": "Not available in production"}), 403

        user_context = "not_available"
        if ENHANCED_USER_CONTEXT:
            try:
                user_context = get_current_user_email()
            except:
                user_context = "error_getting_context"

        return jsonify(
            {
                "environment": app.config.get("ENVIRONMENT"),
                "debug": app.config.get("DEBUG"),
                "database_configured": bool(app.config.get("SUPABASE_URL")),
                "database_config_system": DATABASE_CONFIG_AVAILABLE,
                "max_api_keys": app.config.get("MAX_API_KEYS_PER_USER"),
                "user_context": user_context,
                "session_info": {
                    "has_user_email": bool(session.get("user_email")),
                    "session_permanent": session.permanent,
                },
                "features": {
                    "database_available": DATABASE_AVAILABLE,
                    "enhanced_user_context": ENHANCED_USER_CONTEXT,
                    "database_config_available": DATABASE_CONFIG_AVAILABLE,
                },
            }
        )

    # --- Core API Routes ---
    @app.route("/api/stats", methods=["GET"])
    @require_user_context
    def api_stats():
        return dashboard.get_api_stats()

    @app.route("/api/diagnostics/performance", methods=["GET"])
    @require_user_context
    def api_performance_metrics():
        return diagnostics.get_performance_metrics()

    @app.route("/api/diagnostics/config", methods=["GET"])
    @require_user_context
    def api_diagnostics_config():
        return diagnostics.get_diagnostics_config()

    # --- Surfe Search API Routes ---
    @app.route("/api/v2/people/search", methods=["POST"])
    @require_user_context
    def api_people_search_v2():
        return people_search.search_people_v2()

    @app.route("/api/v2/companies/search", methods=["POST"])
    @require_user_context
    def api_company_search_v2():
        return company_search.search_companies()

    # --- Surfe Enrichment API Routes ---
    @app.route("/api/v2/people/enrich", methods=["POST"])
    @require_user_context
    def api_people_enrich():
        return people_enrichment.enrich_people()

    @app.route("/api/v2/people/enrich/bulk", methods=["POST"])
    @require_user_context
    def api_people_enrich_bulk():
        return people_enrichment.enrich_people_bulk()

    @app.route("/api/v2/people/enrich/status/<enrichment_id>", methods=["GET"])
    @require_user_context
    def api_get_people_enrichment_status(enrichment_id):
        return people_enrichment.get_enrichment_status(enrichment_id)

    @app.route("/api/v2/people/enrich/combinations", methods=["GET"])
    def api_people_enrichment_combinations():
        return people_enrichment.get_enrichment_combinations()

    @app.route("/api/v2/companies/enrich", methods=["POST"])
    @require_user_context
    def api_company_enrich():
        return company_enrichment.enrich_companies()

    @app.route("/api/v2/companies/enrich/bulk", methods=["POST"])
    @require_user_context
    def api_company_enrich_bulk():
        return company_enrichment.enrich_companies_bulk()

    @app.route("/api/v2/companies/enrich/status/<enrichment_id>", methods=["GET"])
    @require_user_context
    def api_get_company_enrichment_status(enrichment_id):
        return company_enrichment.get_enrichment_status(enrichment_id)

    # --- Settings API Routes (Original) ---
    @app.route("/api/settings/config", methods=["GET"])
    @require_user_context
    def api_get_settings_config():
        return settings.get_settings_config()

    @app.route("/api/settings/keys", methods=["POST"])
    @require_user_context
    def api_add_key():
        return settings.add_api_key()

    @app.route("/api/settings/keys", methods=["DELETE"])
    @require_user_context
    def api_remove_key():
        return settings.remove_api_key()

    @app.route("/api/settings/keys/status", methods=["POST"])
    @require_user_context
    def api_update_key_status():
        return settings.update_key_status()

    @app.route("/api/settings/select", methods=["POST"])
    @require_user_context
    def api_select_key():
        return settings.select_api_key()

    @app.route("/api/settings/test", methods=["POST"])
    @require_user_context
    def api_test_key():
        return settings.test_selected_api_key()

    @app.route("/api/settings/refresh", methods=["POST"])
    @require_user_context
    def api_refresh_keys():
        return settings.refresh_api_keys()

    # --- Enhanced Settings Routes (New Database Config System) ---
    # These routes use the new API ID system if available
    if DATABASE_CONFIG_AVAILABLE:

        @app.route("/api/settings/add-api-key", methods=["POST"])
        @require_user_context
        def api_add_api_key_enhanced():
            return settings.add_api_key()

        @app.route("/api/settings/remove-api-key", methods=["POST"])
        @require_user_context
        def api_remove_api_key_enhanced():
            return settings.remove_api_key()

        @app.route("/api/settings/select-api-key", methods=["POST"])
        @require_user_context
        def api_select_api_key_enhanced():
            return settings.select_api_key()

        @app.route("/api/settings/enable-api-key", methods=["POST"])
        @require_user_context
        def api_enable_api_key():
            return settings.enable_api_key()

        @app.route("/api/settings/disable-api-key", methods=["POST"])
        @require_user_context
        def api_disable_api_key():
            return settings.disable_api_key()

        @app.route("/api/settings/test-api-key", methods=["POST"])
        @require_user_context
        def api_test_api_key_enhanced():
            return settings.test_api_key()

        @app.route("/api/settings/list-api-keys", methods=["GET"])
        @require_user_context
        def api_list_api_keys():
            return settings.list_api_keys()

        @app.route("/api/settings/current-user", methods=["GET"])
        @require_user_context
        def api_get_current_user_info():
            return settings.get_current_user_info()

        @app.route("/api/settings/usage-stats", methods=["GET"])
        @require_user_context
        def api_get_usage_stats():
            return settings.get_api_usage_stats()

        @app.route("/auth/login", methods=["GET", "POST"])
        def login_page():
            return auth.login()

        @app.route("/auth/logout", methods=["POST"])
        def logout_page():
            return auth.logout()

        @app.route("/auth/register", methods=["GET", "POST"])
        def register_page():
            return auth.register()

        @app.route("/auth/current-user", methods=["GET"])
        def current_user():
            return auth.get_current_user()

        @app.route("/auth/forgot-password", methods=["GET", "POST"])
        def forgot_password_page():
            if request.method == "GET":
                return render_template("forgot_password.html")
            return auth.request_password_reset()

        @app.route("/auth/reset-password", methods=["GET", "POST"])
        def reset_password_page():
            return auth.reset_password()

        @app.route("/auth/change-password", methods=["POST"])
        @auth.require_auth
        def change_password_page():
            return auth.change_password()


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def not_found_error(error):
        logging.warning(
            f"404 Not Found: The path '{request.path}' was not found on the server."
        )
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"Internal Server Error: {error}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({"error": "Bad request"}), 400
