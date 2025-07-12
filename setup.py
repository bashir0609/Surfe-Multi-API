#!/usr/bin/env python3
# setup.py - Complete setup script for the API key management system

import os
import sys
import subprocess
import json
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                  API Key Management System                   ║
║                   Database Configuration Setup               ║
╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    
    dependencies = [
        "flask",
        "flask-cors", 
        "supabase",
        "python-dotenv",
        "requests",
        "python-dateutil"
    ]
    
    try:
        for dep in dependencies:
            print(f"   Installing {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep], 
                                stdout=subprocess.DEVNULL)
        
        print("✅ All dependencies installed successfully")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_project_structure():
    """Create the project directory structure"""
    print("\n📁 Creating project structure...")
    
    directories = [
        "config",
        "database", 
        "api",
        "api/routes",
        "core",
        "utils",
        "logs",
        "tests"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory in ["config", "database", "api", "api/routes", "core", "utils"]:
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✅ Project structure created")
    return True

def create_env_file():
    """Create .env file with prompts for user input"""
    print("\n🔧 Creating environment configuration...")
    
    env_file = Path(".env")
    
    if env_file.exists():
        response = input("⚠️  .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    print("\nPlease provide your Supabase configuration:")
    print("(You can find these values in your Supabase project dashboard)")
    
    # Get Supabase configuration from user
    supabase_url = input("🌐 Supabase URL (https://your-project-id.supabase.co): ").strip()
    supabase_anon_key = input("🔑 Supabase Anon Key: ").strip()
    supabase_service_key = input("🔐 Supabase Service Role Key (optional): ").strip()
    
    # Get application configuration
    print("\nApplication configuration:")
    app_env = input("🏗️  Environment (development/production) [development]: ").strip() or "development"
    debug_mode = input("🐛 Debug mode (true/false) [true]: ").strip() or "true"
    secret_key = input("🔒 Secret key (leave blank for auto-generation): ").strip()
    
    if not secret_key:
        import secrets
        secret_key = secrets.token_hex(32)
        print(f"   Generated secret key: {secret_key[:20]}...")
    
    # Create .env content
    env_content = f"""# ==============================================
# SUPABASE DATABASE CONFIGURATION
# ==============================================

SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_anon_key}
{f'SUPABASE_SERVICE_ROLE_KEY={supabase_service_key}' if supabase_service_key else '# SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here'}

# ==============================================
# APPLICATION CONFIGURATION
# ==============================================

APP_ENVIRONMENT={app_env}
DEBUG={debug_mode}
SECRET_KEY={secret_key}
API_BASE_URL=http://localhost:5000

# ==============================================
# API KEY MANAGEMENT CONFIGURATION
# ==============================================

MAX_API_KEYS_PER_USER=100
DEFAULT_API_SERVICE=surfe
API_KEY_ROTATION_DAYS=90

# ==============================================
# LOGGING CONFIGURATION
# ==============================================

LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
LOG_FILE=logs/app.log

# ==============================================
# EXTERNAL API CONFIGURATION
# ==============================================

SURFE_API_BASE_URL=https://api.surfe.com
SURFE_API_TIMEOUT=30
SURFE_API_RETRY_ATTEMPTS=3
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print("✅ .env file created successfully")
        return True
    
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def validate_configuration():
    """Validate the configuration"""
    print("\n🧪 Validating configuration...")
    
    try:
        # Import and test configuration
        from config.database_config import validate_environment
        
        if validate_environment():
            print("✅ Configuration is valid!")
            return True
        else:
            print("❌ Configuration validation failed")
            return False
    
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")
        return False

def setup_database_tables():
    """Setup database tables in Supabase"""
    print("\n🗃️  Database table setup...")
    
    sql_script = """
-- SQL script to run in your Supabase SQL editor

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id BIGSERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL REFERENCES users(email) ON DELETE CASCADE,
    service VARCHAR(100) DEFAULT 'surfe',
    api_key TEXT NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    UNIQUE(user_email, key_name)
);

-- Create api_requests table for logging
CREATE TABLE IF NOT EXISTS api_requests (
    id BIGSERIAL PRIMARY KEY,
    user_email VARCHAR(255) NOT NULL,
    service VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255),
    request_data JSONB,
    response_data JSONB,
    status_code INTEGER,
    processing_time FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),
    api_key_id BIGINT REFERENCES api_keys(id) ON DELETE SET NULL
);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_requests ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY users_policy ON users FOR ALL USING (
    email = current_setting('app.current_user_email', true)
    OR current_setting('app.current_user_email', true) = 'system@localhost'
);

