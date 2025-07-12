# database/supabase_client.py - Enhanced version with API ID-based key management

import os
import re
import logging
from supabase.client import create_client, Client
from typing import List, Dict, Optional, Any
from urllib.parse import urlparse
import json
from datetime import datetime

logger = logging.getLogger(__name__)


def clean_domain(domain_input: str) -> str:
    """
    Clean and validate domain input to ensure it's a proper domain name.
    Removes protocols, www prefixes, paths, and query parameters.
    """
    if not domain_input or not isinstance(domain_input, str):
        return ""
    
    domain = domain_input.strip().lower()
    
    # Remove protocol if present
    if domain.startswith(('http://', 'https://')):
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
    
    # Remove www. prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    
    # Remove path, query parameters, and fragments
    domain = domain.split('/')[0].split('?')[0].split('#')[0]
    
    # Remove port number if present
    domain = domain.split(':')[0]
    
    return domain

def is_valid_domain(domain: str) -> bool:
    """
    Validate that a domain follows proper domain name format.
    """
    if not domain or not isinstance(domain, str):
        return False
    
    # Basic domain regex pattern
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    
    # Check length (max 253 characters for full domain)
    if len(domain) > 253:
        return False
    
    # Check pattern
    if not re.match(domain_pattern, domain):
        return False
    
    # Must contain at least one dot (except for localhost cases)
    if '.' not in domain and domain != 'localhost':
        return False
    
    return True

def clean_domains_list(domains: List[str]) -> List[str]:
    """
    Clean a list of domains and return only valid ones.
    """
    cleaned = []
    for domain_input in domains:
        if domain_input and isinstance(domain_input, str):
            cleaned_domain = clean_domain(domain_input.strip())
            if cleaned_domain and is_valid_domain(cleaned_domain):
                cleaned.append(cleaned_domain)
    return cleaned


