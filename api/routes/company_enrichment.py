import logging
import io
import pandas as pd
from flask import request, jsonify
from utils.supabase_api_client import (
    supabase_surfe_client,
    clean_domain,
    is_valid_domain,
)

from core.user_context import set_user_context

logger = logging.getLogger(__name__)


# --- FIX: This helper now returns (dict, int) to be consistent ---
def _validate_and_enrich_companies(data: dict):
    """Validates data and starts the enrichment job, returning a standardized tuple."""
    if (
        "companies" not in data
        or not isinstance(data.get("companies"), list)
        or not data["companies"]
    ):
        return {
            "success": False,
            "error": "Request must contain a non-empty 'companies' array.",
        }, 400

    companies = data["companies"]
    for i, company in enumerate(companies):
        domain = company.get("domain")
        if not domain:
            return {
                "success": False,
                "error": f"Company at index {i} must have a 'domain' field.",
            }, 400
        cleaned_domain = clean_domain(str(domain))
        if not is_valid_domain(cleaned_domain):
            return {
                "success": False,
                "error": f"Company at index {i} has an invalid domain: '{domain}'.",
            }, 400
        company["domain"] = cleaned_domain

    logger.info(f"Submitting company enrichment job with {len(companies)} companies.")

    try:
        response_data = supabase_surfe_client.make_request(
            method="POST",
            endpoint="/v2/companies/enrich",
            json_data={"companies": companies},
        )
        return {"success": True, "data": response_data}, 200
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "rate limit" in error_msg:
            status, err_data = 429, {"error": "API quota exceeded.", "details": str(e)}
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            status, err_data = 401, {
                "error": "Authentication failed. Check API key.",
                "details": str(e),
            }
        else:
            status, err_data = 500, {
                "error": "An unexpected error occurred during enrichment.",
                "details": str(e),
            }
        return {**err_data, "success": False}, status


@require_user_context
def enrich_companies():
    """Enrich a list of companies from a JSON body."""
    data = request.get_json()
    if not data:
        return {"success": False, "error": "Request body is required."}, 400

    # The helper now returns the final tuple directly
    return _validate_and_enrich_companies(data)


@require_user_context
def enrich_companies_bulk():
    """Bulk enrich company data from a CSV file."""
    if "file" not in request.files:
        return {"success": False, "error": "Request must contain a file."}, 400

    file = request.files["file"]

    # --- FIX: More robust file check that should clear the 'red' warning ---
    if not file or not file.filename or not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "A valid .csv file is required."}), 400

    if not file or file.filename == "" or not file.filename.lower().endswith(".csv"):
        return {"success": False, "error": "A valid .csv file is required."}, 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)
        if "domain" not in df.columns:
            return {
                "success": False,
                "error": "CSV file must contain a 'domain' column.",
            }, 400

        companies_list = []
        df["externalID"] = df.get("externalID", df.get("external_id"))
        for _, row in df.iterrows():
            if pd.notna(row["domain"]):
                company = {"domain": row["domain"]}
                if pd.notna(row.get("externalID")):
                    company["externalID"] = str(row["externalID"])
                companies_list.append(company)

        if not companies_list:
            return {
                "success": False,
                "error": "No rows with valid domains found in CSV.",
            }, 400

        # The helper now returns the final tuple directly
        return _validate_and_enrich_companies({"companies": companies_list})

    except Exception as e:
        logger.error(f"Failed to process bulk enrichment CSV: {e}")
        return {
            "success": False,
            "error": "Failed to process CSV file.",
            "details": str(e),
        }, 500


@require_user_context
def get_enrichment_status(enrichment_id: str):
    """Checks the status of a specific company enrichment job."""
    if not enrichment_id:
        return {"success": False, "error": "Enrichment ID is required"}, 400

    logger.info(f"Checking company enrichment status for ID: {enrichment_id}")
    try:
        # ✅ FIXED: Remove /status from the external API call
        result = supabase_surfe_client.make_request(
            method="GET", endpoint=f"/v2/companies/enrich/{enrichment_id}"
        )

        # --- FIX: Determine 'completed' status by the presence of the data array ---
        # If the 'companies' key exists and is a list, the job is done.
        if "companies" in result and isinstance(result["companies"], list):
            enriched_data = result["companies"]
            logger.info(f"Company enrichment job {enrichment_id} is COMPLETED.")
            return {"success": True, "status": "completed", "data": enriched_data}, 200
        else:
            # Otherwise, the job is still pending.
            logger.info(f"Company enrichment job {enrichment_id} is still PENDING.")
            return {
                "success": True,
                "status": "pending",
                "data": result,
            }, 202  # 202 Accepted indicates work is in progress

    except Exception as e:
        logger.error(f"Failed to get enrichment status for ID {enrichment_id}: {e}")
        return {
            "success": False,
            "error": "Failed to retrieve job status.",
            "details": str(e),
        }, 500
