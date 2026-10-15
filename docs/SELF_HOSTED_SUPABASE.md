# Self-hosted Supabase configuration

This project can use either Supabase Cloud or a self-hosted Supabase Docker deployment.

## 1. Self-hosted Supabase

Use the official Supabase self-hosted Docker stack from the `supabase/supabase` repository.

The price tracker only needs the public Supabase API endpoint. It does **not** need direct PostgreSQL access.

Recommended production topology:

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

For a public deployment, configure the Supabase `SUPABASE_PUBLIC_URL`/proxy domain to the HTTPS hostname that GitHub Actions can reach. Do not use `localhost` as the GitHub Actions URL.

## 2. Database migration

Run this migration against the Supabase project before starting the worker:

```text
supabase/migrations/001_initial_schema.sql
```

It creates the tables required by the worker, including `products`, `price_history`, `notification_logs`, `notification_settings`, and `price_check_runs`.

The migration also enables Row Level Security. The scheduled worker uses the server-side service-role key and must never expose that key to the browser.

## 3. GitHub Actions secrets

Open the repository's **Settings → Secrets and variables → Actions** and create:

```text
SUPABASE_URL=https://supabase.example.com
SUPABASE_SERVICE_ROLE_KEY=<SERVICE_ROLE_KEY from the self-hosted Supabase .env>
```

The remaining WhatsApp secrets are only required for WhatsApp notifications:

```text
WHATSAPP_API_VERSION
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_ACCESS_TOKEN
WHATSAPP_RECIPIENT_NUMBER
WHATSAPP_TEMPLATE_NAME
WHATSAPP_TEMPLATE_LANGUAGE
```

Never commit `.env`, `SERVICE_ROLE_KEY`, `JWT_SECRET`, database passwords, or other Supabase secrets.

## 4. Expected REST endpoint

The worker uses the Supabase REST API. With the configuration above, its first database request is equivalent to:

```text
GET https://supabase.example.com/rest/v1/products?select=*&is_active=eq.true
```

Authentication uses both headers:

```text
apikey: <SERVICE_ROLE_KEY>
Authorization: Bearer <SERVICE_ROLE_KEY>
```

Do not append `/rest/v1` to `SUPABASE_URL`; the worker adds that path itself.

## 5. GitHub Actions connectivity check

The `Daily Price Check` workflow now validates the two Supabase secrets before running the worker and performs a small REST API request against `products`.

This separates configuration/network/database problems from price-extraction problems:

- missing secret → workflow fails with an explicit configuration error
- DNS/TLS/network failure → workflow reports a connection error
- HTTP 401/403/404/5xx → workflow reports the Supabase HTTP error
- HTTP 200 → the worker proceeds

## 6. Important production rules

- Use HTTPS for the public Supabase URL.
- Do not expose PostgreSQL port 5432 directly to the Internet for this application.
- Keep `SERVICE_ROLE_KEY` only in server-side environments such as GitHub Actions secrets.
- Keep the browser/dashboard on publishable/anon credentials rather than the service-role key.
- Back up the PostgreSQL data volume independently of Docker container lifecycle.
