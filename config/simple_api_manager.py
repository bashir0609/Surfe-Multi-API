import os
from typing import Dict, Optional, List
from database.supabase_client import supabase_client

class SimpleAPIManager:
    """
    Surfe API Manager - User selects specific Surfe API key to use
    No auto-rotation - respects user's manual key selection
    """
    
    def __init__(self):
        """Initialize Surfe API Manager"""
        self.fallback_keys = self._load_env_surfe_keys()
        self.current_user_email = None
        self.service_name = 'surfe'
    
    def set_current_user(self, user_email: str):
        """Set the current user context for API key retrieval"""
        self.current_user_email = user_email
    
    def _load_env_surfe_keys(self) -> Dict[str, str]:
        """Load all Surfe API keys from environment variables"""
        surfe_keys = {}
        
        # Load from numbered environment variables: SURFE_API_KEY_1, SURFE_API_KEY_2, etc.
        for i in range(1, 25):  # Support up to 24 keys
            key = os.getenv(f'SURFE_API_KEY_{i}')
            if key:
                surfe_keys[f'surfe_key_{i}'] = key.strip()
        
        # Also check for single key
        single_key = os.getenv('SURFE_API_KEY')
        if single_key:
            surfe_keys['surfe_key_default'] = single_key.strip()
            
        return surfe_keys
    
    def get_selected_api_key(self, user_email: str = None) -> Optional[str]:
        """
        Get the user's currently selected Surfe API key
        
        Args:
            user_email: User email (uses current_user_email if not provided)
            
        Returns:
            Selected Surfe API key string or None if not found
        """
        target_user = user_email or self.current_user_email
        
        if not target_user:
            # No user context, return first available fallback key
            return list(self.fallback_keys.values())[0] if self.fallback_keys else None
        
        try:
            # Get user's selected key from database
            user_keys = supabase_client.get_user_api_keys(target_user)
            
            # Find the selected/active Surfe key
            for key_data in user_keys:
                if (key_data.get('service') == 'surfe' and 
                    key_data.get('is_active') and 
                    key_data.get('is_selected', False)):
                    return key_data.get('api_key')
            
            # If no key is marked as selected, get the first active one
            for key_data in user_keys:
                if key_data.get('service') == 'surfe' and key_data.get('is_active'):
                    return key_data.get('api_key')
                    
        except Exception as e:
            print(f"Database error getting selected Surfe key: {e}")
        
        # Fallback to environment keys (return first available)
        return list(self.fallback_keys.values())[0] if self.fallback_keys else None
    
    def get_all_available_keys(self, user_email: str = None) -> Dict:
        """Get all available Surfe keys for user selection"""
        target_user = user_email or self.current_user_email
        
        result = {
            'user_keys': [],
            'system_keys': [],
            'selected_key_id': None
        }
        
        # Get user's database keys
        if target_user:
            try:
                user_keys = supabase_client.get_user_api_keys(target_user)
                surfe_keys = [k for k in user_keys if k.get('service') == 'surfe']
                
                # Don't expose actual API keys, just metadata
                for key in surfe_keys:
                    key_info = {
                        'id': key.get('id'),
                        'key_name': key.get('key_name'),
                        'is_active': key.get('is_active'),
                        'is_selected': key.get('is_selected', False),
                        'created_at': key.get('created_at'),
                        'last_4_chars': key.get('api_key', '')[-4:] if key.get('api_key') else '',
                        'source': 'user'
                    }
                    result['user_keys'].append(key_info)
                    
                    if key.get('is_selected'):
                        result['selected_key_id'] = key.get('id')
                        
            except Exception as e:
                print(f"Error getting user keys: {e}")
        
        # Add system/environment keys
        for key_name, key_value in self.fallback_keys.items():
            system_key = {
                'id': key_name,
                'key_name': key_name.replace('_', ' ').title(),
                'is_active': True,
                'is_selected': False,
                'last_4_chars': key_value[-4:] if key_value else '',
                'source': 'system'
            }
            result['system_keys'].append(system_key)
        
        return result
    
    def select_api_key(self, user_email: str, key_id: int = None, system_key_name: str = None) -> bool:
        """
        Select which API key the user wants to use
        
        Args:
            user_email: User's email
            key_id: Database key ID (for user's personal keys)
            system_key_name: System key name (for environment keys)
            
        Returns:
            True if selection was successful
        """
        try:
            # First, deselect all current keys for this user
            user_keys = supabase_client.get_user_api_keys(user_email)
            for key in user_keys:
                if key.get('service') == 'surfe' and key.get('is_selected'):
                    supabase_client.update_api_key(key['id'], {'is_selected': False})
            
            # If selecting a user's personal key
            if key_id:
                return bool(supabase_client.update_api_key(key_id, {'is_selected': True}))
            
            # If selecting a system key, store the selection
            if system_key_name:
                # Create a record to track system key selection
                selection_data = {
                    'user_email': user_email,
                    'service': 'surfe',
                    'api_key': f'SYSTEM_KEY:{system_key_name}',
                    'key_name': f'System: {system_key_name}',
                    'is_active': True,
                    'is_selected': True,
                    'is_system_key': True
                }
                return bool(supabase_client.add_api_key(user_email, 'surfe', selection_data['api_key'], selection_data['key_name']))
            
            return False
            
        except Exception as e:
            print(f"Error selecting API key: {e}")
            return False
    
    def add_surfe_key(self, user_email: str, api_key: str, key_name: str = None) -> Dict:
        """Add a new personal Surfe API key for a user"""
        try:
            if not key_name:
                existing_count = len([k for k in supabase_client.get_user_api_keys(user_email) if k.get('service') == 'surfe'])
                key_name = f"My Surfe Key #{existing_count + 1}"
            
            return supabase_client.add_api_key(user_email, 'surfe', api_key, key_name)
        except Exception as e:
            print(f"Error adding Surfe key: {e}")
            return {}
    
    def update_surfe_key(self, key_id: int, updates: Dict) -> Dict:
        """Update an existing Surfe API key"""
        try:
            # Don't allow updating selection status through this method
            if 'is_selected' in updates:
                del updates['is_selected']
            return supabase_client.update_api_key(key_id, updates)
        except Exception as e:
            print(f"Error updating Surfe key: {e}")
            return {}
    
    def delete_surfe_key(self, key_id: int, user_email: str) -> bool:
        """Delete a user's Surfe API key"""
        try:
            return supabase_client.delete_api_key(key_id, user_email)
        except Exception as e:
            print(f"Error deleting Surfe key: {e}")
            return False
    
    def test_surfe_key(self, api_key: str) -> Dict:
        """Test if a Surfe API key is valid"""
        if not api_key or len(api_key.strip()) < 10:
            return {'valid': False, 'message': 'API key too short'}
        
        if len(api_key) < 20:
            return {'valid': False, 'message': 'Surfe API key appears too short'}
        
        # TODO: Make actual API call to Surfe to test the key
        return {'valid': True, 'message': 'Surfe API key format appears valid'}
    
    def log_surfe_usage(self, endpoint: str, user_email: str = None, 
                       request_data: Dict = None, response_data: Dict = None,
                       status_code: int = 200, processing_time: float = 0):
        """Log Surfe API usage to database"""
        target_user = user_email or self.current_user_email
        
        if target_user:
            try:
                supabase_client.log_api_request(
                    target_user, 'surfe', endpoint, request_data, 
                    response_data, status_code, processing_time
                )
            except Exception as e:
                print(f"Error logging Surfe usage: {e}")
    
    def get_usage_stats(self, user_email: str = None, days: int = 30) -> Dict:
        """Get Surfe usage statistics for a user"""
        target_user = user_email or self.current_user_email
        
        if target_user:
            try:
                return supabase_client.get_user_usage_stats(target_user, days)
            except Exception as e:
                print(f"Error getting usage stats: {e}")
        
        return {'total_requests': 0, 'service_breakdown': {}, 'status_breakdown': {}}
    
    def get_stats(self) -> Dict:
        """Get system statistics - backwards compatibility method"""
        try:
            user_keys_count = 0
            if self.current_user_email:
                user_keys = self.get_user_surfe_keys(self.current_user_email)
                user_keys_count = len([k for k in user_keys if k.get('is_active')])
            
            return {
                'total_keys': len(self.fallback_keys) + user_keys_count,
                'environment_keys': len(self.fallback_keys),
                'user_keys': user_keys_count,
                'selected_key': self.current_user_email or 'system_managed',
                'database_available': True
            }
        except Exception as e:
            # Fallback stats if database fails
            return {
                'total_keys': len(self.fallback_keys),
                'environment_keys': len(self.fallback_keys),
                'user_keys': 0,
                'selected_key': 'system_managed',
                'database_available': False,
                'error': str(e)
            }
    
    def get_selected_key(self) -> Optional[str]:
        """Get selected API key - backwards compatibility method"""
        return self.get_selected_api_key()

# Global instances - maintaining backwards compatibility
api_manager = SimpleAPIManager()
simple_api_manager = api_manager  # Backwards compatibility for existing code

# Also ensure the old method name exists
if hasattr(simple_api_manager, 'get_selected_api_key'):
    simple_api_manager.get_selected_key = simple_api_manager.get_selected_api_key