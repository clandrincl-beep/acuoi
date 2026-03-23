#!/usr/bin/env python3
"""
Get 51 more cannabis prospects - different keywords
"""
import subprocess
import json
import csv
import random
import time

API_KEY = "bU-QRYx_09EBsiU4d2GJmA"

def api_call(endpoint, payload):
    cmd = [
        "curl", "-s", "-X", "POST",
        f"https://api.apollo.io/api/v1/{endpoint}",
        "-H", "Content-Type: application/json",
        "-H", f"X-Api-Key: {API_KEY}",
        "-d", json.dumps(payload)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout[:200]}

# Load existing IDs to avoid duplicates
existing_ids = set()
with open("/Users/bot/.openclaw/workspace/acuoi/prospects.csv", "r") as f:
    reader = csv.reader(f)
    next(reader)  # skip header
    for row in reader:
        if row:
            existing_ids.add(row[0])

print(f"Loaded {len(existing_ids)} existing prospect IDs")

# Search with different keywords
keywords_groups = [
    ["hemp"],
    ["CBD"],
    ["THC"],
    ["marijuana retail"],
    ["cannabis cultivation"],
    ["grow operation"],
    ["cannabis processing"],
]

all_candidates = []
seen_ids = existing_ids.copy()

for kw_group in keywords_groups:
    print(f"\n🔍 {kw_group}")
    
    for page in range(1, 4):
        payload = {
            "q_organization_keyword_tags": kw_group,
            "organization_locations": ["United States", "Canada"],
            "organization_num_employees_ranges": ["1,10", "11,20", "21,50", "51,100", "101,200", "201,500", "501,1000"],
            "person_titles": ["owner", "founder", "CEO", "CFO", "COO", "president", "GM", "director", "VP", "finance", "controller", "operations", "managing director", "partner"],
            "page": page,
            "per_page": 100
        }
        
        resp = api_call("mixed_people/api_search", payload)
        people = resp.get("people", [])
        
        if not people:
            break
            
        new_this_page = 0
        for p in people:
            pid = p.get("id")
            has_email = p.get("has_email", False)
            if pid and pid not in seen_ids and has_email:
                seen_ids.add(pid)
                new_this_page += 1
                all_candidates.append({
                    "id": pid,
                    "first_name": p.get("first_name", ""),
                    "org_name": (p.get("organization") or {}).get("name", ""),
                    "org_domain": (p.get("organization") or {}).get("primary_domain", ""),
                })
        
        print(f"   Page {page}: +{new_this_page} new, {len(all_candidates)} total new candidates")
        
        if len(all_candidates) >= 100:
            break
    
    if len(all_candidates) >= 100:
        break

print(f"\nNew candidates: {len(all_candidates)}")

# Enrich in batches
print("\n📧 Enriching...")
enriched = []

for i in range(0, min(len(all_candidates), 80), 10):
    batch = all_candidates[i:i+10]
    details = [{"id": c["id"], "first_name": c["first_name"], "organization_name": c["org_name"], "domain": c["org_domain"]} for c in batch]
    
    resp = api_call("people/bulk_match", {"details": details, "reveal_personal_emails": False})
    matches = resp.get("matches", [])
    
    for m in matches:
        if m and m.get("email"):
            enriched.append(m)
    
    print(f"   Batch {i//10 + 1}: {len([m for m in matches if m and m.get('email')])} with email, {len(enriched)} total")
    time.sleep(0.5)
    
    if len(enriched) >= 60:
        break

print(f"\n✅ Got {len(enriched)} more enriched prospects")

# Append to existing CSV
with open("/Users/bot/.openclaw/workspace/acuoi/prospects.csv", "a", newline="") as f:
    writer = csv.writer(f)
    for p in enriched[:55]:  # Only need ~51
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

# Count final
with open("/Users/bot/.openclaw/workspace/acuoi/prospects.csv", "r") as f:
    total = sum(1 for _ in f) - 1  # minus header

print(f"\n📄 Total prospects now: {total}")
