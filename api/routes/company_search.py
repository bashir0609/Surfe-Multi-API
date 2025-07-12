import logging
from flask import request, jsonify
from utils.supabase_api_client import supabase_surfe_client
from core.user_context import set_user_context, get_current_user_email, require_user_context

logger = logging.getLogger(__name__)


@require_user_context
def search_companies():
    """
    Search for companies using Surfe API v2 structure with rotation system and paginated fetching.
    """
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        # --- CORRECTION ---
        # Add validation to ensure at least one filter is provided.
        # Many APIs reject requests with no filters to prevent overly broad searches.
        filters = request_data.get("filters")
        if not filters:  # This checks for None or an empty dictionary {}
            logger.warning("Empty search request received. No filters applied.")
            return (
                jsonify({"error": "Please apply at least one search filter to begin."}),
                400,
            )

        logger.info(f"🔍 Company Search Request: {request_data}")

        # Call the paginated fetch function only if filters are present
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
    user_email = get_current_user_email()
    all_companies = []
    page_token = payload.get("pageToken", "")
    desired_total_limit = payload.get("limit", 10)

    # Make a shallow copy of the payload. It's crucial to remove parameters
    # that are for our internal logic, not for the Surfe API.
    payload_copy = dict(payload)
    if "limit" in payload_copy:
        del payload_copy["limit"]
    if "pageToken" in payload_copy:
        del payload_copy["pageToken"]

    # Loop until we have enough companies or the API runs out of results.
    while len(all_companies) < desired_total_limit:
        payload_copy["pageToken"] = page_token

        # Calculate how many more results we need for the next API call.
        remaining_needed = desired_total_limit - len(all_companies)

        # Use the 'limit' parameter for the page size, which is what the Surfe API
        # likely expects. We cap it at a reasonable max (e.g., 100).
        payload_copy["limit"] = min(remaining_needed, 100)

        # Use the existing client wrapper to make the API request
        result = supabase_surfe_client.make_request(
            method="POST", 
            endpoint="/v2/companies/search", 
            json_data=payload_copy,
            user_email=user_email  # Add this parameter
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
    return all_companies[:desired_total_limit]
