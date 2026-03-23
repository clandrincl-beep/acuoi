#!/usr/bin/env python3
import subprocess
import json

API_KEY = "bU-QRYx_09EBsiU4d2GJmA"

payload = {
    "q_organization_keyword_tags": ["cannabis", "dispensary"],
    "organization_locations": ["United States"],
    "organization_num_employees_ranges": ["11,20", "21,50", "51,100"],
    "person_titles": ["owner", "founder", "CEO", "CFO"],
    "contact_email_status": ["verified"],
    "page": 1,
    "per_page": 10
}

cmd = [
    "curl", "-s", "-X", "POST",
    "https://api.apollo.io/api/v1/mixed_people/api_search",
    "-H", "Content-Type: application/json",
    "-H", f"X-Api-Key: {API_KEY}",
    "-d", json.dumps(payload)
]

result = subprocess.run(cmd, capture_output=True, text=True)
data = json.loads(result.stdout)

print("=== PAGINATION ===")
print(json.dumps(data.get("pagination", {}), indent=2))

print("\n=== FIRST 3 PEOPLE ===")
for i, p in enumerate(data.get("people", [])[:3]):
    print(f"\n--- Person {i+1} ---")
    print(f"ID: {p.get('id')}")
    print(f"Name: {p.get('first_name')} {p.get('last_name')}")
    print(f"Title: {p.get('title')}")
    print(f"Email: {p.get('email')}")
    print(f"Email Status: {p.get('email_status')}")
    org = p.get("organization", {}) or {}
    print(f"Company: {org.get('name')}")
    print(f"All email fields: {[k for k in p.keys() if 'email' in k.lower()]}")
