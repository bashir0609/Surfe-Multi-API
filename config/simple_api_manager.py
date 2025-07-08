import os
from typing import Dict, Optional, List
# This is a placeholder for your actual Supabase client.
# Ensure it has the methods used in this class.
from database.supabase_client import supabase_client

class SimpleAPIManager:
    """
    Surfe API Manager - User selects a specific Surfe API key to use.
    This version handles both user-owned keys from a database and system-wide
    fallback keys from environment variables.
    """

    def __init__(self):
        """Initialize Surfe API Manager."""
        self.fallback_keys = self._load_env_surfe_keys()
        self.current_user_email = None
        self.service_name = 'surfe'

    def set_current_user(self, user_email: str):
        """Set the current user context for API key retrieval."""
        self.current_user_email = user_email

    def _load_env_surfe_keys(self) -> Dict[str, str]:
        """Load all Surfe API keys from environment variables."""
        surfe_keys = {}

        # Load from numbered environment variables: SURFE_API_KEY_1, etc.
        for i in range(1, 25):  # Support up to 24 keys
            key = os.getenv(f'SURFE_API_KEY_{i}')
            if key:
                surfe_keys[f'surfe_key_{i}'] = key.strip()

        # Also check for a single, non-numbered key
        single_key = os.getenv('SURFE_API_KEY')
        if single_key:
            surfe_keys['surfe_key_default'] = single_key.strip()

        return surfe_keys

    def get_selected_api_key(self, user_email: str = None) -> Optional[str]:
        """
        Get the user's currently selected Surfe API key.

        It prioritizes keys in this order:
        1. A user's personal key marked as 'is_selected'.
        2. The first active personal key if none are marked 'is_selected'.
        3. A selected system key preference stored for the user.
        4. Returns None if no user is set or no key is found.

        Args:
            user_email: User's email. Uses the instance's current_user_email
                        if this is not provided.

        Returns:
            The selected Surfe API key string or None if not found.
        """
        target_user = user_email or self.current_user_email

        if not target_user:
            # No user context, so no key can be considered "selected".
            return None

        try:
            user_keys = supabase_client.get_user_api_keys(target_user)
            surfe_user_keys = [k for k in user_keys if k.get('service') == self.service_name]

            # 1. Find a user's personal key marked as selected
            for key_data in surfe_user_keys:
                if (key_data.get('is_active') and
                    key_data.get('is_selected') and not
                    key_data.get('is_system_key')):
                    return key_data.get('api_key')

            # 2. If no personal key is selected, find the first active personal key
            for key_data in surfe_user_keys:
                if key_data.get('is_active') and not key_data.get('is_system_key'):
                    return key_data.get('api_key')

            # 3. Check for a selected system key
            for key_data in surfe_user_keys:
                if (key_data.get('is_active') and
                    key_data.get('is_selected') and
                    key_data.get('is_system_key')):
                    # The api_key field for a system key is stored as 'SYSTEM_KEY:surfe_key_2'
                    system_key_name = key_data.get('api_key', '').replace('SYSTEM_KEY:', '')
                    # Return the actual key value from the loaded environment keys
                    if system_key_name in self.fallback_keys:
                        return self.fallback_keys[system_key_name]

        except Exception as e:
            print(f"Database error getting selected Surfe key: {e}")

        # 4. Final fallback: return the first available environment key
        return list(self.fallback_keys.values())[0] if self.fallback_keys else None

    def get_all_available_keys(self, user_email: str = None) -> Dict:
        """
        Get all available Surfe keys (both user-specific and system-wide)
        for a user to select from.

        Args:
            user_email: The user's email.

        Returns:
            A dictionary containing lists of user and system keys.
        """
        target_user = user_email or self.current_user_email
        result = {'user_keys': [], 'system_keys': [], 'selected_key_id': None}

        # Get user's personal keys from the database
        if target_user:
            try:
                user_keys = supabase_client.get_user_api_keys(target_user)
                surfe_db_keys = [k for k in user_keys if k.get('service') == self.service_name]

                for key in surfe_db_keys:
                    # Do not display system key placeholders as user keys
                    if key.get('is_system_key'):
                        if key.get('is_selected'):
                            system_key_name = key.get('api_key', '').replace('SYSTEM_KEY:', '')
                            result['selected_key_id'] = system_key_name
                        continue

                    key_info = {
                        'id': key.get('id'),
                        'key_name': key.get('key_name'),
                        'is_active': key.get('is_active'),
                        'is_selected': key.get('is_selected', False),
                        'last_4_chars': key.get('api_key', '')[-4:] if key.get('api_key') else '',
                        'source': 'user'
                    }
                    result['user_keys'].append(key_info)

                    if key.get('is_selected'):
                        result['selected_key_id'] = key.get('id')

            except Exception as e:
                print(f"Error getting user keys from database: {e}")

        # Add system/environment keys for selection
        for key_name, key_value in self.fallback_keys.items():
            system_key = {
                'id': key_name, # Use the name (e.g., 'surfe_key_1') as the ID
                'key_name': key_name.replace('_', ' ').title(),
                'is_active': True,
                # The 'is_selected' flag is determined by checking the DB entries
                'is_selected': result['selected_key_id'] == key_name,
                'last_4_chars': key_value[-4:] if key_value else '',
                'source': 'system'
            }
            result['system_keys'].append(system_key)

        return result

    def select_api_key(self, user_email: str, key_id: any = None) -> bool:
        """
        Select which API key the user wants to use. This can be a personal key
        (using its database ID) or a system key (using its name).

        Args:
            user_email: The user's email.
            key_id: The ID of the key to select. Can be an integer for a user key
                    or a string for a system key (e.g., 'surfe_key_1').

        Returns:
            True if the selection was successful, False otherwise.
        """
        if not user_email or key_id is None:
            return False

        try:
            # First, deselect all other keys for this user and service
            user_keys = supabase_client.get_user_api_keys(user_email)
            for key in user_keys:
                if (key.get('service') == self.service_name and
                    key.get('id') is not None and
                    key.get('is_selected')):
                    supabase_client.update_api_key(key['id'], {'is_selected': False})

            # Case 1: Selecting a user's personal key (ID is an integer)
            if isinstance(key_id, int):
                return bool(supabase_client.update_api_key(key_id, {'is_selected': True}))

            # Case 2: Selecting a system key (ID is a string like 'surfe_key_1')
            if isinstance(key_id, str) and key_id in self.fallback_keys:
                # Check if a system key selection record already exists
                existing_system_selection = next((k for k in user_keys if k.get('is_system_key')), None)

                update_data = {
                    'api_key': f'SYSTEM_KEY:{key_id}',
                    'key_name': f"System: {key_id.replace('_', ' ').title()}",
                    'is_selected': True,
                    'is_active': True
                }

                if existing_system_selection:
                    # Update the existing record to point to the new system key
                    return bool(supabase_client.update_api_key(existing_system_selection['id'], update_data))
                else:
                    # Create a new record to track system key selection
                    return bool(supabase_client.add_api_key(
                        user_email,
                        self.service_name,
                        api_key=update_data['api_key'],
                        key_name=update_data['key_name'],
                        is_selected=True,
                        is_system_key=True
                    ))

            return False

        except Exception as e:
            print(f"Error selecting API key: {e}")
            return False

    def add_surfe_key(self, user_email: str, api_key: str, key_name: str = None) -> Dict:
        """Add a new personal Surfe API key for a user."""
        try:
            if not key_name:
                user_keys = supabase_client.get_user_api_keys(user_email)
                surfe_keys_count = sum(1 for k in user_keys if k.get('service') == self.service_name and not k.get('is_system_key'))
                key_name = f"My Surfe Key #{surfe_keys_count + 1}"

            return supabase_client.add_api_key(user_email, self.service_name, api_key, key_name)
        except Exception as e:
            print(f"Error adding Surfe key: {e}")
            return {}

    def update_surfe_key(self, key_id: int, updates: Dict) -> Dict:
        """Update an existing personal Surfe API key."""
        try:
            # Prevent changing selection status through this generic update method
            updates.pop('is_selected', None)
            return supabase_client.update_api_key(key_id, updates)
        except Exception as e:
            print(f"Error updating Surfe key: {e}")
            return {}

    def delete_surfe_key(self, key_id: int, user_email: str) -> bool:
        """Delete a user's personal Surfe API key."""
        try:
            return supabase_client.delete_api_key(key_id, user_email)
        except Exception as e:
            print(f"Error deleting Surfe key: {e}")
            return False

    def test_surfe_key(self, api_key: str) -> Dict:
        """Test if a Surfe API key is valid."""
        if not api_key or len(api_key.strip()) < 20:
            return {'valid': False, 'message': 'API key is missing or too short.'}

        # TODO: Implement an actual API call to a Surfe endpoint (e.g., a 'me' or 'status' endpoint)
        # to validate the key against their service.
        # Example:
        # headers = {'Authorization': f'Bearer {api_key}'}
        # response = requests.get('https://api.surfe.com/v1/me', headers=headers)
        # if response.status_code == 200:
        #     return {'valid': True, 'message': 'Key is valid.'}
        # else:
        #     return {'valid': False, 'message': f'Invalid key. API returned status {response.status_code}'}

        return {'valid': True, 'message': 'Key format appears valid (simulation).'}

    def log_surfe_usage(self, endpoint: str, user_email: str = None,
                       request_data: Dict = None, response_data: Dict = None,
                       status_code: int = 200, processing_time: float = 0):
        """Log a Surfe API request to the database."""
        target_user = user_email or self.current_user_email
        if not target_user:
            return

        try:
            supabase_client.log_api_request(
                target_user, self.service_name, endpoint, request_data,
                response_data, status_code, processing_time
            )
        except Exception as e:
            print(f"Error logging Surfe usage: {e}")

    def get_usage_stats(self, user_email: str = None, days: int = 30) -> Dict:
        """Get Surfe usage statistics for a specific user."""
        target_user = user_email or self.current_user_email
        if not target_user:
            return {}

        try:
            return supabase_client.get_user_usage_stats(target_user, days, service=self.service_name)
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return {}

    def get_stats(self) -> Dict:
        """Get system statistics. (Backwards compatibility)"""
        db_available = True
        user_keys_count = 0
        try:
            if self.current_user_email:
                user_keys = supabase_client.get_user_api_keys(self.current_user_email)
                # Correctly filter for active, non-system keys
                user_keys_count = sum(1 for k in user_keys if
                                      k.get('service') == self.service_name and
                                      k.get('is_active') and not
                                      k.get('is_system_key'))
        except Exception as e:
            db_available = False
            print(f"Database error in get_stats: {e}")


        return {
            'total_keys': len(self.fallback_keys) + user_keys_count,
            'environment_keys': len(self.fallback_keys),
            'user_keys': user_keys_count,
            'selected_key_user_context': self.current_user_email or 'system_managed (no user set)',
            'database_available': db_available
        }

    def get_selected_key(self) -> Optional[str]:
        """Get selected API key. (Backwards compatibility)"""
        return self.get_selected_api_key()

# --- Global Instances ---
# For backwards compatibility with existing code that may import these instances.
api_manager = SimpleAPIManager()
simple_api_manager = api_manager

