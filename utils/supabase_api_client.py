# utils/supabase_api_client.py - Replace simple_api_client.py

"""
Supabase API Client
Uses API keys from Supabase database only, no environment variables
"""
import asyncio
import logging
import aiohttp
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from config.supabase_api_manager import supabase_api_manager
from database.supabase_client import supabase_client

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

class SupabaseSurfeClient:
    """Supabase-powered Surfe API client"""
    
    def __init__(self):
        self.base_url = "https://api.surfe.com"
        self.timeout = 30
        self.default_user_email = "system@localhost"  # Default system user

    async def make_request_async(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        selected_key: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make async request to Surfe API with Supabase-managed keys"""
        
        user_email = user_email or self.default_user_email

        # Get API key from Supabase
        if selected_key:
            # Try to get specific key by name
            api_key = supabase_api_manager.get_key_by_name(selected_key, user_email)
            if not api_key:
                logger.warning(f"Selected key '{selected_key}' not found for user {user_email}, using active key")
                api_key = supabase_api_manager.get_selected_key(user_email)
        else:
            # Get the currently active key
            api_key = supabase_api_manager.get_selected_key(user_email)

        if not api_key:
            raise ValueError(f"No API key available for user: {user_email}")

        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": api_key if api_key.startswith("Bearer ") else f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SurfeMultiAPI/2.0-Supabase"
        }

        method = method.upper()
        logger.info(f"Making {method} request to {endpoint} for user: {user_email}")
        
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

                    # Log API usage to Supabase
                    try:
                        supabase_client.log_api_request(
                            user_email=user_email,
                            service='surfe',
                            endpoint=endpoint,
                            request_data=json_data or {},
                            status_code=response.status,
                            processing_time=0  # Could be calculated if needed
                        )
                    except Exception as log_error:
                        logger.warning(f"Failed to log API request: {log_error}")

                    # Handle successful responses
                    if response.status in [200, 201, 202]:
                        try:
                            result = await response.json()
                            logger.info(f"Successful {method} request to {endpoint} for user: {user_email}")
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
                        logger.error(f"Authentication failed for {endpoint} with user: {user_email}")
                        raise ValueError("Invalid API key or authentication failed")
                    
                    elif response.status == 429:
                        logger.error(f"Rate limit exceeded for {endpoint}")
                        raise Exception("Rate limit exceeded")
                    
                    elif response.status == 404:
                        logger.error(f"Endpoint not found: {endpoint}")
                        raise ValueError(f"Endpoint not found: {endpoint}")
                    
                    elif response.status >= 500:
                        logger.error(f"Server error {response.status} for {endpoint}: {response_text}")
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
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.make_request_async(method, endpoint, json_data, params, timeout, selected_key, user_email)
            )
        finally:
            loop.close()
    
    def get_client_stats(self, user_email: Optional[str] = None) -> Dict[str, Any]:
        """Get client statistics from Supabase"""
        user_email = user_email or self.default_user_email
        
        return {
            "api_manager_stats": supabase_api_manager.get_stats(user_email),
            "base_url": self.base_url,
            "timeout": self.timeout,
            "user_email": user_email,
            "data_source": "supabase"
        }
    
    def sync_keys_from_database(self, user_email: Optional[str] = None):
        """Force sync API keys from Supabase database"""
        user_email = user_email or self.default_user_email
        supabase_api_manager.sync_from_database(user_email)
        logger.info(f"Synced API keys from Supabase for user: {user_email}")

# Global instance
supabase_surfe_client = SupabaseSurfeClient()