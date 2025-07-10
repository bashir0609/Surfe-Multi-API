"""
Company Enrichment API Routes
Handles enriching company data with additional information using Surfe API
"""
import logging
import io
import pandas as pd
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client, clean_domain, is_valid_domain, clean_domains_list
from core.dependencies import validate_request_data
from models import db, ApiRequest
from datetime import datetime
import time
from typing import Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

def get_selected_key_from_request(request_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Get selected key from request headers or body"""
    # Try header first
    selected_key = request.headers.get('X-Selected-Key')
    if selected_key:
        return selected_key.strip()

    # Try from the JSON data that was passed in
    if request_data:
        selected_key = request_data.get('_selectedKey')
        if selected_key:
            return selected_key.strip()

    return None

def enrich_companies() -> Union[tuple, Any]:
    """
    Enrich company data using Surfe API with rotation system
    """
    start_time = time.time()
    api_key_used: Optional[str] = None
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        # Validate request structure
        if not validate_request_data(data):
            return jsonify({"error": "Invalid request structure"}), 400
        
        # Check required fields for enrichment (API v2 structure)
        if not data.get('companies'):
            return jsonify({
                "error": "companies array is required for enrichment"
            }), 400
        
        # Validate companies array structure
        companies = data.get('companies', [])
        if not isinstance(companies, list) or len(companies) == 0:
            return jsonify({
                "error": "companies must be a non-empty array"
            }), 400
        
        # Validate and clean each company's domain field
        for i, company in enumerate(companies):
            if not isinstance(company, dict):
                return jsonify({
                    "error": f"Company at index {i} must be an object"
                }), 400
            
            domain = company.get('domain')
            if not domain:
                return jsonify({
                    "error": f"Company at index {i} must have a domain field"
                }), 400
            
            # Clean and validate domain
            cleaned_domain = clean_domain(str(domain))
            if not cleaned_domain or not is_valid_domain(cleaned_domain):
                return jsonify({
                    "error": f"Company at index {i} has invalid domain: {domain}"
                }), 400
            
            # Update the domain with cleaned version
            companies[i]['domain'] = cleaned_domain
        
        logger.info(f"Processing company enrichment request with {len(companies)} companies")

        selected_key = get_selected_key_from_request(data)

        # Make request through rotation system
        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/companies/enrich',
            json_data=data,
            selected_key=selected_key
        )
        
        # Get the API key that was used (simplified system)
        stats = simple_surfe_client.get_client_stats()
        api_key_used = stats.get('selected_key', 'unknown')
        
        # Record successful request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/companies/enrich'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
            api_request.status_code = 200
            api_request.response_time = time.time() - start_time
            api_request.success = True
            db.session.add(api_request)
            db.session.commit()
        except Exception as db_error:
            logger.warning(f"Failed to record API request: {db_error}")
        
        logger.info(f"Company enrichment successful. Enriched {len(response_data.get('companies', []))} companies")
        
        return jsonify({
            "success": True,
            "data": response_data,
            "metadata": {
                "total_enriched": len(response_data.get('companies', [])),
                "api_key_used": api_key_used[-10:] if api_key_used else None,
                "response_time": round(time.time() - start_time, 3)
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Company enrichment failed: {error_msg}")
        
        # Record failed request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/companies/enrich'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
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
                "error": "Company enrichment failed",
                "details": error_msg
            }), 500
        
def get_enrichment_status(enrichment_id: str) -> Union[tuple, Any]:
    """
    Checks the status of a specific company enrichment job using its ID.
    """
    if not enrichment_id:
        return jsonify({"success": False, "error": "Enrichment ID is required"}), 400

    try:
        # Get selected key from request (passing None explicitly)
        selected_key = get_selected_key_from_request(None)

        # Make request
        result = simple_surfe_client.make_request(
            method="GET",
            endpoint=f"/v2/companies/enrich/status/{enrichment_id}",
            selected_key=selected_key
        )

        if result and 'companies' in result and result['companies']:
            logger.info(f"Enrichment job {enrichment_id} is complete.")
            return jsonify({"success": True, "status": "completed", "data": result['companies']})

        logger.info(f"Enrichment job {enrichment_id} is pending.")
        return jsonify({"success": True, "status": "pending", "data": result})

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Failed to get enrichment status for ID {enrichment_id}: {error_msg}")
        return jsonify({"success": False, "error": error_msg}), 500

def enrich_companies_bulk() -> Union[tuple, Any]:
    """
    Bulk enrich company data with CSV support
    """
    start_time = time.time()
    api_key_used: Optional[str] = None
    
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
                
                # Convert CSV to API v2 enrichment format (companies array only)
                companies = []
                
                for _, row in csv_input.iterrows():
                    # Build company object with required domain and optional externalID
                    if 'domain' in row and pd.notna(row['domain']):
                        raw_domain = str(row['domain']).strip()
                        cleaned_domain = clean_domain(raw_domain)
                        
                        # Only add companies with valid domains
                        if cleaned_domain and is_valid_domain(cleaned_domain):
                            company = {'domain': cleaned_domain}
                            
                            # Add optional externalID if present
                            if 'externalID' in row and pd.notna(row['externalID']):
                                company['externalID'] = str(row['externalID']).strip()
                            elif 'external_id' in row and pd.notna(row['external_id']):
                                company['externalID'] = str(row['external_id']).strip()
                            
                            companies.append(company)
                
                if not companies:
                    return jsonify({"error": "No valid companies found in CSV. Please ensure 'domain' column exists."}), 400
                
                data = {"companies": companies}
                
                # Get selected key from request headers
                selected_key = get_selected_key_from_request(None)
                
                # Process CSV enrichment
                response_data = simple_surfe_client.make_request(
                    method='POST',
                    endpoint='/v2/companies/enrich',
                    json_data=data,
                    selected_key=selected_key
                )
                
                # Get the API key that was used (with proper None handling)
                stats = simple_surfe_client.get_client_stats()
                api_key_used = stats.get('selected_key') if stats else None
                
                # Record successful request
                try:
                    api_request = ApiRequest()
                    api_request.endpoint = '/api/v2/companies/enrich/bulk'
                    api_request.method = 'POST'
                    api_request.api_key_used = api_key_used[-10:] if api_key_used else None
                    api_request.status_code = 200
                    api_request.response_time = time.time() - start_time
                    api_request.success = True
                    db.session.add(api_request)
                    db.session.commit()
                except Exception as db_error:
                    logger.warning(f"Failed to record API request: {db_error}")
                
                logger.info(f"Bulk company enrichment successful. Processed {len(response_data.get('companies', []))} companies")
                
                return jsonify({
                    "success": True,
                    "data": response_data,
                    "metadata": {
                        "total_processed": len(response_data.get('companies', [])),
                        "api_key_used": api_key_used[-10:] if api_key_used else None,
                        "response_time": round(time.time() - start_time, 3)
                    }
                })
                
            else:
                return jsonify({"error": "Only CSV files are supported"}), 400
        else:
            # Get JSON data
            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400
        
            # Get selected key from request
            selected_key = get_selected_key_from_request(data)

            # Process enrichment using the same endpoint
            response_data = simple_surfe_client.make_request(
                method='POST',
                endpoint='/v2/companies/enrich',
                json_data=data,
                selected_key=selected_key
            )
            
            # Get the API key that was used (with proper None handling)
            stats = simple_surfe_client.get_client_stats()
            api_key_used = stats.get('selected_key') if stats else None
            
            # Record successful request
            try:
                api_request = ApiRequest()
                api_request.endpoint = '/api/v2/companies/enrich/bulk'
                api_request.method = 'POST'
                api_request.api_key_used = api_key_used[-10:] if api_key_used else None
                api_request.status_code = 200
                api_request.response_time = time.time() - start_time
                api_request.success = True
                db.session.add(api_request)
                db.session.commit()
            except Exception as db_error:
                logger.warning(f"Failed to record API request: {db_error}")
        
            logger.info(f"Bulk company enrichment successful. Processed {len(response_data.get('companies', []))} companies")
        
            return jsonify({
                "success": True,
                "data": response_data,
                "metadata": {
                    "total_processed": len(response_data.get('companies', [])),
                    "api_key_used": api_key_used[-10:] if api_key_used else None,
                    "response_time": round(time.time() - start_time, 3)
                }
            })
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Bulk company enrichment failed: {error_msg}")
        
        # Record failed request
        try:
            api_request = ApiRequest()
            api_request.endpoint = '/api/v2/companies/enrich/bulk'
            api_request.method = 'POST'
            api_request.api_key_used = api_key_used[-10:] if api_key_used else None
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
                "error": "Bulk company enrichment failed",
                "details": error_msg
            }), 500