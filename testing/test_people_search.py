import requests
import json

# Replace with your actual API key
API_KEY = "MZoaOmxVyUmJvBbbsdCxGyhJrFa2DPOSTt9kBh7vQr0"

url = "https://api.surfe.com/v2/people/search"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

payload = {
    "companies": {
        "domainsExcluded": ["ab-inbev.com"],
        "domains": [],
        "industries": ["Wine And Spirits"],
        "employeeCount": {}
    },
    "people": {
        "countries": [],
        "departments": ["Marketing and Advertising"],
        "jobTitles": [],
        "seniorities": []
    },
    "limit": 5,
    "peoplePerCompany": 2
}

all_people = []
page_token = ""

try:
    while True:
        payload["pageToken"] = page_token
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            break  # Stop the loop if there's an error (quota reached)
        data = response.json()
        people = data.get("people", [])
        all_people.extend(people)
        print(f"Fetched {len(people)} people on this page")
        page_token = data.get("nextPageToken")
        if not page_token or not people:
            break
except Exception as e:
    print(f"Exception occurred: {e}")

# Save or process the collected results
print(f"Total people collected before quota was reached: {len(all_people)}")
with open("surfe_results.json", "w", encoding="utf-8") as f:
    json.dump(all_people, f, indent=2)


with open("surfe_results.json", "w", encoding="utf-8") as f:
    json.dump(all_people, f, indent=2)
print("Results saved to test_people_search_results.json")