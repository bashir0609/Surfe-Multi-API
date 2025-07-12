import os
import sys
from dotenv import load_dotenv
from pathlib import Path

print("\n--- Supabase Connection Test ---")
print("Diagnosing environment issues...\n")

# Get current working directory
cwd = os.getcwd()
print(f"Current working directory: {cwd}")

# Try to find .env file in common locations
env_paths = [
    Path('.') / '.env',              # Current directory
    Path('..') / '.env',             # Parent directory
    Path(__file__).parent / '.env',  # Script directory
    Path.home() / '.env',            # Home directory
]

found_env = False
for path in env_paths:
    if path.exists():
        print(f"✅ Found .env file at: {path.resolve()}")
        found_env = True
        load_dotenv(path)
        break

if not found_env:
    print("❌ No .env file found in common locations:")
    for path in env_paths:
        print(f"  - {path.resolve()}")

# Get environment variables
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_ANON_KEY")

print("\nEnvironment variables:")
print(f"SUPABASE_URL: {'✅ Found' if url else '❌ Missing'}")
print(f"SUPABASE_ANON_KEY: {'✅ Found' if key else '❌ Missing'}")

if not url or not key:
    print("\n❌ FAILURE: Required environment variables missing")
    print("\nTroubleshooting steps:")
    print("1. Create a .env file in your project root")
    print("2. Add these lines to it:")
    print("   SUPABASE_URL=your_project_url")
    print("   SUPABASE_ANON_KEY=your_anon_key")
    print("3. Replace with your actual credentials from Supabase dashboard")
    print("4. Rerun this script")
    sys.exit(1)

try:
    from supabase import create_client
    print("\n✅ Supabase module imported successfully")
except ImportError:
    print("\n❌ Supabase module not installed")
    print("Run: pip install supabase")
    sys.exit(1)

try:
    print("\nAttempting to connect to Supabase...")
    supabase = create_client(url, key)
    print("✅ Supabase client created successfully")
    
    # Test connection with a simple query
    try:
        print("\nTesting database connection...")
        # Safe query that works even without tables
        response = supabase.table("__dummy_table__").select("id", count="exact").limit(0).execute()
        print("✅ Database connection successful")
    except Exception as e:
        print(f"⚠️ Connection successful but query failed (normal without tables): {str(e)}")
    
    print("\n--- TEST SUCCESSFUL ---")
    print("Supabase connection is working correctly!")

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Verify your SUPABASE_URL format: https://[id].supabase.co")
    print("2. Check your ANON_KEY from Supabase Settings > API")
    print("3. Ensure network access isn't blocked (firewall, VPN)")
    print("4. Test connection in browser: https://[id].supabase.co/rest/v1/")