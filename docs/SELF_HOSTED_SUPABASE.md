# Supabase configuration

This project can use Supabase Cloud or a self-hosted Supabase Docker deployment.

The price tracker only needs the public Supabase API endpoint. It does **not** need direct PostgreSQL access.

## 1. Current PriceTracker Supabase project

The connected project uses:

```text
SUPABASE_URL=https://kdsqrqrduziqcurmrphl.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_JWKS_URL=https://kdsqrqrduziqcurmrphl.supabase.co/auth/v1/.well-known/jwks.json
```

Only `SUPABASE_URL` and `SUPABASE_SECRET_KEY` are required by the Python worker.

Do **not** put the actual `sb_secret_...` value in this repository. The publishable key is intended for client/browser use and is not needed by the worker. The JWKS URL is not needed for the current price-check flow.

## 2. REST endpoint

The worker constructs the REST API from `SUPABASE_URL`:

```text
GET https://kdsqrqrduziqcurmrphl.supabase.co/rest/v1/products?select=*&is_active=eq.true
```

Authentication is server-side using the configured Supabase secret key.

Do not append `/rest/v1` to `SUPABASE_URL`; the worker adds that path itself.

## 3. Database migration

Run this migration against the Supabase project before starting the worker:

```text
supabase/migrations/001_initial_schema.sql
```

It creates the tables required by the worker, including `products`, `price_history`, `notification_logs`, `notification_settings`, and `price_check_runs`.

The migration also enables Row Level Security. The scheduled worker uses the server-side secret key and must never expose that key to the browser.

## 4. GitHub Actions secrets

Open the repository's **Settings → Secrets and variables → Actions** and create:

```text
SUPABASE_URL=https://kdsqrqrduziqcurmrphl.supabase.co
SUPABASE_SECRET_KEY=<server-only sb_secret_... value>
```

The current workflow prefers `SUPABASE_SECRET_KEY`. `SUPABASE_SERVICE_ROLE_KEY` remains supported only as a legacy fallback.

The remaining WhatsApp secrets are only required for WhatsApp notifications:

```text
WHATSAPP_API_VERSION
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN
WHATSAPP_RECIPIENT_NUMBER
WHATSAPP_TEMPLATE_NAME
WHATSAPP_TEMPLATE_LANGUAGE
```

Never commit `.env`, the actual `SUPABASE_SECRET_KEY`, JWT secrets, database passwords, or other Supabase secrets.

If a secret is exposed, rotate/revoke it in Supabase and replace the GitHub Actions secret with the new value.

## 5. GitHub Actions connectivity check

The `Daily Price Check` workflow validates `SUPABASE_URL` and `SUPABASE_SECRET_KEY` before running the worker and performs a small REST API request against `products`.

This separates configuration/network/database problems from price-extraction problems:

- missing secret → workflow fails with an explicit configuration error
- DNS/TLS/network failure → workflow reports a connection error
- HTTP 401/403/404/5xx → workflow reports the Supabase HTTP error
- HTTP 200 → the worker proceeds

## 6. Self-hosted deployment

For self-hosted Supabase, use the official Docker stack and expose the API through a public HTTPS reverse proxy such as the Supabase-provided Caddy configuration.

Recommended topology:

```text
GitHub Actions
    |
    | HTTPS
    v
https://supabase.example.com
    |
    v
Caddy :443
    |
    v
API Gateway :8000
    |
    v
PostgREST
    |
    v
PostgreSQL
```

Do not use `localhost` as the GitHub Actions URL and do not expose PostgreSQL port 5432 directly to the Internet for this application.

## 7. Security rules

- Use HTTPS for the public Supabase URL.
- Keep `SUPABASE_SECRET_KEY` only in server-side environments such as GitHub Actions Secrets.
- Use the publishable key only in browser/client applications.
- Back up PostgreSQL independently of the Docker container lifecycle.
