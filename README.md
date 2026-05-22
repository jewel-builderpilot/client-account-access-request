# BuilderPilot — Client Account Access Request

A Flask-based client onboarding system for BuilderPilot. Automates the intake process for new home service business clients, including collecting business information and managing platform access requests for Google and Meta advertising accounts.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Features](#features)
- [Database Schema](#database-schema)
- [Environment Variables](#environment-variables)
- [Local Development Setup](#local-development-setup)
- [Gmail OAuth Setup](#gmail-oauth-setup)
- [Creating the First Admin User](#creating-the-first-admin-user)
- [Running Tests](#running-tests)
- [Deployment](#deployment)
- [Routes Reference](#routes-reference)
- [Email System](#email-system)

---

## Overview

When BuilderPilot onboards a new client (roofing, HVAC, and other home service businesses), the client fills out an 8-step intake form covering business info, services, branding, goals, and advertising platform access. The app then:

1. Stores the client record in Supabase
2. Sends consolidated access request emails (one for Google platforms, one for Meta)
3. Gives each client a unique confirmation link per platform to confirm they've granted access
4. Gives admins a dashboard to track access status, update records, and generate kickoff briefs

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Flask 3.0.3 (Python) |
| Database | Supabase (PostgreSQL, no ORM) |
| Frontend | Jinja2 templates + Tailwind CSS (CDN) + Vanilla JS |
| Email | Gmail API (OAuth2) |
| Auth | Flask-Login + bcrypt |
| Security | Flask-Talisman (CSP headers, CSRF) |
| Hosting | Vercel (serverless Python functions) |
| CI/CD | GitHub Actions |
| Testing | pytest |

---

## Project Structure

```
client-account-access-request/
├── app/
│   ├── __init__.py              # App factory (create_app)
│   ├── auth.py                  # AdminUser class, bcrypt verification
│   ├── config.py                # Dev/Prod config classes
│   ├── models.py                # All Supabase CRUD operations
│   ├── routes/
│   │   ├── client.py            # Client-facing form + confirmation routes
│   │   └── admin.py             # Admin dashboard + settings routes
│   ├── services/
│   │   ├── access_requests.py   # Access request logic + email templates
│   │   └── email.py             # Gmail API wrapper
│   ├── static/
│   │   └── js/form-stepper.js   # Multi-step form UI + client-side validation
│   └── templates/
│       ├── base.html
│       ├── client/
│       │   ├── form.html           # 8-step intake form
│       │   ├── confirm_access.html # Platform confirmation page
│       │   └── success.html        # Submission success page
│       └── admin/
│           ├── login.html
│           ├── dashboard.html      # Client list + stats
│           ├── client_detail.html  # Client details + access request statuses
│           ├── settings.html       # Admin settings + user management
│           └── kickoff_brief.html  # Formatted client kickoff brief
├── api/
│   └── index.py                 # Vercel serverless entry point
├── supabase/
│   └── schema.sql               # PostgreSQL schema (run this in Supabase SQL editor)
├── scripts/
│   ├── create_admin.py          # CLI: create first admin user
│   └── get_gmail_token.py       # CLI: obtain Gmail OAuth2 refresh token
├── tests/
│   └── test_app.py              # pytest smoke tests (mocked DB + email)
├── .github/workflows/
│   └── deploy.yml               # GitHub Actions: test on PR, deploy on main push
├── requirements.txt
├── vercel.json
└── .env.example
```

---

## Features

### Client Intake Form (8 Steps)

Route: `GET /form` → `POST /form/submit`

| Step | Content |
|---|---|
| 1 | Business info (company, owner, phone, email, website, location) |
| 2 | Services and target market |
| 3 | Branding and assets (colors, fonts, logos, photos) |
| 4 | Goals and expectations (revenue, lead volume, timeline) |
| 5 | Platform access (Google Ads, GTM, GA4, GBP, GSC, Meta BM, Facebook Page) |
| 6 | Lead delivery preferences (phone, email, SMS) |
| 7 | Ad approval and launch timeline |
| 8 | Review and submit |

For each platform in Step 5, the client selects one of:
- `has_account` — they have an existing account
- `not_sure` — unsure, access email will be sent
- `needs_created` — BuilderPilot will create the account
- `doesnt_have` — not applicable, no action needed

### Access Request Emails

After form submission, the app automatically sends:

- **Google email** — one consolidated email covering all Google platforms (Ads, GTM, GA4, GBP, GSC) with step-by-step access instructions and a unique confirmation button per platform
- **Meta email** — one email covering Meta Business Manager and Facebook Page

Each confirmation button points to a unique token URL. When the client clicks it, the corresponding access request is marked `access_granted`.

### Admin Dashboard

Route: `/admin/`

- Client list with status badges and per-platform access progress bars
- Per-client detail view: access request statuses, account IDs, onboarding event log
- Manually update request statuses and save account details
- Update client status: `pending` → `active` → `complete`
- Generate formatted kickoff brief for any client

### Admin Settings

Route: `/admin/settings`

- Agency Google Ads Manager ID and Meta Business Manager ID (embedded in emails)
- Email from name and reply-to address
- Google and Meta email subject lines and intro copy (customizable per send)
- Admin user management: add and delete admin accounts

---

## Database Schema

Run `supabase/schema.sql` in the Supabase SQL editor to create all tables.

### Tables

**`settings`** — Key-value config for agency IDs, email templates, etc.

**`admin_users`** — Admin accounts with bcrypt-hashed passwords.

**`clients`** — One row per onboarded client. `step_data` (JSONB) stores the full form submission.

**`access_requests`** — One row per platform per client.

| Column | Notes |
|---|---|
| `platform` | `google_ads`, `gtm`, `ga4`, `gbp`, `gsc`, `meta`, `facebook_page` |
| `client_status` | What the client selected in the form |
| `request_status` | `pending`, `email_sent`, `access_granted`, `not_needed` |
| `confirm_token` | Unique UUID for the confirmation link |
| `granted_at` | Timestamp set when client confirms access |

**`onboarding_logs`** — Audit trail of all significant events per client.

All tables use Row Level Security locked to the `service_role` key only.

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Gmail API (OAuth2)
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token
GMAIL_SENDER_EMAIL=you@gmail.com

# Flask
SECRET_KEY=change-me-to-a-long-random-string
FLASK_ENV=development
```

On Vercel, set all of these as environment variables in the project settings.

---

## Local Development Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd client-account-access-request

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env from the example
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, GMAIL_*, SECRET_KEY

# 5. Run the app
flask run
# App is available at http://localhost:5000
```

---

## Gmail OAuth Setup

The app sends email via the Gmail API using an OAuth2 refresh token (more secure than app passwords).

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create or open a project.
2. Enable the **Gmail API** under APIs & Services.
3. Create an OAuth 2.0 Client ID credential — choose **Desktop app** as the application type.
4. Download the client credentials.
5. Run the helper script:

```bash
python scripts/get_gmail_token.py
```

6. Follow the browser prompt to authorize the Gmail account that will send emails.
7. The script prints the `GMAIL_REFRESH_TOKEN`. Copy it into your `.env` (and into Vercel env vars for production).

---

## Creating the First Admin User

The admin login requires a user in the `admin_users` table. Use the setup script to create the first one:

```bash
python scripts/create_admin.py admin@yourdomain.com yourpassword
```

After that, additional admins can be created through the Settings page in the admin dashboard.

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests use mocked Supabase and Gmail dependencies — no live credentials needed.

---

## Deployment

The app deploys to Vercel via GitHub Actions on every push to `main`.

### Vercel Setup

1. Connect the repo to a Vercel project.
2. Set all environment variables from the [Environment Variables](#environment-variables) section in the Vercel project settings.
3. The `vercel.json` routes all traffic to `api/index.py`, which wraps the Flask app for the Vercel serverless runtime.

### GitHub Actions Secrets

Set the following secrets in your GitHub repository settings:

| Secret | Where to find it |
|---|---|
| `VERCEL_TOKEN` | Vercel account settings → Tokens |
| `VERCEL_ORG_ID` | Vercel project settings → General |
| `VERCEL_PROJECT_ID` | Vercel project settings → General |

### CI/CD Flow

- **Any branch push / PR:** Runs `pytest`. Must pass before deploy.
- **Push to `main`:** Runs tests, then deploys to Vercel production if tests pass.

---

## Routes Reference

### Client Routes

| Method | Path | Description |
|---|---|---|
| GET | `/` | Redirects to `/form` |
| GET | `/form` | Renders the 8-step intake form |
| POST | `/form/submit` | Processes form, creates client + access requests, sends emails |
| GET | `/form/success` | Success page shown after submission |
| GET | `/confirm-access/<token>` | Client confirms a platform's access has been granted |

### Admin Routes (login required)

| Method | Path | Description |
|---|---|---|
| GET/POST | `/admin/login` | Admin login |
| GET | `/admin/logout` | Logs out admin |
| GET | `/admin/` | Dashboard: client list + stats |
| GET | `/admin/client/<id>` | Client detail: access requests, logs, form data |
| POST | `/admin/access-request/<id>/update` | Update request status |
| POST | `/admin/access-request/<id>/details` | Save account name/ID/notes |
| POST | `/admin/client/<id>/status` | Update client status |
| GET/POST | `/admin/settings` | Edit global settings + manage admin users |
| POST | `/admin/settings/admin-users/add` | Add a new admin |
| POST | `/admin/settings/admin-users/<id>/delete` | Remove an admin |
| GET | `/admin/client/<id>/kickoff` | View formatted kickoff brief |

---

## Email System

Emails are sent using the Gmail API with an OAuth2 refresh token stored in environment variables. The token refreshes automatically on each send.

**Google platforms email** covers: Google Ads, GTM, GA4, Google Business Profile, Google Search Console — all in a single email with per-platform step-by-step instructions and individual confirmation buttons.

**Meta platforms email** covers: Meta Business Manager and Facebook Page — in a separate email.

The agency's Manager ID and Meta BM ID are pulled from admin settings and embedded directly in the instructions. The email subject lines and intro copy are also fully customizable per platform type from the Settings page.
