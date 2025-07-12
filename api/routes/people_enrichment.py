import logging
import io
import pandas as pd
from flask import request, jsonify
from utils.supabase_api_client import supabase_surfe_client
from core.user_context import set_user_context, require_user_context

logger = logging.getLogger(__name__)


def get_valid_enrichment_combinations():
    """
    Return the valid enrichment combinations for people enrichment.
    Based on actual Surfe API documentation requirements.
    """
    return {
        "combinations": [
            {
                "id": "linkedin_only",
                "name": "LinkedIn URL Only",
                "description": "Best results - Direct LinkedIn profile enrichment",
                "fields": ["linkedinUrl"],
                "optional_fields": ["externalID"],
                "accuracy": "Very High",
                "success_rate": "95%",
                "example": {
                    "linkedinUrl": "https://www.linkedin.com/in/david-maurice-chevalier",
                    "externalID": "external-id-123",
                },
                "note": "Most reliable method for enrichment",
            },
            {
                "id": "email_only",
                "name": "Email Address Only",
                "description": "High accuracy enrichment using professional email",
                "fields": ["email"],
                "optional_fields": ["externalID"],
                "accuracy": "High",
                "success_rate": "85%",
                "example": {
                    "email": "david@surfe.com",
                    "externalID": "external-id-123",
                },
                "note": "Works best with business email addresses",
            },
            {
                "id": "name_company",
                "name": "Name + Company Name",
                "description": "Good results when you have full name and company",
                "fields": ["firstName", "lastName", "companyName"],
                "optional_fields": ["companyDomain", "externalID"],
                "accuracy": "High",
                "success_rate": "80%",
                "example": {
                    "firstName": "David",
                    "lastName": "Chevalier",
                    "companyName": "Surfe",
                    "companyDomain": "surfe.com",
                    "externalID": "external-id-123",
                },
                "note": "Combining with company domain improves accuracy",
            },
            {
                "id": "name_domain",
                "name": "Name + Company Domain",
                "description": "Good results with name and company website",
                "fields": ["firstName", "lastName", "companyDomain"],
                "optional_fields": ["companyName", "externalID"],
                "accuracy": "High",
                "success_rate": "75%",
                "example": {
                    "firstName": "David",
                    "lastName": "Chevalier",
                    "companyDomain": "surfe.com",
                    "companyName": "Surfe",
                    "externalID": "external-id-123",
                },
                "note": "Domain should be without www or protocols",
            },
            {
                "id": "comprehensive",
                "name": "Comprehensive Data",
                "description": "Maximum accuracy with all available information",
                "fields": ["firstName", "lastName", "companyName", "companyDomain"],
                "optional_fields": ["linkedinUrl", "email", "externalID"],
                "accuracy": "Very High",
                "success_rate": "90%",
                "example": {
                    "firstName": "David",
                    "lastName": "Chevalier",
                    "companyName": "Surfe",
                    "companyDomain": "surfe.com",
                    "linkedinUrl": "https://www.linkedin.com/in/david-maurice-chevalier",
                    "externalID": "external-id-123",
                },
                "note": "Provides best possible enrichment results",
            },
            {
                "id": "name_only",
                "name": "Name Only (Limited)",
                "description": "Limited results - may have validation issues",
                "fields": ["firstName", "lastName"],
                "optional_fields": ["externalID"],
                "accuracy": "Low",
                "success_rate": "40%",
                "example": {
                    "firstName": "David",
                    "lastName": "Chevalier",
                    "externalID": "external-id-123",
                },
                "note": "Often fails validation - not recommended",
            },
        ],
        "include_options": {
            "email": {
                "description": "Email address enrichment",
                "default": True,
                "note": "Most commonly requested data",
            },
            "mobile": {
                "description": "Mobile phone number enrichment",
                "default": True,
                "note": "Phone numbers when available",
            },
            "linkedInUrl": {
                "description": "LinkedIn profile URL enrichment",
                "default": False,
                "note": "LinkedIn URLs when available in our database",
                "requires_setup": False,
            },
            "jobHistory": {
                "description": "Current and past job roles and companies",
                "default": False,
                "note": "Historical employment data when available",
            },
        },
        "field_limits": {
            "firstName": 100,
            "lastName": 100,
            "companyName": 2000,
            "companyDomain": 2000,
            "linkedinUrl": 2000,
            "email": 320,
            "externalID": 200,
        },
        "general_limits": {
            "min_people": 1,
            "max_people": 10000,
            "webhook_url_required": False,
            "https_webhook_supported": True,
            "http_webhook_supported": True,
        },
    }


