"""
People Enrichment API Routes
Handles enriching people data with additional information using Surfe API
"""
import logging
import io
import pandas as pd
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client, clean_domain, is_valid_domain
from core.dependencies import validate_request_data
from models import db, ApiRequest
from datetime import datetime
import time

logger = logging.getLogger(__name__)

def get_selected_key_from_request():
    """Get selected key from request headers or body"""
    # Try header first
    selected_key = request.headers.get('X-Selected-Key')
    if selected_key:
        return selected_key.strip()
    
    # Try from JSON body
    request_data = request.get_json() or {}
    selected_key = request_data.get('_selectedKey')
    if selected_key:
        return selected_key.strip()
    
    return None

def validate_person_data(people_array):
    """
    Validate that each person has sufficient identifying information according to Surfe API v2 spec
    """
    for i, person in enumerate(people_array):
        # Check that each person has sufficient identifying data
        has_name = person.get('firstName', '').strip() or person.get('lastName', '').strip()
        has_linkedin = person.get('linkedinUrl', '').strip()
        
        # According to API spec, need at least name OR LinkedIn URL for person identification
        if not has_name and not has_linkedin:
            return {
                "error": f"Person {i+1}: Must provide at least firstName/lastName OR linkedinUrl for person identification"
            }
        
        # Validate string field lengths according to API spec
        field_limits = {
            'companyDomain': 2000,
            'companyName': 2000,
            'linkedinUrl': 2000
        }
        
        for field, max_length in field_limits.items():
            value = person.get(field, '')
            if value and len(str(value)) > max_length:
                return {
                    "error": f"Person {i+1}: {field} must be {max_length} characters or less"
                }
    
    return None  # No validation errors

