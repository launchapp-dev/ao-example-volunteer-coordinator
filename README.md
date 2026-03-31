# Volunteer Coordinator

An automated volunteer coordination pipeline that handles the full volunteer lifecycle: screening applications, matching to opportunities, generating onboarding packets, scheduling shifts, sending reminders, and compiling monthly impact reports.

Built with [AO](https://github.com/launchapp-dev/ao) — demonstrates multi-agent pipelines with decision routing, the memory MCP for persistent volunteer profiles, and GitHub integration for tracking capacity gaps.

## What It Does

| Workflow | Trigger | What Happens |
|---|---|---|
| `screen-volunteer` | New application arrives | Screen for fit → approve, waitlist, or decline |
| `weekly-matching` | Every Monday 9am | Match approved volunteers to open opportunities |
| `onboard-volunteer` | After matching | Generate personalized packet + schedule orientation |
| `daily-reminders` | Every day 8am | Check shift coverage + send 24hr reminders |
| `monthly-recognition` | 1st of month 10am | Calculate impact metrics + generate certificates |
| `monthly-report` | 1st of month 11am | Compile leadership report + create GitHub issues for gaps |

## Agents

| Agent | Model | Role |
|---|---|---|
| `volunteer-screener` | claude-haiku-4-5 | Reviews applications, makes approve/waitlist/decline decisions |
| `opportunity-matcher` | claude-sonnet-4-6 | Scores volunteer-opportunity fit, routes on match quality |
| `onboarding-writer` | claude-sonnet-4-6 | Generates personalized onboarding packets |
| `shift-scheduler` | claude-haiku-4-5 | Manages rosters, flags coverage gaps, sends reminders |
| `recognition-generator` | claude-sonnet-4-6 | Calculates impact, selects awardees, writes certificates |
| `program-reporter` | claude-haiku-4-5 | Aggregates metrics, compiles leadership reports |

## AO Features Demonstrated

- **Decision contracts** — `screen-application` routes on `approve/waitlist/decline`; `match-to-opportunity` routes on `excellent/good/partial/no-match`
- **Phase routing** — waitlisted applicants bypass profile creation; partial matches trigger gap-flagging instead of notifications
- **Memory MCP** — volunteer profiles persist across workflow runs for matching and personalization
- **Scheduled workflows** — four cron-triggered workflows at different cadences
- **GitHub MCP** — capacity gaps and attrition alerts automatically become GitHub issues

## Quick Start

### Prerequisites

- [AO CLI](https://github.com/launchapp-dev/ao) installed
- `GITHUB_TOKEN` environment variable set (for monthly reporting)
- `ANTHROPIC_API_KEY` environment variable set

```bash
# Clone and enter the example
git clone https://github.com/launchapp-dev/ao-example-volunteer-coordinator
cd ao-example-volunteer-coordinator

# Copy environment config
cp .env.example .env
# Edit .env with your GitHub token

# Start the daemon (scheduled workflows run automatically)
ao daemon start

# Watch live logs
ao daemon stream --pretty
```

### Screen a New Volunteer Application

```bash
ao queue enqueue \
  --title "screen-volunteer" \
  --description "New application from Jordan Taylor" \
  --workflow-ref screen-volunteer
```

Or with application data:

```bash
ao queue enqueue \
  --title "screen-jordan-taylor" \
  --workflow-ref screen-volunteer \
  --input '{
    "name": "Jordan Taylor",
    "email": "jordan@example.com",
    "availability": {"days": ["Tuesday", "Thursday"], "hours_per_week": 6},
    "skills": ["food-handling", "customer-service"],
    "hours_per_month": 16,
    "motivation": "I want to help address food insecurity in our community."
  }'
```

### Run Weekly Matching Manually

```bash
ao workflow run weekly-matching
```

### Check Workflow Status

```bash
ao status
ao task list
```

## Project Structure

```
volunteer-coordinator/
├── .ao/workflows/
│   ├── agents.yaml          # 6 agents: screener, matcher, onboarding, scheduler, recognition, reporter
│   ├── phases.yaml          # 17 phases across 6 workflows
│   ├── workflows.yaml       # 6 workflows with decision routing
│   ├── mcp-servers.yaml     # filesystem, memory, github
│   └── schedules.yaml       # 4 cron schedules
├── config/
│   └── org-profile.yaml     # Organization profile, recognition tiers, orientation schedule
├── data/
│   ├── applications/        # Incoming volunteer applications (pending_review → decided)
│   ├── profiles/            # Approved volunteer profiles + waitlist.json
│   ├── opportunities/       # Open volunteer positions
│   ├── schedules/           # Shift rosters, match results, reminders
│   └── history/             # Monthly metric snapshots for trend analysis
├── onboarding/              # Generated onboarding packets (per volunteer)
├── reports/
│   ├── recognition/         # Monthly recognition certificates
│   └── monthly/             # Monthly impact and program reports
├── scripts/
│   ├── ingest-application.sh      # Normalize incoming applications
│   ├── load-active-volunteers.py  # Summarize volunteer pool for matching
│   ├── calculate-impact.py        # Aggregate hours/attendance for recognition
│   └── aggregate-metrics.py      # Aggregate program stats for leadership report
└── .env.example             # Required environment variables
```

## Data Flow

```
Application arrives
      ↓
ingest-application (bash script normalizes JSON)
      ↓
screen-application (haiku: reviews + scores)
      ↓
approve → create-volunteer-profile → memory MCP stores profile
waitlist → send-waitlist-notice → waitlist.json
decline → send-decline-notice

Weekly:
load-active-volunteers → match-to-opportunity → excellent/good → generate-match-notifications
                                              → partial/no-match → flag-matching-gaps → GitHub issues

Monthly:
calculate-impact.py → select-and-recognize → certificates + impact report
aggregate-metrics.py → compile-program-report → leadership report + GitHub issues
```
