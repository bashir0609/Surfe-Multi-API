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

# --- Database Configuration Integration ---
# Try to use the new database config system, fallback to environment variables
try:
    from config.database_config import db_config, setup_logging

    # Setup logging first
    setup_logging()
    DATABASE_CONFIG_AVAILABLE = True
    print("✅ Database configuration system loaded")
except ImportError as e:
    print(f"⚠️ Database config import failed: {e}. Using environment variables.")
    DATABASE_CONFIG_AVAILABLE = False
    logging.basicConfig(level=logging.INFO)

# --- Application Imports ---
# Use a try-except block for graceful failure if database is not configured
try:
    from database.supabase_client import supabase_client

    DATABASE_AVAILABLE = bool(supabase_client) and supabase_client.is_available
    print("✅ Supabase client loaded")
except ImportError as e:
    print(f"⚠️ Database client import failed: {e}. Running without database features.")
    DATABASE_AVAILABLE = False
    supabase_client = None

# Also import the enhanced user context if available
try:
    from core.user_context import get_current_user_email

    ENHANCED_USER_CONTEXT = True
except ImportError:
    ENHANCED_USER_CONTEXT = False
    print("⚠️ Enhanced user context not available, using basic context")


# --- App Configuration Function ---
def create_app():
    """Create and configure Flask application with integrated database config"""

    # Initialize Flask app
    app = Flask(__name__)

    # Configure Flask with database settings or environment variables
    if DATABASE_CONFIG_AVAILABLE:
        # Use database configuration
        app_config = db_config.get_app_config()
        supabase_config = db_config.get_supabase_config()
        api_keys_config = db_config.get_api_keys_config()

        app.config.update(
            {
                "SECRET_KEY": app_config["secret_key"],
                "DEBUG": app_config["debug"],
                "ENVIRONMENT": app_config["environment"],
                "SUPABASE_URL": supabase_config["url"],
                "MAX_API_KEYS_PER_USER": api_keys_config["max_keys_per_user"],
                # Session configuration
                "SESSION_PERMANENT": False,
                "SESSION_USE_SIGNER": True,
                "SESSION_COOKIE_SECURE": app_config["environment"] == "production",
                "SESSION_COOKIE_HTTPONLY": True,
                "SESSION_COOKIE_SAMESITE": "Lax",
                "PERMANENT_SESSION_LIFETIME": timedelta(days=7),
                # API configuration
                "MAX_CONTENT_LENGTH": 16 * 1024 * 1024,  # 16MB max request size
                "JSON_SORT_KEYS": False,
            }
        )

        print(
            f"✅ Using database configuration - Environment: {app_config['environment']}"
        )

    else:
        # Fallback to environment variables
        app.config.update(
            {
                "SECRET_KEY": os.environ.get(
                    "SESSION_SECRET", "dev-secret-key-change-in-production"
                ),
                "DEBUG": os.environ.get("FLASK_ENV") == "development",
                "ENVIRONMENT": os.environ.get("APP_ENVIRONMENT", "development"),
                "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
                "MAX_API_KEYS_PER_USER": int(
                    os.environ.get("MAX_API_KEYS_PER_USER", "100")
                ),
                # Session configuration
                "SESSION_PERMANENT": False,
                "SESSION_USE_SIGNER": True,
                "SESSION_COOKIE_SECURE": os.environ.get("APP_ENVIRONMENT")
                == "production",
                "SESSION_COOKIE_HTTPONLY": True,
                "SESSION_COOKIE_SAMESITE": "Lax",
                "PERMANENT_SESSION_LIFETIME": timedelta(days=7),
            }
        )

        print(
            f"⚠️ Using environment variables - Environment: {app.config['ENVIRONMENT']}"
        )

    # Enable CORS
    CORS(
        app,
        origins=["http://localhost:3000", "http://localhost:5000"],
        supports_credentials=True,
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-User-Email", "Authorization"],
    )

    # Apply proxy fix for deployment
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    return app


# --- Create App Instance ---
app = create_app()

# After app = create_app()
# Configure email
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

# Initialize mail
init_mail(app)

logger = logging.getLogger(__name__)

