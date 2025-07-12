# config/supabase_api_manager.py

"""
Supabase-Only API Key Manager
Loads API keys exclusively from Supabase database, no environment variables
"""
import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from database.supabase_client import supabase_client
from config.config import SURFE_API_BASE_URL
import json

logger = logging.getLogger(__name__)

class SupabaseApiManager:
    """Database-only API key manager using Supabase"""
    
    def __init__(self):
        self.selected_key_cache = None
        self.cache_timeout = 300  # 5 minutes cache
        self.last_cache_update = None
        self.default_user_email = "system@localhost"  # Default system user
        self.current_user_email = None  # Track current user
    
    def load_keys_from_database(self, user_email: str = None) -> List[Dict]:
        """Load all API keys from Supabase database"""
        try:
            email = user_email or self.default_user_email
            keys = supabase_client.get_user_api_keys(email)
            logger.info(f"Loaded {len(keys)} API keys from Supabase for user: {email}")
            return keys
        except Exception as e:
            logger.error(f"Failed to load API keys from Supabase: {e}")
            return []
    
    def get_selected_key(self, user_email: str = None) -> Optional[str]:
        """Get the currently selected API key value"""
        try:
            email = user_email or self.default_user_email
            
            # Use cache if valid
            if self._is_cache_valid():
                return self.selected_key_cache
            
            # Query Supabase for selected key
            selected_key = supabase_client.get_active_api_key(email, 'surfe')
            
            if selected_key:
                self.selected_key_cache = selected_key
                self.last_cache_update = datetime.utcnow()
                logger.debug(f"Selected API key retrieved for user: {email}")
                return selected_key
            
            # If no active key, try to get the first available key
            all_keys = self.load_keys_from_database(email)
            if all_keys:
                first_key = all_keys[0]
                # Set it as active
                self.set_active_key(first_key['id'], email)
                return first_key['api_key']
            
            logger.warning(f"No API keys found for user: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting selected API key: {e}")
            return None
    
    def get_key_by_name(self, key_name: str, user_email: str = None) -> Optional[str]:
        """Get API key by name"""
        try:
            email = user_email or self.default_user_email
            all_keys = self.load_keys_from_database(email)
            
            for key in all_keys:
                if key.get('key_name') == key_name and key.get('is_active', True):
                    return key['api_key']
            
            logger.warning(f"API key '{key_name}' not found or inactive")
            return None
            
        except Exception as e:
            logger.error(f"Error getting API key by name: {e}")
            return None
    
    def add_api_key(self, key_name: str, api_key: str, user_email: str = None) -> bool:
        """Add new API key to Supabase"""
        try:
            email = user_email or self.default_user_email
            
            result = supabase_client.add_api_key(
                user_email=email,
                service='surfe',
                api_key=api_key,
                key_name=key_name
            )
            
            if result:
                self._invalidate_cache()
                logger.info(f"Added API key: {key_name} for user: {email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to add API key: {e}")
            return False
    
    def remove_api_key(self, key_id: int, user_email: str = None) -> bool:
        """Remove API key from Supabase"""
        try:
            email = user_email or self.default_user_email
            
            success = supabase_client.delete_api_key(key_id, email)
            
            if success:
                self._invalidate_cache()
                logger.info(f"Removed API key ID: {key_id} for user: {email}")
                
                # If no keys left, clear cache
                remaining_keys = self.load_keys_from_database(email)
                if not remaining_keys:
                    self.selected_key_cache = None
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove API key: {e}")
            return False
    
    def set_active_key(self, key_id: int, user_email: str = None) -> bool:
        """Set a specific API key as active (selected)"""
        try:
            email = user_email or self.default_user_email
            
            # First, deactivate all keys for this user
            all_keys = self.load_keys_from_database(email)
            for key in all_keys:
                if key['id'] != key_id:
                    supabase_client.update_api_key(key['id'], {'is_active': False})
            
            # Then activate the selected key
            result = supabase_client.update_api_key(key_id, {'is_active': True})
            
            if result:
                self._invalidate_cache()
                logger.info(f"Set active API key ID: {key_id} for user: {email}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to set active API key: {e}")
            return False
    
    def select_key_by_name(self, key_name: str, user_email: str = None) -> bool:
        """Select API key by name"""
        try:
            email = user_email or self.default_user_email
            all_keys = self.load_keys_from_database(email)
            
            for key in all_keys:
                if key.get('key_name') == key_name:
                    return self.set_active_key(key['id'], email)
            
            logger.error(f"API key '{key_name}' not found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to select API key by name: {e}")
            return False
    
    def enable_key(self, key_id: int, user_email: str = None) -> bool:
        """Enable API key"""
        try:
            email = user_email or self.default_user_email
            
            result = supabase_client.update_api_key(key_id, {
                'is_active': True,
                'updated_at': datetime.utcnow().isoformat()
            })
            
            if result:
                logger.info(f"Enabled API key ID: {key_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to enable API key: {e}")
            return False
    
    def disable_key(self, key_id: int, user_email: str = None) -> bool:
        """Disable API key"""
        try:
            email = user_email or self.default_user_email
            
            result = supabase_client.update_api_key(key_id, {
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            })
            
            if result:
                self._invalidate_cache()
                logger.info(f"Disabled API key ID: {key_id}")
                
                # If this was the active key, try to select another
                self._auto_select_key(email)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to disable API key: {e}")
            return False
    
    def get_stats(self, user_email: str = None) -> Dict:
        """Get API key statistics from Supabase"""
        try:
            email = user_email or self.default_user_email
            all_keys = self.load_keys_from_database(email)
            
            enabled_keys = [k for k in all_keys if k.get('is_active', True)]
            selected_key = next((k for k in all_keys if k.get('is_active', True)), None)
            
            # Get usage stats
            usage_stats = supabase_client.get_user_usage_stats(email)
            
            return {
                'total_keys': len(all_keys),
                'enabled_keys': len(enabled_keys),
                'disabled_keys': len(all_keys) - len(enabled_keys),
                'selected_key': selected_key.get('key_name') if selected_key else None,
                'has_valid_selection': bool(selected_key),
                'system_health': (len(enabled_keys) / len(all_keys) * 100) if all_keys else 0,
                'keys': all_keys,
                'total_requests': usage_stats.get('total_requests', 0),
                'service_breakdown': usage_stats.get('service_breakdown', {}),
                'status_breakdown': usage_stats.get('status_breakdown', {}),
                'user_email': email
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'total_keys': 0,
                'enabled_keys': 0,
                'disabled_keys': 0,
                'selected_key': None,
                'has_valid_selection': False,
                'system_health': 0,
                'keys': [],
                'total_requests': 0,
                'user_email': user_email if user_email else self.default_user_email
            }
    
    def _auto_select_key(self, user_email: str):
        """Automatically select the first available enabled key"""
        try:
            email = user_email or self.default_user_email
            all_keys = self.load_keys_from_database(email)
            
            # Find first enabled key
            for key in all_keys:
                if key.get('is_active', True):
                    self.set_active_key(key['id'], email)
                    logger.info(f"Auto-selected API key: {key.get('key_name')}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to auto-select key: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid"""
        if not self.last_cache_update or not self.selected_key_cache:
            return False
        
        cache_age = (datetime.utcnow() - self.last_cache_update).total_seconds()
        return cache_age < self.cache_timeout
    
    def _invalidate_cache(self):
        """Invalidate the selected key cache"""
        self.selected_key_cache = None
        self.last_cache_update = None
    
    def sync_from_database(self, user_email: str = None):
        """Force sync from Supabase database (invalidate all caches)"""
        self._invalidate_cache()
        email = user_email or self.default_user_email
        logger.info(f"Synced API keys from Supabase for user: {email}")
    
    def get_all_enabled_keys(self, user_email: str = None) -> List[str]:
        """Get all enabled API key values"""
        try:
            email = user_email or self.default_user_email
            all_keys = self.load_keys_from_database(email)
            return [key['api_key'] for key in all_keys if key.get('is_active', True)]
        except Exception as e:
            logger.error(f"Failed to get enabled keys: {e}")
            return []
    
    def sync_env_keys_to_db(self, user_email: str = None) -> Dict[str, Any]:
        """Sync API keys from environment variables to database"""
        import os
        
        # Use environment variable for system user, fallback to default
        email = user_email if user_email else os.getenv('SYSTEM_USER_EMAIL', self.default_user_email)
        synced_count = 0
        
        try:
            # First, ensure the user exists in the database
            from database.supabase_client import supabase_client
            user_profile = supabase_client.get_user_profile(email)
            if not user_profile:
                # Create the system user if it doesn't exist
                supabase_client.create_or_update_user(email, "System User")
                logger.info(f"Created system user: {email}")
            
            # Get existing keys from database
            existing_keys = self.load_keys_from_database(email)
            existing_key_names = {key['key_name'] for key in existing_keys}
            
            # Look for SURFE_API_KEY environment variables
            env_keys = []
            
            # Check for single SURFE_API_KEY
            if os.getenv('SURFE_API_KEY'):
                env_keys.append(('SURFE_API_KEY', os.getenv('SURFE_API_KEY')))
            
            # Check for numbered SURFE_API_KEY_1, SURFE_API_KEY_2, etc.
            for i in range(1, 100):  # Check up to 100 keys
                key_name = f'SURFE_API_KEY_{i}'
                key_value = os.getenv(key_name)
                if key_value:
                    env_keys.append((key_name, key_value))
            
            # Sync each environment key to database
            for key_name, api_key in env_keys:
                if key_name not in existing_key_names:
                    # Add new key to database
                    success = self.add_api_key(key_name, api_key, email)
                    if success:
                        synced_count += 1
                        logger.info(f"Synced environment key {key_name} to database")
                else:
                    logger.debug(f"Key {key_name} already exists in database")
            
            # If this is the first sync and we added keys, select the first one
            if synced_count > 0 and not any(key.get('is_active') for key in existing_keys):
                all_keys = self.load_keys_from_database(email)
                if all_keys:
                    self.set_active_key(all_keys[0]['id'], email)
                    logger.info(f"Auto-selected first key: {all_keys[0]['key_name']}")
            
            logger.info(f"Environment sync complete: {synced_count} new keys added")
            return {
                'synced': synced_count,
                'total_env_keys': len(env_keys),
                'existing_keys': len(existing_keys)
            }
            
        except Exception as e:
            logger.error(f"Failed to sync environment keys: {e}")
            return {
                'synced': 0,
                'error': str(e)
            }
    
    def set_current_user(self, user_email: str):
        """Set the current user context"""
        self.current_user_email = user_email
        self._invalidate_cache()  # Clear cache when user changes
        logger.debug(f"Set current user to: {user_email}")
    
    def get_current_user(self) -> str:
        """Get the current user email"""
        return self.current_user_email or self.default_user_email
    
    def get_detailed_stats(self, user_email: str = None) -> Dict:
        """Get detailed statistics (alias for get_stats for compatibility)"""
        return self.get_stats(user_email)

    
    async def make_request_async(
        self,
        user_email: str,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        selected_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make async request to Surfe API with selected key"""
        
        email = user_email or self.default_user_email
        api_key = self.get_selected_key(email)

        # Get API key
        if selected_key:
            api_key = self.get_key_by_name(selected_key, email)
            if not api_key:
                logger.warning(f"Selected key '{selected_key}' not found, using manager default")
                api_key = self.get_selected_key(email)
        else:
            api_key = self.get_selected_key(email)

        if not api_key:
            raise ValueError("No API key selected or available")

        # Prepare request
        url = f"{SURFE_API_BASE_URL}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SurfeMultiAPI/1.0"
        }

        method = method.upper()
        logger.info(f"Making {method} request to {endpoint}")
        
        # Debug logging for request data
        if json_data:
            logger.debug(f"Request JSON data: {json_data}")
        if params:
            logger.debug(f"Request params: {params}")

        # Build request arguments conditionally
        request_kwargs = {
            'method': method,
            'url': url,
            'headers': headers,
            'timeout': aiohttp.ClientTimeout(total=timeout)
        }
        
        # Add params if provided
        if params:
            request_kwargs['params'] = params
            
        # Only add JSON body for methods that typically have request bodies
        if method in ('POST', 'PUT', 'PATCH') and json_data is not None:
            request_kwargs['json'] = json_data

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(**request_kwargs) as response:
                    response_text = await response.text()

                    # Handle successful responses
                    if response.status in [200, 201, 202]:
                        try:
                            result = await response.json()
                            logger.info(f"Successful {method} request to {endpoint}")
                            return result
                        except (aiohttp.ContentTypeError, ValueError) as json_error:
                            logger.error(f"JSON parsing error for {endpoint}: {json_error}")
                            return {"error": "Invalid JSON response", "raw_response": response_text}
                    
                    # Handle specific error cases
                    elif response.status == 400:
                        logger.error(f"Bad request for {endpoint}: {response_text}")
                        try:
                            error_data = await response.json()
                            raise ValueError(f"Bad request: {error_data.get('message', response_text)}")
                        except:
                            raise ValueError(f"Bad request: {response_text}")
                    
                    elif response.status == 401:
                        logger.error(f"Authentication failed for {endpoint}")
                        raise ValueError("Invalid API key or authentication failed")
                    
                    elif response.status == 429:
                        logger.error(f"Rate limit exceeded for {endpoint}")
                        raise Exception("Rate limit exceeded")
                    
                    elif response.status == 404:
                        logger.error(f"Endpoint not found: {endpoint}")
                        raise ValueError(f"Endpoint not found: {endpoint}")
                    
                    elif response.status >= 500:
                        logger.error(f"Server error {response.status} for {endpoint}: {response_text}")
                        # Try to extract nested error information
                        try:
                            error_data = await response.json()
                            if 'message' in error_data:
                                raise Exception(f"Server error {response.status}: {error_data['message']}")
                            else:
                                raise Exception(f"Server error {response.status}: {response_text}")
                        except:
                            raise Exception(f"Server error {response.status}: {response_text}")
                    
                    else:
                        logger.error(f"HTTP {response.status} error for {endpoint}: {response_text}")
                        raise Exception(f"HTTP {response.status}: {response_text}")

        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {endpoint}")
            raise TimeoutError(f"Request timeout for {endpoint}")
        
        except aiohttp.ClientError as e:
            logger.error(f"Client error for {endpoint}: {str(e)}")
            raise Exception(f"Client error: {str(e)}")
        
        except Exception as e:
            logger.error(f"Unexpected error for {endpoint}: {str(e)}")
            raise

    def make_request(
            self,
            method: str,
            endpoint: str,
            json_data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            timeout: int = 30,
            selected_key: Optional[str] = None,
            user_email: Optional[str] = None
        ) -> Dict[str, Any]:
            """Synchronous wrapper for async request"""
            # Ensure user_email has a value
            email = user_email or self.default_user_email
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.make_request_async(
                        email,  # Use email instead of user_email
                        method, 
                        endpoint, 
                        json_data, 
                        params, 
                        timeout, 
                        selected_key
                    )
                )
            finally:
                loop.close()


# Global instance
supabase_api_manager = SupabaseApiManager()