def _validate_enrichment_request(data):
    """
    Enhanced validation for people enrichment requests.
    Ensures data meets Surfe API requirements for successful enrichment.
    """
    if not data:
        return {"success": False, "error": "Request body is required"}, 400
    if "people" not in data or not isinstance(data.get("people"), list):
        return {"success": False, "error": "The 'people' array is required."}, 400

    people_array = data["people"]
    if not 1 <= len(people_array) <= 10000:
        return {
            "success": False,
            "error": "The 'people' array must contain between 1 and 10,000 items.",
        }, 400

    # Validate include options
    if "include" not in data:
        data["include"] = {
            "email": True,
            "mobile": True,
            "linkedInUrl": False,
            "jobHistory": False,
        }
    if not any(data["include"].values()):
        return {
            "success": False,
            "error": "At least one field in 'include' must be true.",
        }, 400

    # Get valid combinations for validation
    valid_combinations = get_valid_enrichment_combinations()

    # Enhanced validation for each person
    for i, person in enumerate(people_array, 1):
        validation_result = _validate_person_combination(person, valid_combinations)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": f"Person {i}: {validation_result['error']}",
                "valid_combinations": valid_combinations["combinations"],
            }, 400

    return None, 200


def _validate_person_combination(person, valid_combinations):
    """
    Validate that a person object meets at least one valid combination.
    """
    if not person or not isinstance(person, dict):
        return {"valid": False, "error": "Person must be a valid object"}

    # Check each combination to see if this person satisfies it
    for combo in valid_combinations["combinations"]:
        if _person_matches_combination(person, combo):
            return {
                "valid": True,
                "combination": combo["id"],
                "accuracy": combo["accuracy"],
            }

    # If no combination matches, provide helpful error
    available_combos = [combo["name"] for combo in valid_combinations["combinations"]]
    return {
        "valid": False,
        "error": f"Person must satisfy one of these combinations: {', '.join(available_combos)}. "
        f"See /api/v2/people/enrich/combinations for details.",
    }


def _person_matches_combination(person, combination):
    """
    Check if a person object has all required fields for a combination.
    """
    required_fields = combination["fields"]

    # Check that all required fields are present and non-empty
    for field in required_fields:
        value = person.get(field, "").strip()
        if not value:
            return False

        # Additional validation for specific fields
        if field == "email" and "@" not in value:
            return False
        elif field == "linkedinUrl" and "linkedin.com" not in value.lower():
            return False
        elif field == "companyDomain" and "." not in value:
            return False

    return True


def _enhance_people_data(data):
    """
    Enhances people data to improve API success rates.
    Adds missing fields and improves data quality.
    """
    enhanced_data = data.copy()
    enhanced_people = []

    for person in data["people"]:
        enhanced_person = person.copy()

        # Clean and enhance names
        if enhanced_person.get("firstName"):
            enhanced_person["firstName"] = enhanced_person["firstName"].strip().title()
        if enhanced_person.get("lastName"):
            enhanced_person["lastName"] = enhanced_person["lastName"].strip().title()

        # Clean company domain
        if enhanced_person.get("companyDomain"):
            domain = enhanced_person["companyDomain"].strip().lower()
            # Remove protocol and www
            domain = (
                domain.replace("https://", "")
                .replace("http://", "")
                .replace("www.", "")
            )
            # Remove trailing slash
            domain = domain.rstrip("/")
            enhanced_person["companyDomain"] = domain

        # Clean and validate LinkedIn URLs
        if enhanced_person.get("linkedinUrl"):
            linkedin_url = enhanced_person["linkedinUrl"].strip()
            if not linkedin_url.startswith("http"):
                linkedin_url = "https://" + linkedin_url
            if "linkedin.com" in linkedin_url:
                enhanced_person["linkedinUrl"] = linkedin_url
            else:
                # Invalid LinkedIn URL, remove it
                logger.warning(f"Removing invalid LinkedIn URL: {linkedin_url}")
                enhanced_person.pop("linkedinUrl", None)

        # Clean email addresses
        if enhanced_person.get("email"):
            email = enhanced_person["email"].strip().lower()
            if "@" in email and "." in email:
                enhanced_person["email"] = email
            else:
                logger.warning(f"Removing invalid email: {email}")
                enhanced_person.pop("email", None)

        enhanced_people.append(enhanced_person)

    enhanced_data["people"] = enhanced_people
    return enhanced_data


