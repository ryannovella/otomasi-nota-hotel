"""
Helper Script: Onboard / Tambah Hotel Baru dari Arsip
Author: BPPW Jateng / Antigravity
Usage:
    python tambah_hotel.py "Banyumas - Elsotel"
    python tambah_hotel.py "Magelang - Artos"
"""

import os
import sys
import json
import pymupdf

ARCHIVE_BASE = r"e:\Documents\bppw jateng\Receipt Edo Tensei"
APP_BASE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(APP_BASE, "templates")
DATA_DIR = os.path.join(APP_BASE, "data")

def scan_and_setup(hotel_folder_name):
    source_dir = os.path.join(ARCHIVE_BASE, hotel_folder_name)
    if not os.path.exists(source_dir):
        print(f"Error: Folder '{source_dir}' tidak ditemukan!")
        return

    # Cari file PDF atau AI di folder tersebut
    files = os.listdir(source_dir)
    pdf_files = [f for f in files if f.endswith(".pdf")]
    ai_files = [f for f in files if f.endswith(".ai")]

    print(f"=== Menyiapkan Template untuk: {hotel_folder_name} ===")
    print(f"Ditemukan {len(pdf_files)} PDF dan {len(ai_files)} AI.")

    slug = hotel_folder_name.lower().replace(" - ", "_").replace(" ", "_").replace("&", "dan")
    target_tmpl_dir = os.path.join(TEMPLATES_DIR, slug)
    os.makedirs(target_tmpl_dir, exist_ok=True)

    # Ambil sampel PDF pertama untuk diekstrak
    sample_file = None
    if pdf_files:
        sample_file = os.path.join(source_dir, pdf_files[0])
    elif ai_files:
        sample_file = os.path.join(source_dir, ai_files[0])

    if sample_file:
        doc = pymupdf.open(sample_file)
        page = doc[0]
        print(f"Membaca sampel '{os.path.basename(sample_file)}' (Ukuran: {page.rect.width:.1f} x {page.rect.height:.1f})")

        # Ekstrak gambar (stempel jika ada)
        imgs = page.get_images()
        if imgs:
            img_dict = doc.extract_image(imgs[0][0])
            stamp_path = os.path.join(target_tmpl_dir, "stamp.png")
            with open(stamp_path, "wb") as f:
                f.write(img_dict["image"])
            print(f"Stempel diekstrak ke: {stamp_path}")

        # Simpan starter template
        starter_pdf = os.path.join(target_tmpl_dir, "master_1night.pdf")
        doc_starter = pymupdf.open()
        doc_starter.insert_pdf(doc, from_page=0, to_page=0)
        doc_starter.save(starter_pdf)
        print(f"Master template starter disimpan di: {starter_pdf}")

        # Buat starter config.json
        cfg_path = os.path.join(target_tmpl_dir, "config.json")
        cfg_data = {
            "hotel_id": slug,
            "name": hotel_folder_name,
            "master_1night": "master_1night.pdf",
            "stamp_file": "stamp.png" if imgs else "",
            "date_format": "%d-%b-%Y"
        }
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg_data, f, indent=2)
        print(f"Config starter dibuat di: {cfg_path}")
        print("\nSelesai! Silakan cek koordinat dan daftarkan di data/hotels.json.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        scan_and_setup(sys.argv[1])
    else:
        print("Penggunaan: python tambah_hotel.py <Nama Folder Hotel di Arsip>")
        print("Contoh: python tambah_hotel.py \"Banyumas - Elsotel\"")
