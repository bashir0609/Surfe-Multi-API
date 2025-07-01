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
        
        # Make request through rotation system
        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/people/enrich',
            json_data=data
        )
        
        # Get the API key that was used (simplified system)
        stats = simple_surfe_client.get_client_stats()
        api_key_used = stats.get('selected_key', 'unknown')
        
        # Record successful request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-5:] if api_key_used else None
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
                "api_key_used": api_key_used[-5:] if api_key_used else None,
                "response_time": round(time.time() - start_time, 3)
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"People enrichment failed: {error_msg}")
        
        # Record failed request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-5:] if api_key_used else None
            api_request.status_code = 500
            api_request.response_time = time.time() - start_time
            api_request.success = False
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record failed API request: {db_error}")
        
        # Determine appropriate error response
        if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            return jsonify({
                "error": "API quota exceeded. Please try again later.",
                "details": error_msg,
                "retry_after": 3600
            }), 429
        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return jsonify({
                "error": "Authentication failed. Please check API configuration.",
                "details": error_msg
            }), 401
        else:
            return jsonify({
                "error": "People enrichment failed",
                "details": error_msg
            }), 500

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
        
        # Make request through simple API client
        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/people/enrich',
            json_data=data
        )
        
        # Get API key used for logging
        api_manager = simple_surfe_client.api_manager
        api_key_used = api_manager.get_selected_key()
        
        # Record successful request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/people/enrich/bulk'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-5:] if api_key_used else None
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
                "api_key_used": api_key_used[-5:] if api_key_used else None,
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
            api_request.api_key_used = api_key_used[-5:] if api_key_used else None
            api_request.status_code = 500
            api_request.response_time = time.time() - start_time
            api_request.success = False
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record failed bulk API request: {db_error}")
        
        # Determine appropriate error response
        if "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
            return jsonify({
                "error": "API quota exceeded. Please try again later.",
                "details": error_msg,
                "retry_after": 3600
            }), 429
        elif "unauthorized" in error_msg.lower() or "invalid api key" in error_msg.lower():
            return jsonify({
                "error": "API authentication failed. Please check your API keys.",
                "details": error_msg
            }), 401
        else:
            return jsonify({
                "error": "Bulk people enrichment failed",
                "details": error_msg
            }), 500