import json
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

        # Call the updated paginated fetch function
        all_companies = fetch_all_companies_paginated(request_data)

        logger.info(f"✅ Company Search Success: Found {len(all_companies)} companies")
        return jsonify({"success": True, "data": {"companies": all_companies}})

    except Exception as e:
        logger.error(f"❌ Unexpected error in company search: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def fetch_all_companies_paginated(payload):
    """
    Fetches companies from the Surfe API with proper pagination,
    respecting the requested limit and initial page token.
    """
    all_companies = []
    
    # --- CORRECTION ---
    # Use the pageToken from the initial payload if provided. This allows a search
    # to be resumed from a specific page. Default to an empty string to start from the beginning.
    page_token = payload.get("pageToken", "")
    
    # Get the desired limit from payload (default to 10 if not specified)
    desired_limit = payload.get("limit", 10)
    
    # Make a shallow copy of the payload. It's crucial to remove parameters
    # that are for our internal logic, not for the Surfe API.
    payload_copy = dict(payload)
    if 'limit' in payload_copy:
        del payload_copy['limit']
    # Also remove pageToken, as the loop will now manage it directly.
    if 'pageToken' in payload_copy:
        del payload_copy['pageToken']

    # Loop until we have enough companies or the API runs out of results.
    while len(all_companies) < desired_limit:
        # The loop now correctly uses the page_token, which was either
        # set from the initial payload or from the previous API response.
        payload_copy["pageToken"] = page_token
        
        # Calculate how many more results we need and tell the API how many to fetch.
        # Most APIs use a 'pageSize' parameter for this. This is more efficient
        # than fetching a full default page and discarding results.
        remaining_needed = desired_limit - len(all_companies)
        payload_copy["pageSize"] = min(remaining_needed, 100)

        # Use the existing client wrapper to make the API request
        result = simple_surfe_client.make_request(
            method="POST",
            endpoint="/v2/companies/search",
            json_data=payload_copy
        )
        
        # If the API returns an error, log it and stop fetching.
        if "error" in result:
            logger.error(f"❌ Surfe API Error: {result.get('error')}")
            break
            
        companies = result.get("companies", [])
        
        # If the API returns no companies, we've reached the end.
        if not companies:
            break
        
        # Add the fetched companies to our list
        all_companies.extend(companies)
        
        # Get the token for the next page
        page_token = result.get("nextPageToken")
        
        # If there's no next page token, we're done.
        if not page_token:
            break
            
    # As a final safeguard, trim the list to the exact desired limit.
    return all_companies[:desired_limit]
