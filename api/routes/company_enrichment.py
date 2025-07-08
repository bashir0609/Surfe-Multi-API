import logging
import io
import pandas as pd
from flask import request, jsonify
from utils.simple_api_client import simple_surfe_client, clean_domain, is_valid_domain

logger = logging.getLogger(__name__)

def _validate_and_enrich_companies(data: dict):
    """
    Helper function to validate data, make the enrichment request, and handle responses.
    This consolidates logic for both single and bulk endpoints.
    """
    # 1. Validate the incoming data structure
    if 'companies' not in data or not isinstance(data.get('companies'), list) or not data['companies']:
        return {"error": "Request must contain a non-empty 'companies' array."}, 400

    companies = data['companies']
    for i, company in enumerate(companies):
        domain = company.get('domain')
        if not domain:
            return {"error": f"Company at index {i} must have a 'domain' field."}, 400

        cleaned_domain = clean_domain(str(domain))
        if not is_valid_domain(cleaned_domain):
            return {"error": f"Company at index {i} has an invalid domain: '{domain}'."}, 400
        
        # Update the list with the cleaned domain for the API call
        company['domain'] = cleaned_domain

    logger.info(f"Processing company enrichment request with {len(companies)} companies.")

    # 2. Make the API request and handle specific API errors
    try:
        response_data = simple_surfe_client.make_request(
            method='POST',
            endpoint='/v2/companies/enrich',
            json_data={'companies': companies} # Only send the necessary data
        )
        logger.info(f"Enrichment successful. Processed {len(response_data.get('companies', []))} companies.")
        return response_data, 200

    except Exception as e:
        error_msg = str(e).lower()
        logger.error(f"Company enrichment failed: {error_msg}")
        if "quota" in error_msg or "rate limit" in error_msg:
            return {"error": "API quota exceeded.", "details": str(e)}, 429
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            return {"error": "Authentication failed. Check API key.", "details": str(e)}, 401
        else:
            return {"error": "An unexpected error occurred during enrichment.", "details": str(e)}, 500


def enrich_companies():
    """Enrich a list of companies from a JSON body."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body is required."}), 400

    result, status_code = _validate_and_enrich_companies(data)

    if status_code == 200:
        return jsonify({"success": True, "data": result}), status_code
    else:
        return jsonify({"success": False, **result}), status_code


def enrich_companies_bulk():
    """Bulk enrich company data from a CSV file."""
    if 'file' not in request.files:
        return jsonify({"error": "Request must contain a file."}), 400
        
    file = request.files['file']
    if not file or not file.filename.endswith('.csv'):
        return jsonify({"error": "A valid .csv file is required."}), 400
        
    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)

        if 'domain' not in df.columns:
            return jsonify({"error": "CSV file must contain a 'domain' column."}), 400

        # Prepare the list of companies for the API
        companies_list = []
        df['externalID'] = df.get('externalID', df.get('external_id')) # Unify external ID column
        for _, row in df.iterrows():
            if pd.notna(row['domain']):
                company = {'domain': row['domain']}
                if pd.notna(row.get('externalID')):
                    company['externalID'] = str(row['externalID'])
                companies_list.append(company)

        if not companies_list:
            return jsonify({"error": "No rows with valid domains found in CSV."}), 400

        result, status_code = _validate_and_enrich_companies({"companies": companies_list})

        if status_code == 200:
            return jsonify({"success": True, "data": result}), status_code
        else:
            return jsonify({"success": False, **result}), status_code

    except Exception as e:
        logger.error(f"Failed to process bulk enrichment CSV: {e}")
        return jsonify({"error": "Failed to process CSV file.", "details": str(e)}), 500


def get_enrichment_status(enrichment_id: str):
    """Checks the status of a specific company enrichment job."""
    if not enrichment_id:
        return jsonify({"error": "Enrichment ID is required"}), 400

    try:
        result = simple_surfe_client.make_request(
            method="GET",
            endpoint=f"/v2/companies/enrich/{enrichment_id}"
        )
        status = "completed" if 'companies' in result and result['companies'] else "pending"
        return jsonify({"success": True, "status": status, "data": result})

    except Exception as e:
        logger.error(f"Failed to get enrichment status for ID {enrichment_id}: {e}")
        return jsonify({"success": False, "error": "Failed to retrieve job status.", "details": str(e)}), 500

