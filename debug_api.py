#!/usr/bin/env python3
import json
import subprocess

API_KEY = "bU-QRYx_09EBsiU4d2GJmA"

def api_call(endpoint, payload):
    cmd = [
        "curl", "-s", "-X", "POST",
        f"https://api.apollo.io/api/v1/{endpoint}",
        "-H", "Content-Type: application/json",
        "-H", f"x-api-key: {API_KEY}",
        "-d", json.dumps(payload)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

# Test: get a few people with email
result = api_call("mixed_people/api_search", {
    "q_organization_keyword_tags": ["cannabis", "dispensary"],
    "person_titles": ["CEO", "owner"],
    "per_page": 5,
    "page": 1
})

people = result.get("people", [])
print(f"Found {len(people)} people")
if people:
    p = people[0]
    print(f"Sample: {p.get('first_name')} {p.get('last_name_obfuscated')} - {p.get('organization',{}).get('name')}")
    print(f"has_email: {p.get('has_email')}, id: {p.get('id')}")
    
    # Try bulk_match with this ID
    print(f"\nTrying bulk_match...")
    match_result = api_call("people/bulk_match", {
        "details": [{"id": p.get("id")}]
    })
    print(f"Response keys: {match_result.keys()}")
    print(f"Full response: {json.dumps(match_result, indent=2)[:2000]}")
