# Aturan Khusus Proyek Otomasi Nota Hotel

## 1. Preservasi Instansi & Header Asli (Zero Generic Overwrite)
- **Kesesuaian Arsip Referensi:** Saat mengonfigurasi atau membuat template hotel baru/lama, AI Assistant **WAJIB** mempertahankan nama instansi (*agency*), kota, dan format teks di pojok kiri atas persis sesuai berkas master/referensi yang diinstruksikan oleh pengguna.
- **Front One Hotel Sragen:**
  - Instansi di pojok kiri atas **HARUS SELALU** mempertahankan `"KEMENTRIAN PU JATENG"` (sesuai berkas referensi resmi terbaru `SRAGEN FRONTONE 10 Sept Fachrul.pdf`).
  - Kota di pojok kiri atas **HARUS SELALU** mempertahankan `"SEMARANG, JAWA TENGAH"`.
  - Jangan menimpa secara otomatis dengan `"BPPW JAWA TENGAH"` atau `"KEMENTERIAN PU"` umum, kecuali pengguna secara eksplisit meminta instansi khusus lainnya.
  - Nilai ini harus selalu terjaga di:
    1. `data/hotels.json` (`default_agency: "KEMENTRIAN PU JATENG"`, `default_city: "SEMARANG, JAWA TENGAH"`)
    2. `templates/sragen_frontone/config.json` (`default_agency: "KEMENTRIAN PU JATENG"`)
    3. `generator.py` (`render_frontone_sragen_receipt` memprioritaskan `KEMENTRIAN PU JATENG`)
    4. `static/app.js` (`addGuestRow` & `syncGuestRowsWithDefaults`)
- **Grand Artos Hotel & Convention Magelang:**
  - Instansi di atas tabel kanan **HARUS SELALU** menggunakan `"Kementerian PU,"` (dilarang menggunakan `"Kementerian PUPR"`).
  - Sanitasi otomatis: jika input tamu mengandung kata `"PUPR"`, wajib diganti menjadi `"PU"`.
  - Nilai ini terjaga di `data/hotels.json`, `templates/magelang_artos/config.json`, dan `generator.py` (`render_artos_magelang_receipt`).

## 2. Standar Tabel & Penempatan Stempel Front One Hotel Sragen
- **Ekspansi Vertikal Dinamis:** Jika jumlah malam inap > 1, tabel transaksi wajib mengembang ke bawah dengan baris bertambah per malam inap (`checkin_dt + timedelta(days=i)`). Kolom `Qty` untuk setiap baris malam inap **SELALU** bernilai `"1"`.
- **Pergeseran Proporsional Blok Bawah:** Seluruh blok di bawah tabel (baris `Total`, `Balance` berwarna merah, teks *"Come back soon..."*, disclaimer brankas dan perjalanan, garis tanda tangan, dan teks waktu cetak) **WAJIB** bergeser ke bawah mengikuti penambahan baris (`dy = (nights - 1) * ROW_DY`).
- **Penempatan Stempel Anti-Tabrakan (Multi-Malam):**
  - Pada durasi multi-malam (`nights > 1`), stempel **WAJIB** ditempatkan di area tanda tangan (`Signature`) di bawah tabel transaksi (berpusat di sekitar garis tanda tangan), persis seperti referensi Fachrul.
  - Stempel **TIDAK BOLEH BERTABRAKAN** dengan isi konten teks dari tabel transaksi (kolom Date, Room, Description, Qty, Debit, Credit).
  - Pada durasi 1 malam (`nights == 1`), stempel dapat ditempatkan pada posisi standar master 1 malam.

## 3. Preservasi Stempel & Resolusi Vektor
- Gunakan aset stempel asli yang disediakan (`stamp.png` dan `stamp2.png`).
- Variasikan stempel secara organik antar lembar nota agar tampak otentik.
- Pertahankan master PDF berbasis vektor murni tanpa artefak raster/pixelation.
