# test_api_keys.py - Comprehensive debugging for API key system

import os
import sys
from dotenv import load_dotenv
from config.supabase_api_manager import supabase_api_manager

# Load environment variables
load_dotenv()

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from database.supabase_client import supabase_client
    from config.supabase_api_manager import supabase_api_manager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_environment_variables():
    """Test environment variable loading"""
    print_section("ENVIRONMENT VARIABLES TEST")

    # Check Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Missing'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY: {'✅ Set' if supabase_key else '❌ Missing'}")

    if supabase_url:
        print(f"  URL: {supabase_url}")

    # Check SURFE API keys
    surfe_keys = {}
    for i in range(1, 10):
        key = os.getenv(f"SURFE_API_KEY_{i}")
        if key:
            surfe_keys[f"SURFE_API_KEY_{i}"] = f"...{key[-4:]}"

    single_key = os.getenv("SURFE_API_KEY")
    if single_key:
        surfe_keys["SURFE_API_KEY"] = f"...{single_key[-4:]}"

    print(f"\nSURFE API Keys found: {len(surfe_keys)}")
    for key_name, key_suffix in surfe_keys.items():
        print(f"  {key_name}: {key_suffix}")

    return len(surfe_keys) > 0


def test_database_connection():
    """Test database connection and basic operations"""
    print_section("DATABASE CONNECTION TEST")

    print(
        f"Supabase client available: {'✅ Yes' if supabase_client.is_available else '❌ No'}"
    )

    if not supabase_client.is_available:
        print("❌ Cannot proceed with database tests - connection failed")
        return False

    try:
        # Test basic query
        system_keys = supabase_client.get_system_keys()
        user_keys = supabase_client.get_user_api_keys("default-user-id")

        print(f"✅ Database queries successful")
        print(f"  System keys found: {len(system_keys)}")
        print(f"  User keys found: {len(user_keys)}")

        return True
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return False


def test_database_records():
    """Examine database records in detail"""
    print_section("DATABASE RECORDS INSPECTION")

    if not supabase_client.is_available:
        print("❌ Database not available")
        return

    try:
        # Get all system keys
        system_keys = supabase_client.get_system_keys()
        print(f"System keys in database: {len(system_keys)}")

        for i, key in enumerate(system_keys, 1):
            print(f"\n  System Key #{i}:")
            print(f"    ID: {key.get('id')}")
            print(f"    Name: {key.get('name')}")
            print(f"    User ID: {key.get('user_id')}")
            print(f"    Enabled: {key.get('enabled')}")
            print(f"    Is Selected: {key.get('is_selected')}")
            print(f"    Is System Key: {key.get('is_system_key')}")
            print(f"    Key Value: ...{key.get('key_value', '')[-4:]}")
            print(f"    All Fields: {list(key.keys())}")

        # Get user keys
        user_keys = supabase_client.get_user_api_keys("default-user-id")
        print(f"\nUser keys in database: {len(user_keys)}")

        for i, key in enumerate(user_keys, 1):
            print(f"\n  User Key #{i}:")
            print(f"    ID: {key.get('id')}")
            print(f"    Name: {key.get('name')}")
            print(f"    User ID: {key.get('user_id')}")
            print(f"    Enabled: {key.get('enabled')}")
            print(f"    Is Selected: {key.get('is_selected')}")
            print(f"    Is System Key: {key.get('is_system_key')}")
            print(f"    All Fields: {list(key.keys())}")

    except Exception as e:
        print(f"❌ Error inspecting database records: {e}")


