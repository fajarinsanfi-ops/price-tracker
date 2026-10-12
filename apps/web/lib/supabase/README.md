# Supabase client setup

Use `@supabase/ssr` for server and browser clients once authentication is wired into the dashboard. The browser may use only `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`. The service role key is for the Python worker/server only and must never use a `NEXT_PUBLIC_` variable.

The root dashboard is currently a static UI scaffold and does not connect to Supabase yet.
