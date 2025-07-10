"""
Simple Surfe API Client
Uses selected API key instead of rotation system
"""
import asyncio
import logging
import aiohttp
import re
from typing import Dict, Any, Optional, List
from urllib.parse import urlparse
from config.simple_api_manager import simple_api_manager

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

class SimpleSurfeClient:
    """Simple Surfe API client without rotation"""
    
    def __init__(self):
        self.base_url = "https://api.surfe.com"
        self.timeout = 30

    # In utils/simple_api_client.py

    async def make_request_async(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        selected_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make async request to Surfe API with selected key"""

        # Get API key
        if selected_key:
            api_key = simple_api_manager.get_key_by_name(selected_key)
            if not api_key:
                logger.warning(f"Selected key '{selected_key}' not found, using manager default")
                api_key = simple_api_manager.get_selected_key()
        else:
            api_key = simple_api_manager.get_selected_key()

        if not api_key:
            raise ValueError("No API key selected or available")

        # Prepare request
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
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
        selected_key: Optional[str] = None  # Add this parameter
    ) -> Dict[str, Any]:
        """Synchronous wrapper for async request"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.make_request_async(method, endpoint, json_data, params, timeout, selected_key)
            )
        finally:
            loop.close()
    
    def get_client_stats(self) -> Dict[str, Any]:
        """Get client statistics"""
        return {
            "api_manager_stats": simple_api_manager.get_stats(),
            "base_url": self.base_url,
            "timeout": self.timeout
        }

# Global instance
simple_surfe_client = SimpleSurfeClient()