def test_api_manager():
    """Test API manager functionality"""
    print_section("API MANAGER TEST")

    try:
        # Set user context
        supabase_api_manager.set_current_user("default-user-id")
        print("✅ User context set")

        # Test environment key loading
        fallback_keys = supabase_api_manager.fallback_keys
        print(f"✅ Fallback keys loaded: {len(fallback_keys)}")
        for key_name, key_value in fallback_keys.items():
            print(f"  {key_name}: ...{key_value[-4:]}")

        # Test stats
        print("\n--- Testing get_stats() ---")
        stats = supabase_api_manager.get_stats()
        if "error" in stats:
            print(f"❌ Stats error: {stats['error']}")
        else:
            print("✅ Stats generated successfully:")
            for key, value in stats.items():
                print(f"  {key}: {value}")

        # Test get_all_available_keys
        print("\n--- Testing get_all_available_keys() ---")
        keys_data = supabase_api_manager.get_all_available_keys("default-user-id")
        print("✅ Available keys retrieved:")
        print(f"  User keys: {len(keys_data.get('user_keys', []))}")
        print(f"  System keys: {len(keys_data.get('system_keys', []))}")
        print(f"  Selected key ID: {keys_data.get('selected_key_id')}")

        # Show system keys detail
        for key in keys_data.get("system_keys", []):
            print(f"\n  System Key Details:")
            print(f"    ID: {key.get('id')}")
            print(f"    Name: {key.get('key_name')}")
            print(f"    Active: {key.get('is_active')}")
            print(f"    Source: {key.get('source')}")
            print(f"    Last 4: {key.get('last_4_chars')}")

        # Test selected key retrieval
        print("\n--- Testing get_selected_api_key() ---")
        selected_key = supabase_api_manager.get_selected_api_key()
        if selected_key:
            print(f"✅ Selected key: ...{selected_key[-4:]}")
        else:
            print("ℹ️ No key selected")

    except Exception as e:
        print(f"❌ API Manager test failed: {e}")
        import traceback

        traceback.print_exc()


def test_sync_operation():
    """Test syncing environment keys to database"""
    print_section("SYNC OPERATION TEST")

    try:
        print("Testing sync_env_keys_to_db()...")
        result = supabase_api_manager.sync_env_keys_to_db()

        if "error" in result:
            print(f"❌ Sync failed: {result['error']}")
        else:
            print("✅ Sync completed:")
            print(f"  Synced: {result.get('synced', 0)} new keys")
            print(f"  Total env keys: {result.get('total_env_keys', 0)}")

        # Check database after sync
        print("\n--- Database state after sync ---")
        system_keys = supabase_client.get_system_keys()
        print(f"System keys in database: {len(system_keys)}")
        for key in system_keys:
            print(
                f"  {key.get('name')}: enabled={key.get('enabled')}, selected={key.get('is_selected')}"
            )

    except Exception as e:
        print(f"❌ Sync test failed: {e}")
        import traceback

        traceback.print_exc()


def test_key_operations():
    """Test key selection and update operations"""
    print_section("KEY OPERATIONS TEST")

    try:
        # Get available keys first
        keys_data = supabase_api_manager.get_all_available_keys("default-user-id")
        system_keys = keys_data.get("system_keys", [])

        if not system_keys:
            print("❌ No system keys available for testing")
            return

        test_key = system_keys[0]
        key_id = test_key.get("id")

        print(f"Testing with key: {test_key.get('key_name')} (ID: {key_id})")

        # Test enable/disable
        print("\n--- Testing enable operation ---")
        result = supabase_api_manager.update_surfe_key(key_id, {"enabled": True})
        if result:
            print("✅ Enable operation successful")
        else:
            print("❌ Enable operation failed")

        # Test selection
        print("\n--- Testing select operation ---")
        result = supabase_api_manager.select_api_key("default-user-id", key_id)
        if result:
            print("✅ Select operation successful")
        else:
            print("❌ Select operation failed")

        # Check final state
        print("\n--- Final state check ---")
        stats = supabase_api_manager.get_stats()
        print(f"Has valid selection: {stats.get('has_valid_selection')}")
        print(f"Selected key: {stats.get('selected_key')}")
        print(f"Enabled keys: {stats.get('enabled_keys')}")

    except Exception as e:
        print(f"❌ Key operations test failed: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all tests"""
    print("🧪 API KEY SYSTEM DEBUG TEST")
    print("This test will examine your entire API key setup")

    # Run tests in order
    env_ok = test_environment_variables()
    db_ok = test_database_connection()

    if not env_ok:
        print("\n❌ Environment variables missing - cannot continue")
        return

    if not db_ok:
        print("\n❌ Database connection failed - cannot continue")
        return

    # Run detailed tests
    test_database_records()
    test_api_manager()
    test_sync_operation()
    test_key_operations()

    print_section("TEST SUMMARY")
    print("✅ All tests completed!")
    print("Check the output above for any ❌ errors that need fixing.")
    print("\nIf all tests pass, your settings page should work correctly.")


if __name__ == "__main__":
    main()
