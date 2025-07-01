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
    
    async def make_request_async(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make async request to Surfe API with selected key"""
        
        # Get the selected API key
        api_key = simple_api_manager.get_selected_key()
        if not api_key:
            raise Exception("No API key selected or available")
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SurfeMultiAPI/1.0"
        }
        
        logger.info(f"Making {method} request to {endpoint}")
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    params=params,
                    headers=headers
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status in [200, 201]:
                        try:
                            result = await response.json()
                            logger.info(f"Successful request to {endpoint}")
                            return result
                        except Exception as json_error:
                            logger.error(f"JSON parsing error: {json_error}")
                            return {"error": "Invalid JSON response", "raw_response": response_text}
                    
                    elif response.status == 401:
                        logger.error(f"Authentication failed for {endpoint}")
                        raise Exception("Invalid API key or authentication failed")
                    
                    elif response.status == 429:
                        logger.error(f"Rate limit exceeded for {endpoint}")
                        raise Exception("Rate limit exceeded")
                    
                    else:
                        logger.error(f"HTTP {response.status} error for {endpoint}: {response_text}")
                        raise Exception(f"HTTP {response.status}: {response_text}")
                        
        except asyncio.TimeoutError:
            logger.error(f"Request timeout for {endpoint}")
            raise Exception("Request timeout")
        except Exception as e:
            logger.error(f"Request failed for {endpoint}: {str(e)}")
            raise
    
    def make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Synchronous wrapper for async request"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.make_request_async(method, endpoint, json_data, params, timeout)
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