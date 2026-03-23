#!/usr/bin/env python3
"""
Cannabis industry: Search with has_email filter, then bulk enrich to get real data
Target: 250 enriched prospects
"""
import subprocess
import json
import csv
import random
import time

API_KEY = "bU-QRYx_09EBsiU4d2GJmA"

def api_call(endpoint, payload, method="POST"):
    cmd = [
        "curl", "-s", "-X", method,
        f"https://api.apollo.io/api/v1/{endpoint}",
        "-H", "Content-Type: application/json",
        "-H", f"X-Api-Key: {API_KEY}",
        "-d", json.dumps(payload)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stdout[:500]}

print("=" * 60)
print("CANNABIS - SEARCH + ENRICH")
print("Target: 250 enriched prospects with email")
print("=" * 60)

# Step 1: Search for people with email
all_candidates = []
seen_ids = set()

keywords_groups = [
    ["cannabis"],
    ["dispensary"],
    ["marijuana"],
    ["hemp", "CBD"],
    ["cultivation", "cultivator"],
]

for kw_group in keywords_groups:
    print(f"\n🔍 Searching: {kw_group}")
    
    for page in range(1, 6):  # Up to 5 pages per group
        payload = {
            "q_organization_keyword_tags": kw_group,
            "organization_locations": ["United States", "Canada"],
            "organization_num_employees_ranges": ["1,10", "11,20", "21,50", "51,100", "101,200", "201,500"],
            "person_titles": ["owner", "founder", "CEO", "CFO", "COO", "president", "general manager", "director", "VP", "finance", "controller", "operations"],
            "page": page,
            "per_page": 100
        }
        
        resp = api_call("mixed_people/api_search", payload)
        people = resp.get("people", [])
        
        if not people:
            break
            
        for p in people:
            pid = p.get("id")
            has_email = p.get("has_email", False)
            if pid and pid not in seen_ids and has_email:
                seen_ids.add(pid)
                all_candidates.append({
                    "id": pid,
                    "first_name": p.get("first_name", ""),
                    "title": p.get("title", ""),
                    "org_name": (p.get("organization") or {}).get("name", ""),
                    "org_domain": (p.get("organization") or {}).get("primary_domain", ""),
                })
        
        print(f"   Page {page}: +{len(people)}, {len(all_candidates)} candidates with email flag")
        
        if len(all_candidates) >= 400:
            break
    
    if len(all_candidates) >= 400:
        print("✅ Got 400+ candidates, moving to enrichment")
        break

print(f"\n{'=' * 60}")
print(f"CANDIDATES WITH has_email=true: {len(all_candidates)}")
print(f"{'=' * 60}")

if len(all_candidates) < 250:
    print(f"⚠️ Only {len(all_candidates)} candidates - proceeding anyway")

# Step 2: Randomize and select 300 for enrichment (buffer for failures)
random.shuffle(all_candidates)
to_enrich = all_candidates[:300]
print(f"\n📧 Enriching {len(to_enrich)} candidates...")

# Step 3: Bulk match to get emails
enriched = []
batch_size = 10  # Apollo allows up to 10 per call

for i in range(0, len(to_enrich), batch_size):
    batch = to_enrich[i:i+batch_size]
    
    # Build match request
    details = []
    for c in batch:
        details.append({
            "id": c["id"],
            "first_name": c["first_name"],
            "organization_name": c["org_name"],
            "domain": c["org_domain"]
        })
    
    payload = {"details": details, "reveal_personal_emails": False}
    resp = api_call("people/bulk_match", payload)
    
    matches = resp.get("matches", [])
    for m in matches:
        if m and m.get("email"):
            enriched.append(m)
    
    print(f"   Batch {i//batch_size + 1}: {len(matches)} matched, {len(enriched)} total enriched")
    time.sleep(0.3)  # Rate limit
    
    if len(enriched) >= 250:
        print("✅ Got 250 enriched!")
        break

print(f"\n{'=' * 60}")
print(f"ENRICHED WITH EMAIL: {len(enriched)}")
print(f"{'=' * 60}")

# Save to CSV
final = enriched[:250]
with open("/Users/bot/.openclaw/workspace/acuoi/prospects.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "first_name", "last_name", "title", "linkedin_url", "email", 
                     "company", "domain", "website", "company_linkedin", "email_1", "hook"])
    for p in final:
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

print(f"\n✅ Saved {len(final)} prospects to prospects.csv")
print(f"\nSample:")
for p in final[:5]:
    org = p.get("organization", {}) or {}
    print(f"  - {p.get('first_name')} {p.get('last_name')}, {p.get('title')} @ {org.get('name')}")
    print(f"    {p.get('email')}")
