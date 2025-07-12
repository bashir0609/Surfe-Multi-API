import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Surfe API Configuration - This is the only part we need.
SURFE_API_BASE_URL = "https://api.surfe.com"

# The SURFE_API_KEYS loading logic is now handled exclusively by the SimpleAPIManager
# to ensure a single source of truth. We remove the old load_api_keys() function.
logger.info("Configuration loaded. API key management is delegated to the API Manager.")