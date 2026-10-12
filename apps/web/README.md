# Price Tracker Web Dashboard

Next.js App Router dashboard UI scaffold.

## Run locally

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Current behavior

- Responsive dashboard layout and product table.
- Add URL modal validates basic URL format.
- URLs are stored in React state only and disappear on refresh.
- Product prices, activity metrics, and chart are not connected to real data.
- Supabase auth, product CRUD API, history chart, and dashboard persistence remain to be implemented.

Use `.env.example` for future public Supabase URL and anon key only. Never expose the service role key or WhatsApp token in a browser bundle.
