-- Run this in the Supabase SQL editor to create all required tables.
-- Enable UUID extension (already enabled by default in Supabase).
create extension if not exists "pgcrypto";


-- ─── settings ─────────────────────────────────────────────────────────────────
create table if not exists settings (
  key        text primary key,
  value      text not null default '',
  updated_at timestamptz default now()
);

alter table settings enable row level security;
create policy "service_role_only" on settings
  using (auth.role() = 'service_role');

-- Seed default empty values
insert into settings (key, value) values
  ('agency_ads_manager_id', ''),
  ('agency_meta_bm_id', ''),
  ('email_from_name', ''),
  ('email_reply_to', ''),
  ('google_email_subject', 'Action Required: Grant Google Account Access'),
  ('google_email_intro', 'As part of your onboarding, we need admin or manager access to the following Google platforms so we can start setting up and managing your campaigns. This is a quick one-time step — it typically takes less than 5 minutes per platform.'),
  ('meta_email_subject', 'Action Required: Grant Meta Account Access'),
  ('meta_email_intro', 'To run Facebook and Instagram ads for your business, we need partner access to your Meta accounts. This is a one-time setup that gives us the access we need to manage your campaigns on your behalf.')
on conflict (key) do nothing;


-- ─── admin_users ──────────────────────────────────────────────────────────────
create table if not exists admin_users (
  id            uuid primary key default gen_random_uuid(),
  email         text unique not null,
  password_hash text not null,
  created_at    timestamptz default now()
);

-- Only the service role can read/write admin_users.
alter table admin_users enable row level security;
create policy "service_role_only" on admin_users
  using (auth.role() = 'service_role');


-- ─── clients ──────────────────────────────────────────────────────────────────
create table if not exists clients (
  id                    uuid primary key default gen_random_uuid(),
  created_at            timestamptz default now(),
  status                text not null default 'pending'
                          check (status in ('pending','active','complete')),
  company_name          text not null,
  owner_name            text not null,
  phone                 text not null,
  best_email            text not null,
  lead_notif_email      text,
  website               text,
  city_state            text,
  years_in_business     text,
  licensed_bonded_insured text,
  tagline               text,
  company_values        text,
  step_data             jsonb  -- full form payload
);

alter table clients enable row level security;
-- Anon users cannot read client PII.
create policy "service_role_only" on clients
  using (auth.role() = 'service_role');


-- ─── access_requests ──────────────────────────────────────────────────────────
create table if not exists access_requests (
  id              uuid primary key default gen_random_uuid(),
  client_id       uuid not null references clients(id) on delete cascade,
  platform        text not null
                    check (platform in ('google_ads','gtm','ga4','gbp','gsc','meta','facebook_page')),
  client_status   text not null default 'not_sure'
                    check (client_status in ('not_sure','has_account','needs_created','doesnt_have')),
  request_status  text not null default 'pending'
                    check (request_status in ('pending','email_sent','access_granted','not_needed')),
  email_sent_at   timestamptz,
  granted_at      timestamptz,
  notes           text,
  confirm_token   uuid unique default gen_random_uuid(),
  account_name    text,
  account_id      text,
  account_notes   text,
  created_at      timestamptz default now()
);

alter table access_requests enable row level security;
create policy "service_role_only" on access_requests
  using (auth.role() = 'service_role');


-- ─── onboarding_logs ──────────────────────────────────────────────────────────
create table if not exists onboarding_logs (
  id          uuid primary key default gen_random_uuid(),
  client_id   uuid not null references clients(id) on delete cascade,
  event       text not null,
  detail      text,
  created_at  timestamptz default now()
);

alter table onboarding_logs enable row level security;
create policy "service_role_only" on onboarding_logs
  using (auth.role() = 'service_role');


-- ─── Indexes ──────────────────────────────────────────────────────────────────
create index if not exists idx_access_requests_client_id on access_requests(client_id);
create index if not exists idx_onboarding_logs_client_id on onboarding_logs(client_id);
create index if not exists idx_clients_status on clients(status);
create index if not exists idx_clients_created_at on clients(created_at desc);
