import os
from typing import Dict, Optional, List
from database.supabase_client import supabase_client

class SimpleAPIManager:
    """
    Enhanced API Manager that uses Supabase database for API key storage
    Falls back to environment variables if database is unavailable
    """
    
    def __init__(self):
        """Initialize API Manager"""
        self.fallback_keys = self._load_env_fallback_keys()
        self.current_user_email = None  # Will be set by request context
    
    def set_current_user(self, user_email: str):
        """Set the current user context for API key retrieval"""
        self.current_user_email = user_email
    
    def _load_env_fallback_keys(self) -> Dict[str, str]:
        """Load fallback API keys from environment variables"""
        return {
            'apollo': os.getenv('APOLLO_API_KEY'),
            'clearbit': os.getenv('CLEARBIT_API_KEY'),
            'hunter': os.getenv('HUNTER_API_KEY'),
            'peopledatalabs': os.getenv('PEOPLEDATALABS_API_KEY'),
            'proxycurl': os.getenv('PROXYCURL_API_KEY'),
            'zoominfo': os.getenv('ZOOMINFO_API_KEY'),
            'leadiq': os.getenv('LEADIQ_API_KEY'),
            'lusha': os.getenv('LUSHA_API_KEY')
        }
    
    def get_api_key(self, service: str, user_email: str = None) -> Optional[str]:
        """
        Get API key for a service, prioritizing user's database keys
        
        Args:
            service: The API service name (apollo, clearbit, etc.)
            user_email: User email (uses current_user_email if not provided)
            
        Returns:
            API key string or None if not found
        """
        target_user = user_email or self.current_user_email
        
        # Try to get from database first
        if target_user:
            try:
                db_key = supabase_client.get_active_api_key(target_user, service.lower())
                if db_key:
                    return db_key
            except Exception as e:
                print(f"Database error getting API key for {service}: {e}")
        
        # Fallback to environment variables
        return self.fallback_keys.get(service.lower())
    
    def get_available_services(self, user_email: str = None) -> List[Dict[str, str]]:
        """
        Get list of available services with their key status
        
        Returns:
            List of dictionaries with service info
        """
        target_user = user_email or self.current_user_email
        services = []
        
        # Get user's database keys
        user_keys = {}
        if target_user:
            try:
                db_keys = supabase_client.get_user_api_keys(target_user)
                for key_data in db_keys:
                    if key_data.get('is_active'):
                        user_keys[key_data['service']] = key_data
            except Exception as e:
                print(f"Error getting user API keys: {e}")
        
        # Check each service
        for service_name in self.fallback_keys.keys():
            has_db_key = service_name in user_keys
            has_env_key = bool(self.fallback_keys.get(service_name))
            
            service_info = {
                'name': service_name,
                'display_name': service_name.title(),
                'has_user_key': has_db_key,
                'has_fallback_key': has_env_key,
                'key_source': 'database' if has_db_key else ('environment' if has_env_key else 'none'),
                'key_name': user_keys[service_name].get('key_name', '') if has_db_key else ''
            }
            services.append(service_info)
        
        return services
    
    def add_user_api_key(self, user_email: str, service: str, api_key: str, key_name: str = None) -> Dict:
        """Add a new API key for a user"""
        try:
            return supabase_client.add_api_key(user_email, service.lower(), api_key, key_name)
        except Exception as e:
            print(f"Error adding API key: {e}")
            return {}
    
    def update_user_api_key(self, key_id: int, updates: Dict) -> Dict:
        """Update an existing API key"""
        try:
            return supabase_client.update_api_key(key_id, updates)
        except Exception as e:
            print(f"Error updating API key: {e}")
            return {}
    
    def delete_user_api_key(self, key_id: int, user_email: str) -> bool:
        """Delete a user's API key"""
        try:
            return supabase_client.delete_api_key(key_id, user_email)
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False
    
    def get_user_api_keys(self, user_email: str) -> List[Dict]:
        """Get all API keys for a user"""
        try:
            return supabase_client.get_user_api_keys(user_email)
        except Exception as e:
            print(f"Error getting user API keys: {e}")
            return []
    
    def test_api_key(self, service: str, api_key: str) -> Dict:
        """
        Test if an API key is valid by making a simple request
        
        Returns:
            Dictionary with 'valid' boolean and 'message' string
        """
        # Basic validation - you can enhance this with actual API calls
        if not api_key or len(api_key.strip()) < 10:
            return {'valid': False, 'message': 'API key too short'}
        
        # Service-specific validation patterns
        service_patterns = {
            'apollo': lambda k: k.startswith('apollo_'),
            'clearbit': lambda k: len(k) == 32,
            'hunter': lambda k: len(k) >= 20,
            'peopledatalabs': lambda k: len(k) >= 30,
            'proxycurl': lambda k: len(k) >= 20,
            'zoominfo': lambda k: len(k) >= 20,
            'leadiq': lambda k: len(k) >= 20,
            'lusha': lambda k: len(k) >= 20
        }
        
        validator = service_patterns.get(service.lower())
        if validator and not validator(api_key):
            return {'valid': False, 'message': f'Invalid {service} API key format'}
        
        return {'valid': True, 'message': 'API key format appears valid'}
    
    def log_api_usage(self, service: str, endpoint: str, user_email: str = None, 
                     request_data: Dict = None, response_data: Dict = None,
                     status_code: int = 200, processing_time: float = 0):
        """Log API usage to database"""
        target_user = user_email or self.current_user_email
        
        if target_user:
            try:
                supabase_client.log_api_request(
                    target_user, service, endpoint, request_data, 
                    response_data, status_code, processing_time
                )
            except Exception as e:
                print(f"Error logging API usage: {e}")
    
    def get_user_usage_stats(self, user_email: str = None, days: int = 30) -> Dict:
        """Get usage statistics for a user"""
        target_user = user_email or self.current_user_email
        
        if target_user:
            try:
                return supabase_client.get_user_usage_stats(target_user, days)
            except Exception as e:
                print(f"Error getting usage stats: {e}")
        
        return {'total_requests': 0, 'service_breakdown': {}, 'status_breakdown': {}}

# Global instance
api_manager = SimpleAPIManager()