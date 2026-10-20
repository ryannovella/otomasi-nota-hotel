# Otomasi Nota Hotel

Aplikasi desktop lokal untuk membuat nota hotel resmi (*Guest Folio* / *Bill*) perjalanan dinas secara otomatis, cepat, dan berpresisi tinggi berbasis template vektor PDF dan PyMuPDF.

---

## Fitur Utama

- **Presisi Vektor Asli**: Merekonstruksi tata letak, tipografi font, dan layout invoice asli hotel secara piksel-akurat tanpa degradasi raster.
- **Smart Defaults & Generator Otomatis**:
  - Penomoran kamar dan folio otomatis sesuai format masing-masing hotel.
  - Perhitungan durasi inap (*multi-nights*) dan ekspansi tabel dinamis.
  - Perhitungan nominal dan ejaan kalimat terbilang rupiah secara *real-time*.
- **Variasi Stempel Otentik**: Stempel digital dengan rotasi dan opasitas organik agar tampak otentik.
- **Multi-Export**:
  - 1 Berkas PDF Gabungan (*multi-page*) untuk seluruh daftar rombongan dinas.
  - Berkas PDF perorangan (*individual*) untuk kelengkapan administrasi SPJ.
- **Dukungan Template Hotel**:
  - Facade Boutique Hotel Tawangmangu
  - Golden Hotel & Villa Wonogiri
  - Trio Azana Style Hotel Kebumen
  - Front One Hotel Sragen
  - Ardiana Suite Hotel Purworejo
  - Hotel Surya Yudha Banjarnegara
  - Grand Artos Hotel & Convention Magelang
  - Atrium Premiere Hotel Cilacap
  - Hotel Wisata Niaga Purwokerto
  - Braling Grand Hotel Purbalingga
  - Hotel Aliyana Temanggung
  - Dan hotel lainnya yang dapat ditambahkan dengan mudah via `tambah_hotel.py`.

---

## Persyaratan Sistem

- Python 3.10+
- OS: Windows 10 / 11

### Instalasi Dependensi

```bash
pip install -r requirements.txt
```

---

## Cara Menjalankan

### Cara 1: Dobel-klik (Desktop App)
Jalankan file:
```cmd
Mulai_Aplikasi.bat
```

### Cara 2: Command Line
Mode desktop window:
```bash
python app.py
```

Mode browser:
```bash
python app.py --browser
```

---

## Struktur Proyek

```text
├── app.py                # Server backend Bottle & launcher GUI
├── generator.py          # PDF generation engine (PyMuPDF)
├── tambah_hotel.py       # Helper CLI untuk inisialisasi template baru
├── data/                 # Master data pegawai dan konfigurasi hotel
├── templates/            # Template PDF vektor, metadata, dan aset stempel
├── static/               # Frontend UI (HTML, CSS, JS)
├── requirements.txt      # Daftar dependensi Python
└── PANDUAN_PENGGUNAAN.md # Panduan komprehensif operasional
```

---

## Lisensi

Didistribusikan untuk keperluan otomasi administrasi perjalanan dinas.
