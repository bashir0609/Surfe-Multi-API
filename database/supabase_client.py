import os
from supabase import create_client, Client
from typing import List, Dict, Optional
import json
from datetime import datetime

class SupabaseClient:
    def __init__(self):
        """Initialize Supabase client with environment variables"""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY environment variables required")
        
        self.client: Client = create_client(self.url, self.key)
    
    # ===== API KEYS MANAGEMENT =====
    
    def get_user_api_keys(self, user_email: str) -> List[Dict]:
        """Get all API keys for a user"""
        try:
            response = self.client.table('api_keys').select('*').eq('user_email', user_email).execute()
            return response.data
        except Exception as e:
            print(f"Error getting API keys: {e}")
            return []
    
    def add_api_key(self, user_email: str, service: str, api_key: str, key_name: str = None) -> Dict:
        """Add a new API key for a user"""
        try:
            data = {
                'user_email': user_email,
                'service': service,
                'api_key': api_key,
                'key_name': key_name or f"{service} Key",
                'created_at': datetime.utcnow().isoformat(),
                'is_active': True
            }
            
            response = self.client.table('api_keys').insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error adding API key: {e}")
            return {}
    
    def update_api_key(self, key_id: int, updates: Dict) -> Dict:
        """Update an existing API key"""
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            response = self.client.table('api_keys').update(updates).eq('id', key_id).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error updating API key: {e}")
            return {}
    
    def delete_api_key(self, key_id: int, user_email: str) -> bool:
        """Delete an API key (only if it belongs to the user)"""
        try:
            response = self.client.table('api_keys').delete().eq('id', key_id).eq('user_email', user_email).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error deleting API key: {e}")
            return False
    
    def get_active_api_key(self, user_email: str, service: str) -> Optional[str]:
        """Get the active API key for a specific service"""
        try:
            response = self.client.table('api_keys').select('api_key').eq('user_email', user_email).eq('service', service).eq('is_active', True).limit(1).execute()
            
            if response.data:
                return response.data[0]['api_key']
            return None
        except Exception as e:
            print(f"Error getting active API key: {e}")
            return None
    
    # ===== USAGE TRACKING =====
    
    def log_api_request(self, user_email: str, service: str, endpoint: str, 
                       request_data: Dict = None, response_data: Dict = None, 
                       status_code: int = 200, processing_time: float = 0) -> Dict:
        """Log an API request"""
        try:
            data = {
                'user_email': user_email,
                'service': service,
                'endpoint': endpoint,
                'request_data': json.dumps(request_data) if request_data else None,
                'response_data': json.dumps(response_data) if response_data else None,
                'status_code': status_code,
                'processing_time': processing_time,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = self.client.table('api_requests').insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error logging API request: {e}")
            return {}
    
    def get_user_usage_stats(self, user_email: str, days: int = 30) -> Dict:
        """Get usage statistics for a user"""
        try:
            # Get request count and service breakdown
            response = self.client.table('api_requests').select('service, status_code').eq('user_email', user_email).execute()
            
            requests = response.data
            total_requests = len(requests)
            
            # Service breakdown
            service_stats = {}
            status_stats = {}
            
            for req in requests:
                service = req['service']
                status = req['status_code']
                
                service_stats[service] = service_stats.get(service, 0) + 1
                status_stats[status] = status_stats.get(status, 0) + 1
            
            return {
                'total_requests': total_requests,
                'service_breakdown': service_stats,
                'status_breakdown': status_stats
            }
        except Exception as e:
            print(f"Error getting usage stats: {e}")
            return {}
    
    # ===== USER MANAGEMENT =====
    
    def create_or_update_user(self, email: str, name: str = None) -> Dict:
        """Create or update user profile"""
        try:
            # Check if user exists
            existing = self.client.table('users').select('*').eq('email', email).execute()
            
            if existing.data:
                # Update existing user
                updates = {'last_login': datetime.utcnow().isoformat()}
                if name:
                    updates['name'] = name
                
                response = self.client.table('users').update(updates).eq('email', email).execute()
                return response.data[0] if response.data else {}
            else:
                # Create new user
                data = {
                    'email': email,
                    'name': name or email.split('@')[0],
                    'created_at': datetime.utcnow().isoformat(),
                    'last_login': datetime.utcnow().isoformat()
                }
                
                response = self.client.table('users').insert(data).execute()
                return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error creating/updating user: {e}")
            return {}
    
    def get_user_profile(self, email: str) -> Dict:
        """Get user profile"""
        try:
            response = self.client.table('users').select('*').eq('email', email).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {}

# Global instance
supabase_client = SupabaseClient()