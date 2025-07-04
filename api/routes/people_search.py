import json
import logging
import asyncio
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client
from config.simple_api_manager import simple_api_manager # given by perplexity for pagination
from core.dependencies import validate_request_data

logger = logging.getLogger(__name__)
    
def search_people_v1():
    """
    Search for people using v1 format, converted to v2 with rotation
    """
    try:
        # Get JSON data from request
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Convert v1 format to v2 format
        v2_data = convert_v1_to_v2_dict(request_data)
        logger.info(f"🔄 Converting v1 to v2: {request_data} -> {v2_data}")

        # Make request using synchronous wrapper
        result = simple_surfe_client.make_request(
            method="POST",
            endpoint="/v2/people/search",
            json_data=v2_data
        )

        if "error" in result:
            error_detail = result.get("details", result.get("error", "An unknown API error occurred."))
            return jsonify({"error": error_detail}), 500

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"❌ Error in v1 people search: {str(e)}")
        return jsonify({"error": f"Error in v1 endpoint: {str(e)}"}), 500

def convert_v1_to_v2_dict(v1_data: dict) -> dict:
    """Convert v1 request format to v2 format"""
    v2_data = {
        "companies": {},
        "people": {},
        "limit": v1_data.get("limit", 10),
        "peoplePerCompany": v1_data.get("people_per_company", 1),
        "pageToken": ""
    }

    filters = v1_data.get("filters", {})

    # Map v1 filters to v2 structure
    if "industries" in filters:
        v2_data["companies"]["industries"] = filters["industries"]
    if "seniorities" in filters:
        v2_data["people"]["seniorities"] = filters["seniorities"]
    if "locations" in filters:
        v2_data["people"]["countries"] = filters["locations"]
    if "job_titles" in filters:
        v2_data["people"]["jobTitles"] = filters["job_titles"]
    if "departments" in filters:
        v2_data["people"]["departments"] = filters["departments"]
    if "company_domains" in filters:
        v2_data["companies"]["domains"] = filters["company_domains"]
    if "company_names" in filters:
        v2_data["companies"]["names"] = filters["company_names"]
    if "company_domains_excluded" in filters:
        v2_data["companies"]["domainsExcluded"] = filters["company_domains_excluded"]

    return v2_data

def search_people_v2():
    """
    Search for people using Surfe API v2 structure with rotation system and paginated fetching.
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        logger.info(f"🔍 People Search v2 Request: {request_data}")

        if not validate_request_data(request_data):
            return jsonify({
                "error": "At least one company or people filter must be provided"
            }), 400

        all_people = fetch_all_people_paginated(request_data)

        logger.info(f"✅ People Search v2 Success: Found {len(all_people)} people")
        return jsonify({"success": True, "data": {"people": all_people}})

    except Exception as e:
        logger.error(f"❌ Unexpected error in people search v2: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def fetch_all_people_paginated(payload):
    all_people = []
    page_token = ""
    
    # Get the desired limit from payload (default to 10 if not specified)
    desired_limit = payload.get("limit", 10)
    
    # Make a shallow copy of payload to avoid mutating the original dict
    payload_copy = dict(payload)
    
    while True:
        payload_copy["pageToken"] = page_token
        
        # Calculate how many more results we need
        remaining_needed = desired_limit - len(all_people)
        
        # If we already have enough results, break
        if remaining_needed <= 0:
            break
            
        # Use existing client wrapper
        result = simple_surfe_client.make_request(
            method="POST",
            endpoint="/v2/people/search",
            json_data=payload_copy
        )
        
        if "error" in result:
            logger.error(f"❌ Surfe API Error: {result.get('error')}")
            break
            
        people = result.get("people", [])
        
        if not people:
            break  # Stop if no people returned
            
        # Add people but don't exceed the desired limit
        people_to_add = people[:remaining_needed]
        all_people.extend(people_to_add)
        
        # If we've reached our desired limit, stop
        if len(all_people) >= desired_limit:
            break
        
        page_token = result.get("nextPageToken")
        if not page_token:
            break  # Stop if no more pages
            
    return all_people
