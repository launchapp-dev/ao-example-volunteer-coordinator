#!/usr/bin/env bash
# ingest-application.sh — Normalize incoming volunteer application into data/applications/
# Usage: bash scripts/ingest-application.sh '<dispatch_input_json>'
set -euo pipefail

DISPATCH_INPUT="${1:-{}}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APPLICATIONS_DIR="$PROJECT_ROOT/data/applications"
mkdir -p "$APPLICATIONS_DIR"

python3 - <<PYTHON
import json, sys, os, datetime, hashlib

dispatch_input = json.loads('''$DISPATCH_INPUT''') if '''$DISPATCH_INPUT''' != '{}' else {}

# Generate a volunteer ID from name or timestamp
name = dispatch_input.get('name', 'unknown')
ts = datetime.datetime.utcnow().isoformat()
vol_id = 'vol-' + hashlib.md5(f"{name}-{ts}".encode()).hexdigest()[:8]

# Build normalized application record
application = {
    "application_id": vol_id,
    "submitted_at": ts,
    "status": "pending_review",
    "name": dispatch_input.get('name', ''),
    "email": dispatch_input.get('email', ''),
    "phone": dispatch_input.get('phone', ''),
    "availability": dispatch_input.get('availability', {}),
    "skills": dispatch_input.get('skills', []),
    "interests": dispatch_input.get('interests', []),
    "years_experience": dispatch_input.get('years_experience', 0),
    "motivation": dispatch_input.get('motivation', ''),
    "hours_per_month": dispatch_input.get('hours_per_month', 0),
    "emergency_contact": dispatch_input.get('emergency_contact', {}),
    "source": dispatch_input.get('source', 'direct')
}

# If no real application data, create a sample one for demonstration
if not application['name']:
    application.update({
        "application_id": "vol-demo001",
        "name": "Jordan Taylor",
        "email": "jordan.taylor@example.com",
        "phone": "(555) 234-5678",
        "availability": {
            "days": ["Tuesday", "Thursday", "Saturday"],
            "hours_per_week": 6
        },
        "skills": ["customer-service", "food-handling", "physical-activity"],
        "interests": ["food-security", "community-support"],
        "years_experience": 2,
        "motivation": "I want to give back to my community and help address food insecurity.",
        "hours_per_month": 16,
        "emergency_contact": {
            "name": "Casey Taylor",
            "phone": "(555) 345-6789",
            "relationship": "spouse"
        }
    })
    vol_id = application['application_id']

app_path = os.path.join('$APPLICATIONS_DIR', f"{vol_id}.json")
with open(app_path, 'w') as f:
    json.dump(application, f, indent=2)

print(json.dumps({"status": "ingested", "application_id": vol_id, "application_path": app_path}))
PYTHON
