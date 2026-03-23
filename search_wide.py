#!/usr/bin/env python3
"""
Wide search for cannabis industry - get 250 prospects WITH EMAIL
Using correct endpoint: mixed_people/api_search
"""
import subprocess
import json
import csv
import random

API_KEY = "bU-QRYx_09EBsiU4d2GJmA"

def api_call(endpoint, payload):
    cmd = [
        "curl", "-s", "-X", "POST",
        f"https://api.apollo.io/api/v1/{endpoint}",
        "-H", "Content-Type: application/json",
        "-H", "Cache-Control: no-cache",
        "-H", f"X-Api-Key: {API_KEY}",
        "-d", json.dumps(payload)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        print(f"Parse error: {result.stdout[:500]}")
        return {}

# WIDE cannabis keywords
keywords_groups = [
    ["cannabis", "marijuana", "dispensary"],
    ["hemp", "CBD", "THC"],
    ["cultivation", "cultivator", "grower"],
    ["cannabis retail", "cannabis delivery"],
    ["extraction", "concentrate", "edibles"],
]

# Include small companies too
employee_ranges = ["1,10", "11,20", "21,50", "51,100", "101,200", "201,500"]

# US + Canada
locations = ["United States", "Canada"]

# Broad titles
titles = [
    "owner", "founder", "co-founder", "CEO", "CFO", "COO",
    "president", "general manager", "director", "VP",
    "finance", "controller", "accounting", "operations",
    "head of finance", "head of operations"
]

print("=" * 60)
print("CANNABIS INDUSTRY - WIDE SEARCH (api_search endpoint)")
print("=" * 60)

all_people = []
seen_ids = set()

for kw_group in keywords_groups:
    print(f"\n🔍 Searching: {kw_group}")
    
    for page in range(1, 4):  # 3 pages per keyword group
        payload = {
            "q_organization_keyword_tags": kw_group,
            "organization_locations": locations,
            "organization_num_employees_ranges": employee_ranges,
            "person_titles": titles,
            "contact_email_status": ["verified"],  # Verified emails only
            "page": page,
            "per_page": 100
        }
        
        resp = api_call("mixed_people/api_search", payload)
        
        if "people" in resp and resp["people"]:
            for p in resp["people"]:
                pid = p.get("id")
                email = p.get("email")
                if pid and pid not in seen_ids and email:
                    seen_ids.add(pid)
                    all_people.append(p)
            print(f"   Page {page}: {len(resp['people'])} people, {len(all_people)} total unique")
            
            # Check pagination
            pagination = resp.get("pagination", {})
            if page >= pagination.get("total_pages", 1):
                break
        else:
            error = resp.get("error") or resp.get("message") or "no results"
            print(f"   Page {page}: {error}")
            break
    
    if len(all_people) >= 500:
        print("\n✅ Got 500+ candidates, stopping")
        break

print(f"\n{'=' * 60}")
print(f"TOTAL UNIQUE PEOPLE WITH EMAIL: {len(all_people)}")
print(f"{'=' * 60}")

# Randomize and select 250
if len(all_people) >= 250:
    random.shuffle(all_people)
    selected = all_people[:250]
    status = "✅"
else:
    selected = all_people
    status = "⚠️"

print(f"{status} Selected {len(selected)} prospects")

# Save to CSV
with open("/Users/bot/.openclaw/workspace/acuoi/prospects_wide.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "first_name", "last_name", "title", "linkedin_url", "email", 
                     "company", "domain", "website", "company_linkedin", "email_1", "hook"])
    for p in selected:
        org = p.get("organization", {}) or {}
        writer.writerow([
            p.get("id", ""),
            p.get("first_name", ""),
            p.get("last_name", ""),
            p.get("title", ""),
            p.get("linkedin_url", ""),
            p.get("email", ""),
            org.get("name", ""),
            org.get("primary_domain", ""),
            org.get("website_url", ""),
            org.get("linkedin_url", ""),
            "",
            ""
        ])

print(f"\n📄 Saved to prospects_wide.csv")
print(f"\nSample prospects:")
for p in selected[:5]:
    org = p.get("organization", {}) or {}
    print(f"  - {p.get('first_name')} {p.get('last_name')}, {p.get('title')} @ {org.get('name')} ({p.get('email')})")