def _handle_enrichment_exception(e):
    """Handles exceptions and returns a standardized error response tuple."""
    error_msg = str(e).lower()
    logger.error(f"Enrichment exception: {error_msg}", exc_info=True)

    if "no api key selected" in error_msg:
        code, err_data = 401, {
            "error": "Configuration Error",
            "details": "No API key is selected.",
        }
    elif "no email credits left" in error_msg:
        code, err_data = 402, {
            "error": "No Email Credits Available",
            "details": "There are no email credits left to start an enrichment",
            "suggestions": [
                "Uncheck 'Email Address' in the include options",
                "Contact your administrator to add more email credits",
                "You can still enrich phone numbers if you have mobile credits",
            ],
        }
    elif "no mobile credits left" in error_msg:
        code, err_data = 402, {
            "error": "No Mobile Credits Available",
            "details": "There are no mobile phone credits left to start an enrichment",
            "suggestions": [
                "Uncheck 'Phone Number' in the include options",
                "Contact your administrator to add more mobile credits",
                "You can still enrich email addresses if you have email credits",
            ],
        }
    elif "quota" in error_msg or "rate limit" in error_msg:
        code, err_data = 429, {
            "error": "API Limit Reached",
            "details": "Quota or rate limit exceeded.",
        }
    else:
        code, err_data = 500, {
            "error": "An unexpected server error occurred.",
            "details": str(e),
        }

    return {**err_data, "success": False}, code


@require_user_context
def get_enrichment_combinations():
    """Return available enrichment combinations for the frontend."""
    try:
        combinations_data = get_valid_enrichment_combinations()
        return {"success": True, "data": combinations_data}, 200
    except Exception as e:
        logger.error(f"❌ Failed to get enrichment combinations: {str(e)}")
        return {
            "success": False,
            "error": "Failed to retrieve enrichment combinations",
        }, 500


@require_user_context
def enrich_people():
    """Submits a job to enrich a list of people from a JSON body."""
    try:
        data = request.get_json()
        logger.info(
            f"Received enrichment request for {len(data.get('people', []))} people"
        )

        error_response, status_code = _validate_enrichment_request(data)
        if error_response:
            return error_response, status_code

        # Enhance the data before sending to API
        enhanced_data = _enhance_people_data(data)
        logger.info(f"Enhanced enrichment request: {enhanced_data}")

        response_data = supabase_surfe_client.make_request(
            method="POST", endpoint="/v2/people/enrich", json_data=enhanced_data
        )

        enrichment_id = (
            response_data.get("enrichmentID")
            or response_data.get("enrichment_id")
            or response_data.get("id")
        )
        if enrichment_id:
            logger.info(
                f"✅ Enrichment job created successfully with ID: {enrichment_id}"
            )
        else:
            logger.warning(
                f"⚠️ Enrichment job created but no ID found in response: {response_data}"
            )

        return {"success": True, "data": response_data}, 200
    except Exception as e:
        return _handle_enrichment_exception(e)


