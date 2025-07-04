import logging
import asyncio
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client
from config.simple_api_manager import simple_api_manager 

logger = logging.getLogger(__name__)

def search_companies():
    """
    Search for companies using Surfe API v2 structure with rotation system and paginated fetching.
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        logger.info(f"🔍 Company Search Request: {request_data}")

        # Get the currently selected API key from your key manager
        api_key = simple_api_manager.get_selected_key()
        if not api_key:
            logger.error("No Surfe API key is selected or available!")
            return jsonify({"error": "No Surfe API key is configured. Please check your settings."}), 500

        all_companies = fetch_all_companies_paginated(api_key, request_data)

        logger.info(f"✅ Company Search Success: Found {len(all_companies)} companies")
        return jsonify({"success": True, "data": {"companies": all_companies}})

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Unexpected error in company search: {str(e)}")
        status_code = 500
        if "No API key selected" in error_msg:
            status_code = 400
        return jsonify({"success": False, "error": error_msg}), status_code

def fetch_all_companies_paginated(api_key, payload):
    import requests

    url = "https://api.surfe.com/v2/companies/search"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    all_companies = []
    page_token = ""
    
    # Get the desired limit from payload (default to 10 if not specified)
    desired_limit = payload.get("limit", 10)
    
    # Make a shallow copy of payload to avoid mutating the original dict
    payload_copy = dict(payload)
    
    while True:
        payload_copy["pageToken"] = page_token
        
        # Calculate how many more results we need
        remaining_needed = desired_limit - len(all_companies)
        
        # If we already have enough results, break
        if remaining_needed <= 0:
            break
            
        response = requests.post(url, headers=headers, json=payload_copy, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Error: {response.status_code} - {response.text}")
            break  # Stop if quota is reached or any error occurs
            
        data = response.json()
        companies = data.get("companies", [])
        
        if not companies:
            break  # Stop if no companies returned
            
        # Add companies but don't exceed the desired limit
        companies_to_add = companies[:remaining_needed]
        all_companies.extend(companies_to_add)
        
        # If we've reached our desired limit, stop
        if len(all_companies) >= desired_limit:
            break
        
        page_token = data.get("nextPageToken")
        if not page_token:
            break  # Stop if no more pages
            
    return all_companies
