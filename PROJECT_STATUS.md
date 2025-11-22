# Lead Generation System - Project Status

## Overview

Modular lead generation automation system for Kazakhstan market (OLX, Kaspi) with WhatsApp/Telegram integration.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI |
| Database | Supabase (PostgreSQL) |
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Messaging | Telegram Bot API, WAHA (WhatsApp) |
| Analytics | Yandex.Metrika API, Custom Data Intake |
| AI | OpenAI GPT-4, Anthropic Claude |

## Architecture

```
Market Research → Traffic Generation → Lead Qualification → Sales Handoff → Analytics
```

## Modules Status

| Module | Status | Description |
|--------|--------|-------------|
| 1-market-research | Planned | Niche analysis, competitor research |
| 2-traffic-generation | Planned | Ad posting automation (OLX, Kaspi) |
| 3-lead-qualification | In Progress | Visitor tracking, lead scoring |
| 4-sales-handoff | Planned | CRM integration, notifications |
| 5-analytics | Active | Dashboards, reporting |
| competitor_parser | Done | OLX competitor ad parsing |
| platforms (OLX/Satu) | In Progress | Platform-specific APIs |

## Data Intake Pipeline (NEW)

3-layer ETL architecture for analytics:

```
L1 (Raw)        → L2 (Normalized)     → L3 (Features)
raw_events      → normalized_events   → feature_store
```

### Database Tables

| Table | Layer | Purpose |
|-------|-------|---------|
| `raw_events` | L1 | Raw data from all sources |
| `normalized_events` | L2 | Unified event format |
| `feature_store` | L3 | Computed features (hot_score, segment_type) |
| `visitors` | - | Website visitor tracking |
| `user_feature_aggregates` | - | User-level aggregates |
| `data_intake_log` | - | ETL pipeline logs |

### Key Features Computed

- `hot_score_base` (0-100) - Lead temperature
- `engagement_score` - User engagement level
- `intent_score` - Purchase intent
- `segment_type` - User segment classification
- `decision_stage` - Funnel position

## API Endpoints

### Backend (Port 8001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/metrika/counters` | GET | Yandex.Metrika counters |
| `/api/metrika/report` | GET | Metrika reports |
| `/api/data-intake/health` | GET | Data Intake status |
| `/api/data-intake/pipeline/run` | POST | Run ETL pipeline |
| `/api/data-intake/features` | GET | Get computed features |
| `/api/data-intake/features/hot` | GET | Get hot leads |

### Frontend (Port 3001)

| Route | Description |
|-------|-------------|
| `/dashboard` | Main dashboard |
| `/dashboard/analytics` | Analytics overview |
| `/dashboard/analytics/yandex-metrika` | Metrika reports |
| `/dashboard/analytics/data-intake` | Data Intake Pipeline UI |

## Quick Start

```bash
# Backend
source venv/bin/activate
uvicorn core.api.main:app --reload --port 8001

# Frontend
cd frontend && npm run dev
```

## Environment Variables

Required in `.env`:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon key
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `YANDEX_METRIKA_TOKEN` - Yandex.Metrika OAuth token
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (optional)

## Current Focus

1. Data Intake Pipeline - collecting analytics data
2. Feature Store - computing lead scores
3. Analytics Agent integration (upcoming)

---
Last updated: 2025-11-22
