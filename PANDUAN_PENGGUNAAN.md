# Panduan Penggunaan: Otomasi Nota Hotel (BPPW Jawa Tengah)

Aplikasi desktop lokal untuk membuat nota hotel resmi (Guest Folio / Bill) perjalanan dinas secara otomatis, cepat, dan presisi tinggi sesuai standar SPPD BPPW Jawa Tengah / Kementerian PU.

---

## 1. Cara Menjalankan Aplikasi

1. Buka folder: `g:\My Drive\Apps\Otomasi Nota Hotel`
2. Dobel-klik file: **`Mulai_Aplikasi.bat`**
3. Aplikasi akan langsung terbuka dalam jendela desktop mandiri (native window).
   *(Jika ingin membuka via tab browser biasa seperti Chrome atau Edge, jalankan perintah `python app.py --browser`).*

---

## 2. Fitur Utama

### A. Generator Nota Cerdas (Smart Defaults)
- **Pilihan Hotel**: Pilih hotel yang dituju (misal: *Facade Boutique Hotel Tawangmangu*, *Golden Hotel & Villa Wonogiri*, *Trio Azana Style Hotel Kebumen*, atau *Front One Hotel Sragen*).
- **Penghitungan Durasi Otomatis**: Pilih tanggal Check-In dan Check-Out, sistem otomatis menghitung jumlah malam.
- **Daftar Personel Rombongan**: Centang personel yang berangkat dari daftar master 28 pegawai BPPW Jateng yang sudah tersedia.
- **Smart Defaults Otomatis**:
  - Nomor kamar terisi urut otomatis (misal: 201, 202, 203, 205...).
  - Nomor folio/bill terisi acak berformat asli hotel (misal `FL.810xxxxx / 0` atau `0xx/GuestBill/GH/...`).
  - Tarif per malam otomatis terisi sesuai standar hotel/SBM.
- **Tabel Siap Diedit**: Anda tetap bisa mengubah nomor kamar, nomor folio, maupun tarif langsung pada tabel sebelum mencetak.
- **Pratinjau Terbilang Otomatis**: Menampilkan ejaan kata rupiah resmi secara *real-time* (misal: *"LIMA RATUS LIMA PULUH RIBU RUPIAH"*).
- **Opsi Stempel Digital**: Toggle untuk menyertakan stempel transparan hotel di atas garis tanda tangan, atau dimatikan jika ingin nota polos untuk cap basah manual.

### B. Output Berkas PDF Lengkap
Setiap kali mengklik **Generate Dokumen PDF Nota**:
1. Berkas tersimpan otomatis di: `output/<Tanggal>_<NamaHotel>/`
2. Dihasilkan **1 Berkas PDF Gabungan (Multi-page)** berisi seluruh nota tamu rombongan (1 orang per lembar, standar SPJ).
3. Dihasilkan **Berkas PDF Satuan** di dalam subfolder `Individu/` untuk keperluan lampiran perorangan.
4. Tersedia tombol langsung di aplikasi:
   - **Buka File PDF Langsung**
   - **Buka Folder di Windows Explorer**

### C. Kelola Personel (Master Data)
- Tab **Daftar Personel** memudahkan Anda menambah, mengedit, atau menghapus nama pejabat/staf.
- Data tersimpan permanen di `data/employees.json`.

---

## 3. Menambahkan Hotel Baru

Untuk menambahkan hotel ke-3, ke-4, dan seterusnya dari 35+ hotel di arsip Anda:
1. Jalankan script pembantu:
   ```bash
   python tambah_hotel.py "Banyumas - Elsotel"
   ```
2. Master template dan stempel otomatis diekstrak ke `templates/banyumas_elsotel/`.
3. Daftarkan profil hotel di file `data/hotels.json`.
