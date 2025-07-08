import logging
import io
import pandas as pd
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client
# Assuming you have your Supabase manager available for logging
from config.simple_api_manager import api_manager
from datetime import datetime
import time

logger = logging.getLogger(__name__)

def _validate_enrichment_request(data):
    """
    A helper function to validate the enrichment request data.
    Consolidates validation logic for both single and bulk endpoints.
    """
    if not data:
        return {"error": "Request body is required"}, 400

    if 'people' not in data or not isinstance(data['people'], list):
        return {"error": "The 'people' array is required."}, 400

    people_array = data['people']
    if not 1 <= len(people_array) <= 10000:
        return {"error": "The 'people' array must contain between 1 and 10,000 items."}, 400

    # Validate include configuration, setting a default if not present
    if 'include' not in data:
        data['include'] = {'email': True, 'mobile': True, 'linkedInUrl': False}
    
    include_config = data['include']
    if not any(include_config.values()):
        return {"error": "At least one field in the 'include' configuration must be true."}, 400

    # Validate each person in the array
    for i, person in enumerate(people_array, 1):
        if not (person.get('firstName') or person.get('lastName') or person.get('linkedinUrl')):
            return {"error": f"Person {i}: Must provide at least firstName/lastName or linkedinUrl."}, 400
        
        field_limits = {'companyDomain': 2000, 'companyName': 2000, 'linkedinUrl': 2000}
        for field, max_length in field_limits.items():
            if len(str(person.get(field, ''))) > max_length:
                return {"error": f"Person {i}: {field} exceeds max length of {max_length} characters."}, 400

    return None, None # No error

def _handle_enrichment_exception(e, endpoint):
    """
    A helper function to handle exceptions and return appropriate JSON responses.
    """
    error_msg = str(e).lower()
    logger.error(f"Enrichment failed at {endpoint}: {error_msg}")

    if "no api key selected" in error_msg:
        code, response = 401, {"error": "Configuration Error", "details": "No API key is selected."}
    elif "feature_not_available" in error_msg:
        code, response = 403, {"error": "Feature Not Available", "details": "This feature is not available in your current plan."}
    elif "no mobile credits left" in error_msg:
        code, response = 402, {"error": "Insufficient Credits", "details": "No mobile credits left for this request."}
    elif "quota" in error_msg or "rate limit" in error_msg:
        code, response = 429, {"error": "API Limit Reached", "details": "Quota or rate limit exceeded."}
    else:
        code, response = 500, {"error": "An unexpected server error occurred.", "details": str(e)}

    # Logging is now handled by the @log_api_usage decorator in app.py
    return jsonify(response), code

def enrich_people():
    """Enrich a list of people provided in a JSON body."""
    try:
        data = request.get_json()
        error, status_code = _validate_enrichment_request(data)
        if error:
            return jsonify(error), status_code

        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/people/enrich',
            json_data=data
        )

        return jsonify({"success": True, "data": response_data})

    except Exception as e:
        return _handle_enrichment_exception(e, '/v2/people/enrich')

def enrich_people_bulk():
    """Bulk enrich people from a JSON body or a CSV file."""
    try:
        if 'file' in request.files:
            file = request.files['file']
            if not file or not file.filename.endswith('.csv'):
                return jsonify({"error": "A valid .csv file is required."}), 400
            
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            df = pd.read_csv(stream)
            
            # Convert DataFrame to list of dictionaries
            people_data = df.rename(columns={
                'first_name': 'firstName',
                'last_name': 'lastName',
                'company_name': 'companyName',
                'company_domain': 'companyDomain',
                'linkedin_url': 'linkedinUrl'
            }).to_dict('records')
            
            data = {"people": people_data}
        else:
            data = request.get_json()

        error, status_code = _validate_enrichment_request(data)
        if error:
            return jsonify(error), status_code

        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/people/enrich',
            json_data=data
        )

        return jsonify({"success": True, "data": response_data})

    except Exception as e:
        return _handle_enrichment_exception(e, '/v2/people/enrich/bulk')

def get_enrichment_status(enrichment_id: str):
    """Checks the status of a specific people enrichment job."""
    if not enrichment_id:
        return jsonify({"error": "Enrichment ID is required"}), 400

    try:
        result = simple_surfe_client.make_request(
            method="GET",
            endpoint=f"/v2/people/enrich/{enrichment_id}"
        )
        # A completed job has a 'people' array in the response
        status = "completed" if 'people' in result else "pending"
        return jsonify({"success": True, "status": status, "data": result})

    except Exception as e:
        logger.error(f"Failed to get enrichment status for ID {enrichment_id}: {e}")
        return jsonify({"success": False, "error": "Failed to retrieve job status.", "details": str(e)}), 500
