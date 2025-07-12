# config/database_config.py - Database configuration with environment integration

import os
from typing import Dict, Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration manager that integrates with environment variables"""
    
    def __init__(self):
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict:
        """Load database configuration from environment variables"""
        return {
            # Supabase Configuration
            'supabase': {
                'url': os.getenv('SUPABASE_URL'),
                'anon_key': os.getenv('SUPABASE_ANON_KEY'),
                'service_role_key': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),  # Optional, for admin operations
                'jwt_secret': os.getenv('SUPABASE_JWT_SECRET'),  # Optional, for JWT validation
            },
            
            # Application Configuration
            'app': {
                'environment': os.getenv('APP_ENVIRONMENT', 'development'),
                'debug': os.getenv('DEBUG', 'False').lower() == 'true',
                'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key'),
                'api_base_url': os.getenv('API_BASE_URL', 'http://localhost:5000'),
            },
            
            # API Key Management
            'api_keys': {
                'max_keys_per_user': int(os.getenv('MAX_API_KEYS_PER_USER', '100')),
                'default_service': os.getenv('DEFAULT_API_SERVICE', 'surfe'),
                'key_rotation_days': int(os.getenv('API_KEY_ROTATION_DAYS', '90')),
            },
            
            # Logging Configuration
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'format': os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'file': os.getenv('LOG_FILE', 'app.log'),
            },
            
            # Redis Configuration (Optional, for caching/sessions)
            'redis': {
                'url': os.getenv('REDIS_URL'),
                'host': os.getenv('REDIS_HOST', 'localhost'),
                'port': int(os.getenv('REDIS_PORT', '6379')),
                'db': int(os.getenv('REDIS_DB', '0')),
                'password': os.getenv('REDIS_PASSWORD'),
            },
            
            # External API Configuration
            'external_apis': {
                'surfe': {
                    'base_url': os.getenv('SURFE_API_BASE_URL', 'https://api.surfe.com'),
                    'timeout': int(os.getenv('SURFE_API_TIMEOUT', '30')),
                    'retry_attempts': int(os.getenv('SURFE_API_RETRY_ATTEMPTS', '3')),
                },
            },
        }
    
    def _validate_config(self):
        """Validate required configuration values"""
        required_vars = [
            ('SUPABASE_URL', self.config['supabase']['url']),
            ('SUPABASE_ANON_KEY', self.config['supabase']['anon_key']),
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        logger.info("Database configuration validated successfully")
    
    def get_supabase_config(self) -> Dict:
        """Get Supabase-specific configuration"""
        return self.config['supabase']
    
    def get_app_config(self) -> Dict:
        """Get application-specific configuration"""
        return self.config['app']
    
    def get_api_keys_config(self) -> Dict:
        """Get API key management configuration"""
        return self.config['api_keys']
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.config['app']['environment'].lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.config['app']['environment'].lower() == 'development'

# Global configuration instance
db_config = DatabaseConfig()

# Environment Variables Template (.env file)
ENV_TEMPLATE = """
# ==============================================
# SUPABASE DATABASE CONFIGURATION
# ==============================================

# Required: Supabase project configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Optional: JWT configuration for enhanced security
SUPABASE_JWT_SECRET=your-jwt-secret-here

# ==============================================
# APPLICATION CONFIGURATION
# ==============================================

# Application environment (development, staging, production)
APP_ENVIRONMENT=development

# Debug mode (true/false)
DEBUG=true

# Secret key for session management
SECRET_KEY=your-super-secret-key-here

# API base URL
API_BASE_URL=http://localhost:5000

# ==============================================
# API KEY MANAGEMENT CONFIGURATION
# ==============================================

# Maximum API keys per user (1-100)
MAX_API_KEYS_PER_USER=100

# Default service name for API keys
DEFAULT_API_SERVICE=surfe

# API key rotation period in days
API_KEY_ROTATION_DAYS=90

# ==============================================
# LOGGING CONFIGURATION
# ==============================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Log format
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Log file path
LOG_FILE=logs/app.log

# ==============================================
# EXTERNAL API CONFIGURATION
# ==============================================

# Surfe API configuration
SURFE_API_BASE_URL=https://api.surfe.com
SURFE_API_TIMEOUT=30
SURFE_API_RETRY_ATTEMPTS=3

# ==============================================
# OPTIONAL: REDIS CONFIGURATION (for caching)
# ==============================================

# Redis connection (optional)
# REDIS_URL=redis://localhost:6379/0
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=your-redis-password

# ==============================================
# OPTIONAL: ADDITIONAL CONFIGURATIONS
# ==============================================

# Email configuration (for notifications)
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USERNAME=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
# FROM_EMAIL=noreply@yourapp.com

# Webhook configuration (for external integrations)
# WEBHOOK_SECRET=your-webhook-secret
# WEBHOOK_URL=https://yourapp.com/webhooks

# Rate limiting (requests per minute)
# RATE_LIMIT_PER_MINUTE=60
# RATE_LIMIT_BURST=10
"""

def create_env_file():
    """Create a template .env file"""
    env_file_path = '.env'
    
    if os.path.exists(env_file_path):
        print(f"⚠️  .env file already exists at {env_file_path}")
        response = input("Do you want to overwrite it? (y/N): ")
        if response.lower() != 'y':
            print("Aborted. Existing .env file preserved.")
            return False
    
    try:
        with open(env_file_path, 'w') as f:
            f.write(ENV_TEMPLATE)
        
        print(f"✅ Created .env template file at {env_file_path}")
        print("📝 Please edit the file and add your actual configuration values.")
        return True
    
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        return False

def validate_environment():
    """Validate the current environment configuration"""
    try:
        config = DatabaseConfig()
        print("✅ Environment configuration is valid!")
        
        # Print configuration summary
        print("\n📋 Configuration Summary:")
        print(f"   Environment: {config.get_app_config()['environment']}")
        print(f"   Debug Mode: {config.get_app_config()['debug']}")
        print(f"   Supabase URL: {config.get_supabase_config()['url'][:50]}...")
        print(f"   Max Keys per User: {config.get_api_keys_config()['max_keys_per_user']}")
        print(f"   Default Service: {config.get_api_keys_config()['default_service']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Environment configuration error: {e}")
        print("\n💡 To fix this:")
        print("   1. Create a .env file with: python -c 'from config.database_config import create_env_file; create_env_file()'")
        print("   2. Edit the .env file with your actual values")
        print("   3. Run this validation again")
        return False

# Example usage functions
def get_database_connection_string():
    """Get database connection information for debugging"""
    config = db_config.get_supabase_config()
    return f"Supabase URL: {config['url']}, Has Key: {bool(config['anon_key'])}"

def setup_logging():
    log_level = logging.INFO if not DEBUG else logging.DEBUG
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]  # Console only
    )
if __name__ == "__main__":
    print("🔧 Database Configuration Manager")
    print("=" * 50)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("📄 No .env file found.")
        create_env_file()
    else:
        print("📄 .env file found. Validating configuration...")
        if validate_environment():
            print("\n🚀 Your environment is ready to go!")
        else:
            print("\n🔧 Please fix the configuration issues above.")