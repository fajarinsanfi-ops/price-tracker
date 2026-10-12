# Web dashboard (planned)

The Next.js dashboard is not implemented in this starter commit. Planned screens:

- `/login` — private single-user authentication.
- `/dashboard` — product totals, last run status, latest price drops.
- `/products/new` — submit product URL and review extracted title/price.
- `/products/[id]` — price history and monitoring status.

Use Supabase Auth for the browser session. Keep `SUPABASE_SERVICE_ROLE_KEY`, WhatsApp tokens, and worker job tokens server-only; never prefix secrets with `NEXT_PUBLIC_`.

The worker can currently be run by GitHub Actions or from a local Python environment while the UI is developed.