# --- Register all routes ---
from routes import register_routes, register_error_handlers

register_routes(app)
register_error_handlers(app)

# --- Initial Sync on Startup ---
# This ensures system keys from .env are in the DB when the app starts.
if DATABASE_AVAILABLE:
    try:
        from config.supabase_api_manager import supabase_api_manager

        print("🚀 Performing initial sync of environment keys to database...")
        try:
            with app.app_context():
                result = supabase_api_manager.sync_env_keys_to_db()
                print(f"✅ Synced {result.get('synced', 0)} new environment keys.")
        except Exception as e:
            print(f"❌ Failed to sync environment keys: {e}")
    except ImportError:
        print("⚠️ API manager not available for sync")


# --- Application Initialization ---
# Flask 2.2+ removed before_first_request, so we'll use a different approach
@app.before_request
def initialize_application():
    """Initialize application on first request"""
    # Use a flag to ensure this only runs once
    if not hasattr(app, "_initialized"):
        app._initialized = True
        try:
            logger.info("🚀 Initializing application...")
            logger.info(f"Environment: {app.config.get('ENVIRONMENT')}")
            logger.info(f"Debug mode: {app.config.get('DEBUG')}")
            logger.info(f"Database available: {DATABASE_AVAILABLE}")
            logger.info(f"Database config system: {DATABASE_CONFIG_AVAILABLE}")
            logger.info(f"Enhanced user context: {ENHANCED_USER_CONTEXT}")

            # Test database connection if available
            if DATABASE_AVAILABLE and supabase_client:
                try:
                    supabase_client.client.table("users").select("count").limit(
                        1
                    ).execute()
                    logger.info("✅ Database connection successful")
                except Exception as e:
                    logger.warning(f"⚠️ Database connection test failed: {e}")

        except Exception as e:
            logger.error(f"❌ Application initialization failed: {e}")


# --- Request Logging Middleware ---
@app.before_request
def log_request_info():
    """Log request information in development mode"""
    if app.config.get("DEBUG"):
        user_email = request.headers.get("X-User-Email", "anonymous")
        logger.debug(f"Request: {request.method} {request.path} from {user_email}")


# --- Main Execution ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    # Determine debug mode
    if DATABASE_CONFIG_AVAILABLE:
        debug_mode = app.config.get("DEBUG", False)
    else:
        debug_mode = os.environ.get("FLASK_ENV") == "development"

    print(f"🚀 Starting Flask app on port {port}")
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"💾 Database available: {DATABASE_AVAILABLE}")
    print(f"⚙️ Database config system: {DATABASE_CONFIG_AVAILABLE}")
    print(f"👤 Enhanced user context: {ENHANCED_USER_CONTEXT}")

    # Validate configuration if available
    if DATABASE_CONFIG_AVAILABLE:
        try:
            from config.database_config import validate_environment

            if validate_environment():
                print("✅ Environment configuration validated")
            else:
                print("⚠️ Environment validation warnings (check logs)")
        except Exception as e:
            print(f"⚠️ Configuration validation error: {e}")

    app.run(host="0.0.0.0", port=port, debug=debug_mode, threaded=True)


# --- Production Configuration ---
def create_production_app():
    """Create app for production deployment"""
    app = create_app()

    # Production-specific configuration
    if app.config.get("ENVIRONMENT") == "production":
        app.config["DEBUG"] = False

        # Enable security headers
        @app.after_request
        def add_security_headers(response):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
            return response

    return app


# --- Configuration Testing ---
def test_configuration():
    """Test the complete configuration"""
    import sys

    print("🧪 Testing integrated configuration...")

    try:
        # Test basic app creation
        test_app = create_app()
        print("✅ Flask app created successfully")

        # Test database config if available
        if DATABASE_CONFIG_AVAILABLE:
            config = db_config.get_supabase_config()
            print(f"✅ Database config: {config['url'][:50]}...")

        # Test database client if available
        if DATABASE_AVAILABLE:
            print("✅ Database client available")

        print("✅ Configuration test passed")
        return True

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


# Configuration check
if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "test":
    import sys

    test_configuration()
