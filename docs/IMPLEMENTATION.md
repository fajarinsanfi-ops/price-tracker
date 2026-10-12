# MVP implementation checklist

## 1. Supabase
1. Buat project Supabase.
2. Jalankan `supabase/migrations/001_initial_schema.sql` di SQL Editor.
3. Simpan service role key hanya di server/worker.
4. Tambahkan produk melalui SQL Editor. Contoh ini placeholder; ganti dengan URL produk nyata yang boleh diakses:

```sql
insert into public.products (url, store_domain, product_name, currency, is_active)
values ('https://YOUR-STORE.example/product', 'YOUR-STORE.example', 'Product name', 'IDR', true);
```

Kosongkan `current_price` pada produk baru agar harga valid pertama menjadi baseline dan tidak mengirim alert.

## 2. GitHub Actions
Masuk ke Settings → Secrets and variables → Actions → New repository secret. Isi semua secrets yang dibutuhkan sesuai README. Gunakan tab Actions → Daily Price Check → Run workflow untuk uji awal.

## 3. WhatsApp
Konfigurasikan Meta app dan WhatsApp Business Account. Pastikan penerima telah memberikan opt-in dan template yang digunakan telah disetujui bila diwajibkan. Jangan pernah menyimpan token di file kode atau log.

## 4. Uji lokal
```bash
cd worker
python -m venv .venv
# PowerShell: .venv\\Scripts\\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pytest
python -m app.main
```

## 5. Extractor website
Validasi harga yang terbaca terhadap harga untuk varian yang benar. Jika JSON-LD tidak memberikan harga, implementasikan extractor domain-spesifik. Jangan melewati CAPTCHA atau kontrol akses.

## 6. Hardening sebelum produksi
- Jalankan tests pada semua perubahan kode.
- Validasi URL dan setiap redirect serta pertimbangkan egress controls jaringan.
- Rekonsiliasi kegagalan WhatsApp yang ambigu sebelum retry agar tidak menggandakan pesan.
- Tambahkan dashboard Next.js, authentication, product CRUD API, grafik riwayat, dan status worker.
- Jalankan uji end-to-end dengan produk dan nomor uji Meta sebelum mengandalkan notifikasi.
