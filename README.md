# Personal Price Tracker

MVP personal price tracker untuk memantau harga produk dari URL website toko, mencatat riwayat harga, dan mengirim notifikasi WhatsApp ketika harga turun.

## MVP scope
- Single-user / personal deployment.
- Produk ditambahkan melalui URL.
- Pengecekan harga harian (default 01:00 UTC / 08:00 WIB).
- Riwayat harga di PostgreSQL (Supabase).
- Notifikasi WhatsApp Cloud API ketika harga lebih rendah dari observasi valid sebelumnya.
- Extractor generik JSON-LD Product/Offer; toko tertentu mungkin memerlukan extractor khusus.

## Current deployment status
The repository is configured for the connected Supabase project:

```text
SUPABASE_URL=https://kdsqrqrduziqcurmrphl.supabase.co
```

The worker uses the current server-side `SUPABASE_SECRET_KEY` first and keeps `SUPABASE_SERVICE_ROLE_KEY` as a legacy fallback. The actual secret value must exist only in GitHub Actions secrets or another server-side secret store.

The Supabase schema used by the worker contains:

- `products`
- `price_history`
- `notification_logs`
- `notification_settings`
- `price_check_runs`

## Repository structure
- `apps/web/`: responsive Next.js dashboard UI scaffold (currently local browser state only).
- `worker/app/`: Python price checker, Supabase repository, URL safety, JSON-LD extractor, WhatsApp sender.
- `worker/tests/`: Python unit tests.
- `supabase/migrations/001_initial_schema.sql`: database schema.
- `.github/workflows/tests.yml`: Python unit-test CI.
- `.github/workflows/web-check.yml`: web application checks.
- `.github/workflows/daily-price-check.yml`: scheduled production price check.
- `.github/workflows/supabase-integration.yml`: Supabase REST/API integration checks.
- `docs/IMPLEMENTATION.md`: deployment checklist.
- `docs/SELF_HOSTED_SUPABASE.md`: Supabase deployment and connectivity notes.

## Run the worker locally
1. Use a Supabase project and apply `supabase/migrations/001_initial_schema.sql`.
2. Copy `.env.example` to `.env` and fill server-side credentials. Never commit `.env`.
3. For a server-side worker, use `SUPABASE_SECRET_KEY` as the primary credential. `SUPABASE_PUBLISHABLE_KEY` is for client/browser use and is not required by the worker.
4. Python 3.11+:

   ```bash
   cd worker
   python -m venv .venv
   # Windows PowerShell: .venv\\Scripts\\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   pytest
   python -m app.main
   ```

5. Add valid products to `products` through Supabase SQL Editor. Leave `current_price` empty so the first successful price read becomes the baseline.

## Supabase configuration
The current PriceTracker project uses:

```text
SUPABASE_URL=https://kdsqrqrduziqcurmrphl.supabase.co
SUPABASE_SECRET_KEY=<server-only secret; keep this value out of source control>
SUPABASE_PUBLISHABLE_KEY=<client/browser key; not used by the worker>
SUPABASE_JWKS_URL=https://kdsqrqrduziqcurmrphl.supabase.co/auth/v1/.well-known/jwks.json
```

The worker only needs `SUPABASE_URL` and `SUPABASE_SECRET_KEY`. It constructs the REST endpoint as `<SUPABASE_URL>/rest/v1`.

## GitHub Actions setup
Open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `SUPABASE_URL` = `https://kdsqrqrduziqcurmrphl.supabase.co`
- `SUPABASE_SECRET_KEY` = server-only `sb_secret_...` value from the Supabase project
- `WHATSAPP_API_VERSION`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_RECIPIENT_NUMBER`
- `WHATSAPP_TEMPLATE_NAME` (optional; default `price_drop_alert`)
- `WHATSAPP_TEMPLATE_LANGUAGE` (optional; default `id`)

`SUPABASE_SERVICE_ROLE_KEY` remains supported as a legacy fallback by the workflow and worker, but new deployments should use `SUPABASE_SECRET_KEY`.

**Never commit or paste the actual `sb_secret_...` value into source code, `.env.example`, issues, or documentation.** If a secret has been exposed, rotate it in Supabase before using it in production.

## Testing and verification
The repository now separates unit, web, Supabase integration, and production price-check validation:

| Check | Workflow | Purpose |
|---|---|---|
| Python unit tests | `tests.yml` | Extractor, comparator, URL safety, WhatsApp behavior |
| Web checks | `web-check.yml` | Next.js lint/build/static checks |
| Supabase integration | `supabase-integration.yml` | Verify GitHub secrets, HTTPS endpoint, authentication, and all required REST tables |
| Daily price check | `daily-price-check.yml` | Run the real worker against configured products and send notifications |

The Supabase integration workflow checks these REST resources before the worker is allowed to run in production:

```text
/rest/v1/products
/rest/v1/price_history
/rest/v1/notification_logs
/rest/v1/notification_settings
/rest/v1/price_check_runs
```

Each check uses the server-side key through GitHub Actions secrets and verifies a successful HTTP response without printing the secret.

### Manual production test
Run **Daily Price Check → Run workflow** after the Supabase integration workflow is green. The production workflow performs its own configuration and REST connectivity validation before executing `python -m app.main`.

The daily schedule is `01:00 UTC` (08:00 WIB). GitHub scheduled runs may be delayed and are not guaranteed to start at the exact minute.

## WhatsApp Cloud API
Prepare a WhatsApp Business Account, server-side token, phone number ID, recipient number with opt-in, and an approved template according to Meta messaging rules. The default template uses six text body parameters: product name, old price, new price, percentage decrease, check time, and URL. Match the template name, language, and parameter order to the actual Meta template.

## Extractor support
The generic extractor reads Schema.org Product/Offer JSON-LD from HTML. It may not work for pages that render prices in the browser, require login/location selection, or use non-standard markup. Add a domain-specific extractor when necessary. Respect website terms and do not bypass CAPTCHA or access controls.

## Known MVP limitations
- The Next.js dashboard is currently a UI scaffold and is not yet connected to Supabase authentication or CRUD APIs.
- No store-specific extractor is guaranteed without testing real product URLs.
- WhatsApp delivery is an external integration and must be validated with the configured Meta account/template.
- Because the checker runs once per day, short-lived price drops between scheduled checks are not detected.
