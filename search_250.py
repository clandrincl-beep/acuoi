#!/usr/bin/env python3
"""
Re-search acuoi (Cannabis Payments) to get 250 prospects WITH EMAIL.
Keep searching until we have enough candidates with has_email=true.
"""

import json
import subprocess
import csv
import random
from datetime import datetime
import os
import shutil

API_KEY = "bU-QRYx_09EBsiU4d2GJmA"
FOLDER = "/Users/bot/.openclaw/workspace/acuoi"
TARGET = 250

# Load existing ICP from state.json
with open(f"{FOLDER}/state.json") as f:
    state = json.load(f)

ORG_FILTERS = state["icp"]["org_filters"]
PEOPLE_TITLES = state["icp"]["people_filters"]["person_titles"]

print(f"ICP loaded from state.json")
print(f"Org filters: {json.dumps(ORG_FILTERS, indent=2)}")
print(f"People titles: {PEOPLE_TITLES}")
print(f"Target: {TARGET} prospects with email")
print("-" * 50)

def api_call(endpoint, payload):
    cmd = [
        'curl', '-s', '-X', 'POST',
        f'https://api.apollo.io/api/v1/{endpoint}',
        '-H', 'Content-Type: application/json',
        '-H', f'x-api-key: {API_KEY}',
        '-d', json.dumps(payload)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"API error: {result.stdout[:500]}")
        return {}

# Archive existing prospects.csv
if os.path.exists(f"{FOLDER}/prospects.csv"):
    archive_dir = f"{FOLDER}/archive"
    os.makedirs(archive_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.move(f"{FOLDER}/prospects.csv", f"{archive_dir}/prospects-{timestamp}.csv")
    print(f"Archived existing prospects.csv")

# Phase 1: Search until we have TARGET candidates with has_email
candidates = []  # (person, org_data)
org_data = {}  # company_name -> org info
companies_seen = set()
page = 1
max_pages = 100  # Search up to 10,000 orgs if needed

print(f"\n=== Phase 1: Searching for {TARGET} candidates with email ===\n")

while len(candidates) < TARGET and page <= max_pages:
    # Fetch orgs
    org_payload = {
        **ORG_FILTERS,
        "page": page,
        "per_page": 100
    }
    org_result = api_call("mixed_companies/search", org_payload)
    orgs = org_result.get('organizations', [])
    
    if not orgs:
        print(f"Page {page}: No more orgs found")
        break
    
    org_ids = [o['id'] for o in orgs]
    org_name_to_data = {o['name']: o for o in orgs}
    
    # Fetch people with title filters
    people_result = api_call("mixed_people/api_search", {
        "organization_ids": org_ids,
        "person_titles": PEOPLE_TITLES,
        "per_page": 100,
        "page": 1
    })
    people = people_result.get('people', [])
    
    page_added = 0
    # 1 person per company, ONLY if has_email
    for p in people:
        # CRITICAL: skip if no email available
        if not p.get('has_email'):
            continue
        
        company_name = p.get('organization', {}).get('name')
        if not company_name or company_name in companies_seen:
            continue
        
        companies_seen.add(company_name)
        candidates.append(p)
        org_data[company_name] = org_name_to_data.get(company_name, {})
        page_added += 1
    
    print(f"Page {page}: +{page_added} with email → Total: {len(candidates)}/{TARGET}")
    page += 1

print(f"\n=== Found {len(candidates)} candidates with email from {page-1} pages ===\n")

if len(candidates) < TARGET:
    print(f"⚠️  Only found {len(candidates)} candidates with email (target: {TARGET})")
    print("Consider broadening filters or accepting fewer prospects.")
    # Continue with what we have
    TARGET = len(candidates)

# RANDOMIZE and select
random.shuffle(candidates)
selected = candidates[:TARGET]
person_ids = [p.get('id') for p in selected]

print(f"Selected {len(person_ids)} random prospects")

# Phase 2: Bulk enrich to get full names + emails
print(f"\n=== Phase 2: Enriching {len(person_ids)} prospects ===\n")

enriched = []
batch_size = 10

for i in range(0, len(person_ids), batch_size):
    batch = person_ids[i:i+batch_size]
    result = api_call("people/bulk_match", {
        "details": [{"id": pid} for pid in batch]
    })
    matches = result.get('matches', [])
    enriched.extend(matches)
    print(f"Enriched {len(enriched)}/{len(person_ids)}...")

# Phase 3: Export CSV
print(f"\n=== Phase 3: Exporting CSV ===\n")

rows = []
with_email = 0
unique_companies = set()

for p in enriched:
    company_name = p.get('organization', {}).get('name', '')
    org = org_data.get(company_name, {})
    email = p.get('email', '')
    
    if email:
        with_email += 1
    if company_name:
        unique_companies.add(company_name)
    
    rows.append({
        'person_id': p.get('id', ''),
        'first_name': p.get('first_name', ''),
        'last_name': p.get('last_name', ''),
        'title': p.get('title', ''),
        'linkedin_url': p.get('linkedin_url', ''),
        'email': email,
        'company_name': company_name,
        'company_domain': org.get('primary_domain', '') or p.get('organization', {}).get('primary_domain', ''),
        'company_website': org.get('website_url', ''),
        'company_linkedin': org.get('linkedin_url', ''),
        'company_employees': org.get('estimated_num_employees', ''),
    })

output_path = f"{FOLDER}/prospects.csv"
with open(output_path, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

# Update state.json
state["steps"]["find-prospects"] = {
    "status": "completed",
    "candidates_found": len(candidates),
    "selected": len(selected),
    "with_email": with_email,
    "credits_used": len(person_ids)
}
with open(f"{FOLDER}/state.json", 'w') as f:
    json.dump(state, f, indent=2)

print(f"""
✅ Prospects exported

Total contacts:     {len(rows)}
Unique companies:   {len(unique_companies)}
With email:         {with_email}
Credits used:       {len(person_ids)}

Saved: {output_path}
State updated: {FOLDER}/state.json
""")