def enrich_people():
    """
    Enrich people data using Surfe API with rotation system
    """
    start_time = time.time()
    api_key_used = None
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate request structure
        if not validate_request_data(data):
            return jsonify({"error": "Invalid request structure"}), 400
        
        # Check required fields for enrichment (Surfe API v2 structure)
        if not data.get('people'):
            return jsonify({
                "error": "The 'people' array is required for enrichment in Surfe API v2 format"
            }), 400
        
        # Validate include configuration (required by API v2)
        if 'include' not in data:
            data['include'] = {
                'email': True,
                'linkedInUrl': False,
                'mobile': True
            }
        
        # Validate that at least one field is included (required by API spec)
        include_config = data['include']
        if not any([include_config.get('email'), include_config.get('linkedInUrl'), include_config.get('mobile')]):
            return jsonify({
                "error": "At least one field must be included in the include configuration"
            }), 400
        
        # Validate people array size (1-10000 according to API spec)
        people_array = data.get('people', [])
        if len(people_array) == 0:
            return jsonify({
                "error": "At least one person is required in the people array"
            }), 400
        
        if len(people_array) > 10000:
            return jsonify({
                "error": "Maximum 10,000 people allowed per enrichment request"
            }), 400
        
        # Validate field lengths for each person
        for i, person in enumerate(people_array):
            # Validate string field lengths according to API spec
            field_limits = {
                'companyDomain': 2000,
                'companyName': 2000,
                'linkedinUrl': 2000
            }
            
            for field, max_length in field_limits.items():
                value = person.get(field, '')
                if value and len(str(value)) > max_length:
                    return jsonify({
                        "error": f"Person {i+1}: {field} must be {max_length} characters or less"
                    }), 400
        
        # Validate notificationOptions if provided
        if 'notificationOptions' in data:
            notification_options = data['notificationOptions']
            webhook_url = notification_options.get('webhookUrl', '')
            
            if webhook_url and not webhook_url.startswith(('http://', 'https://')):
                return jsonify({
                    "error": "Webhook URL must be a valid HTTP or HTTPS URL"
                }), 400
        
        people_count = len(data.get('people', []))
        include_config = data.get('include', {})
        logger.info(f"Processing people enrichment request with {people_count} people. "
                   f"Include config: email={include_config.get('email', False)}, "
                   f"linkedIn={include_config.get('linkedInUrl', False)}, "
                   f"mobile={include_config.get('mobile', False)}")
        
        # Get selected key from request
        selected_key = get_selected_key_from_request()

        # Make request through rotation system
        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/people/enrich',
            json_data=data,
            selected_key=selected_key  # Add this parameter
        )
        
        # Get the API key that was used (simplified system)
        stats = simple_surfe_client.get_client_stats()
        api_key_used = stats.get('selected_key', 'unknown')
        
        # Record successful request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
            api_request.status_code = 200
            api_request.response_time = time.time() - start_time
            api_request.success = True
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record API request: {db_error}")
        
        logger.info(f"People enrichment successful. Enriched {len(response_data.get('people', []))} people")
        
        return jsonify({
            "success": True,
            "data": response_data,
            "metadata": {
                "total_enriched": len(response_data.get('people', [])),
                "api_key_used": api_key_used[-10:] if api_key_used else None,
                "response_time": round(time.time() - start_time, 3)
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"People enrichment failed: {error_msg}")
        status_code_to_log = 500

        # Determine the correct error response and status code
    if "No API key selected" in error_msg:
        status_code_to_log = 400
        response = jsonify({
            "error": "Configuration Error",
            "details": "No Surfe API key is selected. Please go to the Settings page to select a key."
        }), status_code_to_log
        
    elif "feature_not_available" in error_msg.lower():
        status_code_to_log = 403
        response = jsonify({
            "error": "Feature Not Available",
            "details": "The 'LinkedIn enrichment' feature is not available in your current plan.",
            "code": "feature_not_available",
            "action": "Please contact api.support@surfe.com to upgrade."
        }), status_code_to_log

    elif "no mobile credits left" in error_msg.lower():
        status_code_to_log = 402 # Payment Required
        response = jsonify({
            "error": "Insufficient Credits",
            "details": "There are no mobile credits left to start an enrichment for this request."
        }), status_code_to_log

    elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
        status_code_to_log = 429
        response = jsonify({
            "error": "API quota exceeded. Please try again later.",
            "details": error_msg
        }), status_code_to_log

    elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
        status_code_to_log = 401
        response = jsonify({
            "error": "Authentication failed. Please check API configuration.",
            "details": error_msg
        }), status_code_to_log

    else:
        status_code_to_log = 500
        response = jsonify({
            "error": "An unexpected server error occurred.",
            "details": error_msg
        }), status_code_to_log
        
        # Record failed request
        try:
            db.session.rollback()
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
            status_code=status_code_to_log,
            api_request.response_time = time.time() - start_time
            api_request.success = False
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record failed API request: {db_error}")
    return response
        
        
def enrich_people_bulk():
    """
    Bulk enrich people data with CSV support using Surfe API v2 format
    """
    start_time = time.time()
    api_key_used = None
    
    try:
        # Handle file upload if present
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            if file and file.filename and file.filename.endswith('.csv'):
                # Read CSV file
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_input = pd.read_csv(stream)
                
                # Convert CSV to Surfe API v2 people array format
                people_data = []
                
                for _, row in csv_input.iterrows():
                    person = {
                        "firstName": row.get('first_name', ''),
                        "lastName": row.get('last_name', ''),
                        "companyName": row.get('company_name', row.get('company', '')),
                        "companyDomain": row.get('company_domain', ''),
                        "linkedinUrl": row.get('linkedin_url', ''),
                        "externalID": row.get('external_id', f"bulk-{len(people_data) + 1}")
                    }
                    # Only add if we have some identifying data
                    if any([person["firstName"], person["lastName"], person["linkedinUrl"]]):
                        people_data.append(person)
                
                # Create default include configuration
                data = {
                    "include": {
                        "email": True,
                        "linkedInUrl": True,
                        "mobile": True
                    },
                    "people": people_data
                }
            else:
                return jsonify({"error": "Only CSV files are supported"}), 400
        else:
            # Get JSON data in Surfe API v2 format
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
        
        # Apply the same validation as regular enrichment
        if 'people' not in data:
            return jsonify({
                "error": "The 'people' array is required for enrichment in Surfe API v2 format"
            }), 400
        
        # Validate include configuration (required by API v2)
        if 'include' not in data:
            data['include'] = {
                'email': True,
                'linkedInUrl': False,
                'mobile': True
            }
        
        # Validate that at least one field is included (required by API spec)
        include_config = data['include']
        if not any([include_config.get('email'), include_config.get('linkedInUrl'), include_config.get('mobile')]):
            return jsonify({
                "error": "At least one field must be included in the include configuration"
            }), 400
        
        # Validate people array size (1-10000 according to API spec)
        people_array = data.get('people', [])
        if len(people_array) == 0:
            return jsonify({
                "error": "At least one person is required in the people array"
            }), 400
        
        if len(people_array) > 10000:
            return jsonify({
                "error": "Maximum 10,000 people allowed per enrichment request"
            }), 400
        
        # Validate field lengths for each person
        for i, person in enumerate(people_array):
            # Validate string field lengths according to API spec
            field_limits = {
                'companyDomain': 2000,
                'companyName': 2000,
                'linkedinUrl': 2000
            }
            
            for field, max_length in field_limits.items():
                value = person.get(field, '')
                if value and len(str(value)) > max_length:
                    return jsonify({
                        "error": f"Person {i+1}: {field} must be {max_length} characters or less"
                    }), 400
        
        # Validate notificationOptions if provided
        if 'notificationOptions' in data:
            notification_options = data['notificationOptions']
            webhook_url = notification_options.get('webhookUrl', '')
            
            if webhook_url and not webhook_url.startswith(('http://', 'https://')):
                return jsonify({
                    "error": "Webhook URL must be a valid HTTP or HTTPS URL"
                }), 400
        
        people_count = len(data.get('people', []))
        include_config = data.get('include', {})
        logger.info(f"Processing bulk people enrichment request with {people_count} people. "
                   f"Include config: email={include_config.get('email', False)}, "
                   f"linkedIn={include_config.get('linkedInUrl', False)}, "
                   f"mobile={include_config.get('mobile', False)}")
        
        # Get selected key from request
        selected_key = get_selected_key_from_request()

        # Make request through simple API client
        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/people/enrich',
            json_data=data,
            selected_key=selected_key  # Add this parameter
        )

         
        # Get API key used for logging
        stats = simple_surfe_client.get_client_stats()
        api_manager_stats = stats.get("api_manager_stats", {})
        api_key_used = api_manager_stats.get('selected_key')

        # Get API key used for logging
        api_manager = simple_surfe_client.get_client_stats().get("api_manager_stats", {})
        api_key_used = api_manager.get("selected_key")
        
        # Record successful request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich/bulk'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
            api_request.status_code = 200
            api_request.response_time = time.time() - start_time
            api_request.success = True
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record bulk API request: {db_error}")
        
        logger.info(f"Bulk people enrichment successful. Enriched {len(response_data.get('people', []))} people")
        
        return jsonify({
            "success": True,
            "data": response_data,
            "metadata": {
                "total_enriched": len(response_data.get('people', [])),
                "api_key_used": api_key_used[-10:] if api_key_used else None,
                "response_time": round(time.time() - start_time, 3)
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Bulk people enrichment failed: {error_msg}")
        
        # Record failed request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich/bulk'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
            api_request.status_code = 500
            api_request.response_time = time.time() - start_time
            api_request.success = False
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record failed bulk API request: {db_error}")
        
        # Determine the correct error response and status code
    if "No API key selected" in error_msg:
        status_code_to_log = 400
        response = jsonify({
            "error": "Configuration Error",
            "details": "No Surfe API key is selected. Please go to the Settings page to select a key."
        }), status_code_to_log
        
    elif "feature_not_available" in error_msg.lower():
        status_code_to_log = 403
        response = jsonify({
            "error": "Feature Not Available",
            "details": "The 'LinkedIn enrichment' feature is not available in your current plan.",
            "code": "feature_not_available",
            "action": "Please contact api.support@surfe.com to upgrade."
        }), status_code_to_log

    elif "no mobile credits left" in error_msg.lower():
        status_code_to_log = 402 # Payment Required
        response = jsonify({
            "error": "Insufficient Credits",
            "details": "There are no mobile credits left to start an enrichment for this request."
        }), status_code_to_log

    elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
        status_code_to_log = 429
        response = jsonify({
            "error": "API quota exceeded. Please try again later.",
            "details": error_msg
        }), status_code_to_log

    elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
        status_code_to_log = 401
        response = jsonify({
            "error": "Authentication failed. Please check API configuration.",
            "details": error_msg
        }), status_code_to_log

    else:
        status_code_to_log = 500
        response = jsonify({
            "error": "An unexpected server error occurred.",
            "details": error_msg
        }), status_code_to_log
    return response

def get_enrichment_status(enrichment_id):
    """Get the status of a people enrichment job"""
    try:
        # Get selected key from request
        selected_key = get_selected_key_from_request()
        
        result = simple_surfe_client.make_request(
            method="GET",
            endpoint=f"/v2/people/enrich/status/{enrichment_id}",
            selected_key=selected_key  # Add this parameter
        )

        if "error" in result:
            error_detail = result.get("details", result.get("error", "An unknown API error occurred."))
            return jsonify({"error": error_detail}), 500

        return jsonify({"success": True, "status": result.get("status"), "data": result.get("data")})

    except Exception as e:
        logger.error(f"❌ Error getting enrichment status: {str(e)}")
        return jsonify({"error": f"Error getting enrichment status: {str(e)}"}), 500