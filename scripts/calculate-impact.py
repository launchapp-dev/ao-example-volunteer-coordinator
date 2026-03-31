#!/usr/bin/env python3
"""calculate-impact.py — Aggregate volunteer hours and shift attendance for monthly recognition."""
import json
import os
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data", "history")
PROFILES_DIR = os.path.join(PROJECT_ROOT, "data", "profiles")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "history")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)

today = datetime.date.today()
last_month = (today.replace(day=1) - datetime.timedelta(days=1))
period = last_month.strftime("%Y-%m")

# Collect metrics per volunteer from history logs
volunteer_metrics = {}

if os.path.isdir(PROFILES_DIR):
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json") and filename != "waitlist.json":
            filepath = os.path.join(PROFILES_DIR, filename)
            try:
                with open(filepath) as f:
                    profile = json.load(f)
                vol_id = profile.get("volunteer_id", filename.replace(".json", ""))
                volunteer_metrics[vol_id] = {
                    "volunteer_id": vol_id,
                    "name": profile.get("name", "Unknown"),
                    "email": profile.get("email", ""),
                    "hours_this_month": profile.get("hours_logged", 0),
                    "shifts_completed": 0,
                    "shifts_scheduled": 0,
                    "reliability_score": profile.get("reliability_score", 1.0),
                    "months_active": profile.get("months_active", 1),
                    "lifetime_hours": profile.get("hours_logged", 0),
                    "consecutive_months": 1,
                }
            except (json.JSONDecodeError, KeyError):
                pass

# Write aggregated metrics
metrics_output = {
    "period": period,
    "calculated_at": datetime.datetime.utcnow().isoformat(),
    "total_volunteers": len(volunteer_metrics),
    "total_hours": sum(v["hours_this_month"] for v in volunteer_metrics.values()),
    "volunteer_metrics": list(volunteer_metrics.values()),
}

output_path = os.path.join(OUTPUT_DIR, f"impact-metrics-{period}.json")
with open(output_path, "w") as f:
    json.dump(metrics_output, f, indent=2)

print(json.dumps({
    "status": "calculated",
    "period": period,
    "volunteers_measured": len(volunteer_metrics),
    "total_hours": metrics_output["total_hours"],
    "output_path": output_path,
}))
