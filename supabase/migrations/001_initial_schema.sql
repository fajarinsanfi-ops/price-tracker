-- Personal Price Tracker MVP schema
-- Run in Supabase SQL Editor or via Supabase CLI migrations.
create extension if not exists pgcrypto;

create table if not exists public.products (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  url text not null,
  store_domain text not null,
  product_name text not null,
  image_url text,
  currency varchar(3) not null default 'IDR',
  current_price numeric(14,2),
  is_active boolean not null default true,
  last_checked_at timestamptz,
  last_check_status text not null default 'pending'
    check (last_check_status in ('pending', 'success', 'error')),
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint products_url_nonempty check (length(trim(url)) > 0),
  constraint products_name_nonempty check (length(trim(product_name)) > 0),
  constraint products_positive_price check (current_price is null or current_price > 0)
);

create index if not exists products_active_idx
  on public.products (is_active) where is_active = true;
create index if not exists products_user_id_idx on public.products (user_id);

create table if not exists public.price_history (
  id bigint generated always as identity primary key,
  product_id uuid not null references public.products(id) on delete cascade,
  price numeric(14,2) not null check (price > 0),
  currency varchar(3) not null default 'IDR',
  availability text,
  source text not null default 'jsonld',
  checked_at timestamptz not null default now()
);
create index if not exists price_history_product_time_idx
  on public.price_history(product_id, checked_at desc);

create table if not exists public.notification_logs (
  id uuid primary key default gen_random_uuid(),
  product_id uuid not null references public.products(id) on delete cascade,
  old_price numeric(14,2) not null,
  new_price numeric(14,2) not null,
  currency varchar(3) not null default 'IDR',
  channel text not null default 'whatsapp',
  idempotency_key text not null unique,
  status text not null default 'pending'
    check (status in ('pending', 'sent', 'failed', 'unknown')),
  provider_message_id text,
  created_at timestamptz not null default now(),
  sent_at timestamptz,
  error_message text,
  constraint notification_price_drop check (new_price < old_price)
);
create index if not exists notification_logs_product_time_idx
  on public.notification_logs(product_id, created_at desc);

create table if not exists public.notification_settings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid unique references auth.users(id) on delete cascade,
  whatsapp_number text not null,
  is_enabled boolean not null default false,
  opted_in_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint whatsapp_number_nonempty check (length(trim(whatsapp_number)) > 0)
);

-- Dashboard users must only see runs that belong to their own products. A run row
-- does not contain user_id in this single-user worker design, so access is restricted
-- to server-side service-role clients. Do not expose run rows directly from the browser.
create table if not exists public.price_check_runs (
  id uuid primary key default gen_random_uuid(),
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  status text not null default 'running'
    check (status in ('running', 'success', 'partial', 'failed')),
  products_checked integer not null default 0,
  products_succeeded integer not null default 0,
  errors_count integer not null default 0,
  summary jsonb not null default '{}'::jsonb
);

create index if not exists price_check_runs_started_idx
  on public.price_check_runs(started_at desc);

-- RLS: dashboard users may access only their own rows.
-- The service-role worker bypasses RLS and must only run server-side.
alter table public.products enable row level security;
alter table public.price_history enable row level security;
alter table public.notification_logs enable row level security;
alter table public.notification_settings enable row level security;
alter table public.price_check_runs enable row level security;

drop policy if exists "Users manage own products" on public.products;
create policy "Users manage own products" on public.products
  for all to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users read own price history" on public.price_history;
create policy "Users read own price history" on public.price_history
  for select to authenticated
  using (exists (
    select 1 from public.products p
    where p.id = price_history.product_id and p.user_id = auth.uid()
  ));

drop policy if exists "Users read own notification logs" on public.notification_logs;
create policy "Users read own notification logs" on public.notification_logs
  for select to authenticated
  using (exists (
    select 1 from public.products p
    where p.id = notification_logs.product_id and p.user_id = auth.uid()
  ));

drop policy if exists "Users manage own notification settings" on public.notification_settings;
create policy "Users manage own notification settings" on public.notification_settings
  for all to authenticated
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "Users read own check runs" on public.price_check_runs;
-- No direct authenticated-user SELECT policy for check runs. Read them only through
-- a server-side API that verifies the signed-in user and filters appropriately.

comment on table public.products is 'Products tracked by the personal price tracker';
comment on table public.price_history is 'Valid price observations only';
comment on table public.notification_logs is 'WhatsApp price-drop notification attempts';
