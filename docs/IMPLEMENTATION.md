# MVP implementation checklist

## 1. Supabase

1. Create a Supabase project.
2. Run `supabase/migrations/001_initial_schema.sql` in SQL Editor.
3. Keep the service role key private.
4. For the personal setup, insert one product row via SQL Editor. Fill `url`, `store_domain`, `product_name`, `currency`, and `is_active=true`. Leave `current_price` null for first-run baseline or set it only if you have verified a matching price.

Example insert:

```sql
insert into public.products (url, store_domain, product_name, currency, is_active)
values ('https://YOUR-STORE.example/product', 'YOUR-STORE.example', 'Product name', 'IDR', true);
```

This is a placeholder. Replace it with an actual product URL from a store you are allowed to access.

## 2. GitHub Actions

Open repository Settings → Secrets and variables → Actions → New repository secret. Add every required key listed in the main README. The schedule uses 01:00 UTC, or 08:00 in Asia/Jakarta. Use Actions → Daily Price Check → Run workflow to test manually after setting secrets.

## 3. WhatsApp Cloud API

Configure a Meta app and WhatsApp Business Account, then add the recipient's explicit opt-in. The approved template must match `WHATSAPP_TEMPLATE_NAME`, `WHATSAPP_TEMPLATE_LANGUAGE`, and six body text parameters in the order documented in README. Never place tokens in files or logs.

## 4. Test locally

```bash
cd worker
python -m venv .venv
# PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest
python -m app.main
```

## 5. Store-specific extractor

First test the real product page manually. Confirm extracted price corresponds to the correct variant, currency and offer. If generic JSON-LD doesn't provide a price, implement a domain-specific extractor. Do not bypass CAPTCHA, login walls or access controls.

## 6. Production hardening before wider use

- Add redirect-by-redirect URL validation and egress restrictions at the network layer.
- Use a durable notification queue/outbox and reconcile ambiguous WhatsApp API timeouts to avoid duplicate sends.
- Add tests for extractor output and the notification state machine.
- Move from sequential per-product requests to a bounded worker pool only when needed.
- Implement the Next.js dashboard and product CRUD API.
- Run a manual test with a Meta test number and a real price change before relying on the system.
