#!/usr/bin/env python3
"""load-active-volunteers.py — Summarize active and unmatched volunteer profiles for matching run."""
import json
import os
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILES_DIR = os.path.join(PROJECT_ROOT, "data", "profiles")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "schedules")

os.makedirs(OUTPUT_DIR, exist_ok=True)

active_volunteers = []
unmatched_volunteers = []

if os.path.isdir(PROFILES_DIR):
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json") and filename != "waitlist.json":
            filepath = os.path.join(PROFILES_DIR, filename)
            try:
                with open(filepath) as f:
                    profile = json.load(f)
                if profile.get("status") == "active":
                    active_volunteers.append(profile["volunteer_id"])
                    if not profile.get("matched_opportunities"):
                        unmatched_volunteers.append(profile["volunteer_id"])
            except (json.JSONDecodeError, KeyError):
                pass

summary = {
    "run_date": datetime.datetime.utcnow().isoformat(),
    "total_active": len(active_volunteers),
    "total_unmatched": len(unmatched_volunteers),
    "active_volunteers": active_volunteers,
    "unmatched_volunteers": unmatched_volunteers,
}

output_path = os.path.join(OUTPUT_DIR, "volunteer-summary.json")
with open(output_path, "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps({"status": "loaded", "active": len(active_volunteers), "unmatched": len(unmatched_volunteers)}))
