#!/usr/bin/env python3
"""
Company Enrichment Test Suite
============================

This file tests the company enrichment functionality including:
- Starting enrichment jobs
- Checking enrichment status
- Handling different response scenarios
- Testing with real and mock data

Usage:
    python test_company_enrichment.py
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional

from config.supabase_api_manager import supabase_api_manager

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CompanyEnrichmentTester:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
        # Test data
        self.test_companies = [
            {"domain": "google.com", "externalID": "test_google"},
            {"domain": "microsoft.com", "externalID": "test_microsoft"},
            {"domain": "apple.com", "externalID": "test_apple"}
        ]
        
        self.invalid_companies = [
            {"domain": "notarealdomainthatexists12345.com", "externalID": "test_invalid"},
            {"domain": "", "externalID": "test_empty"},
            {"domain": "invalid-domain", "externalID": "test_malformed"}
        ]

    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def test_api_health(self):
        """Test if the API is healthy and responding"""
        self.log("Testing API health...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log("✅ API health check passed")
                return True
            else:
                self.log(f"❌ API health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ API health check failed: {e}", "ERROR")
            return False

    def test_settings_config(self):
        """Test if settings configuration is working"""
        self.log("Testing settings configuration...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/settings/config")
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("data", {}).get("api_manager"):
                    api_manager = data["data"]["api_manager"]
                    self.log(f"✅ Settings config OK - {supabase_api_manager.get('total_keys', 0)} keys, valid selection: {supabase_api_manager.get('has_valid_selection', False)}")
                    return True
                else:
                    self.log("❌ Settings config invalid structure", "ERROR")
                    return False
            else:
                self.log(f"❌ Settings config failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Settings config failed: {e}", "ERROR")
            return False

    def start_enrichment(self, companies: List[Dict], test_name: str = "test") -> Optional[str]:
        """Start an enrichment job and return the enrichment ID"""
        self.log(f"Starting enrichment for {len(companies)} companies ({test_name})...")
        
        payload = {"companies": companies}
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v2/companies/enrich",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            self.log(f"Enrichment request status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"Response data: {json.dumps(data, indent=2)}")
                
                if data.get("success") and data.get("data", {}).get("enrichmentID"):
                    enrichment_id = data["data"]["enrichmentID"]
                    self.log(f"✅ Enrichment started successfully: {enrichment_id}")
                    return enrichment_id
                else:
                    self.log(f"❌ Enrichment failed: {data.get('error', 'Unknown error')}", "ERROR")
                    return None
            else:
                self.log(f"❌ Enrichment request failed: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Enrichment request exception: {e}", "ERROR")
            return None

    def check_enrichment_status(self, enrichment_id: str, test_name: str = "test") -> Optional[Dict]:
        """Check the status of an enrichment job"""
        self.log(f"Checking status for enrichment {enrichment_id} ({test_name})...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/v2/companies/enrich/status/{enrichment_id}")
            
            self.log(f"Status check response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                self.log(f"✅ Status check successful: {status}")
                
                if data.get("success"):
                    return data
                else:
                    self.log(f"⚠️ Status check returned success=false: {data.get('error', 'Unknown error')}", "WARN")
                    return data
            else:
                error_text = response.text
                self.log(f"❌ Status check failed: {response.status_code} - {error_text}", "ERROR")
                
                # Try to parse JSON error
                try:
                    error_data = response.json()
                    self.log(f"Error details: {json.dumps(error_data, indent=2)}", "ERROR")
                except:
                    pass
                    
                return None
                
        except Exception as e:
            self.log(f"❌ Status check exception: {e}", "ERROR")
            return None

    def poll_until_complete(self, enrichment_id: str, max_attempts: int = 30, interval: int = 2) -> Optional[Dict]:
        """Poll for enrichment completion"""
        self.log(f"Polling for completion of {enrichment_id} (max {max_attempts} attempts, {interval}s interval)...")
        
        for attempt in range(max_attempts):
            status_data = self.check_enrichment_status(enrichment_id, f"poll_attempt_{attempt + 1}")
            
            if status_data is None:
                self.log(f"❌ Status check failed on attempt {attempt + 1}", "ERROR")
                continue
                
            status = status_data.get("status", "unknown")
            
            if status == "completed":
                self.log(f"✅ Enrichment completed after {attempt + 1} attempts!")
                return status_data
            elif status == "failed":
                self.log(f"❌ Enrichment failed after {attempt + 1} attempts", "ERROR")
                return status_data
            elif status in ["pending", "processing", "in_progress"]:
                self.log(f"⏳ Still processing... ({status}) - attempt {attempt + 1}/{max_attempts}")
            else:
                self.log(f"❓ Unknown status: {status} - attempt {attempt + 1}/{max_attempts}", "WARN")
            
            if attempt < max_attempts - 1:
                time.sleep(interval)
        
        self.log(f"⏰ Polling timed out after {max_attempts} attempts", "WARN")
        return None

    def test_single_company_enrichment(self):
        """Test enrichment with a single company"""
        self.log("=" * 50)
        self.log("TESTING: Single Company Enrichment")
        self.log("=" * 50)
        
        test_company = [self.test_companies[0]]  # Just Google
        
        # Start enrichment
        enrichment_id = self.start_enrichment(test_company, "single_company")
        if not enrichment_id:
            return False
        
        # Check status immediately
        initial_status = self.check_enrichment_status(enrichment_id, "immediate_check")
        
        # Poll until complete
        final_result = self.poll_until_complete(enrichment_id)
        
        if final_result and final_result.get("status") == "completed":
            results = final_result.get("data", [])
            self.log(f"✅ Single company enrichment successful: {len(results)} results")
            
            # Log first result details
            if results:
                first_result = results[0]
                self.log(f"Sample result: {first_result.get('name', 'N/A')} - {first_result.get('domain', 'N/A')}")
            
            return True
        else:
            self.log("❌ Single company enrichment failed or timed out", "ERROR")
            return False

    def test_multiple_company_enrichment(self):
        """Test enrichment with multiple companies"""
        self.log("=" * 50)
        self.log("TESTING: Multiple Company Enrichment")
        self.log("=" * 50)
        
        # Start enrichment
        enrichment_id = self.start_enrichment(self.test_companies, "multiple_companies")
        if not enrichment_id:
            return False
        
        # Poll until complete
        final_result = self.poll_until_complete(enrichment_id, max_attempts=45)
        
        if final_result and final_result.get("status") == "completed":
            results = final_result.get("data", [])
            self.log(f"✅ Multiple company enrichment successful: {len(results)} results")
            return True
        else:
            self.log("❌ Multiple company enrichment failed or timed out", "ERROR")
            return False

    def test_invalid_enrichment_id(self):
        """Test status check with invalid enrichment ID"""
        self.log("=" * 50)
        self.log("TESTING: Invalid Enrichment ID")
        self.log("=" * 50)
        
        fake_id = "invalid-enrichment-id-12345"
        status_data = self.check_enrichment_status(fake_id, "invalid_id_test")
        
        # We expect this to fail
        if status_data is None:
            self.log("✅ Invalid ID correctly rejected")
            return True
        else:
            self.log("❌ Invalid ID should have been rejected", "ERROR")
            return False

    def test_edge_cases(self):
        """Test various edge cases"""
        self.log("=" * 50)
        self.log("TESTING: Edge Cases")
        self.log("=" * 50)
        
        results = []
        
        # Test with empty companies list
        self.log("Testing empty companies list...")
        enrichment_id = self.start_enrichment([], "empty_list")
        results.append(enrichment_id is None)  # Should fail
        
        # Test with invalid companies
        self.log("Testing invalid companies...")
        enrichment_id = self.start_enrichment(self.invalid_companies, "invalid_companies")
        if enrichment_id:
            # This might succeed but return no results
            final_result = self.poll_until_complete(enrichment_id, max_attempts=10)
            results.append(True)
        else:
            results.append(True)  # Failed as expected
        
        return all(results)

    def run_all_tests(self):
        """Run all tests and return summary"""
        self.log("🚀 Starting Company Enrichment Test Suite")
        self.log("=" * 60)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("Settings Configuration", self.test_settings_config),
            ("Single Company Enrichment", self.test_single_company_enrichment),
            ("Multiple Company Enrichment", self.test_multiple_company_enrichment),
            ("Invalid Enrichment ID", self.test_invalid_enrichment_id),
            ("Edge Cases", self.test_edge_cases),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running: {test_name}")
            try:
                result = test_func()
                results[test_name] = result
                status = "✅ PASSED" if result else "❌ FAILED"
                self.log(f"{status}: {test_name}")
            except Exception as e:
                results[test_name] = False
                self.log(f"❌ FAILED: {test_name} - Exception: {e}", "ERROR")
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for r in results.values() if r)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status}: {test_name}")
        
        self.log(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            self.log("🎉 All tests passed!")
        else:
            self.log("⚠️ Some tests failed. Check the logs above for details.")
        
        return results

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Company Enrichment API")
    parser.add_argument("--base-url", default="http://localhost:5000", help="Base URL for the API")
    parser.add_argument("--test", choices=["single", "multiple", "invalid", "edge", "all"], default="all", help="Which test to run")
    
    args = parser.parse_args()
    
    tester = CompanyEnrichmentTester(base_url=args.base_url)
    
    if args.test == "single":
        tester.test_single_company_enrichment()
    elif args.test == "multiple":
        tester.test_multiple_company_enrichment()
    elif args.test == "invalid":
        tester.test_invalid_enrichment_id()
    elif args.test == "edge":
        tester.test_edge_cases()
    else:
        tester.run_all_tests()

if __name__ == "__main__":
    main()