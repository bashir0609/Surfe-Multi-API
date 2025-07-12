from dotenv import load_dotenv

load_dotenv()
import os
import logging
from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_cors import CORS
from datetime import timedelta
from config.supabase_api_manager import supabase_api_manager
from utils.email_service import init_mail
# <-- The 'from flask_session import Session' line has been removed.

# --- Database Configuration Integration ---
try:
    from config.database_config import db_config, setup_logging
    setup_logging()
    DATABASE_CONFIG_AVAILABLE = True
    print("✅ Database configuration system loaded")
except ImportError as e:
    print(f"⚠️ Database config import failed: {e}. Using environment variables.")
    DATABASE_CONFIG_AVAILABLE = False
    logging.basicConfig(level=logging.INFO)

# --- Application Imports ---
try:
    from database.supabase_client import supabase_client
    DATABASE_AVAILABLE = bool(supabase_client) and supabase_client.is_available
    print("✅ Supabase client loaded")
except ImportError as e:
    print(f"⚠️ Database client import failed: {e}. Running without database features.")
    DATABASE_AVAILABLE = False
    supabase_client = None

# --- Custom Session Interface Import ---
try:
    from utils.supabase_session_interface import SupabaseSessionInterface
    SESSION_INTERFACE_AVAILABLE = True
    print("✅ Supabase session interface loaded")
except ImportError as e:
    SESSION_INTERFACE_AVAILABLE = False
    print(f"⚠️ Supabase session interface import failed: {e}.")


# --- App Configuration Function ---
def create_app():
    """Create and configure Flask application with integrated database config"""
    app = Flask(__name__)

    # --- VERCEL FIX: SERVER-SIDE SESSION CONFIGURATION ---
    # Use a stable secret key from environment variables
    app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", "a-strong-dev-secret-key")
    
    # Configure session cookie properties directly
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["SESSION_COOKIE_NAME"] = "surfe_session" # Set a specific cookie name
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("APP_ENVIRONMENT") == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Override the session interface with our custom Supabase implementation
    if DATABASE_AVAILABLE and SESSION_INTERFACE_AVAILABLE:
        app.session_interface = SupabaseSessionInterface(supabase_client)
        print("✅ Flask session interface configured for Supabase.")
    else:
        print("⚠️ Could not configure Supabase session interface. Using default Flask session.")
    # --- END VERCEL FIX ---

    if DATABASE_CONFIG_AVAILABLE:
        app_config = db_config.get_app_config()
        supabase_config = db_config.get_supabase_config()
        api_keys_config = db_config.get_api_keys_config()
        app.config.update(
            {
                "DEBUG": app_config["debug"],
                "ENVIRONMENT": app_config["environment"],
                "SUPABASE_URL": supabase_config["url"],
                "MAX_API_KEYS_PER_USER": api_keys_config["max_keys_per_user"],
                "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,
                "JSON_SORT_KEYS": False,
            }
        )
        print(f"✅ Using database configuration - Environment: {app_config['environment']}")
    else:
        app.config.update(
            {
                "DEBUG": os.environ.get("FLASK_ENV") == "development",
                "ENVIRONMENT": os.environ.get("APP_ENVIRONMENT", "development"),
                "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                "MAX_API_KEYS_PER_USER": int(os.environ.get("MAX_API_KEYS_PER_USER", "100")),
            }
        )
        print(f"⚠️ Using environment variables - Environment: {app.config['ENVIRONMENT']}")

    CORS(
        app,
        origins=["http://localhost:3000", "http://localhost:5000"],
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-User-Email", "Authorization"],
    )
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    return app

# --- Create App Instance ---
app = create_app()

# Configure and initialize email
app.config.update(
    {
        "MAIL_SERVER": os.environ.get("MAIL_SERVER", "smtp.gmail.com"),
        "MAIL_PORT": int(os.environ.get("MAIL_PORT", 587)),
        "MAIL_USE_TLS": os.environ.get("MAIL_USE_TLS", "true").lower() == "true",
        "MAIL_USE_SSL": os.environ.get("MAIL_USE_SSL", "false").lower() == "true",
        "MAIL_USERNAME": os.environ.get("MAIL_USERNAME"),
        "MAIL_PASSWORD": os.environ.get("MAIL_PASSWORD"),
        "MAIL_DEFAULT_SENDER": os.environ.get("MAIL_DEFAULT_SENDER"),
    }
)
init_mail(app)

logger = logging.getLogger(__name__)

# --- Register Routes & Error Handlers ---
from routes import register_routes, register_error_handlers
register_routes(app)
register_error_handlers(app)

# The rest of the file remains the same...
# (The original code for sync, initialization, logging, main execution, etc. follows here)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug_mode = app.config.get("DEBUG", False)
    app.run(host="0.0.0.0", port=port, debug=debug_mode, threaded=True)
