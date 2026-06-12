# LeadStack — Personal Multi-Industry CRM (GoHighLevel Alternative)

A self-owned, white-label CRM platform that runs multiple isolated businesses
(Real Estate, Music Production, E-commerce, AI Consulting, …) from a single
deployment. FastAPI + PostgreSQL backend, React + Tailwind frontend.

## Core capabilities

| Area | What ships |
| --- | --- |
| **Multi-tenancy** | Agency → SubAccount → Member hierarchy. Every CRM row carries `sub_account_id`; a SQLAlchemy `do_orm_execute` listener injects row-level filtering on every ORM query, so cross-workspace leaks are impossible. The active workspace is selected via the `X-SubAccount-ID` header (set globally by the frontend switcher). |
| **Deal pipeline** | 6 stages (New Lead → Contacted → Qualified → Proposal Sent → Won / Lost). Drag-and-drop Kanban (`@dnd-kit`), enforced lost reasons, and instant cross-tab sync over the `/ws/pipeline` WebSocket. |
| **Lead capture** | Visual form builder (drag-to-order fields, required toggles), one-tag iframe embed (`Copy Embed Code`), public unauthenticated ingestion that maps submissions into the owning workspace. Framing explicitly allowed (`frame-ancestors *`) with permissive CORS on the public endpoints only. |
| **Automation engine** | Workflow → Steps → ExecutionLog with explicit states: `PENDING`, `COMPLETED`, `FAILED`, `SKIPPED_COMPLIANCE`, `PAUSED_QUIET_HOURS`. Merge tags (`{{contact.first_name}}`, `{{sub_account.name}}`) interpolated just before transmission. Background asyncio runner executes due steps. |
| **A2P compliance** | `ComplianceRegistry` per workspace. Inbound STOP/UNSUBSCRIBE/QUIT flips `has_opted_out` instantly; a pre-flight interceptor blocks ANY outbound SMS/email to registered numbers. Quiet hours respected per workspace timezone with automatic rescheduling. |
| **Speed-to-Lead** | Seeded per workspace: Form Submission → instant SMS → instant Email → Wait 1 min → internal owner notification. |
| **AI receptionist** | One isolated persona per workspace (`AIReceptionistConfig`). Train it from a URL or pasted text (HTML/scripts/CSS stripped to clean markdown). Provider chain: Anthropic Claude 3.5 → OpenAI → local Ollama. Answers web chat + inbound SMS and autonomously extracts name/phone, promoting sessions into Contacts. |
| **White-label** | `BrandingConfig` (name, logos, colors, domain) backed by `.env` defaults and editable live. Frontend binds its entire palette to CSS custom properties at runtime; outbound sender identity (From name / Reply-To / SMS sender) follows the active sub-account profile. |
| **Marketing site** | `/landing` — dark/neon-purple single page: hero, 6-step strategy, workspace showcase, feature matrix, GHL/HubSpot comparison table, interactive ROI calculator, FAQ accordion. |

## Running it

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in Twilio/SendGrid/AI keys as available
uvicorn app.main:app --reload --port 8000
```

Requires PostgreSQL (`DATABASE_URL` in `.env`). Tables are created and a
default agency with four business workspaces (plus their Speed-to-Lead
workflows) is seeded on first boot.

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173  (VITE_API_URL to point elsewhere)
```

### Tests

```bash
cd backend
python -m pytest tests/test_tenancy.py tests/test_pipeline.py \
  tests/test_forms_and_automations.py tests/test_ai_receptionist.py \
  tests/test_branding.py -q
```

## Key endpoints

- `GET/POST /api/v1/sub-accounts/` — workspace management (unscoped)
- `/api/v1/contacts|deals|conversations|messages|forms|automations|receptionist/...` — tenant-scoped (require `X-SubAccount-ID`)
- `GET /api/v1/public/forms/{id}/render` — embeddable form document
- `POST /api/v1/public/forms/{id}/submit` — public lead ingestion
- `POST /api/v1/public/chat/{sub_account_id}` — web-chat widget
- `GET /api/v1/public/branding` — theme bootstrap
- `POST /api/v1/webhooks/twilio/sms` — inbound SMS (opt-outs + AI routing)
- `WS /ws/pipeline?sub_account_id=...` — real-time Kanban sync

---

Built on the bones of the public `omni-channel-crm` scaffold; its original
PRDs and module specs remain available in that repository.