@require_user_context
def enrich_people_bulk():
    """Submits a job to enrich people from a CSV file."""
    try:
        if "file" not in request.files:
            return {"success": False, "error": "Request must contain a file."}, 400

        file = request.files["file"]

        if not file or not file.filename or not file.filename.lower().endswith(".csv"):
            return {"success": False, "error": "A valid .csv file is required."}, 400

        logger.info(f"Processing CSV file: {file.filename}")

        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        df = pd.read_csv(stream)

        logger.info(f"CSV contains {len(df)} rows")

        people_data = df.rename(
            columns={
                "first_name": "firstName",
                "last_name": "lastName",
                "company_name": "companyName",
                "company_domain": "companyDomain",
                "linkedin_url": "linkedinUrl",
                "external_id": "externalID",
            }
        ).to_dict("records")

        data = {
            "people": people_data,
            "include": {
                "email": True,
                "mobile": True,
                "linkedInUrl": False,
                "jobHistory": False,
            },
        }

        error_response, status_code = _validate_enrichment_request(data)
        if error_response:
            return error_response, status_code

        enhanced_data = _enhance_people_data(data)
        response_data = supabase_surfe_client.make_request(
            method="POST", endpoint="/v2/people/enrich", json_data=enhanced_data
        )

        enrichment_id = (
            response_data.get("enrichmentID")
            or response_data.get("enrichment_id")
            or response_data.get("id")
        )
        logger.info(
            f"✅ Bulk enrichment job created with ID: {enrichment_id} for {len(people_data)} people"
        )

        return {"success": True, "data": response_data}, 200
    except Exception as e:
        return _handle_enrichment_exception(e)


@require_user_context
def get_enrichment_status(enrichment_id: str):
    """
    Checks the status of a specific people enrichment job.
    """
    if not enrichment_id:
        return {"success": False, "error": "Enrichment ID is required"}, 400

    logger.info(f"🔍 Checking enrichment status for ID: {enrichment_id}")

    try:
        endpoint = f"/v2/people/enrich/{enrichment_id}"
        logger.info(f"📡 Calling endpoint: {endpoint}")

        result = supabase_surfe_client.make_request(method="GET", endpoint=endpoint)

        logger.info(f"📥 API Response: {result}")

        # Check the actual status field from the API response
        api_status = result.get("status", "").upper()
        percent_completed = result.get("percentCompleted", 0)
        people_data = result.get("people", [])

        logger.info(
            f"📊 Status Analysis: API Status='{api_status}', Percent={percent_completed}%, People Count={len(people_data)}"
        )

        # The job is only truly completed when the API says status is 'COMPLETED'
        if api_status == "COMPLETED":
            completed_people = (
                [p for p in people_data if p.get("status") == "COMPLETED"]
                if people_data
                else []
            )
            total_people = len(people_data)
            completed_count = len(completed_people)

            logger.info(
                f"✅ Enrichment {enrichment_id} COMPLETED: {completed_count}/{total_people} people enriched"
            )

            return {"success": True, "status": "completed", "data": people_data}, 200

        elif api_status in ["IN_PROGRESS", "PENDING", "PROCESSING"]:
            completed_people = (
                [p for p in people_data if p.get("status") == "COMPLETED"]
                if people_data
                else []
            )
            in_progress_people = (
                [p for p in people_data if p.get("status") == "IN_PROGRESS"]
                if people_data
                else []
            )

            logger.info(
                f"⏳ Enrichment {enrichment_id} PENDING: {percent_completed}% complete ({len(completed_people)} done, {len(in_progress_people)} in progress)"
            )

            return {
                "success": True,
                "status": "pending",
                "data": result,
                "progress": percent_completed,
            }, 202

        elif api_status in ["FAILED", "ERROR"]:
            logger.error(f"❌ Enrichment {enrichment_id} FAILED")
            return {
                "success": False,
                "status": "failed",
                "error": "Enrichment job failed",
                "data": result,
            }, 200

        else:
            logger.warning(
                f"🤔 Unknown status '{api_status}' for enrichment {enrichment_id}, treating as pending"
            )
            return {"success": True, "status": "pending", "data": result}, 202

    except Exception as e:
        error_msg = str(e)
        logger.error(
            f"❌ Failed to get enrichment status for {enrichment_id}: {error_msg}"
        )
        return {
            "success": False,
            "error": "Failed to retrieve job status.",
            "details": error_msg,
        }, 500
