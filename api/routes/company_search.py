import logging
import asyncio
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client

logger = logging.getLogger(__name__)

def search_companies():
    """
    Search for companies using Surfe API with rotation system
    """
    try:
        # Get JSON data from request
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON data provided"}), 400

        logger.info(f"🔍 Company Search Request: {request_data}")

        # Make request using synchronous wrapper to Surfe v2 API
        result = simple_surfe_client.make_request(
            method="POST",
            endpoint="/v2/companies/search",
            json_data=request_data
        )

        if "error" in result:
            error_detail = result.get("details", result.get("error", "An unknown API error occurred."))
            logger.error(f"❌ Surfe API Error: {error_detail}")
            return jsonify({"error": error_detail}), 500

        logger.info(f"✅ Company Search Success: Found {len(result.get('companies', []))} companies")
        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"❌ Unexpected error in company search: {str(e)}")
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500
