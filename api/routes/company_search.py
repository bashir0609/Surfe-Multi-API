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

        all_companies = fetch_all_companies_paginated(request_data)

        logger.info(f"✅ Company Search Success: Found {len(all_companies)} companies")
        return jsonify({"success": True, "data": {"companies": all_companies}})

    except Exception as e:
        logger.error(f"❌ Unexpected error in company search: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def fetch_all_companies_paginated(payload):
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
            
        # Use existing client wrapper
        result = simple_surfe_client.make_request(
            method="POST",
            endpoint="/v2/companies/search",
            json_data=payload_copy
        )
        
        if "error" in result:
            logger.error(f"❌ Surfe API Error: {result.get('error')}")
            break
            
        companies = result.get("companies", [])
        
        if not companies:
            break  # Stop if no companies returned
            
        # Add companies but don't exceed the desired limit
        companies_to_add = companies[:remaining_needed]
        all_companies.extend(companies_to_add)
        
        # If we've reached our desired limit, stop
        if len(all_companies) >= desired_limit:
            break
        
        page_token = result.get("nextPageToken")
        if not page_token:
            break  # Stop if no more pages
            
    return all_companies