CREATE POLICY api_keys_policy ON api_keys FOR ALL USING (
    user_email = current_setting('app.current_user_email', true)
    OR current_setting('app.current_user_email', true) = 'system@localhost'
);

CREATE POLICY api_requests_policy ON api_requests FOR ALL USING (
    user_email = current_setting('app.current_user_email', true)
    OR current_setting('app.current_user_email', true) = 'system@localhost'
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_api_keys_user_email ON api_keys(user_email);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(user_email, is_active);
CREATE INDEX IF NOT EXISTS idx_api_requests_user_email ON api_requests(user_email);
CREATE INDEX IF NOT EXISTS idx_api_requests_timestamp ON api_requests(timestamp);
"""
    
    # Save SQL script to file
    sql_file = Path("setup_database.sql")
    with open(sql_file, 'w') as f:
        f.write(sql_script)
    
    print(f"✅ Database setup script saved to: {sql_file}")
    print("📋 Next steps for database setup:")
    print("   1. Go to your Supabase project dashboard")
    print("   2. Open the SQL Editor")
    print("   3. Copy and run the contents of setup_database.sql")
    print("   4. Verify that all tables and policies are created")
    
    return True

def test_setup():
    """Test the complete setup"""
    print("\n🧪 Testing complete setup...")
    
    try:
        # Test configuration import
        from config.database_config import db_config
        print("✅ Database config imported successfully")
        
        # Test Supabase client
        from database.supabase_client import supabase_client
        print("✅ Supabase client imported successfully")
        
        # Test Flask app creation
        from app import create_app
        app = create_app()
        print("✅ Flask app created successfully")
        
        print("\n🎉 Setup completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure all dependencies are installed")
        print("   2. Check that your .env file has correct values")
        print("   3. Verify Supabase connection details")
        return False

def show_next_steps():
    """Show next steps after setup"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                        SETUP COMPLETE                        ║
╚══════════════════════════════════════════════════════════════╝

🎉 Your API Key Management System is ready!

📋 Next Steps:

1. Database Setup:
   - Run the SQL script in Supabase: setup_database.sql
   - Verify tables are created: users, api_keys, api_requests

2. Start the Application:
   python app.py

3. Test the API:
   curl -X GET http://localhost:5000/health
   curl -X GET http://localhost:5000/config-info

4. Add Your First API Key:
   curl -X POST http://localhost:5000/api/settings/add-api-key \\
        -H "Content-Type: application/json" \\
        -H "X-User-Email: your-email@example.com" \\
        -d '{"api_key": "your-surfe-api-key"}'

📁 Project Structure:
   ├── config/database_config.py    # Database configuration
   ├── database/supabase_client.py  # Supabase client
   ├── api/routes/settings.py       # API endpoints
   ├── core/user_context.py         # User context management
   ├── app.py                       # Flask application
   ├── .env                         # Environment variables
   └── setup_database.sql           # Database setup script

🔗 Useful URLs:
   - Health Check: http://localhost:5000/health
   - Config Info: http://localhost:5000/config-info
   - API Docs: http://localhost:5000/api/settings/

💡 Tips:
   - Use X-User-Email header for API authentication
   - Check logs/app.log for debugging
   - API keys are automatically named: SURFE_API_KEY_1, SURFE_API_KEY_2, etc.

Happy coding! 🚀
    """)

def main():
    """Main setup function"""
    print_banner()
    
    # Check prerequisites
    if not check_python_version():
        return False
    
    # Setup steps
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Creating project structure", create_project_structure), 
        ("Creating environment configuration", create_env_file),
        ("Validating configuration", validate_configuration),
        ("Setting up database scripts", setup_database_tables),
        ("Testing setup", test_setup)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{'='*50}")
        print(f"Step: {step_name}")
        print('='*50)
        
        if not step_func():
            print(f"\n❌ Setup failed at step: {step_name}")
            return False
    
    # Show completion message
    show_next_steps()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)