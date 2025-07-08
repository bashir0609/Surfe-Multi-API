from dotenv import load_dotenv
load_dotenv()
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Safe database integration imports - won't break if files don't exist
try:
    from database.supabase_client import supabase_client
    from config.simple_api_manager import api_manager
    DATABASE_AVAILABLE = True
    print("✅ Database integration available")
except ImportError as e:
    print(f"ℹ️  Database imports not available: {e}. Running in session-only mode.")
    DATABASE_AVAILABLE = False

import time
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///surfe_api.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created
    import models  # noqa: F401
    db.create_all()

# Import and register routes
from api.routes import people_search, company_search, dashboard, people_enrichment, company_enrichment, settings

# Helper functions for optional database integration
def get_user_from_request():
    """Extract user email from request headers (optional feature)"""
    from flask import request
    return request.headers.get('X-User-Email') or request.form.get('user_email') or request.args.get('user_email')

def log_api_usage(f):
    """Optional decorator to log API usage to database"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not DATABASE_AVAILABLE:
            # Just run the original function if database not available
            return f(*args, **kwargs)
            
        from flask import request
        start_time = time.time()
        user_email = get_user_from_request()
        endpoint = request.endpoint or 'unknown'
        
        try:
            response = f(*args, **kwargs)
            processing_time = time.time() - start_time
            
            # Log successful request only if user email provided
            if user_email:
                try:
                    api_manager.log_surfe_usage(
                        endpoint=endpoint,
                        user_email=user_email,
                        request_data={'method': request.method, 'url': request.url},
                        response_data={'status': 'success'},
                        status_code=200,
                        processing_time=processing_time
                    )
                except Exception as log_error:
                    # Silent logging failure - don't break the main function
                    logger.debug(f"Logging failed: {log_error}")
            
            return response
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            # Log failed request only if user email provided
            if user_email:
                try:
                    api_manager.log_surfe_usage(
                        endpoint=endpoint,
                        user_email=user_email,
                        request_data={'method': request.method, 'url': request.url},
                        response_data={'error': str(e)},
                        status_code=500,
                        processing_time=processing_time
                    )
                except Exception as log_error:
                    # Silent logging failure - don't break the main function
                    logger.debug(f"Error logging failed: {log_error}")
            
            raise e
    
    return decorated_function

@app.before_request
def before_request():
    """Set user context before each request (optional)"""
    if DATABASE_AVAILABLE:
        user_email = get_user_from_request()
        if user_email:
            try:
                api_manager.set_current_user(user_email)
            except Exception as e:
                # Silent failure - don't break requests
                logger.debug(f"User context setting failed: {e}")

@app.route('/')
def index():
    """Main dashboard route"""
    return dashboard.dashboard_view()

@app.route('/people-search')
def people_search_page():
    """People search page"""
    from flask import render_template
    return render_template('people_search.html')

@app.route('/people-search-v2')
def people_search_v2_page():
    """People search page v2 with improved layout"""
    from flask import render_template
    return render_template('people_search_v2.html')

@app.route('/company-search')
def company_search_page():
    """Company search page"""
    from flask import render_template
    return render_template('company_search.html')

@app.route('/company-search-v2')
def company_search_v2_page():
    """Company search page v2 with improved layout"""
    from flask import render_template
    return render_template('company_search_v2.html')

@app.route('/people-enrichment')
def people_enrichment_page():
    """People enrichment page"""
    from flask import render_template
    return render_template('people_enrichment.html')

@app.route('/company-enrichment')
def company_enrichment_page():
    """Company enrichment page"""
    from flask import render_template
    return render_template('company_enrichment.html')

@app.route('/diagnostics')
def diagnostics_page():
    """API diagnostics page"""
    from flask import render_template
    return render_template('diagnostics.html')

@app.route('/settings')
def settings_page():
    """Settings and configuration page"""
    from flask import render_template
    return render_template('settings.html')

# API Routes - UNCHANGED, your existing functionality preserved
@app.route('/api/v2/people/search', methods=['POST'])
def api_people_search_v2():
    """People search API v2 endpoint with simple API management"""
    return people_search.search_people_v2()

@app.route('/api/v1/people/search', methods=['POST'])
def api_people_search_v1():
    """People search API v1 endpoint"""
    return people_search.search_people_v1()

@app.route('/api/v2/people/enrich', methods=['POST'])
def api_people_enrich():
    """People enrichment API endpoint"""
    return people_enrichment.enrich_people()

@app.route('/api/v2/people/enrich/bulk', methods=['POST'])
def api_people_enrich_bulk():
    """Bulk people enrichment API endpoint"""
    return people_enrichment.enrich_people_bulk()


@app.route('/api/v2/people/enrich/status/<enrichment_id>', methods=['GET'])
def api_get_people_enrichment_status(enrichment_id):
    """Check the status of a people enrichment job"""
    return people_enrichment.get_enrichment_status(enrichment_id)

@app.route('/api/v1/companies/search', methods=['POST'])
def api_company_search():
    """Company search API endpoint"""
    return company_search.search_companies()

# ADD THIS NEW ROUTE DEFINITION
@app.route('/api/v2/companies/search', methods=['POST'])
def api_company_search_v2():
    """Company search API v2 endpoint"""
    return company_search.search_companies()

@app.route('/api/v2/companies/enrich', methods=['POST'])
def api_company_enrich():
    """Company enrichment API endpoint"""
    return company_enrichment.enrich_companies()

@app.route('/api/v2/companies/enrich/bulk', methods=['POST'])
def api_company_enrich_bulk():
    """Bulk company enrichment API endpoint"""
    return company_enrichment.enrich_companies_bulk()


@app.route('/api/v2/companies/enrich/status/<enrichment_id>', methods=['GET'])
def api_get_company_enrichment_status(enrichment_id):
    """Check the status of a company enrichment job"""
    return company_enrichment.get_enrichment_status(enrichment_id)

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check with simple system status"""
    return dashboard.api_health_check()

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API key system statistics"""
    return dashboard.get_api_stats()

# Settings API Routes - UNCHANGED, your existing functionality preserved
@app.route('/api/settings/keys', methods=['POST'])
def api_add_key():
    """Add new API key"""
    return settings.add_api_key()

@app.route('/api/settings/keys', methods=['DELETE'])
def api_remove_key():
    """Remove API key"""
    return settings.remove_api_key()

@app.route('/api/settings/keys/enable', methods=['POST'])
def api_enable_key():
    """Enable API key"""
    return settings.enable_api_key()

@app.route('/api/settings/keys/disable', methods=['POST'])
def api_disable_key():
    """Disable API key"""
    return settings.disable_api_key()

@app.route('/api/settings/keys/test', methods=['POST'])
def api_test_key():
    """Test API key"""
    return settings.test_api_key()

@app.route('/api/settings/config', methods=['GET'])
def api_get_config():
    """Get system configuration"""
    return settings.get_system_config()

@app.route('/api/settings/select', methods=['POST'])
def api_select_key():
    """Select API key"""
    return settings.select_api_key()

@app.route('/api/settings/refresh', methods=['POST'])
def api_refresh_keys():
    """Refresh API keys from environment"""
    return settings.refresh_api_keys()

# NEW OPTIONAL ROUTES - Only work if database is available, otherwise return 503
@app.route('/api/settings/keys/available', methods=['GET'])
def api_get_available_keys():
    """Get all available keys for user selection (Database feature)"""
    if DATABASE_AVAILABLE:
        return settings.get_available_keys()
    else:
        from flask import jsonify
        return jsonify({
            "error": "Database not available", 
            "message": "This feature requires database setup. Your existing settings still work!"
        }), 503

@app.route('/api/settings/usage', methods=['GET'])
def api_get_usage_stats():
    """Get usage statistics for user (Database feature)"""
    if DATABASE_AVAILABLE:
        user_email = get_user_from_request()
        if not user_email:
            from flask import jsonify
            return jsonify({
                'error': 'User email required in X-User-Email header',
                'message': 'Add X-User-Email header to enable personal usage tracking'
            }), 400
        
        from flask import request, jsonify
        days = request.args.get('days', 30, type=int)
        
        try:
            stats = api_manager.get_usage_stats(user_email, days)
            return jsonify(stats)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        from flask import jsonify
        return jsonify({
            "error": "Database not available",
            "message": "This feature requires database setup. Your existing settings still work!"
        }), 503

@app.route('/api/user/profile', methods=['POST'])
def api_create_user_profile():
    """Create or update user profile (Database feature)"""
    if DATABASE_AVAILABLE:
        from flask import request, jsonify
        data = request.get_json()
        email = data.get('email')
        name = data.get('name')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        try:
            user = supabase_client.create_or_update_user(email, name)
            return jsonify({'user': user})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        from flask import jsonify
        return jsonify({
            "error": "Database not available",
            "message": "This feature requires database setup. Your existing settings still work!"
        }), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)