class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client with database configuration"""
        
        # Initialize defaults
        self.client: Optional[Client] = None
        self.admin_client = None
        self.is_available = False
        
        try:
            # Try advanced database config first
            from config.database_config import db_config
            
            # Get Supabase configuration
            supabase_config = db_config.get_supabase_config()
            self.url = supabase_config.get('url')
            self.key = supabase_config.get('anon_key')
            self.service_role_key = supabase_config.get('service_role_key')
            
            # Get additional configuration
            self.app_config = db_config.get_app_config()
            self.api_keys_config = db_config.get_api_keys_config()
            
            print("✅ Using advanced database configuration")
            
        except ImportError:
            # Fallback to environment variables
            print("⚠️ Database config not found, using environment variables")
            
            self.url = os.getenv('SUPABASE_URL')
            self.key = os.getenv('SUPABASE_ANON_KEY')
            self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            
            # Set default configs
            self.app_config = {
                'environment': os.getenv('APP_ENVIRONMENT', 'development'),
                'debug': os.getenv('DEBUG', 'true').lower() == 'true'
            }
            self.api_keys_config = {
                'max_keys_per_user': int(os.getenv('MAX_API_KEYS_PER_USER', '100'))
            }
        
        # Validate required configuration
        if not self.url or not self.key:
            raise ValueError(
                "Missing required Supabase configuration. "
                "Please set SUPABASE_URL and SUPABASE_ANON_KEY"
            )
        
        try:
            # Create main client
            self.client = create_client(self.url, self.key)
            print("✅ Main Supabase client created")
            
            # Create admin client if key is available
            if self.service_role_key and self.service_role_key.strip():
                try:
                    self.admin_client = create_client(self.url, self.service_role_key)
                    print("✅ Admin client created (service role key found)")
                except Exception as e:
                    print(f"⚠️ Failed to create admin client: {e}")
                    self.admin_client = None
            else:
                self.admin_client = None
                print("ℹ️ No admin client (no service role key)")
            
            # Test the connection - use self.client here, not self._client
            test_response = self.client.table('users').select('count').limit(1).execute()
            
            # Mark as available
            self.is_available = True
            
            print(f"✅ Supabase client initialized successfully")
            print(f"   Environment: {self.app_config.get('environment', 'unknown')}")
            print(f"   Max keys per user: {self.api_keys_config.get('max_keys_per_user', 100)}")
            print(f"   Admin access: {'Yes' if self.admin_client else 'No'}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Supabase client: {e}")
            self.is_available = False
            raise
    
    @property
    def _client(self) -> Client:
        """Get the client, raising an error if not available"""
        if not self.client:
            raise RuntimeError("Supabase client is not initialized")
        return self.client

    @property
    def _admin(self) -> Client:
        """Get the admin client, raising an error if not available"""
        if not self.admin_client:
            raise RuntimeError("Supabase admin client is not initialized")
        return self.admin_client
    
    def get_system_keys(self) -> List[Dict]:
        """Get system-wide API keys (for sync purposes)"""
        try:
            # Get all API keys from the system user
            response = self._client.table('api_keys').select('*').eq('user_email', 'system@localhost').execute()
            return response.data or []
        except Exception as e:
            print(f"Error getting system keys: {e}")
            return []

    def get_all_api_keys(self) -> List[Dict]:
        """Get all API keys in the system (admin function)"""
        try:
            if self.has_admin_access():
                # Use admin client to get all keys
                response = self._admin.table('api_keys').select('*').execute()
                return response.data or []
            else:
                # Regular client can only see public keys
                response = self._client.table('api_keys').select('*').execute()
                return response.data or []
        except Exception as e:
            print(f"Error getting all API keys: {e}")
            return []
        
    def has_admin_access(self) -> bool:
        """Check if admin operations are available"""
        return self.admin_client is not None and self.is_available
    
    def set_user_context(self, user_email: str):
        """Set user context for RLS policies"""
        if not self.is_available:
            return False
        
        try:
            # Try to call the Supabase RLS function (if it exists)
            self._client.rpc('set_user_context', {'user_email_param': user_email}).execute()
            return True
        except Exception as e:
            # If function doesn't exist, that's OK - RLS might not be set up yet
            if "function" in str(e).lower() and "does not exist" in str(e).lower():
                # Function doesn't exist - silently continue (RLS not configured)
                return False
            else:
                # Real error - log it
                print(f"Error setting user context: {e}")
                return False

    def set_user_context_safe(self, user_email: str) -> bool:
        """Set user context - won't fail if RLS function doesn't exist"""
        try:
            return self.set_user_context(user_email)
        except:
            # Silently fail - RLS is optional
            return False
    
    def generate_key_name(self, api_id: int) -> str:
        """Generate standardized key name from API ID"""
        return f"SURFE_API_KEY_{api_id}"
    
    # ===== ENHANCED API KEYS MANAGEMENT WITH API ID FOCUS =====
    
    def get_user_api_keys(self, user_email: str) -> List[Dict]:
        """Get all API keys for a user, sorted by ID"""
        try:
            response = self._client.table('api_keys').select('*').eq('user_email', user_email).order('id').execute()
            return response.data
        except Exception as e:
            print(f"Error getting API keys: {e}")
            return []
    
    def get_api_key_by_id(self, api_id: int, user_email: str = None) -> Optional[Dict]:
        """Get API key by ID, optionally filtered by user"""
        try:
            query = self._client.table('api_keys').select('*').eq('id', api_id)
            if user_email:
                query = query.eq('user_email', user_email)
            
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting API key by ID: {e}")
            return None
    
    def add_api_key(self, user_email: str = None, service: str = 'surfe', api_key: str = None, key_name: str = None, user_id: str = None) -> Dict:
        """Add a new API key for a user - returns the created key with ID"""
        
        # Handle both user_email and user_id for backward compatibility
        if user_id and not user_email:
            user_email = user_id
        elif not user_email and not user_id:
            raise ValueError("Either user_email or user_id must be provided")
        
        try:
            # Check if this is the first key for the user
            existing_keys = self.get_user_api_keys(user_email)
            is_first_key = len(existing_keys) == 0
            
            # Check user's key limit
            max_keys = self.api_keys_config['max_keys_per_user']
            if len(existing_keys) >= max_keys:
                raise ValueError(f"User has reached maximum limit of {max_keys} API keys")
            
            # First, create the key without the name to get the ID
            data = {
                'user_email': user_email,
                'service': service,
                'api_key': api_key,
                'key_name': key_name or 'temp',  # Temporary name
                'created_at': datetime.utcnow().isoformat(),
                'is_active': is_first_key  # First key is auto-selected
            }
            
            response = self._client.table('api_keys').insert(data).execute()
            
            if response.data:
                created_key = response.data[0]
                api_id = created_key['id']
                
                # Update with the proper name if it wasn't provided
                if not key_name:
                    proper_key_name = self.generate_key_name(api_id)
                    self.update_api_key(api_id, {'key_name': proper_key_name})
                    created_key['key_name'] = proper_key_name
                
                # If this is the first key, make sure no other keys are active
                if is_first_key:
                    self.set_single_active_key(api_id, user_email)
                
                # Log the creation in development mode
                if self.app_config['environment'] == 'development':
                    print(f"🔑 Created API key: {created_key['key_name']} (ID: {api_id}) for {user_email}")
                
                return created_key
            
            return {}
        except Exception as e:
            print(f"Error adding API key: {e}")
            return {}
    
    def update_api_key(self, api_id: int, updates: Dict) -> Dict:
        """Update an existing API key by ID"""
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            response = self._client.table('api_keys').update(updates).eq('id', api_id).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error updating API key: {e}")
            return {}
    
    def delete_api_key(self, api_id: int, user_email: str) -> bool:
        """Delete an API key by ID (only if it belongs to the user)"""
        try:
            response = self._client.table('api_keys').delete().eq('id', api_id).eq('user_email', user_email).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False
    
    def get_active_api_key_by_name(self, user_email: str, service: str = 'surfe') -> Optional[str]:
        """Get the active API key name for a service"""
        try:
            response = self._client.table('api_keys').select('key_name').eq('user_email', user_email).eq('service', service).eq('is_active', True).limit(1).execute()
            
            if response.data:
                return response.data[0]['key_name']  # Return the key_name, not the api_key
            return None
        except Exception as e:
            print(f"Error getting active API key name: {e}")
            return None
    
    def get_active_api_key(self, user_email: str, service: str) -> Optional[str]:
        """Get the active API key for a specific service"""
        try:
            response = self._client.table('api_keys').select('api_key').eq('user_email', user_email).eq('service', service).eq('is_active', True).limit(1).execute()
            
            if response.data:
                return response.data[0]['api_key']
            return None
        except Exception as e:
            print(f"Error getting active API key: {e}")
            return None
    
    def get_active_api_key_info(self, user_email: str, service: str) -> Optional[Dict]:
        """Get the active API key info (including ID) for a specific service"""
        try:
            response = self._client.table('api_keys').select('*').eq('user_email', user_email).eq('service', service).eq('is_active', True).limit(1).execute()
            
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error getting active API key info: {e}")
            return None
    
    def set_single_active_key(self, api_id: int, user_email: str) -> bool:
        """Set a single key as active and deactivate all others for the user"""
        try:
            # First, deactivate all keys for the user
            self._client.table('api_keys').update({'is_active': False}).eq('user_email', user_email).execute()
            
            # Then activate the selected key
            response = self._client.table('api_keys').update({'is_active': True}).eq('id', api_id).eq('user_email', user_email).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error setting active API key: {e}")
            return False
    
    def enable_api_key(self, api_id: int, user_email: str) -> bool:
        """Enable an API key by ID"""
        try:
            response = self._client.table('api_keys').update({'is_active': True}).eq('id', api_id).eq('user_email', user_email).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error enabling API key: {e}")
            return False
    
    def disable_api_key(self, api_id: int, user_email: str) -> bool:
        """Disable an API key by ID"""
        try:
            response = self._client.table('api_keys').update({'is_active': False}).eq('id', api_id).eq('user_email', user_email).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error disabling API key: {e}")
            return False
    
    def get_api_key_by_name(self, key_name: str, user_email: str = None) -> Optional[Dict]:
        """Get API key by name (this is now the primary method)"""
        try:
            query = self._client.table('api_keys').select('*').eq('key_name', key_name)
            if user_email:
                query = query.eq('user_email', user_email)
            
            response = query.execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Error getting API key by name: {e}")
            return None
        
    def select_api_key_by_name(self, key_name: str, user_email: str) -> bool:
        """Select an API key by its name (primary identifier)"""
        try:
            # First, deactivate all keys for the user
            self._client.table('api_keys').update({'is_active': False}).eq('user_email', user_email).execute()
            
            # Then activate the selected key by name
            response = self._client.table('api_keys').update({'is_active': True}).eq('key_name', key_name).eq('user_email', user_email).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error selecting API key by name: {e}")
            return False
    
    def delete_api_key_by_name(self, key_name: str, user_email: str) -> bool:
        """Delete an API key by name (primary identifier)"""
        try:
            response = self._client.table('api_keys').delete().eq('key_name', key_name).eq('user_email', user_email).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting API key by name: {e}")
            return False
        
    def increment_api_key_usage_by_name(self, key_name: str, user_email: str) -> bool:
        """Increment usage counter for an API key by name"""
        try:
            # Get current usage count
            current = self._client.table('api_keys').select('usage_count').eq('key_name', key_name).eq('user_email', user_email).execute()
            
            if current.data:
                new_count = (current.data[0].get('usage_count', 0) or 0) + 1
                response = self._client.table('api_keys').update({
                    'usage_count': new_count,
                    'last_used': datetime.utcnow().isoformat()
                }).eq('key_name', key_name).eq('user_email', user_email).execute()
                
                return len(response.data) > 0
            
            return False
        except Exception as e:
            print(f"Error incrementing API key usage: {e}")
            return False
    
    def increment_api_key_usage(self, api_id: int) -> bool:
        """Increment usage counter for an API key by ID"""
        try:
            # Get current usage count
            current = self._client.table('api_keys').select('usage_count').eq('id', api_id).execute()
            
            if current.data:
                new_count = (current.data[0].get('usage_count', 0) or 0) + 1
                response = self._client.table('api_keys').update({
                    'usage_count': new_count,
                    'last_used': datetime.utcnow().isoformat()
                }).eq('id', api_id).execute()
                
                return len(response.data) > 0
            
            return False
        except Exception as e:
            print(f"Error incrementing API key usage: {e}")
            return False
    
    def get_api_key_stats(self, user_email: str = None) -> Dict:
        """Get comprehensive API key statistics"""
        try:
            # Build query
            query = self._client.table('api_keys').select('*')
            if user_email:
                query = query.eq('user_email', user_email)
            
            response = query.execute()
            keys = response.data
            
            # Calculate statistics
            total_keys = len(keys)
            active_keys = len([k for k in keys if k.get('is_active', False)])
            total_usage = sum(k.get('usage_count', 0) or 0 for k in keys)
            
            # Group by service
            service_breakdown = {}
            for key in keys:
                service = key.get('service', 'unknown')
                if service not in service_breakdown:
                    service_breakdown[service] = 0
                service_breakdown[service] += 1
            
            # Get ID ranges for user's keys
            user_key_ids = [k['id'] for k in keys]
            min_id = min(user_key_ids) if user_key_ids else 0
            max_id = max(user_key_ids) if user_key_ids else 0
            
            return {
                'total_keys': total_keys,
                'active_keys': active_keys,
                'inactive_keys': total_keys - active_keys,
                'total_usage': total_usage,
                'service_breakdown': service_breakdown,
                'id_range': {'min': min_id, 'max': max_id},
                'keys': keys
            }
        except Exception as e:
            print(f"Error getting API key stats: {e}")
            return {
                'total_keys': 0,
                'active_keys': 0,
                'inactive_keys': 0,
                'total_usage': 0,
                'service_breakdown': {},
                'id_range': {'min': 0, 'max': 0},
                'keys': []
            }
    
    # ===== ENHANCED USAGE TRACKING WITH API ID =====
    def log_api_request_by_name(self, user_email: str, service: str, endpoint: str, 
                           request_data: Dict = None, response_data: Dict = None, 
                           status_code: int = 200, processing_time: float = 0,
                           api_key_name: str = None) -> Dict:
        """Log API request using key_name as identifier"""
        try:
            # Get the key ID from the name if provided
            api_key_id = None
            if api_key_name:
                key_obj = self.get_api_key_by_name(api_key_name, user_email)
                if key_obj:
                    api_key_id = key_obj['id']
            
            data = {
                'user_email': user_email,
                'service': service,
                'endpoint': endpoint,
                'request_data': json.dumps(request_data) if request_data else None,
                'response_data': json.dumps(response_data) if response_data else None,
                'status_code': status_code,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat(),
                'api_key_name': api_key_name,  # Store the key name
                'api_key_id': api_key_id  # Also store the ID
            }
            
            response = self._client.table('api_requests').insert(data).execute()
            
            # Increment usage by name
            if api_key_name:
                self.increment_api_key_usage_by_name(api_key_name, user_email)
            
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error logging API request: {e}")
            return {}
        
    
    def log_api_request(self, user_email: str, service: str, endpoint: str, 
                       request_data: Dict = None, response_data: Dict = None, 
                       status_code: int = 200, processing_time: float = 0,
                       api_key_id: int = None) -> Dict:
        """Enhanced API request logging with key ID tracking"""
        try:
            data = {
                'user_email': user_email,
                'service': service,
                'endpoint': endpoint,
                'request_data': json.dumps(request_data) if request_data else None,
                'response_data': json.dumps(response_data) if response_data else None,
                'status_code': status_code,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat(),
                'api_key_id': api_key_id  # Track which key ID was used
            }
            
            response = self._client.table('api_requests').insert(data).execute()
            
            # Also increment the key usage counter if key_id provided
            if api_key_id:
                self.increment_api_key_usage(api_key_id)
            
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error logging API request: {e}")
            return {}
    
    def get_user_usage_stats(self, user_email: str, days: int = 30) -> Dict:
        """Enhanced usage statistics with API ID breakdown"""
        try:
            # Get request count and service breakdown
            response = self._client.table('api_requests').select('service, status_code, api_key_id').eq('user_email', user_email).execute()
            
            requests = response.data
            total_requests = len(requests)
            
            # Service breakdown
            service_stats = {}
            status_stats = {}
            key_usage = {}
            
            for req in requests:
                service = req['service']
                status = req['status_code']
                key_id = req.get('api_key_id')
                
                service_stats[service] = service_stats.get(service, 0) + 1
                status_stats[status] = status_stats.get(status, 0) + 1
                
                if key_id:
                    key_usage[key_id] = key_usage.get(key_id, 0) + 1
            
            # Get key names for the usage breakdown
            key_usage_with_names = {}
            for key_id, usage_count in key_usage.items():
                key_obj = self.get_api_key_by_id(key_id, user_email)
                key_name = key_obj['key_name'] if key_obj else f"DELETED_KEY_{key_id}"
                key_usage_with_names[f"{key_name} (ID: {key_id})"] = usage_count
            
            return {
                'total_requests': total_requests,
                'service_breakdown': service_stats,
                'status_breakdown': status_stats,
                'key_usage_breakdown': key_usage_with_names,
                'key_id_usage': key_usage  # Raw ID usage for programmatic access
            }
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return {}
    
    # ===== USER MANAGEMENT (Enhanced) =====
    
    def create_or_update_user(self, email: str, name: str = None) -> Dict:
        """Create or update user profile"""
        try:
            # Check if user exists
            existing = self._client.table('users').select('*').eq('email', email).execute()
            
            if existing.data:
                # Update existing user
                updates = {'last_login': datetime.utcnow().isoformat()}
                if name:
                    updates['name'] = name
                
                response = self._client.table('users').update(updates).eq('email', email).execute()
                return response.data[0] if response.data else {}
            else:
                # Create new user
                data = {
                    'email': email,
                    'name': name or email.split('@')[0],
                    'created_at': datetime.utcnow().isoformat(),
                    'last_login': datetime.utcnow().isoformat()
                }
                
                response = self._client.table('users').insert(data).execute()
                return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return {}
    
    def get_user_profile(self, email: str) -> Dict:
        """Get user profile"""
        try:
            response = self._client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {}
    
    # ===== UTILITY METHODS FOR API ID SYSTEM =====
    
    def get_next_available_id_info(self, user_email: str) -> Dict:
        """Get information about the next available ID for key naming"""
        try:
            user_keys = self.get_user_api_keys(user_email)
            used_ids = [key['id'] for key in user_keys]
            
            # For display purposes, show what the next key name would be
            max_id = max(used_ids) if used_ids else 0
            next_suggested_name = f"SURFE_API_KEY_{max_id + 1}"  # This is just a preview
            
            return {
                'used_ids': used_ids,
                'total_keys': len(used_ids),
                'next_suggested_name': next_suggested_name,
                'note': 'Actual ID will be assigned by database on creation'
            }
        except Exception as e:
            print(f"Error getting next available ID info: {e}")
            return {}
        
    def set_password_reset_token(self, email: str, token: str, expires: datetime) -> bool:
        """Set password reset token for user"""
        try:
            response = self._client.table('users').update({
                'reset_token': token,
                'reset_token_expires': expires.isoformat()
            }).eq('email', email).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error setting reset token: {e}")
            return False

    def verify_reset_token(self, email: str, token: str) -> bool:
        """Verify password reset token"""
        try:
            response = self._client.table('users').select('reset_token, reset_token_expires').eq('email', email).execute()
            
            if not response.data:
                return False
            
            user = response.data[0]
            stored_token = user.get('reset_token')
            expires_str = user.get('reset_token_expires')
            
            if not stored_token or stored_token != token:
                return False
            
            if expires_str:
                expires = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                if datetime.utcnow() > expires:
                    return False
            
            return True
        except Exception as e:
            print(f"Error verifying reset token: {e}")
            return False

    def update_user_password(self, email: str, password_hash: str) -> bool:
        """Update user password"""
        try:
            response = self._client.table('users').update({
                'password_hash': password_hash,
                'reset_token': None,  # Clear reset token
                'reset_token_expires': None,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('email', email).execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating password: {e}")
            return False

# Global instance
supabase_client = SupabaseClient()