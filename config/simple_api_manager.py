"""
Simple API Key Manager for Vercel Environment
Replaces the complex rotation system with simple key selection
"""
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ApiKey:
    """Simple API key representation"""
    name: str
    key: str
    enabled: bool = True
    selected: bool = False
    last_used: Optional[datetime] = None
    usage_count: int = 0

class SimpleApiManager:
    """Simple API key manager without rotation"""
    
    def __init__(self):
        self.keys: Dict[str, ApiKey] = {}
        self.selected_key: Optional[str] = None
        self.dynamic_keys: Dict[str, ApiKey] = {}  # Keys added dynamically via UI
        self.load_keys_from_env()
    
    def add_dynamic_key(self, key_name: str, api_key: str) -> bool:
        """Add a new API key dynamically via UI"""
        if key_name in self.keys or key_name in self.dynamic_keys:
            return False  # Key already exists
        
        dynamic_key = ApiKey(
            name=key_name,
            key=api_key,
            enabled=True,
            selected=len(self.keys) + len(self.dynamic_keys) == 0  # First key is selected
        )
        
        self.dynamic_keys[key_name] = dynamic_key
        self._update_combined_keys()
        
        if len(self.keys) == 1:  # First key added
            self.selected_key = key_name
            
        logger.info(f"Added dynamic API key: {key_name} (...{api_key[-10:]})")
        return True
    
    def remove_dynamic_key(self, key_name: str) -> bool:
        """Remove a dynamically added API key"""
        if key_name in self.dynamic_keys:
            del self.dynamic_keys[key_name]
            self._update_combined_keys()
            
            # If this was the selected key, select another
            if self.selected_key == key_name:
                self._select_first_enabled_key()
                
            logger.info(f"Removed dynamic API key: {key_name}")
            return True
        return False
    
    def _update_combined_keys(self):
        """Update the combined keys dict with both environment and dynamic keys"""
        self.keys.clear()
        # Add environment keys first
        env_keys = self._load_env_keys()
        self.keys.update(env_keys)
        # Add dynamic keys
        self.keys.update(self.dynamic_keys)

    def load_keys_from_env(self):
        """Load API keys from Vercel environment variables"""
        env_keys = self._load_env_keys()
        self.keys.clear()
        if env_keys:
            self.keys.update(env_keys)
        if self.dynamic_keys:
            self.keys.update(self.dynamic_keys)  # Keep dynamic keys
        
        if self.selected_key and self.selected_key not in self.keys:
            self.selected_key = None
        
        if not self.selected_key:
            self._select_first_enabled_key()
    
    def _load_env_keys(self) -> Dict[str, ApiKey]:
        """Load environment keys and return them"""
        env_keys = {}
        
        # Common environment variable patterns for Surfe API keys
        env_patterns = [
            'SURFE_API_KEY',
            'SURFE_API_KEY_1',
            'SURFE_API_KEY_2', 
            'SURFE_API_KEY_3',
            'SURFE_API_KEY_4',
            'SURFE_API_KEY_5',
            'SURFE_API_KEY_6',
            'SURFE_API_KEY_7',
            'SURFE_API_KEY_8',
            'SURFE_API_KEY_9',
            'SURFE_API_KEY_10',
            'SURFE_KEY_1',
            'SURFE_KEY_2',
            'SURFE_KEY_3',
            'API_KEY_SURFE',
            'SURFE_TOKEN'
        ]
        
        keys_found = 0
        for pattern in env_patterns:
            key_value = os.environ.get(pattern)
            if key_value and key_value.strip():
                key_name = pattern
                api_key = ApiKey(
                    name=key_name,
                    key=key_value.strip(),
                    enabled=True,
                    selected=(keys_found == 0)  # First key is selected by default
                )
                env_keys[key_name] = api_key
                keys_found += 1
                logger.info(f"Loaded API key: {key_name} (...{key_value[-10:]})")
        
        if keys_found == 0:
            logger.warning("No Surfe API keys found in environment variables")
        else:
            logger.info(f"Loaded {keys_found} API keys from environment")
        
        return env_keys
    
    def get_selected_key(self) -> Optional[str]:
        """Get the currently selected API key"""
        if self.selected_key and self.selected_key in self.keys:
            key_obj = self.keys[self.selected_key]
            if key_obj.enabled:
                # Update usage statistics
                key_obj.last_used = datetime.utcnow()
                key_obj.usage_count += 1
                return key_obj.key
        return None
    
    def select_key(self, key_name: str) -> bool:
        """Select a specific API key"""
        if key_name in self.keys and self.keys[key_name].enabled:
            # Deselect all other keys
            for key in self.keys.values():
                key.selected = False
            
            # Select the specified key
            self.keys[key_name].selected = True
            self.selected_key = key_name
            logger.info(f"Selected API key: {key_name}")
            return True
        return False
    
    def enable_key(self, key_name: str) -> bool:
        """Enable a specific API key"""
        if key_name in self.keys:
            self.keys[key_name].enabled = True
            logger.info(f"Enabled API key: {key_name}")
            return True
        return False
    
    def disable_key(self, key_name: str) -> bool:
        """Disable a specific API key"""
        if key_name in self.keys:
            self.keys[key_name].enabled = False
            # If this was the selected key, select another enabled key
            if self.selected_key == key_name:
                self._select_first_enabled_key()
            logger.info(f"Disabled API key: {key_name}")
            return True
        return False
    
    def _select_first_enabled_key(self):
        """Select the first enabled key as default"""
        for key_name, key_obj in self.keys.items():
            if key_obj.enabled:
                self.select_key(key_name)
                return
        self.selected_key = None
    
    def get_all_keys(self) -> List[Dict]:
        """Get all keys with their status"""
        return [
            {
                'name': key_obj.name,
                'key_suffix': key_obj.key[-10:] if len(key_obj.key) >= 5 else key_obj.key,
                'enabled': key_obj.enabled,
                'selected': key_obj.selected,
                'last_used': key_obj.last_used.isoformat() if key_obj.last_used else None,
                'usage_count': key_obj.usage_count
            }
            for key_obj in self.keys.values()
        ]
    
    def get_stats(self) -> Dict:
        """Get simple statistics"""
        total_keys = len(self.keys)
        enabled_keys = sum(1 for key in self.keys.values() if key.enabled)
        selected_key_name = self.selected_key
        
        # Calculate system health (percentage of enabled keys)
        system_health = (enabled_keys / total_keys * 100) if total_keys > 0 else 0
        
        return {
            'total_keys': total_keys,
            'enabled_keys': enabled_keys,
            'disabled_keys': total_keys - enabled_keys,
            'selected_key': selected_key_name,
            'has_valid_selection': bool(self.get_selected_key()),
            'system_health': system_health,
            'keys': self.get_all_keys()
        }

# Global instance
simple_api_manager = SimpleApiManager()