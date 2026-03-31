# Volunteer Coordinator — Agent Context

## What This Project Is

An automated volunteer coordination pipeline for Riverside Community Foundation. The system manages the complete volunteer lifecycle: application screening, opportunity matching, onboarding packet generation, shift scheduling, reminders, and monthly recognition/reporting.

Six workflows run at different cadences: on-demand application screening, weekly matching, on-demand onboarding, daily reminders, and two monthly workflows (recognition and reporting).

## Data Model — What's in Each File

| File | What It Contains | Who Reads It | Who Writes It |
|---|---|---|---|
| `config/org-profile.yaml` | Org profile, recognition tiers, orientation slots, GitHub repo info | All agents | Never modified by agents |
| `data/applications/<vol-id>.json` | Raw volunteer applications (status: pending_review) | volunteer-screener | ingest-application.sh |
| `data/applications/<vol-id>-decision.json` | Screening decisions and notification content | volunteer-screener | volunteer-screener |
| `data/profiles/<vol-id>.json` | Approved volunteer profiles (name, skills, availability, hours, status) | All agents | volunteer-screener (create), opportunity-matcher (update matched_opportunities) |
| `data/profiles/waitlist.json` | Waitlisted volunteers with priority scores | opportunity-matcher | volunteer-screener |
| `data/opportunities/<opp-id>.json` | Open volunteer positions (required_count, confirmed_count, schedule, skills) | volunteer-screener, opportunity-matcher | opportunity-matcher (decrement spots) |
| `data/schedules/upcoming-shifts.json` | Upcoming shift roster with volunteer assignments and coverage status | shift-scheduler | shift-scheduler |
| `data/schedules/matches-<date>.json` | Weekly matching results (volunteer → opportunity assignments) | opportunity-matcher | opportunity-matcher |
| `data/schedules/notifications/<id>-match.json` | Match notifications (personalized per volunteer) | Volunteers | opportunity-matcher |
| `data/schedules/reminders-<date>.json` | Daily shift reminders per volunteer | Volunteers | shift-scheduler |
| `data/schedules/coverage-<date>.json` | Daily coverage summary across all shifts | program-reporter | shift-scheduler |
| `data/schedules/gaps-<date>.json` | Matching gap records (unmatched volunteers, unfilled opportunities) | program-reporter | opportunity-matcher |
| `data/history/impact-metrics-<YYYY-MM>.json` | Monthly volunteer hours and attendance metrics | recognition-generator | calculate-impact.py |
| `data/history/program-metrics-<YYYY-MM>.json` | Monthly program-wide aggregated stats | program-reporter | aggregate-metrics.py |
| `onboarding/<vol-id>-onboarding.md` | Personalized onboarding packet (welcome letter, role overview, checklist) | Volunteers | onboarding-writer |
| `reports/recognition/<vol-id>-certificate-<YYYY-MM>.md` | Individual recognition certificates | Volunteers | recognition-generator |
| `reports/monthly/impact-<YYYY-MM>.md` | Monthly volunteer impact report | Leadership, program-reporter | recognition-generator |
| `reports/monthly/program-<YYYY-MM>.md` | Monthly program leadership report | Leadership | program-reporter |

## Memory MCP — Volunteer Profile Store

The memory MCP is the primary runtime store for volunteer profiles. It persists across workflow runs and enables:
- `opportunity-matcher`: Load all active volunteer profiles without reading individual files
- `recognition-generator`: Access full volunteer history including qualitative notes from shift supervisors
- `onboarding-writer`: Personalize packets without re-reading profile JSON files
- `program-reporter`: Assess retention and lifecycle without iterating file system

When `create-volunteer-profile` runs, it stores the profile in BOTH memory AND data/profiles/. Memory is the live cache; files are the durable backup.

## Volunteer Status Lifecycle

```
Application submitted → pending_review
   ↓ screen-application
approved → active (profile created, in matching pool)
waitlisted → waitlisted (in data/profiles/waitlist.json, not active)
declined → no profile stored

active → matched (after opportunity-matcher assigns a role)
matched → onboarded (after onboarding packet delivered and orientation scheduled)
onboarded → active (ongoing, shifts logged)
active → inactive (60+ days no shifts — flag for outreach in monthly report)
```

## Decision Contracts

**screen-application** — verdict options:
- `approve`: Skills and availability match at least one opportunity. Create profile and enter matching pool.
- `waitlist`: Qualified applicant but no current opportunity fits. Save to waitlist with priority score.
- `decline`: Incomplete application, below minimum hours commitment, or no viable fit.

**match-to-opportunity** — verdict options:
- `excellent` (85-100 score): Strong match. Assign and notify immediately.
- `good` (65-84 score): Good match with minor gaps. Assign with notes.
- `partial` (40-64 score): Weak match. Assign only if no alternatives; flag for manager review.
- `no-match` (<40 score): No viable assignment. Flag gaps; create GitHub issue if persistent.

## Key Invariants Agents Must Respect

1. **No double-assignment**: Before matching a volunteer to an opportunity, check their `matched_opportunities` array. Never assign the same opportunity twice.

2. **Spot limits**: Always decrement `confirmed_count` and check `confirmed_count < required_count` before assigning a volunteer to an opportunity. If `confirmed_count >= required_count`, the opportunity is full.

3. **Availability check**: Every match must verify the volunteer's available days/times overlap with the opportunity schedule. A mismatch on availability is an immediate disqualifier.

4. **Background check gate**: Opportunities with `"background_check": "required"` may only receive volunteers who have `background_check_cleared: true` in their profile (or this field is absent, meaning not yet assessed — flag for follow-up).

5. **Waitlist priority**: When a spot opens and multiple waitlisted volunteers qualify, sort by `priority_score` descending, then by `waitlisted_date` ascending (FIFO tiebreak).

6. **Memory sync**: After any profile update (matching, hours logged, status change), update BOTH memory MCP and the JSON file in data/profiles/. They must stay in sync.

7. **Certificate specificity**: Recognition certificates must include the volunteer's actual hours, specific shifts, and named contributions. Generic certificates undermine the program's volunteer retention goals.

## Workflow Entry Points

| Workflow | When to Run | Command |
|---|---|---|
| `screen-volunteer` | New application received | `ao queue enqueue --title "screen-<name>" --workflow-ref screen-volunteer --input '<application JSON>'` |
| `weekly-matching` | Every Monday (auto) | `ao workflow run weekly-matching` |
| `onboard-volunteer` | After matching completes | `ao workflow run onboard-volunteer` |
| `daily-reminders` | Every morning at 8am (auto) | `ao workflow run daily-reminders` |
| `monthly-recognition` | 1st of month at 10am (auto) | `ao workflow run monthly-recognition` |
| `monthly-report` | 1st of month at 11am (auto) | `ao workflow run monthly-report` |

## Script Assumptions

The Python scripts use only the standard library (json, os, datetime, hashlib). They expect:
- Python 3.8+ with no external packages
- Working directory is `examples/volunteer-coordinator/` (all paths are relative to project root)
- Existing data directory structure (scripts create missing dirs with os.makedirs)
- Scripts handle missing/empty files gracefully with sensible defaults
