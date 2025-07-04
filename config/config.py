import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Surfe API Configuration
SURFE_API_BASE_URL = "https://api.surfe.com"

# API Key Configuration
def load_api_keys():
    """Load API keys from environment variables with multiple fallback methods"""
    keys_found = []
    
    # Method 1: Try numbered environment variables
    ENV_VAR_KEY_NAMES = [f"SURFE_API_KEY_{i}" for i in range(1, 11)]  # Check up to 10 keys
    for env_var_name in ENV_VAR_KEY_NAMES:
        api_key_value = os.getenv(env_var_name)
        if api_key_value and api_key_value.strip():
            keys_found.append(api_key_value.strip())
            logger.info(f"Loaded API key from {env_var_name}")
    
    # Method 2: Try single environment variable
    single_key = os.getenv("SURFE_API_KEY")
    if single_key and single_key.strip():
        keys_found.append(single_key.strip())
        logger.info("Loaded API key from SURFE_API_KEY")
    
    # Method 3: Try comma-separated list
    keys_list = os.getenv("SURFE_API_KEYS")
    if keys_list:
        for key in keys_list.split(','):
            key = key.strip()
            if key:
                keys_found.append(key)
        logger.info(f"Loaded {len(keys_list.split(','))} API keys from SURFE_API_KEYS")
    
    # Remove duplicates while preserving order
    unique_keys = []
    for key in keys_found:
        if key not in unique_keys:
            unique_keys.append(key)
    
    return unique_keys

# Load API keys on module import
SURFE_API_KEYS = load_api_keys()

if not SURFE_API_KEYS:
    logger.error(
        "ERROR: No Surfe API keys found. Please set environment variables: "
        "SURFE_API_KEY_1, SURFE_API_KEY_2, etc. or SURFE_API_KEY or SURFE_API_KEYS"
    )
    logger.error("Application will not function without valid API keys.")
    SURFE_API_KEYS = []
