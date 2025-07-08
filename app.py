from dotenv import load_dotenv
load_dotenv()
import os
import logging
from flask import Flask, request, jsonify, render_template
from werkzeug.middleware.proxy_fix import ProxyFix
import time
from functools import wraps

# --- Supabase Integration Setup ---
# This is now the ONLY database integration.
try:
    from database.supabase_client import supabase_client
    from config.simple_api_manager import api_manager
    DATABASE_AVAILABLE = True
    print("✅ Supabase database integration is available.")
except ImportError as e:
    print(f"⚠️ Supabase imports not available: {e}. Some features will be disabled.")
    DATABASE_AVAILABLE = False
    # Define dummy objects if imports fail so the app doesn't crash
    supabase_client = None
    api_manager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App Initialization ---
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
# Correctly set up app to work behind a proxy (like Vercel)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


# --- Route and API Imports ---
# Assumes these files contain the route logic
from api.routes import people_search, company_search, dashboard, people_enrichment, company_enrichment, settings


# --- Helper Functions & Decorators ---
def get_user_from_request():
    """
    Extracts user email from request headers.
    SECURITY NOTE: This method is for identification, not secure authentication.
    Use JWT or session tokens in a real production environment for security.
    """
    return request.headers.get('X-User-Email') or request.form.get('user_email') or request.args.get('user_email')

def log_api_usage(f):
    """Decorator to log API usage to Supabase if available."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not DATABASE_AVAILABLE:
            return f(*args, **kwargs)

        start_time = time.time()
        user_email = get_user_from_request()
        endpoint = request.endpoint or 'unknown'
        response = None
        status_code = 500
        error_message = ""

        try:
            response = f(*args, **kwargs)
            # Try to get status code from response tuple or response object
            if isinstance(response, tuple):
                status_code = response[1]
            else:
                status_code = response.status_code
            return response
        except Exception as e:
            error_message = str(e)
            # Re-raise the exception so Flask handles it
            raise e
        finally:
            processing_time = time.time() - start_time
            if user_email:
                try:
                    request_data = {'method': request.method, 'url': request.url}
                    response_data = {'error': error_message} if error_message else {'status': 'success'}
                    
                    api_manager.log_surfe_usage(
                        endpoint=endpoint,
                        user_email=user_email,
                        request_data=request_data,
                        response_data=response_data,
                        status_code=status_code,
                        processing_time=processing_time
                    )
                except Exception as log_error:
                    # Logging should never crash the main request
                    logger.debug(f"Failed to log API usage: {log_error}")

    return decorated_function

# --- Request Hooks ---
@app.before_request
def before_request_hook():
    """Set user context from request header before each request."""
    if DATABASE_AVAILABLE:
        user_email = get_user_from_request()
        if user_email and api_manager:
            try:
                api_manager.set_current_user(user_email)
            except Exception as e:
                logger.debug(f"Could not set user context: {e}")


# --- HTML Page Rendering Routes ---
@app.route('/')
def index():
    return dashboard.dashboard_view()

@app.route('/people-search')
def people_search_page():
    return render_template('people_search.html')

@app.route('/company-search')
def company_search_page():
    return render_template('company_search.html')

@app.route('/people-enrichment')
def people_enrichment_page():
    return render_template('people_enrichment.html')

@app.route('/company-enrichment')
def company_enrichment_page():
    return render_template('company_enrichment.html')

@app.route('/diagnostics')
def diagnostics_page():
    return render_template('diagnostics.html')

@app.route('/settings')
def settings_page():
    return render_template('settings.html')


# --- Core API Routes ---
@app.route('/api/v2/people/search', methods=['POST'])
@log_api_usage
def api_people_search_v2():
    return people_search.search_people_v2()

@app.route('/api/v2/people/enrich/bulk', methods=['POST'])
@log_api_usage
def api_people_enrich_bulk():
    return people_enrichment.enrich_people_bulk()

@app.route('/api/v2/companies/search', methods=['POST'])
@log_api_usage
def api_company_search_v2():
    # TODO: This should ideally point to a new v2 function if logic differs from v1
    return company_search.search_companies()

@app.route('/api/v2/companies/enrich/bulk', methods=['POST'])
@log_api_usage
def api_company_enrich_bulk():
    return company_enrichment.enrich_companies_bulk()

@app.route('/api/health', methods=['GET'])
def api_health():
    return dashboard.api_health_check()


# --- Settings API Routes ---
# A single route handles multiple methods for the same resource
@app.route('/api/settings/keys', methods=['POST', 'DELETE'])
@log_api_usage
def manage_api_keys():
    if request.method == 'POST':
        return settings.add_api_key()
    if request.method == 'DELETE':
        return settings.remove_api_key()
    return jsonify({"error": "Method Not Allowed"}), 405

@app.route('/api/settings/keys/status', methods=['POST'])
@log_api_usage
def manage_api_key_status():
    data = request.get_json()
    if data.get('is_active') is True:
        return settings.enable_api_key()
    elif data.get('is_active') is False:
        return settings.disable_api_key()
    return jsonify({"error": "Invalid request, 'is_active' boolean is required."}), 400

@app.route('/api/settings/keys/test', methods=['POST'])
@log_api_usage
def api_test_key():
    return settings.test_api_key()

@app.route('/api/settings/keys/available', methods=['GET'])
def api_get_available_keys():
    if not DATABASE_AVAILABLE:
        return jsonify({"error": "This feature is disabled; database not connected."}), 503
    return settings.get_available_keys()

@app.route('/api/settings/select', methods=['POST'])
@log_api_usage
def api_select_key():
    return settings.select_api_key()

@app.route('/api/settings/config', methods=['GET'])
def api_get_config():
    return settings.get_system_config()


# --- Main Execution ---
if __name__ == '__main__':
    # Use port from environment variable for services like Vercel, default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
