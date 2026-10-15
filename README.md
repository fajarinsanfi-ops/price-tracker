# Personal Price Tracker

MVP personal price tracker untuk memantau harga produk dari URL website toko, mencatat riwayat harga, dan mengirim notifikasi WhatsApp ketika harga turun.

## MVP scope
- Single-user / personal deployment.
- Produk ditambahkan melalui URL.
- Pengecekan harga harian (default 01:00 UTC / 08:00 WIB).
- Riwayat harga di PostgreSQL (Supabase).
- Notifikasi WhatsApp Cloud API ketika harga lebih rendah dari observasi valid sebelumnya.
- Extractor generik JSON-LD Product/Offer; toko tertentu mungkin memerlukan extractor khusus.

> Ini adalah starter code. Dashboard web belum diimplementasikan; konfigurasi Supabase, WhatsApp, GitHub Secrets, dan pengujian URL toko nyata tetap diperlukan sebelum penggunaan produksi.

## Struktur
- `apps/web/`: responsive Next.js dashboard UI scaffold (currently local browser state only).
- `worker/app/`: Python price checker, Supabase repository, URL safety, JSON-LD extractor, WhatsApp sender.
- `worker/tests/`: unit tests.
- `supabase/migrations/001_initial_schema.sql`: database schema.
- `.github/workflows/daily-price-check.yml`: daily schedule.
- `docs/IMPLEMENTATION.md`: deployment checklist.
- `docs/SELF_HOSTED_SUPABASE.md`: Supabase deployment and connectivity notes.

## Jalankan worker lokal
1. Buat project Supabase, lalu jalankan `supabase/migrations/001_initial_schema.sql` di SQL Editor.
2. Salin `.env.example` menjadi `.env` dan isi kredensial server. Jangan commit file `.env`.
3. Untuk worker server-side, gunakan `SUPABASE_SECRET_KEY` sebagai credential utama. `SUPABASE_PUBLISHABLE_KEY` hanya untuk client/browser dan tidak diperlukan worker.
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

5. Tambahkan produk valid ke tabel `products` melalui Supabase SQL Editor. Kosongkan `current_price` untuk menjadikan pembacaan sukses pertama sebagai baseline.

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
Buka Settings → Secrets and variables → Actions → New repository secret, lalu tambahkan:
- `SUPABASE_URL` = `https://kdsqrqrduziqcurmrphl.supabase.co`
- `SUPABASE_SECRET_KEY` = server-only `sb_secret_...` value from the Supabase project
- `WHATSAPP_API_VERSION`
- `WHATSAPP_PHONE_NUMBER_ID`
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_RECIPIENT_NUMBER`
- `WHATSAPP_TEMPLATE_NAME` (opsional; default `price_drop_alert`)
- `WHATSAPP_TEMPLATE_LANGUAGE` (opsional; default `id`)

`SUPABASE_SERVICE_ROLE_KEY` remains supported as a legacy fallback by the workflow and worker, but new deployments should use `SUPABASE_SECRET_KEY`.

**Never commit or paste the actual `sb_secret_...` value into source code, `.env.example`, issues, or documentation.** If a secret has been exposed, rotate it in Supabase before using it in production.

Workflow berjalan setiap hari pukul 01:00 UTC, setara 08:00 WIB. Jalankan manual via Actions untuk pengujian awal. GitHub scheduled runs dapat terlambat dan tidak dijamin tepat pada menitnya.

## WhatsApp Cloud API
Siapkan WhatsApp Business Account, token server-side, phone number ID, nomor penerima dengan opt-in, serta template yang telah disetujui sesuai aturan pesan Meta. Template default menggunakan enam parameter body teks: nama produk, harga lama, harga baru, persentase penurunan, waktu pengecekan, dan URL. Cocokkan template name, language, serta urutan parameter dengan template aktual.

## Extractor support
Generic extractor membaca Schema.org Product/Offer JSON-LD dari HTML. Ini belum tentu bekerja untuk halaman yang merender harga di browser, mengharuskan login/pilihan lokasi, atau memakai markup nonstandar. Buat extractor khusus per domain bila perlu. Hormati ketentuan website dan jangan melewati CAPTCHA/access controls.

## Batasan MVP
- Dashboard Next.js tersedia sebagai UI scaffold, tetapi belum terhubung ke Supabase, autentikasi, atau API CRUD.
- Belum ada extractor toko spesifik yang tervalidasi tanpa URL nyata.
- Belum melakukan tes end-to-end terhadap akun Supabase dan Meta.
- Karena pengecekan sekali sehari, penurunan singkat di antara dua jadwal tidak terdeteksi.
