# Personal Price Tracker

MVP personal price tracker untuk memantau harga produk dari URL website toko, mencatat riwayat harga, dan mengirim notifikasi WhatsApp ketika harga turun.

## MVP scope

- Single-user / personal deployment.
- Menambahkan produk melalui URL.
- Pengecekan harga harian (default workflow pukul 01:00 UTC / 08:00 WIB).
- Riwayat harga di PostgreSQL (Supabase).
- Notifikasi WhatsApp Cloud API ketika harga lebih rendah dari observasi valid sebelumnya.
- Extractor generik JSON-LD Product/Offer; website toko tertentu mungkin memerlukan extractor khusus.

> **Penting:** Starter ini adalah fondasi kode, bukan layanan yang sudah live. Anda perlu mengonfigurasi Supabase, repository secrets, WhatsApp Cloud API, dan menguji extractor pada URL produk sebenarnya sebelum mengandalkannya.

## Repository layout

```text
apps/web/                 # scaffold placeholder untuk dashboard Next.js
worker/app/               # Python price checker
  main.py                 # entrypoint worker
  config.py               # environment config
  db.py                   # Supabase/PostgREST access
  price_checker.py        # extraction + comparison + persistence
  whatsapp.py              # WhatsApp Cloud API
  extractors/
    jsonld.py              # generic Product/Offer JSON-LD extractor
supabase/migrations/       # database schema
.github/workflows/         # scheduled worker
.env.example
```

## Quick start — worker lokal

1. Buat project di Supabase dan jalankan SQL dari `supabase/migrations/001_initial_schema.sql`.
2. Salin `.env.example` menjadi `.env`, lalu isi kredensial server-side. Jangan commit file `.env`.
3. Python 3.11+:

   ```bash
   cd worker
   python -m venv .venv
   # Windows PowerShell: .venv\\Scripts\\Activate.ps1
   # macOS/Linux: source .venv/bin/activate
   pip install -r requirements.txt
   python -m app.main
   ```

4. Tambahkan produk ke tabel `products` melalui Supabase SQL Editor atau aplikasi web yang akan dibangun. Set `is_active = true`.
5. Jalankan worker lagi. Harga valid pertama akan menjadi baseline; pesan baru dikirim hanya saat ada penurunan berikutnya.

## Supabase configuration

Worker memakai Supabase REST API dengan `SUPABASE_URL` dan `SUPABASE_SERVICE_ROLE_KEY`. Service role key hanya boleh berada di environment server/worker; jangan pernah menaruhnya dalam kode browser. Untuk aplikasi web, gunakan Supabase Auth dan aktifkan RLS. Migration ini menyiapkan tabel dan kebijakan dasar.

## WhatsApp Cloud API

Isi environment berikut berdasarkan Meta WhatsApp Cloud API:

- `WHATSAPP_API_VERSION` — versi Graph API yang masih didukung di akun Anda.
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_RECIPIENT_NUMBER` — format internasional tanpa tanda `+`, contoh `62812...`
- `WHATSAPP_TEMPLATE_NAME` — template yang sudah disetujui (default `price_drop_alert`).
- `WHATSAPP_TEMPLATE_LANGUAGE` — kode bahasa template (default `id`).

Template body default membutuhkan enam parameter teks berurutan: nama produk, harga lama, harga baru, persentase penurunan, waktu pengecekan, dan URL. Cocokkan jumlah dan bahasa parameter dengan template aktual di Meta. Pesan template dapat memerlukan persetujuan sesuai kebijakan WhatsApp yang berlaku.

## Daily GitHub Actions workflow

Workflow `.github/workflows/daily-price-check.yml` dijadwalkan setiap hari pukul 01:00 UTC (08:00 WIB). Set repository secrets berikut:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `WHATSAPP_API_VERSION`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_RECIPIENT_NUMBER`
- `WHATSAPP_TEMPLATE_NAME` (opsional)
- `WHATSAPP_TEMPLATE_LANGUAGE` (opsional)

GitHub Actions menyediakan cara mudah menjalankan worker terjadwal, tetapi penjadwalan pada layanan shared runner tidak dijamin tepat pada menitnya. Untuk operasional yang lebih kritis, pindahkan scheduler ke layanan worker terkelola. Jangan commit secrets ke repository.

## Extractor support

Generic extractor reads Schema.org `Product` / `Offer` JSON-LD data from page HTML. It may not work when a store:
- renders data client-side only;
- hides price until login/location selection;
- uses nonstandard markup, anti-bot protections, or an incompatible product schema;
- shows a variant-specific, coupon, member, shipping-inclusive, or personalized price.

Implement one explicit extractor in `worker/app/extractors/` per store when necessary. Respect the store's terms and access restrictions. Do not bypass CAPTCHA or access controls. The worker blocks non-public IP destinations as a basic SSRF safeguard.

## Current limitations

- Dashboard / Next.js user interface is not implemented yet.
- Product management API is not implemented yet.
- No live store-specific extractor has been validated yet.
- Check history and notification delivery should be verified against a real Supabase project and a Meta test number before production use.
- Because checks occur once daily, short-lived price drops between checks will not be detected.
