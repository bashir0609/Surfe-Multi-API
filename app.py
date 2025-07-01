import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

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

# API Routes
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

@app.route('/api/v1/companies/search', methods=['POST'])
def api_company_search():
    """Company search API endpoint"""
    return company_search.search_companies()

@app.route('/api/v2/companies/enrich', methods=['POST'])
def api_company_enrich():
    """Company enrichment API endpoint"""
    return company_enrichment.enrich_companies()

@app.route('/api/v2/companies/enrich/bulk', methods=['POST'])
def api_company_enrich_bulk():
    """Bulk company enrichment API endpoint"""
    return company_enrichment.enrich_companies_bulk()

@app.route('/api/health', methods=['GET'])
def api_health():
    """API health check with simple system status"""
    return dashboard.api_health_check()

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """API key system statistics"""
    return dashboard.get_api_stats()

# Settings API Routes
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
