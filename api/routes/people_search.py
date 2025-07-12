import json
import logging
from flask import request, jsonify
from utils.supabase_api_client import supabase_api_manager
from core.dependencies import validate_request_data
from core.user_context import set_user_context

logger = logging.getLogger(__name__)


@set_user_context
def search_people_v1():
    """
    Search for people using v1 format, which is converted to v2 format
    before being sent to the Surfe API.
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Convert v1 format to v2 format
        v2_data = _convert_v1_to_v2_dict(request_data)
        logger.info(f"🔄 Converting v1 request to v2: {v2_data}")

        # Make request using the synchronous client
        result = supabase_api_manager.make_request(
            method="POST", endpoint="/v2/people/search", json_data=v2_data
        )

        if "error" in result:
            error_detail = result.get(
                "details", result.get("error", "An unknown API error occurred.")
            )
            return jsonify({"error": error_detail}), 500

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"❌ Error in v1 people search endpoint: {str(e)}")
        return jsonify({"error": "An internal server error occurred."}), 500


def _convert_v1_to_v2_dict(v1_data: dict) -> dict:
    """Helper function to convert v1 request format to v2 format."""
    v2_data = {
        "companies": {},
        "people": {},
        "limit": v1_data.get("limit", 10),
        "peoplePerCompany": v1_data.get("people_per_company", 1),
        "pageToken": "",
    }
    filters = v1_data.get("filters", {})

    # Map v1 filters to the nested v2 structure
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


@set_user_context
def search_people_v2():
    """
    Search for people using Surfe API v2, with server-side pagination
    to fetch all results up to the specified limit.
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        if not validate_request_data(request_data):
            return (
                jsonify(
                    {
                        "error": "Invalid request: at least one company or people filter must be provided."
                    }
                ),
                400,
            )

        logger.info(f"🔍 Starting paginated people search for request: {request_data}")

        all_people = _fetch_all_people_paginated(request_data)

        logger.info(f"✅ People Search v2 Success: Found {len(all_people)} people.")
        return jsonify({"success": True, "data": {"people": all_people}})

    except Exception as e:
        logger.error(f"❌ Unexpected error in people search v2: {str(e)}")
        return jsonify({"error": "An unexpected server error occurred."}), 500


def _fetch_all_people_paginated(payload: dict) -> list:
    """
    Handles paginated fetching from the Surfe API to collect all people
    up to the desired limit.
    """
    all_people = []
    page_token = ""
    page_count = 0
    max_pages = 25  # Safety break to prevent accidental infinite loops

    desired_limit = payload.get("limit", 10)
    # Make a shallow copy of payload to avoid mutating the original dict
    payload_copy = dict(payload)

    while page_count < max_pages:
        payload_copy["pageToken"] = page_token
        remaining_needed = desired_limit - len(all_people)

        if remaining_needed <= 0:
            break  # We have enough results

        result = supabase_api_manager.make_request(
            method="POST", endpoint="/v2/people/search", json_data=payload_copy
        )

        if "error" in result:
            logger.error(f"❌ Surfe API Error during pagination: {result.get('error')}")
            break  # Stop on API error

        people = result.get("people", [])
        if not people:
            break  # Stop if no more people are returned

        # Add only the people needed to reach the desired limit
        people_to_add = people[:remaining_needed]
        all_people.extend(people_to_add)

        page_token = result.get("nextPageToken")
        if not page_token:
            break  # Stop if the API indicates there are no more pages

        page_count += 1

    return all_people
