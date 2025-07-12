from flask import render_template, jsonify, session, request
from datetime import datetime
import logging
from functools import wraps
from core.user_context import set_user_context
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
    "index",
    "login_page",
    "register_page",
    "forgot_password_page",
    "reset_password_page",
    "health_check",
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
    @set_user_context
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
    @set_user_context
    def api_stats():
        return dashboard.get_api_stats()

    @app.route("/api/diagnostics/performance", methods=["GET"])
    @set_user_context
    def api_performance_metrics():
        return diagnostics.get_performance_metrics()

    @app.route("/api/diagnostics/config", methods=["GET"])
    @set_user_context
    def api_diagnostics_config():
        return diagnostics.get_diagnostics_config()

    # --- Surfe Search API Routes ---
    @app.route("/api/v2/people/search", methods=["POST"])
    @set_user_context
    def api_people_search_v2():
        return people_search.search_people_v2()

    @app.route("/api/v2/companies/search", methods=["POST"])
    @set_user_context
    def api_company_search_v2():
        return company_search.search_companies()

    # --- Surfe Enrichment API Routes ---
    @app.route("/api/v2/people/enrich", methods=["POST"])
    @set_user_context
    def api_people_enrich():
        return people_enrichment.enrich_people()

    @app.route("/api/v2/people/enrich/bulk", methods=["POST"])
    @set_user_context
    def api_people_enrich_bulk():
        return people_enrichment.enrich_people_bulk()

    @app.route("/api/v2/people/enrich/status/<enrichment_id>", methods=["GET"])
    @set_user_context
    def api_get_people_enrichment_status(enrichment_id):
        return people_enrichment.get_enrichment_status(enrichment_id)

    @app.route("/api/v2/people/enrich/combinations", methods=["GET"])
    def api_people_enrichment_combinations():
        return people_enrichment.get_enrichment_combinations()

    @app.route("/api/v2/companies/enrich", methods=["POST"])
    @set_user_context
    def api_company_enrich():
        return company_enrichment.enrich_companies()

    @app.route("/api/v2/companies/enrich/bulk", methods=["POST"])
    @set_user_context
    def api_company_enrich_bulk():
        return company_enrichment.enrich_companies_bulk()

    @app.route("/api/v2/companies/enrich/status/<enrichment_id>", methods=["GET"])
    @set_user_context
    def api_get_company_enrichment_status(enrichment_id):
        return company_enrichment.get_enrichment_status(enrichment_id)

    # --- Settings API Routes (Original) ---
    @app.route("/api/settings/config", methods=["GET"])
    @set_user_context
    def api_get_settings_config():
        return settings.get_settings_config()

    @app.route("/api/settings/keys", methods=["POST"])
    @set_user_context
    def api_add_key():
        return settings.add_api_key()

    @app.route("/api/settings/keys", methods=["DELETE"])
    @set_user_context
    def api_remove_key():
        return settings.remove_api_key()

    @app.route("/api/settings/keys/status", methods=["POST"])
    @set_user_context
    def api_update_key_status():
        return settings.update_key_status()

    @app.route("/api/settings/select", methods=["POST"])
    @set_user_context
    def api_select_key():
        return settings.select_api_key()

    @app.route("/api/settings/test", methods=["POST"])
    @set_user_context
    def api_test_key():
        return settings.test_selected_api_key()

    @app.route("/api/settings/refresh", methods=["POST"])
    @set_user_context
    def api_refresh_keys():
        return settings.refresh_api_keys()

    @app.route("/api/debug/check-keys")
    @set_user_context
    def debug_check_keys():
        from core.user_context import get_current_user_email
        from database.supabase_client import supabase_client
        
        user_email = get_current_user_email()
        keys = supabase_client.get_user_api_keys(user_email)
        
        # Get the active key
        active_key = next((k for k in keys if k.get('is_active')), None)
        
        result = {
            "user_email": user_email,
            "total_keys": len(keys),
            "active_key": {
                "id": active_key['id'],
                "name": active_key['key_name'],
                "has_value": bool(active_key.get('api_key')),
                "value_length": len(active_key.get('api_key', '')) if active_key.get('api_key') else 0,
                "starts_with": active_key.get('api_key', '')[:10] + "..." if active_key.get('api_key') else "NO_VALUE"
            } if active_key else None,
            "all_keys": [{
                "id": k['id'],
                "name": k['key_name'],
                "active": k.get('is_active', False),
                "has_value": bool(k.get('api_key')),
                "value_length": len(k.get('api_key', '')) if k.get('api_key') else 0
            } for k in keys]
        }
        
        return jsonify(result)

    @app.route("/api/debug/test-surfe-call")
    @set_user_context
    def debug_test_surfe_call():
        from core.user_context import get_current_user_email
        from database.supabase_client import supabase_client
        from utils.supabase_api_client import supabase_surfe_client
        import aiohttp
        import asyncio
        
        user_email = get_current_user_email()
        
        # Get the active API key directly
        active_key_record = supabase_client.get_active_api_key_info(user_email, 'surfe')
        
        # Also get it through the manager
        from config.supabase_api_manager import supabase_api_manager
        manager_key = supabase_api_manager.get_selected_key(user_email)
        
        # Test making a simple API call
        test_result = None
        try:
            # Make a minimal test request
            result = supabase_surfe_client.make_request(
                method="POST",
                endpoint="/v2/companies/search",
                json_data={"filters": {"industries": ["Software"]}, "limit": 1},
                user_email=user_email
            )
            test_result = {"success": True, "data": result}
        except Exception as e:
            test_result = {"success": False, "error": str(e)}
        
        return jsonify({
            "user_email": user_email,
            "active_key_from_db": {
                "found": bool(active_key_record),
                "id": active_key_record.get('id') if active_key_record else None,
                "name": active_key_record.get('key_name') if active_key_record else None,
                "has_value": bool(active_key_record.get('api_key')) if active_key_record else False,
                "value_preview": active_key_record.get('api_key', '')[:10] + "..." if active_key_record and active_key_record.get('api_key') else None
            },
            "key_from_manager": {
                "found": bool(manager_key),
                "value_preview": manager_key[:10] + "..." if manager_key else None
            },
            "test_api_call": test_result,
            "surfe_base_url": supabase_surfe_client.base_url
        })

    @app.route("/api/debug/raw-surfe-test")
    @set_user_context
    def debug_raw_surfe_test():
        import requests
        from core.user_context import get_current_user_email
        from config.supabase_api_manager import supabase_api_manager
        
        user_email = get_current_user_email()
        api_key = supabase_api_manager.get_selected_key(user_email)
        
        # Test with raw requests library
        url = "https://api.surfe.com/v2/companies/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SurfeMultiAPI/2.0-Debug"
        }
        payload = {
            "filters": {"industries": ["Software"]},
            "limit": 1
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            return jsonify({
                "request_info": {
                    "url": url,
                    "method": "POST",
                    "headers": {k: v if k != "Authorization" else f"Bearer {v[:10]}..." for k, v in headers.items()},
                    "payload": payload
                },
                "response_info": {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text[:500] if response.text else None,
                    "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
                },
                "api_key_info": {
                    "length": len(api_key) if api_key else 0,
                    "preview": f"{api_key[:10]}..." if api_key else None
                }
            })
        except Exception as e:
            return jsonify({
                "error": str(e),
                "type": type(e).__name__
            })
        
    @app.route("/api/debug/check-raw-key")
    @set_user_context
    def debug_check_raw_key():
        from core.user_context import get_current_user_email
        from database.supabase_client import supabase_client
        
        user_email = get_current_user_email()
        
        # Get the active key directly from database
        active_key = supabase_client.get_active_api_key_info(user_email, 'surfe')
        
        if active_key:
            api_key_value = active_key.get('api_key', '')
            return jsonify({
                "user_email": user_email,
                "key_id": active_key['id'],
                "key_name": active_key['key_name'],
                "raw_value_preview": api_key_value[:20] + "...",
                "starts_with_bearer": api_key_value.startswith("Bearer "),
                "value_length": len(api_key_value),
                "first_10_chars": repr(api_key_value[:10])
            })
        else:
            return jsonify({"error": "No active key found"})

    @app.route("/api/debug/test-final")
    @set_user_context
    def debug_test_final():
        from core.user_context import get_current_user_email
        from utils.supabase_api_client import supabase_surfe_client
        
        user_email = get_current_user_email()
        
        try:
            # Test the actual company search using the client
            result = supabase_surfe_client.make_request(
                method="POST",
                endpoint="/v2/companies/search",
                json_data={
                    "filters": {"industries": ["Software"]},
                    "limit": 3
                },
                user_email=user_email
            )
            
            return jsonify({
                "success": True,
                "companies_found": len(result.get('companies', [])),
                "companies": result.get('companies', []),
                "next_page_token": result.get('nextPageToken')
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            })
        
    @app.route("/api/debug/test-direct-api")
    @set_user_context
    def debug_test_direct_api():
        import requests
        from core.user_context import get_current_user_email
        from database.supabase_client import supabase_client
        
        user_email = get_current_user_email()
        
        # Get the active key directly
        active_key = supabase_client.get_active_api_key(user_email, 'surfe')
        
        if not active_key:
            return jsonify({"error": "No active API key found"})
        
        # Make a direct request
        url = "https://api.surfe.com/v2/companies/search"
        headers = {
            "Authorization": f"Bearer {active_key}",
            "Content-Type": "application/json"
        }
        payload = {"filters": {"industries": ["Software"]}, "limit": 1}
        
        response = requests.post(url, json=payload, headers=headers)
        
        return jsonify({
            "api_key_used": {
                "length": len(active_key),
                "preview": f"{active_key[:10]}...",
                "full_auth_header": headers["Authorization"][:30] + "..."
            },
            "response": {
                "status": response.status_code,
                "body": response.json() if response.status_code != 200 else "Success!",
                "headers": dict(response.headers)
            }
        })

    @app.route("/api/debug/verify-api-key")
    @set_user_context
    def debug_verify_api_key():
        import requests
        
        # Use a hardcoded test to isolate the issue
        test_key = "Nqi9CDiiVwnDYLzGBVlLXT2BKR3m_VR7KGNIia_xqKc"  # Your key from the database
        
        url = "https://api.surfe.com/v2/companies/search"
        headers = {
            "Authorization": f"Bearer {test_key}",
            "Content-Type": "application/json"
        }
        payload = {"filters": {"industries": ["Software"]}, "limit": 1}
        
        response = requests.post(url, json=payload, headers=headers)
        
        return jsonify({
            "test_key_used": test_key[:10] + "...",
            "status_code": response.status_code,
            "response": response.json(),
            "conclusion": "API key is VALID" if response.status_code == 200 else "API key is INVALID - you need a new key from Surfe"
        })
        

    # --- Enhanced Settings Routes (New Database Config System) ---
    # These routes use the new API ID system if available
    if DATABASE_CONFIG_AVAILABLE:

        @app.route("/api/settings/add-api-key", methods=["POST"])
        @set_user_context
        def api_add_api_key_enhanced():
            return settings.add_api_key()

        @app.route("/api/settings/remove-api-key", methods=["POST"])
        @set_user_context
        def api_remove_api_key_enhanced():
            return settings.remove_api_key()

        @app.route("/api/settings/select-api-key", methods=["POST"])
        @set_user_context
        def api_select_api_key_enhanced():
            return settings.select_api_key()

        @app.route("/api/settings/enable-api-key", methods=["POST"])
        @set_user_context
        def api_enable_api_key():
            return settings.enable_api_key()

        @app.route("/api/settings/disable-api-key", methods=["POST"])
        @set_user_context
        def api_disable_api_key():
            return settings.disable_api_key()

        @app.route("/api/settings/test-api-key", methods=["POST"])
        @set_user_context
        def api_test_api_key_enhanced():
            return settings.test_api_key()

        @app.route("/api/settings/list-api-keys", methods=["GET"])
        @set_user_context
        def api_list_api_keys():
            return settings.list_api_keys()

        @app.route("/api/settings/current-user", methods=["GET"])
        @set_user_context
        def api_get_current_user_info():
            return settings.get_current_user_info()

        @app.route("/api/settings/usage-stats", methods=["GET"])
        @set_user_context
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
