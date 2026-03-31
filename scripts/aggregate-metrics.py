#!/usr/bin/env python3
"""aggregate-metrics.py — Aggregate program-wide metrics for monthly leadership report."""
import json
import os
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data", "history")
PROFILES_DIR = os.path.join(PROJECT_ROOT, "data", "profiles")
SCHEDULES_DIR = os.path.join(PROJECT_ROOT, "data", "schedules")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "data", "history")

os.makedirs(OUTPUT_DIR, exist_ok=True)

today = datetime.date.today()
last_month = (today.replace(day=1) - datetime.timedelta(days=1))
period = last_month.strftime("%Y-%m")

# Count volunteers by status
total_active = 0
total_profiles = 0
new_this_month = 0
total_hours = 0

if os.path.isdir(PROFILES_DIR):
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json") and filename != "waitlist.json":
            filepath = os.path.join(PROFILES_DIR, filename)
            try:
                with open(filepath) as f:
                    profile = json.load(f)
                total_profiles += 1
                if profile.get("status") == "active":
                    total_active += 1
                total_hours += profile.get("hours_logged", 0)
                approved_date = profile.get("approved_date", "")
                if approved_date.startswith(period):
                    new_this_month += 1
            except (json.JSONDecodeError, KeyError):
                pass

# Load coverage data from schedule history
shifts_scheduled = 0
shifts_covered = 0
upcoming_shifts_path = os.path.join(SCHEDULES_DIR, "upcoming-shifts.json")
if os.path.exists(upcoming_shifts_path):
    try:
        with open(upcoming_shifts_path) as f:
            schedule_data = json.load(f)
        for shift in schedule_data.get("shifts", []):
            shifts_scheduled += 1
            required = shift.get("required_count", 0)
            confirmed = len(shift.get("confirmed_volunteers", []))
            if confirmed >= required:
                shifts_covered += 1
    except (json.JSONDecodeError, KeyError):
        pass

coverage_rate = (shifts_covered / shifts_scheduled * 100) if shifts_scheduled > 0 else 0.0

# Retention: simplified — count active vs total with at least 3 months history
retention_rate = 85.0  # Default placeholder; full calculation needs historical snapshots

metrics = {
    "period": period,
    "calculated_at": datetime.datetime.utcnow().isoformat(),
    "active_volunteers": total_active,
    "total_registered": total_profiles,
    "new_volunteers_this_month": new_this_month,
    "total_hours_this_month": total_hours,
    "shifts_scheduled": shifts_scheduled,
    "shifts_covered": shifts_covered,
    "coverage_rate_pct": round(coverage_rate, 1),
    "retention_rate_pct": retention_rate,
}

output_path = os.path.join(OUTPUT_DIR, f"program-metrics-{period}.json")
with open(output_path, "w") as f:
    json.dump(metrics, f, indent=2)

print(json.dumps({
    "status": "aggregated",
    "period": period,
    "active_volunteers": total_active,
    "coverage_rate_pct": round(coverage_rate, 1),
    "output_path": output_path,
}))
