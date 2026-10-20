"""
Core Generator Engine for Hotel Receipts (Nota Hotel)
Author: BPPW Jateng / Antigravity
"""

import os
import io
import json
import random
import re
import datetime
import time
import pymupdf
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

ID_MONTHS = [
    "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

ID_MONTHS_SHORT = [
    "", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
]

EN_MONTHS_SHORT = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

EN_MONTHS = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

def terbilang_angka(n: int) -> str:
    """Helper untuk mengonversi bilangan integer ke kata-kata bahasa Indonesia."""
    satuan = ["", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "sebelas"]
    n = int(n)
    if n < 12:
        return satuan[n]
    elif n < 20:
        return terbilang_angka(n - 10) + " belas"
    elif n < 100:
        return terbilang_angka(n // 10) + " puluh " + satuan[n % 10]
    elif n < 200:
        return "seratus " + terbilang_angka(n - 100)
    elif n < 1000:
        return terbilang_angka(n // 100) + " ratus " + terbilang_angka(n % 100)
    elif n < 2000:
        return "seribu " + terbilang_angka(n - 1000)
    elif n < 1000000:
        return terbilang_angka(n // 1000) + " ribu " + terbilang_angka(n % 1000)
    elif n < 1000000000:
        return terbilang_angka(n // 1000000) + " juta " + terbilang_angka(n % 1000000)
    elif n < 1000000000000:
        return terbilang_angka(n // 1000000000) + " milyar " + terbilang_angka(n % 1000000000)
    return str(n)

def terbilang(n: int) -> str:
    """Mengembalikan format terbilang resmi kapital lengkap dengan kata RUPIAH."""
    res = terbilang_angka(n).strip()
    # Bersihkan multiple spaces
    res = " ".join(res.split())
    return (res + " rupiah").upper()

def format_rupiah_dot(n: int) -> str:
    """550000 -> '550.000'"""
    return f"{n:,.0f}".replace(",", ".")

def format_rupiah_comma(n: int) -> str:
    """678000 -> '678,000'"""
    return f"{n:,.0f}"

FONT_MAP = {
    "arial": r"C:\Windows\Fonts\arial.ttf",
    "arial_bold": r"C:\Windows\Fonts\arialbd.ttf",
    "arial_italic": r"C:\Windows\Fonts\ariali.ttf",
    "cambria_italic": r"C:\Windows\Fonts\cambriai.ttf",
    "constantia_italic": r"C:\Windows\Fonts\constani.ttf",
    "trebuchet": r"C:\Windows\Fonts\trebuc.ttf",
    "trebuchet_bold": r"C:\Windows\Fonts\trebucbd.ttf",
    "tahoma": r"C:\Windows\Fonts\tahoma.ttf",
    "lucida": r"C:\Windows\Fonts\l_10646.ttf",
    "comic": r"C:\Windows\Fonts\comic.ttf",
    "comic_bold": r"C:\Windows\Fonts\comicbd.ttf",
    "comic_bold_italic": r"C:\Windows\Fonts\comicz.ttf",
    "calibri": r"C:\Windows\Fonts\calibri.ttf",
    "calibri_bold": r"C:\Windows\Fonts\calibrib.ttf"
}

def register_fonts(page: pymupdf.Page, font_names=("arial",)):
    """Mendaftarkan hanya font spesifik yang dibutuhkan ke halaman PDF agar ukuran berkas tidak membengkak."""
    for alias in font_names:
        fpath = FONT_MAP.get(alias)
        if fpath and os.path.exists(fpath):
            try:
                page.insert_font(fontname=alias, fontfile=fpath)
            except Exception:
                pass

def insert_realistic_stamp(page: pymupdf.Page, stamp_path: str, base_rect: list, dx_range=(-4.0, 4.0), dy_range=(-2.5, 2.5), angle_range=(-2.2, 2.2), fill_color=None, opacity_range=(0.88, 0.96), overlay=True):
    """
    Menyisipkan stempel ke halaman PDF dengan rotasi/kemiringan halus
    serta dislokasi acak sumbu X dan Y agar terlihat realistis seperti cap basah manual asli (no editan).
    Mendukung format vektor murni (.svg) untuk ukuran file minimal dan ketajaman 100% tanpa pixelation.
    Parameter overlay=False memungkinkan penempatan stempel di layer latar belakang (di balik teks/garis).
    """
    if not os.path.exists(stamp_path):
        return

    x0, y0, x1, y1 = base_rect
    base_w = x1 - x0
    base_h = y1 - y0
    base_cx = (x0 + x1) / 2.0
    base_cy = (y0 + y1) / 2.0

    # Dislokasi halus sumbu X dan Y
    dx = random.uniform(*dx_range)
    dy = random.uniform(*dy_range)
    cx = base_cx + dx
    cy = base_cy + dy

    # Sudut kemiringan acak halus
    if angle_range[0] == angle_range[1]:
        angle = angle_range[0]
    else:
        angle = random.uniform(min(angle_range), max(angle_range))
    target_rect = pymupdf.Rect(cx - base_w / 2.0, cy - base_h / 2.0, cx + base_w / 2.0, cy + base_h / 2.0)

    # 1. Mode Vektor Murni (.svg)
    if stamp_path.lower().endswith(".svg"):
        try:
            with open(stamp_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
            if fill_color:
                svg_content = svg_content.replace('class="cls-1"', f'fill="{fill_color}"')
            doc_svg = pymupdf.open(stream=svg_content.encode("utf-8"), filetype="svg")
            doc_vector_pdf = pymupdf.open("pdf", doc_svg.convert_to_pdf())
            page.show_pdf_page(target_rect, doc_vector_pdf, 0, rotate=angle, overlay=overlay)
            doc_svg.close()
            doc_vector_pdf.close()
            return
        except Exception:
            pass

    # 2. Mode Raster PNG (Fallback)
    try:
        img = Image.open(stamp_path).convert("RGBA")
        orig_w, orig_h = img.size
        rotated = img.rotate(angle, resample=Image.BICUBIC, expand=True)

        opacity = random.uniform(*opacity_range)
        r, g, b, a = rotated.split()
        a = a.point(lambda p: int(p * opacity))
        rotated.putalpha(a)

        buf = io.BytesIO()
        rotated.save(buf, format="PNG")
        buf.seek(0)

        scale_w = rotated.size[0] / orig_w
        scale_h = rotated.size[1] / orig_h

        w = base_w * scale_w
        h = base_h * scale_h
        target_rect = pymupdf.Rect(cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0)
        page.insert_image(target_rect, stream=buf.getvalue(), overlay=overlay)
    except Exception:
        target_rect = pymupdf.Rect(cx - base_w / 2.0, cy - base_h / 2.0, cx + base_w / 2.0, cy + base_h / 2.0)
        page.insert_image(target_rect, filename=stamp_path, overlay=overlay)

def render_facade_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = False) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Facade Boutique Hotel Tawangmangu (Azana PMS Format).
    Mendukung durasi multi-malam dinamis (1 malam, 2 malam, 4 malam, dst.) dengan pergeseran
    tata letak footer dan garis pembatas presisi sesuai arsip master referensi Facade.
    Default tidak menggunakan stempel sesuai preferensi Facade Hotel.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "karanganyar_facade"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_name = cfg.get("master_pdf", "master_base.pdf")
    master_pdf_path = os.path.join(tmpl_folder, master_pdf_name)
    if not os.path.exists(master_pdf_path):
        master_pdf_path = os.path.join(tmpl_folder, "master_1night.pdf")

    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("arial", "arial_italic", "cambria_italic"))

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    arr_str = f"{checkin_dt.day:02d}-{EN_MONTHS_SHORT[checkin_dt.month]}-{checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d}-{EN_MONTHS_SHORT[checkout_dt.month]}-{checkout_dt.year}"

    # Printed timestamp (pagi hari saat checkout, diprioritaskan dari trip/guest untuk batch yang logis)
    print_dt = guest.get("print_dt") or trip.get("print_dt")
    if not print_dt:
        print_dt = checkout_dt.replace(hour=random.randint(5, 6), minute=random.randint(2, 45), second=random.randint(10, 55))
    printed_user = hotel_cfg.get("printed_user", cfg.get("printed_user", "YANUAR"))
    printed_str = f"Printed : {printed_user} on {print_dt.strftime('%d-%m-%Y %H:%M:%S')}"

    # Kamar & Folio
    room_no = guest.get("room_no", "202")
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "PRMTT"))
    room_full = f":   {room_no} - {room_suffix}"

    folio_no = guest.get("folio_no")
    if not folio_no:
        yr_short = str(checkin_dt.year)[-2:]
        folio_no = f"FL.{yr_short}01{random.randint(1000, 9999)} / 0"
    if not folio_no.startswith(":"):
        folio_full = f":   {folio_no}"
    else:
        folio_full = folio_no

    rate = guest.get("rate", hotel_cfg.get("default_rate", 550000))
    total_amount = rate * nights
    rate_str = format_rupiah_comma(rate)
    total_str = format_rupiah_comma(total_amount)

    font_color = (35/255, 31/255, 32/255) # 0x231F20
    red_color = (237/255, 35/255, 36/255) # 0xED2324 (Red for Balance)
    line_color = (0.01, 0.015, 0.016)

    # 1. Agency, Nama Tamu, Kota
    agency_txt = guest.get("agency", hotel_cfg.get("default_agency", "KEMENTERIAN PU")).upper()
    guest_name_txt = guest.get("name", "").upper()
    city_txt = guest.get("city", hotel_cfg.get("default_city", "SEMARANG")).upper()

    page.insert_text((53.55, 118.0), agency_txt, fontname="arial", fontsize=10.0, color=font_color)
    page.insert_text((53.55, 130.0), guest_name_txt, fontname="arial", fontsize=10.0, color=font_color)
    page.insert_text((53.55, 142.0), city_txt, fontname="arial", fontsize=10.0, color=font_color)

    # 2. Kolom Metadata Kanan
    page.insert_text((383.59, 125.0), room_full, fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((383.59, 135.8), folio_full, fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((383.59, 146.6), f":   {arr_str}", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((383.59, 156.4), f":   {dep_str}", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((383.59, 178.0), f":   {nights}", fontname="arial", fontsize=9.0, color=font_color)

    # Helper rata kanan untuk kolom nominal (target tepi kanan tabel: x = 460.5)
    font_path = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font_obj = pymupdf.Font("helv")

    def right_align_x(text, target_right_x=460.5, fontsize=9.0):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 5.2
        return target_right_x - w

    # 3. Garis Header Tabel (Atas & Bawah Header Kolom)
    shape_hdr = page.new_shape()
    shape_hdr.draw_line(pymupdf.Point(53.54, 192.74), pymupdf.Point(537.17, 192.74))
    shape_hdr.draw_line(pymupdf.Point(53.54, 212.87), pymupdf.Point(537.17, 212.87))
    shape_hdr.finish(color=line_color, width=0.5)
    shape_hdr.commit()

    # 4. Baris Tabel Transaksi Dinamis (Tiap malam dicatat sebagai baris tersendiri)
    ROW_DY = 20.136
    for i in range(nights):
        cur_dt = checkin_dt + datetime.timedelta(days=i)
        cur_date_str = f"{cur_dt.day:02d}-{EN_MONTHS_SHORT[cur_dt.month]}-{cur_dt.year}"
        base_y = 226.2 + (i * ROW_DY)

        page.insert_text((56.40, base_y), cur_date_str, fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((124.19, base_y), str(room_no), fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((165.27, base_y), hotel_cfg.get("default_room_desc", "ROOM BREAKFAST"), fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((383.36, base_y), "1", fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((right_align_x(rate_str), base_y), rate_str, fontname="arial", fontsize=9.0, color=font_color)

        # Garis pembatas horizontal tiap baris
        line_y = 233.01 + (i * ROW_DY)
        shape = page.new_shape()
        shape.draw_line(pymupdf.Point(53.54, line_y), pymupdf.Point(537.17, line_y))
        shape.finish(color=line_color, width=0.5)
        shape.commit()

    # 4. Total & Balance
    dy_totals = (nights - 1) * ROW_DY
    total_base_y = 253.0 + dy_totals
    bal_base_y = 270.6 + dy_totals

    page.insert_text((379.41, total_base_y), "Total :", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((right_align_x(total_str), total_base_y), total_str, fontname="arial", fontsize=9.0, color=font_color)

    page.insert_text((365.90, bal_base_y), "Balance :", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((right_align_x(total_str), bal_base_y), total_str, fontname="arial", fontsize=9.0, color=red_color)

    # 5. Blok Footer Bawah (Come Back Soon, Signature, Disclaimer, Alamat)
    if nights <= 2:
        come_back_y0 = 256.25 + ((nights - 1) * ROW_DY)
    else:
        come_back_y0 = 256.25 + (nights * ROW_DY)

    page.insert_text((57.19, come_back_y0 + 10.9), "Come Back Soon...", fontname="arial_italic", fontsize=12.0, color=font_color)
    page.insert_text((57.19, come_back_y0 + 28.3), "Please check that you have not left any valuables in the room personal safe.", fontname="cambria_italic", fontsize=7.0, color=font_color)
    page.insert_text((57.19, come_back_y0 + 36.7), "Thank You for choosing to stay with us and we wish you pleasant onward journey.", fontname="cambria_italic", fontsize=7.0, color=font_color)

    # Signature
    page.insert_text((393.64, come_back_y0 + 70.1), "Signature", fontname="arial", fontsize=9.0, color=font_color)
    shape = page.new_shape()
    sig_line_y = come_back_y0 + 68.41
    shape.draw_line(pymupdf.Point(442.82, sig_line_y), pymupdf.Point(533.87, sig_line_y))
    shape.finish(color=line_color, width=0.5)
    shape.commit()

    # Printed footer
    page.insert_text((50.03, come_back_y0 + 103.2), printed_str, fontname="arial", fontsize=9.0, color=font_color)

    # Alamat & Telp Hotel
    page.insert_text((152.01, come_back_y0 + 122.3), "Jl. Balaikambang, Kalisoro, Kec. Tawangmangu, Kabupaten Karanganyar, Jawa Tengah 57792", fontname="arial", fontsize=7.0, color=font_color)
    page.insert_text((264.73, come_back_y0 + 133.3), "Telp: 0812-6688-8821", fontname="arial", fontsize=7.0, color=font_color)

    # Stempel Digital (Hanya jika has_stamp True pada konfigurasi hotel)
    if apply_stamp and hotel_cfg.get("has_stamp", False):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            s_top = come_back_y0 + 1.51
            base_rect = [443.51, s_top, 561.33, s_top + 117.82]
            insert_realistic_stamp(page, stamp_file, base_rect, dx_range=(-4.0, 4.0), dy_range=(-2.5, 2.5), angle_range=(-2.0, 2.0))

    return doc

def format_golden_guest_name(name: str, max_width: float = 142.0, base_fontsize: float = 11.0) -> tuple:
    """
    Memformat nama tamu Golden Hotel agar pas dengan margin tabel.
    Memastikan jika nama asli memiliki minimal 2 kata, maka hasil pemendekan
    tetap mempertahankan minimal 2 kata (contoh: 'Indah Retnaningtyas'),
    bukan hanya 1 kata tunggal ('Indah').
    """
    if not name:
        return "", base_fontsize
    
    tokens = name.replace(",", " ").replace(".", " ").split()
    words = []
    for t in tokens:
        if t.upper() in ["FX", "H.", "HJ."]:
            words.append(t.upper())
        else:
            words.append(t.capitalize())

    if not words:
        return "", base_fontsize

    font_path = r"C:\Windows\Fonts\l_10646.ttf"
    try:
        font = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font = pymupdf.Font("helv")

    min_words = min(2, len(words))

    # Cek kandidat dari jumlah kata terbanyak turun hingga min_words (minimal 2 kata jika aslinya >= 2 kata)
    for k in range(len(words), min_words - 1, -1):
        cand = " ".join(words[:k])
        text = f"Name: {cand}"
        try:
            w = font.text_length(text, fontsize=base_fontsize)
        except Exception:
            w = len(text) * 6.5
        if w <= max_width:
            return cand, base_fontsize

    # Jika kandidat 2 kata masih sedikit melampaui max_width pada font 11.0,
    # sesuaikan ukuran font dengan lembut (misal 10.5 - 10.8) agar 2 kata tetap utuh dan rapi
    cand = " ".join(words[:min_words])
    text = f"Name: {cand}"
    try:
        w = font.text_length(text, fontsize=base_fontsize)
        adjusted_fs = min(base_fontsize, max(8.5, base_fontsize * (max_width / w)))
    except Exception:
        adjusted_fs = base_fontsize

    return cand, adjusted_fs

def render_golden_terbilang(page: pymupdf.Page, total_amount: int, font_name: str = "lucida", base_fontsize: float = 17.87):
    """
    Mencetak teks terbilang resmi pada nota Golden Hotel dalam 1 baris rata tengah (center align).
    Mempertahankan ukuran font asli template (17.87), dan jika teks sangat panjang hingga berisiko
    keluar dari kertas, ukuran font disesuaikan secara proporsional agar tetap pas dan rapi.
    """
    raw_terbilang = terbilang(total_amount).strip()
    full_text = f"\u201c {raw_terbilang}\u201d"

    font_path = r"C:\Windows\Fonts\l_10646.ttf"
    try:
        font = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font = pymupdf.Font("helv")

    page_width = page.rect.width  # 595.28 pt
    safe_margin_x = 42.0  # margin aman dari tepi kiri dan kanan kertas
    max_w = page_width - (2 * safe_margin_x)  # ~511.28 pt

    # Hitung lebar pada ukuran font asli template (17.87)
    try:
        w_base = font.text_length(full_text, fontsize=base_fontsize)
    except Exception:
        w_base = len(full_text) * 9.5

    if w_base <= max_w:
        fs = base_fontsize
        w = w_base
    else:
        # Jika melebihi batas aman kertas, skala font secara proporsional
        fs = base_fontsize * (max_w / w_base)
        try:
            w = font.text_length(full_text, fontsize=fs)
        except Exception:
            w = max_w

    # Posisi rata tengah horizontal (center align)
    start_x = (page_width - w) / 2
    y_pos = 427.2  # Posisi vertikal asli template Golden

    page.insert_text((start_x, y_pos), full_text, fontname=font_name, fontsize=fs)

def render_golden_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Golden Hotel & Villa Wonogiri (Guest Bill & Terbilang Format).
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "wonogiri_golden"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_1night", "master_1night.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("lucida",))

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = trip.get("nights", 1)

    en_month_full = EN_MONTHS[checkin_dt.month]
    en_month_short = EN_MONTHS_SHORT[checkin_dt.month]
    en_checkout_month = EN_MONTHS[checkout_dt.month]

    # Folio & Room Number (Kamar Golden tersedia rentang 16 kamar: 001 s.d. 016)
    room_no = guest.get("room_no")
    if room_no:
        clean_digits = "".join(filter(str.isdigit, str(room_no)))
        if clean_digits:
            r_int = int(clean_digits)
            if r_int > 16:
                r_int = ((r_int - 1) % 16) + 1
            room_str = f"{r_int:03d}"
        else:
            room_str = str(room_no)
    else:
        room_str = f"{random.randint(1, 16):03d}"

    folio_no = guest.get("folio_no")
    if folio_no:
        if "/GuestBill" in folio_no:
            parts = folio_no.split("/GuestBill", 1)
            folio_no = f"{room_str}/GuestBill{parts[1]}"
    else:
        month_name = ID_MONTHS[checkin_dt.month]
        folio_no = f"{room_str}/GuestBill/GH/{month_name}/{checkin_dt.year}"

    # Doc Date
    doc_date_day = f"{checkin_dt.day:02d}" if checkin_dt.day < 10 else f"{checkin_dt.day}"
    doc_date_str = f"{doc_date_day} {en_month_full} {checkin_dt.year}"
    
    # Table dates
    if checkin_dt.month == checkout_dt.month:
        table_date_str = f"{checkin_dt.day:02d}-{checkout_dt.day:02d} {en_month_short} {checkin_dt.year}"
    else:
        table_date_str = f"{checkin_dt.day:02d} {en_month_short} - {checkout_dt.day:02d} {EN_MONTHS_SHORT[checkout_dt.month]} {checkin_dt.year}"

    rate = guest.get("rate", hotel_cfg.get("default_rate", 650000))
    total_amount = rate * nights
    rate_str = format_rupiah_dot(rate)
    total_str = format_rupiah_dot(total_amount)
    
    font_name = "lucida"

    # Injeksi Teks Presisi sesuai Referensi Golden Terbaru
    page.insert_text((146.0, 187.4), f": {folio_no}", fontname=font_name, fontsize=11.0)
    page.insert_text((95.6, 234.9), f"Doc Date : {doc_date_str}", fontname=font_name, fontsize=11.0)
    
    # Format nama tamu agar selalu rapi dalam margin/padding tabel (minimal 2 kata jika aslinya >= 2 kata)
    golden_name, name_fontsize = format_golden_guest_name(guest.get("name", ""))
    page.insert_text((410.1, 187.4), f"Name: {golden_name}", fontname=font_name, fontsize=name_fontsize)

    # Tabel Transaksi
    page.insert_text((100.9, 330.6), table_date_str, fontname=font_name, fontsize=11.0)
    page.insert_text((225.2, 330.6), guest.get("room_type", hotel_cfg.get("default_room_type", "1 Familly room")), fontname=font_name, fontsize=11.0)
    page.insert_text((336.6, 331.4), str(nights), fontname=font_name, fontsize=11.0)
    page.insert_text((370.4, 331.4), f"IDR. {rate_str}", fontname=font_name, fontsize=11.0)
    
    total_x = 466.5 if total_amount >= 1000000 else 471.7
    page.insert_text((total_x, 331.4), f"IDR. {total_str}", fontname=font_name, fontsize=11.0)

    # Terbilang Resmi (Otomatis turun ke baris ke-2 jika panjang agar tidak terpotong batas kertas)
    render_golden_terbilang(page, total_amount, font_name=font_name, base_fontsize=17.87)

    # Total & Pelunasan
    page.insert_text((50.3, 474.6), f"Total Rp. {total_str}", fontname=font_name, fontsize=11.0)
    page.insert_text((50.3, 494.6), f"Pelunasan Rp.{total_str}", fontname=font_name, fontsize=11.0)

    # Tanda Tangan
    checkout_day_str = f"{checkout_dt.day:02d}" if checkout_dt.day < 10 else f"{checkout_dt.day}"
    city_date_str = f"Wonogiri, {checkout_day_str} {en_checkout_month} {checkout_dt.year}"
    page.insert_text((395.5, 578.3), city_date_str, fontname=font_name, fontsize=11.0)

    # Stempel digital realistis
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            base_rect = cfg.get("stamp_rect", [392.5, 532.4, 539.4, 679.3])
            insert_realistic_stamp(page, stamp_file, base_rect, dx_range=(-4.0, 4.0), dy_range=(-2.5, 2.5), angle_range=(-2.0, 2.0))

    return doc

def render_golden_v2_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Golden Hotel & Villa Wonogiri Versi 2.0 (Invoice Raster Base Format).
    Sesuai master referensi resmi GOLDEN Wonogiri 4 Okt.pdf.
    Menggunakan master background raster murni resolusi tinggi 180 DPI A4,
    dengan injeksi teks tajam berpresisi piksel menggunakan font asli lengkap:
    - Arial (Label & Value Info Tamu, Transaksi Kamar)
    - Arial Bold (Header Label Kepada)
    - Arial Narrow Bold (Header Day, Total, Total Amount, Balance)
    - Bebas Neue (Header Date)
    Mendukung format invoice 7 digit, durasi menginap (QTY malam), dan stempel realistis.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "wonogiri_golden_v2"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_1night", "master_1night.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]

    # Register fonts lengkap resmi dari folder template (Full Windows TTF)
    fonts_cfg = cfg.get("fonts", {})
    font_arial = os.path.join(tmpl_folder, fonts_cfg.get("arial", "fonts/arial.ttf"))
    font_bold = os.path.join(tmpl_folder, fonts_cfg.get("arial_bold", "fonts/arial_bold.ttf"))
    font_narrow = os.path.join(tmpl_folder, fonts_cfg.get("arial_narrow", "fonts/arial_narrow_bold.ttf"))
    font_bebas = os.path.join(tmpl_folder, fonts_cfg.get("bebas", "fonts/bebas_regular.ttf"))

    page.insert_font(fontname="Arial", fontfile=font_arial)
    page.insert_font(fontname="ArialBold", fontfile=font_bold)
    page.insert_font(fontname="ArialNarrowBold", fontfile=font_narrow)
    page.insert_font(fontname="Bebas", fontfile=font_bebas)

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = trip.get("nights", 1)

    # 1. Header Date: Hari (checkout) + Tanggal (dd/mm/yyyy)
    # Dihitung dinamis agar hari apapun tidak bertabrakan dengan tanggal dan selalu rata kanan rapi
    en_weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday_str = en_weekdays[checkout_dt.weekday()] + " "
    date_str = checkout_dt.strftime("%d/%m/%Y")

    font_narrow_obj = pymupdf.Font(fontfile=font_narrow)
    font_bebas_obj = pymupdf.Font(fontfile=font_bebas)
    w_day = font_narrow_obj.text_length(weekday_str, fontsize=10.54)
    w_date = font_bebas_obj.text_length(date_str, fontsize=10.54)

    # Posisi rata kanan ke batas tabel (target_right_x = 563.30)
    target_right_x = 563.30
    start_day_x = target_right_x - w_day - w_date
    date_x = start_day_x + w_day

    page.insert_text((start_day_x, 187.87), weekday_str, fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((date_x, 187.87), date_str, fontname="Bebas", fontsize=10.54)

    # 2. Labels Info Tamu - 'Kepada' murni tanpa instansi sesuai referensi master
    page.insert_text((35.35, 204.92), "Kepada", fontname="ArialBold", fontsize=11.22)
    page.insert_text((35.35, 218.90), "No. Invoice", fontname="Arial", fontsize=10.03)
    page.insert_text((35.35, 232.94), "Nama", fontname="Arial", fontsize=10.03)
    page.insert_text((35.35, 247.99), "Tanggal Check in", fontname="Arial", fontsize=10.03)
    page.insert_text((35.35, 262.03), "Tanggal Check out", fontname="Arial", fontsize=10.03)

    # 3. Values Info Tamu - Kolom titik dua ':' diatur di x=126.5 agar tidak menabrak huruf 't' dari 'Tanggal Check out'
    inv_no = guest.get("folio_no") or guest.get("invoice_no") or ""
    clean_digits = "".join(filter(str.isdigit, str(inv_no)))
    if len(clean_digits) >= 5:
        inv_str = clean_digits
    else:
        inv_str = f"127{random.randint(1000, 9999)}"

    guest_name = guest.get("name", "Tamu")
    checkin_str = f"{checkin_dt.day:02d} {ID_MONTHS[checkin_dt.month]} {checkin_dt.year}"
    checkout_str = f"{checkout_dt.day:02d} {ID_MONTHS[checkout_dt.month]} {checkout_dt.year}"

    colon_x = 126.5
    page.insert_text((colon_x, 218.90), f": {inv_str}", fontname="Arial", fontsize=10.03)
    page.insert_text((colon_x, 232.94), f": {guest_name}", fontname="Arial", fontsize=10.03)
    page.insert_text((colon_x, 247.99), f": {checkin_str}", fontname="Arial", fontsize=10.03)
    page.insert_text((colon_x, 262.03), f": {checkout_str}", fontname="Arial", fontsize=10.03)

    # 4. Tabel Transaksi
    rate = guest.get("rate", hotel_cfg.get("default_rate", 650000))
    total_amount = rate * nights
    room_type = guest.get("room_type", hotel_cfg.get("default_room_type", "1 family  room"))

    page.insert_text((60.33, 324.99), "1", fontname="Arial", fontsize=10.54)
    page.insert_text((98.0, 324.99), room_type, fontname="Arial", fontsize=10.54)
    page.insert_text((257.30, 324.99), str(nights), fontname="Arial", fontsize=10.54)
    page.insert_text((302.34, 324.99), f"Rp.{format_rupiah_dot(rate)}", fontname="Arial", fontsize=10.54)

    amount_x = 431.50 if total_amount >= 1000000 else 437.26
    page.insert_text((amount_x, 324.99), f"IDR.{format_rupiah_dot(total_amount)}", fontname="Arial", fontsize=10.54)

    # 5. Summary Bawah Tabel (Format referensi: label, titik dua, dan angka terpisah sejajar)
    total_comma = f"{total_amount:,}"
    # Line 1: Total
    page.insert_text((386.97, 406.51), "Total", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((445.41, 406.51), ":", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((450.69, 406.51), total_comma, fontname="ArialNarrowBold", fontsize=10.54)

    # Line 2: Total Amount
    page.insert_text((388.29, 419.16), "Total", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((410.39, 419.16), "Amount", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((445.41, 419.16), ":", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((450.69, 419.16), total_comma, fontname="ArialNarrowBold", fontsize=10.54)

    # Line 3: Balance
    page.insert_text((388.26, 431.80), "Balance", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((445.41, 431.80), ":", fontname="ArialNarrowBold", fontsize=10.54)
    page.insert_text((450.69, 431.80), total_comma, fontname="ArialNarrowBold", fontsize=10.54)

    # 6. Stempel Digital & Tanda Tangan
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            base_rect = cfg.get("stamp_rect", [402.4, 470.4, 506.0, 550.4])
            insert_realistic_stamp(page, stamp_file, base_rect, dx_range=(-2.0, 2.0), dy_range=(-1.5, 1.5), angle_range=(-1.5, 1.5))

    return doc

def render_trio_azana_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Trio Azana Style Hotel Kebumen (Azana Style Format).
    Mendukung durasi multi-malam dinamis (1 malam, 2 malam, 3 malam, dst.) dengan penambahan
    baris transaksi tabel secara proporsional dan penyesuaian posisi Total & Balance.
    Footer (Come back soon, Signature, Alamat Hotel, Page 1 of 1) berada tetap di bagian bawah halaman.
    Stempel digital resmi FO Dept merah diletakkan di atas garis tanda tangan jika diaktifkan.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "kebumen_trio_azana"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("arial", "arial_bold"))

    # Sisipkan Logo Header jika belum ada di dalam master_base.pdf
    has_top_graphics = any(d["rect"].y1 < 100 for d in page.get_drawings()) or (len(page.get_images()) > 0)
    if not has_top_graphics:
        logo_header_path = os.path.join(tmpl_folder, "logo_header.png")
        if not os.path.exists(logo_header_path):
            svg_path = os.path.join(tmpl_folder, "logo trio azana.svg")
            if os.path.exists(svg_path):
                try:
                    with open(svg_path, "r", encoding="utf-8") as f:
                        svg_content = f.read()
                    svg_fixed = svg_content.replace('class="cls-1"', 'fill="#6d3118"')
                    doc_svg = pymupdf.open(stream=svg_fixed.encode("utf-8"), filetype="svg")
                    doc_svg[0].get_pixmap(dpi=300, alpha=True).save(logo_header_path)
                    doc_svg.close()
                except Exception:
                    pass
        if os.path.exists(logo_header_path):
            page.insert_image(pymupdf.Rect(193.3, 32.0, 401.8, 72.8), filename=logo_header_path)

    font_path = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font_obj = pymupdf.Font("helv")

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    arr_str = f"{checkin_dt.day:02d}-{ID_MONTHS_SHORT[checkin_dt.month]}-{checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d}-{ID_MONTHS_SHORT[checkout_dt.month]}-{checkout_dt.year}"

    # Kamar & Folio
    room_no = guest.get("room_no", "201")
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "DLT"))
    room_full = f":   {room_no} - {room_suffix}"

    folio_no = guest.get("folio_no")
    if not folio_no:
        yr_short = str(checkin_dt.year)[-2:]
        rand_folio = random.randint(1000, 9999)
        folio_no = f"FL.{yr_short}00{rand_folio} / 0"
    if not folio_no.startswith(":"):
        folio_full = f":   {folio_no}"
    else:
        folio_full = folio_no

    rate = guest.get("rate", hotel_cfg.get("default_rate", 600000))
    total_amount = rate * nights
    rate_str = format_rupiah_comma(rate)
    total_str = format_rupiah_comma(total_amount)

    font_color = (35/255, 31/255, 32/255) # 0x231F20
    red_color = (237/255, 28/255, 36/255) # 0xED1C24
    line_color = (0.136, 0.121, 0.124)

    # 1. Left Header: Agency, Nama Tamu, Kota
    raw_agency = guest.get("agency")
    if not raw_agency or "BPPW" in raw_agency or raw_agency.upper() in ["KEMENTERIAN PU", "KEMENTRIAN PU"]:
        agency_txt = hotel_cfg.get("default_agency", "KEMENTRIAN PU").upper()
    else:
        agency_txt = raw_agency.upper()
    guest_name_txt = guest.get("name", "").upper()
    city_txt = guest.get("city", hotel_cfg.get("default_city", "SEMARANG")).upper()

    page.insert_text((46.45, 131.61), agency_txt, fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((46.45, 143.40), guest_name_txt, fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((46.45, 164.52), city_txt, fontname="arial", fontsize=9.0, color=font_color)

    # 2. Right Header: Metadata
    page.insert_text((389.92, 131.65), room_full, fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((389.92, 143.45), folio_full, fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((389.92, 155.25), f":   {arr_str}", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((389.92, 167.05), f":   {dep_str}", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((389.92, 178.85), f":   {nights}", fontname="arial", fontsize=9.0, color=font_color)

    def right_align_x(text, target_right_x=467.10, fontsize=9.0):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 5.2
        return target_right_x - w

    # 3. Baris Tabel Transaksi Dinamis
    ROW_DY = 11.0
    for i in range(nights):
        cur_dt = checkin_dt + datetime.timedelta(days=i)
        cur_date_str = f"{cur_dt.day:02d}-{ID_MONTHS_SHORT[cur_dt.month]}-{cur_dt.year}"
        base_y = 229.09 + (i * ROW_DY)

        page.insert_text((51.09, base_y), cur_date_str, fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((125.73, base_y), str(room_no), fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((160.68, base_y), hotel_cfg.get("default_room_desc", "ROOM BREAKFAST"), fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((380.12, base_y), "1", fontname="arial", fontsize=9.0, color=font_color)
        page.insert_text((right_align_x(rate_str), base_y), rate_str, fontname="arial", fontsize=9.0, color=font_color)

        line_y = 230.20 + (i * ROW_DY)
        shape = page.new_shape()
        shape.draw_line(pymupdf.Point(43.23, line_y), pymupdf.Point(541.83, line_y))
        shape.finish(color=line_color, width=0.5)
        shape.commit()

    # 4. Total & Balance
    dy_totals = (nights - 1) * ROW_DY
    total_y = 246.05 + dy_totals
    bal_y = 257.44 + dy_totals

    page.insert_text((370.96, total_y), "Total :", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((right_align_x(total_str), total_y), total_str, fontname="arial", fontsize=9.0, color=font_color)

    page.insert_text((357.45, bal_y), "Balance :", fontname="arial", fontsize=9.0, color=font_color)
    page.insert_text((right_align_x(total_str), bal_y), total_str, fontname="arial", fontsize=9.0, color=red_color)

    # 5. Stempel Digital Realistis (Vektor Murni)
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "logo stempel.svg"))
        if not os.path.exists(stamp_file):
            stamp_file = os.path.join(tmpl_folder, "stamp.png")
        if os.path.exists(stamp_file):
            base_rect = cfg.get("stamp_rect", [403.0, 660.0, 554.0, 706.6])
            insert_realistic_stamp(page, stamp_file, base_rect, dx_range=(-4.0, 4.0), dy_range=(-2.5, 2.5), angle_range=(-2.2, 2.2), fill_color="#be1e2d")

    return doc

def render_frontone_sragen_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Front One Hotel Sragen (Azana PMS / Front One Format).
    Mendukung format Front One PMS resmi dengan logo vektor murni resolusi tinggi,
    penempatan tabel dan footer presisi, serta pemilihan stempel digital cap basah
    organik (stamp.png dan stamp2.png).
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "sragen_frontone"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("arial", "arial_italic", "constantia_italic"))

    font_path = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font_obj = pymupdf.Font("helv")

    def right_align_x(text, target_right_x=471.31, fontsize=8.0):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 4.6
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    arr_str = f"{checkin_dt.day:02d}-{EN_MONTHS_SHORT[checkin_dt.month]}-{checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d}-{EN_MONTHS_SHORT[checkout_dt.month]}-{checkout_dt.year}"

    # Print timestamp
    print_dt = guest.get("print_dt") or trip.get("print_dt")
    if not print_dt:
        print_dt = checkout_dt.replace(hour=random.randint(7, 8), minute=random.randint(15, 45), second=random.randint(10, 55))
    printed_user = hotel_cfg.get("printed_user", cfg.get("printed_user", "IKHSAN"))
    printed_str = f"Printed : {printed_user} on {print_dt.strftime('%d-%m-%Y %H:%M:%S')}"

    # Room & Folio
    room_no = guest.get("room_no", "207")
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "DLT"))
    room_full = f":   {room_no} - {room_suffix}"

    folio_no = guest.get("folio_no")
    if not folio_no:
        yr_short = str(checkin_dt.year)[-2:]
        rand_fol = random.randint(1000, 9999)
        folio_no = f"FL.{yr_short}00{rand_fol}  /  0"
    if not folio_no.startswith(":"):
        folio_full = f":   {folio_no}"
    else:
        folio_full = folio_no

    rate = guest.get("rate", hotel_cfg.get("default_rate", 680000))
    total_amount = rate * nights
    rate_str = format_rupiah_comma(rate)
    total_str = format_rupiah_comma(total_amount)

    font_color = (3/255, 4/255, 5/255) # #030405
    red_color = (237/255, 33/255, 39/255) # #ED2127
    line_color = (0.135, 0.121, 0.124) # #221F20

    # 1. Left Header: Agency, Name, City (Sesuai referensi resmi Front One Sragen: KEMENTRIAN PU JATENG)
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "KEMENTRIAN PU JATENG")
    if not raw_agency or "BPPW" in raw_agency.upper() or raw_agency.upper() in ["KEMENTERIAN PU", "KEMENTRIAN PU", "BPBPK", "BPBPK JAWA TENGAH", "KEMENTRIAN PU JATENG", "KEMENTERIAN PU JATENG"]:
        agency_txt = default_agency.upper()
    else:
        agency_txt = raw_agency.upper()
    guest_name_txt = guest.get("name", "").upper()
    city_txt = guest.get("city", hotel_cfg.get("default_city", "SEMARANG, JAWA TENGAH")).upper()

    page.insert_text((53.57, 79.35), agency_txt, fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((53.57, 91.16), guest_name_txt, fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((53.57, 102.97), city_txt, fontname="arial", fontsize=8.0, color=font_color)

    # 2. Right Header Labels & Values
    page.insert_text((325.70, 79.35), "Room", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((325.70, 91.16), "Folio", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((325.70, 102.96), "Arrival", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((325.70, 114.77), "Departure", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((325.70, 126.58), "Room Night", fontname="arial", fontsize=8.0, color=font_color)

    page.insert_text((396.17, 79.36), room_full, fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((396.17, 91.16), folio_full, fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((396.17, 102.97), f":   {arr_str}", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((396.17, 114.78), f":   {dep_str}", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((396.17, 126.59), f":   {nights}", fontname="arial", fontsize=8.0, color=font_color)

    # 3. Table Header Lines & Column Names
    shape = page.new_shape()
    shape.draw_line(pymupdf.Point(46.12, 140.44), pymupdf.Point(549.16, 140.44))
    shape.draw_line(pymupdf.Point(46.12, 159.54), pymupdf.Point(549.16, 159.54))
    shape.finish(color=line_color, width=0.5)
    shape.commit()

    page.insert_text((74.65, 157.84), "Date", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((129.18, 157.84), "Room", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((247.40, 157.84), "Description", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((381.35, 157.84), "Qty", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((430.57, 157.84), "Debit", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((499.84, 157.84), "Credit", fontname="arial", fontsize=8.0, color=font_color)

    # 4. Transaction Rows (Dinamis bertambah ke bawah per malam, Qty tiap malam selalu 1)
    ROW_DY = 13.93
    for i in range(nights):
        cur_night_dt = checkin_dt + datetime.timedelta(days=i)
        cur_night_str = f"{cur_night_dt.day:02d}-{EN_MONTHS_SHORT[cur_night_dt.month]}-{cur_night_dt.year}"
        row_y = 169.99 + (i * ROW_DY)

        page.insert_text((60.89, row_y), cur_night_str, fontname="arial", fontsize=8.0, color=font_color)
        page.insert_text((132.56, row_y), str(room_no), fontname="arial", fontsize=8.0, color=font_color)
        page.insert_text((168.18, row_y), hotel_cfg.get("default_room_desc", "ROOM BREAKFAST"), fontname="arial", fontsize=8.0, color=font_color)
        page.insert_text((384.90, row_y), "1", fontname="arial", fontsize=8.0, color=font_color)
        page.insert_text((right_align_x(rate_str), row_y), rate_str, fontname="arial", fontsize=8.0, color=font_color)

        # Garis pembatas horizontal tiap baris transaksi
        line_y = 173.47 + (i * ROW_DY)
        shape_row = page.new_shape()
        shape_row.draw_line(pymupdf.Point(46.12, line_y), pymupdf.Point(549.16, line_y))
        shape_row.finish(color=line_color, width=0.5)
        shape_row.commit()

    # Pergeseran dinamis untuk seluruh blok bawah (Total, Balance, Footer, Signature, Stamp)
    dy = (nights - 1) * ROW_DY

    # 5. Total & Balance
    total_y = 187.41 + dy
    bal_y = 199.41 + dy
    page.insert_text((380.88, total_y), "Total :", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((right_align_x(total_str), total_y), total_str, fontname="arial", fontsize=8.0, color=font_color)

    page.insert_text((368.88, bal_y), "Balance :", fontname="arial", fontsize=8.0, color=font_color)
    page.insert_text((right_align_x(total_str), bal_y), total_str, fontname="arial", fontsize=8.0, color=red_color)

    # 6. Footer (Come back soon, notices, Signature, Printed)
    page.insert_text((48.49, 199.32 + dy), "Come back soon...", fontname="arial_italic", fontsize=12.0, color=font_color)
    page.insert_text((46.12, 217.84 + dy), "Please check that you have not left any valuables in the room personal safe.", fontname="constantia_italic", fontsize=7.5, color=font_color)
    page.insert_text((46.12, 229.84 + dy), "Thank you for choosing to stay with us and we wish you pleasant onward journey.", fontname="constantia_italic", fontsize=7.5, color=font_color)

    page.insert_text((410.99, 248.92 + dy), "Signature", fontname="arial", fontsize=8.0, color=font_color)
    shape_sig = page.new_shape()
    shape_sig.draw_line(pymupdf.Point(449.10, 248.92 + dy), pymupdf.Point(545.03, 248.92 + dy))
    shape_sig.finish(color=line_color, width=0.5)
    shape_sig.commit()

    page.insert_text((47.08, 260.36 + dy), printed_str, fontname="arial", fontsize=8.0, color=font_color)

    # 7. Stempel Digital Realistis
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        # Pilih acak antara stamp2.png dan stamp.png untuk variasi cap basah realistis
        stamp_candidates = cfg.get("stamp_files", ["stamp2.png", "stamp.png"])
        selected_stamp = random.choice(stamp_candidates)
        stamp_file = os.path.join(tmpl_folder, selected_stamp)
        if not os.path.exists(stamp_file):
            stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp2.png"))
        if os.path.exists(stamp_file):
            if nights > 1:
                # Multi-malam: stempel diletakkan di bawah tabel pada area tanda tangan (Signature)
                # sesuai referensi Fachrul agar sama sekali tidak menabrak baris teks transaksi tabel
                sig_y = 248.92 + dy
                base_rect = [438.0, sig_y - 40.0, 554.0, sig_y + 36.0]
            else:
                # 1 malam: gunakan posisi standar master (Apr2026)
                base_rect = [430.0, 155.0, 555.0, 245.0]

            insert_realistic_stamp(
                page,
                stamp_file,
                base_rect,
                dx_range=(-3.5, 3.5),
                dy_range=(-2.0, 2.0),
                angle_range=(-1.8, 1.8),
                opacity_range=(0.78, 0.86)
            )

    return doc

def render_ardiana_purworejo_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Sajiwa by Ardiana Suite Hotel Purworejo (Azana PMS Format).
    Menggunakan master_base.pdf vektor murni beresolusi tinggi, susunan tabel condensed 1 baris
    dengan Qty = malam inap, Debit = tarif kamar (format titik), Total & Balance = total transaksi (format koma),
    Instansi 'KEMENTERIAN PU' di pojok kiri atas, serta stempel digital 'LOGO ARDIANA' autentik.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "purworejo_ardiana"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("arial", "arial_italic"))

    font_path = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font_obj = pymupdf.Font("helv")

    def right_align_x(text, target_right_x=467.02, fontsize=7.36):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 4.4
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    arr_str = f"{checkin_dt.day:02d}-{EN_MONTHS_SHORT[checkin_dt.month]}-{checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d}-{EN_MONTHS_SHORT[checkout_dt.month]}-{checkout_dt.year}"

    # Print timestamp
    print_dt = guest.get("print_dt") or trip.get("print_dt")
    if not print_dt:
        print_dt = checkout_dt.replace(hour=random.randint(5, 7), minute=random.randint(15, 45), second=random.randint(10, 55))
    printed_user = hotel_cfg.get("printed_user", cfg.get("printed_user", "BAYU"))
    printed_str = f"Printed : {printed_user} on {print_dt.strftime('%d-%m-%Y %H:%M:%S')}"

    # Room & Folio
    room_no = guest.get("room_no", "202")
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "CT"))
    room_full = f":   {room_no} - {room_suffix}"

    folio_no = guest.get("folio_no")
    if not folio_no:
        yr_short = str(checkin_dt.year)[-2:]
        rand_fol = random.randint(1000, 9999)
        folio_no = f"FL.{yr_short}00{rand_fol} / 0"
    if not folio_no.startswith(":"):
        folio_full = f":   {folio_no}"
    else:
        folio_full = folio_no

    rate = guest.get("rate", hotel_cfg.get("default_rate", 500000))
    total_amount = rate * nights
    debit_str = format_rupiah_dot(rate)
    total_str = format_rupiah_comma(total_amount)

    font_color = (0, 0, 0)
    red_color = (244/255, 0, 0) # #F40000

    # 1. Left Header: Agency, Name, City (WAJIB KEMENTERIAN PU)
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "KEMENTERIAN PU")
    if not raw_agency or any(k in raw_agency.upper() for k in ["BPPW", "PUPR", "KEMENTERIAN PU", "KEMENTRIAN PU", "BPBPK"]):
        agency_txt = default_agency.upper()
    else:
        agency_txt = raw_agency.upper()
    guest_name_txt = guest.get("name", "").upper()
    city_txt = guest.get("city", hotel_cfg.get("default_city", "PURWOREJO")).upper()

    page.insert_text((61.07, 92.06), agency_txt, fontname="arial", fontsize=7.43, color=font_color)
    page.insert_text((61.07, 103.56), guest_name_txt, fontname="arial", fontsize=7.43, color=font_color)
    page.insert_text((61.07, 127.29), city_txt, fontname="arial", fontsize=7.43, color=font_color)

    # 2. Right Header Values
    page.insert_text((394.02, 92.56), room_full, fontname="arial", fontsize=7.63, color=font_color)
    page.insert_text((394.02, 104.56), folio_full, fontname="arial", fontsize=7.63, color=font_color)
    page.insert_text((394.03, 116.57), f":   {arr_str}", fontname="arial", fontsize=7.63, color=font_color)
    page.insert_text((393.96, 128.57), f":   {dep_str}", fontname="arial", fontsize=7.63, color=font_color)
    page.insert_text((393.96, 140.57), f":   {nights}", fontname="arial", fontsize=7.63, color=font_color)

    # 3. Table Row 1 (Format khas Ardiana: 1 baris terpadu, Qty = jumlah malam inap)
    page.insert_text((67.83, 178.96), arr_str, fontname="arial", fontsize=7.36, color=font_color)
    page.insert_text((139.15, 178.95), str(room_no), fontname="arial", fontsize=7.36, color=font_color)
    page.insert_text((171.91, 178.95), hotel_cfg.get("default_room_desc", "ROOM BREAKFAST"), fontname="arial", fontsize=7.36, color=font_color)
    page.insert_text((383.92, 178.95), str(nights), fontname="arial", fontsize=7.36, color=font_color)
    page.insert_text((right_align_x(debit_str), 178.95), debit_str, fontname="arial", fontsize=7.36, color=font_color)

    # 4. Total & Balance
    page.insert_text((right_align_x(total_str), 197.13), total_str, fontname="arial", fontsize=7.36, color=font_color)
    page.insert_text((right_align_x(total_str), 208.48), total_str, fontname="arial", fontsize=7.36, color=red_color)

    # 5. Printed
    page.insert_text((56.13, 266.81), printed_str, fontname="arial", fontsize=7.21, color=font_color)

    # 6. Realistic Stamp
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            base_rect = [446.0, 220.0, 550.0, 252.0]
            insert_realistic_stamp(
                page,
                stamp_file,
                base_rect,
                dx_range=(-2.5, 2.5),
                dy_range=(-1.5, 1.5),
                angle_range=(-1.5, 1.5),
                opacity_range=(0.84, 0.92)
            )

    return doc

def render_surya_yudha_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Hotel Surya Yudha Banjarnegara.
    Mendukung durasi multi-malam dinamis (1 malam, 2 malam, dst.) dengan penambahan
    baris transaksi tabel secara proporsional dan pergeseran Total & Balance.
    Stempel digital cap basah ungu/merah ditempatkan realistis di atas garis Signature.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "banjarnegara_surya_yudha"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("arial", "arial_italic", "calibri", "verdana", "verdana_italic"))

    font_path = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj = pymupdf.Font(fontfile=font_path) if os.path.exists(font_path) else pymupdf.Font("helv")
    except Exception:
        font_obj = pymupdf.Font("helv")

    def right_align_x(text, target_right_x=480.05, fontsize=8.19):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 4.8
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    arr_str = f"{checkin_dt.day:02d}-{EN_MONTHS_SHORT[checkin_dt.month]}-{checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d}-{EN_MONTHS_SHORT[checkout_dt.month]}-{checkout_dt.year}"

    # Room & Folio
    room_no = guest.get("room_no", "412")
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "SPD"))
    room_full = f"{room_no} - {room_suffix}"

    folio_no = guest.get("folio_no")
    if not folio_no:
        yr_short = str(checkin_dt.year)[-2:]
        rand_fol = random.randint(1000, 9999)
        folio_no = f"FL.{yr_short}00{rand_fol}  /  0"
    if folio_no.startswith(":"):
        folio_no = folio_no.lstrip(":").strip()

    rate = guest.get("rate", hotel_cfg.get("default_rate", 440000))
    total_amount = rate * nights
    rate_str = format_rupiah_comma(rate)
    total_str = format_rupiah_comma(total_amount)

    font_color = (0, 0, 0)
    line_color = (0, 0, 0)

    # 1. Left Header: Nama Tamu, Instansi, Kota
    guest_name_txt = guest.get("name", "").upper()
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "KEMENTERIAN PU")
    if not raw_agency or raw_agency.upper() in ["KEMENTERIAN PU", "KEMENTRIAN PU", "PU"]:
        agency_txt = default_agency.upper()
    else:
        agency_txt = raw_agency.upper()
    city_txt = guest.get("city", hotel_cfg.get("default_city", "SEMARANG")).upper()

    page.insert_text((58.69, 113.01), guest_name_txt, fontname="arial", fontsize=8.93, color=font_color)
    page.insert_text((58.69, 125.00), agency_txt, fontname="arial", fontsize=8.93, color=font_color)
    page.insert_text((58.69, 137.00), city_txt, fontname="arial", fontsize=8.93, color=font_color)

    # 2. Right Header Values
    page.insert_text((403.63,  99.98), room_full, fontname="arial", fontsize=8.19, color=font_color)
    page.insert_text((403.63, 112.00), folio_no, fontname="arial", fontsize=8.19, color=font_color)
    page.insert_text((403.63, 124.03), arr_str, fontname="arial", fontsize=8.19, color=font_color)
    page.insert_text((403.63, 136.06), dep_str, fontname="arial", fontsize=8.19, color=font_color)
    page.insert_text((403.63, 148.08), str(nights), fontname="arial", fontsize=8.19, color=font_color)

    # 3. Baris Tabel Transaksi Dinamis
    ROW_DY = 12.02
    for i in range(nights):
        cur_night_dt = checkin_dt + datetime.timedelta(days=i)
        cur_date_str = f"{cur_night_dt.day:02d}-{EN_MONTHS_SHORT[cur_night_dt.month]}-{cur_night_dt.year}"
        row_y = 197.18 + (i * ROW_DY)

        page.insert_text((64.30, row_y), cur_date_str, fontname="arial", fontsize=8.19, color=font_color)
        page.insert_text((141.40, row_y), str(room_no), fontname="arial", fontsize=8.19, color=font_color)
        page.insert_text((176.56, row_y), hotel_cfg.get("default_room_desc", "ROOM CHARGE"), fontname="arial", fontsize=8.19, color=font_color)
        page.insert_text((394.57, row_y), "1", fontname="arial", fontsize=8.19, color=font_color)
        page.insert_text((right_align_x(rate_str), row_y), rate_str, fontname="arial", fontsize=8.19, color=font_color)

        line_y = 200.40 + (i * ROW_DY)
        shape_row = page.new_shape()
        shape_row.draw_line(pymupdf.Point(53.60, line_y), pymupdf.Point(542.00, line_y))
        shape_row.finish(color=line_color, width=0.5)
        shape_row.commit()

    dy = (nights - 1) * ROW_DY
    total_y = 214.50 + dy
    bal_y = 226.52 + dy

    page.insert_text((389.66, total_y), "Total :", fontname="arial", fontsize=8.19, color=font_color)
    page.insert_text((right_align_x(total_str), total_y), total_str, fontname="arial", fontsize=8.19, color=font_color)

    page.insert_text((377.37, bal_y), "Balance :", fontname="arial", fontsize=8.19, color=font_color)
    page.insert_text((right_align_x(total_str), bal_y), total_str, fontname="arial", fontsize=8.19, color=font_color)

    # 4. Realistic Stamp (Layer paling belakang / overlay=False)
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            base_rect = [409.92, 626.80, 546.24, 724.24]
            insert_realistic_stamp(
                page,
                stamp_file,
                base_rect,
                dx_range=(-3.0, 3.0),
                dy_range=(-2.0, 2.0),
                angle_range=(-1.8, 1.8),
                opacity_range=(0.84, 0.92),
                overlay=False
            )

    # 5. Teks Signature & Garis (Wajib berada di layer paling depan di atas stempel)
    page.insert_text((409.46, 711.70), "Signature _____________________", fontname="arial", fontsize=8.19, color=font_color)

    return doc

def render_artos_magelang_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = False) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Grand Artos Hotel & Convention Magelang.
    Mendukung durasi multi-malam dinamis (1 malam, 2 malam, dst.) dengan penambahan
    baris transaksi tabel secara proporsional dan pergeseran baris Balance.
    Font murni Comic Sans MS sesuai master folio resmi referensi Artos.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "magelang_artos"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("comic", "comic_bold"))

    font_path_bold = r"C:\Windows\Fonts\comicbd.ttf"
    font_path_reg = r"C:\Windows\Fonts\comic.ttf"
    try:
        font_obj_bold = pymupdf.Font(fontfile=font_path_bold) if os.path.exists(font_path_bold) else pymupdf.Font("helv")
        font_obj_reg = pymupdf.Font(fontfile=font_path_reg) if os.path.exists(font_path_reg) else pymupdf.Font("helv")
    except Exception:
        font_obj_bold = pymupdf.Font("helv")
        font_obj_reg = pymupdf.Font("helv")

    def right_align_x(font_obj, text, target_right_x=570.78, fontsize=8.86):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * (fontsize * 0.55)
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    # Format tanggal PMS Artos: e.g. "23 Aug 2024"
    arr_str = f"{checkin_dt.day:02d} {EN_MONTHS_SHORT[checkin_dt.month]} {checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d} {EN_MONTHS_SHORT[checkout_dt.month]} {checkout_dt.year}"

    # Nama Tamu (Format Artos: diakhiri koma)
    raw_name = guest.get("name", "").strip()
    guest_name_val = f": {raw_name}," if not raw_name.endswith(",") else f": {raw_name}"

    # Room No (murni angka tanpa suffix, default 501+)
    room_no = str(guest.get("room_no", "501"))
    room_val = f": {room_no}"

    # Arrival & Departure
    arr_val = f": {arr_str}"
    dep_val = f": {dep_str}"

    # Reservation No (default 6 digit, e.g. 172895)
    res_no = guest.get("reservation_no") or guest.get("res_no")
    if not res_no:
        res_no = str(random.randint(142000, 178000))
    res_val = f": {res_no}"

    # Bill No (default e.g. 333577 / 1)
    bill_no = guest.get("bill_no") or guest.get("folio_no")
    if not bill_no:
        rand_bill = random.randint(333500, 333599)
        bill_no = f"{rand_bill} / 1"
    if bill_no.startswith(":"):
        bill_no = bill_no.lstrip(":").strip()
    bill_val = f": {bill_no}"

    # Agency at Right Header (Right-aligned, WAJIB Kementerian PU, dilarang PUPR)
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "Kementerian PU")
    if not raw_agency or any(k in raw_agency.upper() for k in ["PUPR", "KEMENTERIAN PU", "KEMENTRIAN PU", "PU", "BPPW"]):
        agency_name = default_agency.strip()
    else:
        agency_name = raw_agency.strip()

    # Sanitasi ketat: pastikan kata PUPR tidak pernah muncul
    if "PUPR" in agency_name.upper():
        agency_name = agency_name.replace("PUPR", "PU").replace("pupr", "PU").replace("Pupr", "PU")

    agency_disp = f"{agency_name}," if not agency_name.endswith(",") else agency_name

    font_color = (0.136, 0.121, 0.124) # #231F20 exact PMS color

    # 1. Left Header Values (origin x = 109.76)
    page.insert_text((109.76, 135.25), guest_name_val, fontname="comic_bold", fontsize=8.0, color=font_color)
    page.insert_text((109.76, 146.95), room_val, fontname="comic_bold", fontsize=8.0, color=font_color)
    page.insert_text((109.76, 158.65), arr_val, fontname="comic_bold", fontsize=8.0, color=font_color)
    page.insert_text((109.76, 170.36), dep_val, fontname="comic_bold", fontsize=8.0, color=font_color)
    page.insert_text((109.76, 182.06), res_val, fontname="comic_bold", fontsize=8.0, color=font_color)
    page.insert_text((109.76, 193.76), bill_val, fontname="comic_bold", fontsize=8.0, color=font_color)

    # 2. Right Agency Header (Right-aligned to 570.78, y origin = 195.47)
    agency_x = right_align_x(font_obj_bold, agency_disp, target_right_x=570.78, fontsize=8.86)
    page.insert_text((agency_x, 195.47), agency_disp, fontname="comic_bold", fontsize=8.86, color=font_color)

    # 3. Baris Tabel Transaksi Dinamis
    rate = guest.get("rate", hotel_cfg.get("default_rate", 670000))
    total_amount = rate * nights
    rate_str = f"{rate:,.2f}" # "670,000.00"
    total_str = f"{total_amount:,.2f}"

    ROW_DY = 14.76
    for i in range(nights):
        cur_night_dt = checkin_dt + datetime.timedelta(days=i)
        cur_date_str = f"{cur_night_dt.day:02d} {EN_MONTHS_SHORT[cur_night_dt.month]} {cur_night_dt.year}"
        row_y = 257.55 + (i * ROW_DY)

        page.insert_text((59.29, row_y), cur_date_str, fontname="comic", fontsize=9.07, color=font_color)
        page.insert_text((226.77, row_y), hotel_cfg.get("default_room_desc", "Room Charge"), fontname="comic", fontsize=9.07, color=font_color)
        amt_x = right_align_x(font_obj_reg, rate_str, target_right_x=562.20, fontsize=9.07)
        page.insert_text((amt_x, row_y), rate_str, fontname="comic", fontsize=9.07, color=font_color)

    # Garis pembatas sebelum Balance
    div_y = 261.85 + (nights - 1) * ROW_DY
    shape_div = page.new_shape()
    shape_div.draw_line(pymupdf.Point(45.93, div_y), pymupdf.Point(564.59, div_y))
    shape_div.finish(color=font_color, width=0.5)
    shape_div.commit()

    # Baris Balance
    bal_y = 272.31 + (nights - 1) * ROW_DY
    page.insert_text((390.60, bal_y), "Balance", fontname="comic_bold", fontsize=9.07, color=font_color)
    bal_amt_x = right_align_x(font_obj_bold, total_str, target_right_x=565.30, fontsize=9.07)
    page.insert_text((bal_amt_x, bal_y), total_str, fontname="comic_bold", fontsize=9.07, color=font_color)

    # 4. Footer Printed by
    print_dt = guest.get("print_dt") or trip.get("print_dt")
    if not print_dt:
        print_dt = checkout_dt.replace(hour=random.randint(1, 2), minute=random.randint(35, 55))
    printed_user = hotel_cfg.get("printed_user", cfg.get("printed_user", "468"))
    # Format e.g. "24 August 2024 02:40"
    print_dt_str = f"{print_dt.day:02d} {EN_MONTHS[print_dt.month]} {print_dt.year} {print_dt.strftime('%H:%M')}"
    printed_txt = f"Printed by : {printed_user} - {print_dt_str}"
    page.insert_text((42.56, 666.81), printed_txt, fontname="comic_bold", fontsize=8.0, color=font_color)

    # 5. Optional stamp jika ada
    if apply_stamp and hotel_cfg.get("has_stamp", False):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            insert_realistic_stamp(page, stamp_file, [427.0, 640.0, 565.0, 730.0], overlay=False)

    return doc

def render_atrium_cilacap_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Atrium Premiere Hotel Cilacap.
    Mendukung format resmi Atrium Premiere Hotel Cilacap dengan watermark logo murni,
    header logo bintang 3 emas, rincian reservasi akurat, dan tabel transaksi dinamis
    multi-malam (1 malam, 2 malam, dst.) lengkap dengan stempel cap basah otentik PAID.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "cilacap_atrium"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]

    font_path_arial = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj_arial = pymupdf.Font(fontfile=font_path_arial) if os.path.exists(font_path_arial) else pymupdf.Font("helv")
    except Exception:
        font_obj_arial = pymupdf.Font("helv")

    def right_align_amount(text, target_right_x=522.30, fontsize=9.0):
        try:
            w = font_obj_arial.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 5.0
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    # Format dates: DD/MM/YY
    arr_str = checkin_dt.strftime("%d/%m/%y")
    dep_str = checkout_dt.strftime("%d/%m/%y")

    # Format Nama Tamu khas Atrium PMS (prefix MR. ,)
    raw_name = guest.get("name", "").strip().upper()
    if not (raw_name.startswith("MR.") or raw_name.startswith("MRS.") or raw_name.startswith("MS.")):
        guest_name_val = f"MR. ,{raw_name}"
    else:
        guest_name_val = raw_name

    # Instansi (Header Kanan)
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "KEMENTERIAN PU")
    if not raw_agency or any(k in raw_agency.upper() for k in ["PU", "PUPR", "BPPW", "KEMENTERIAN PU", "KEMENTRIAN PU"]):
        agency_name = default_agency.strip()
    else:
        agency_name = raw_agency.strip()

    # Room number
    room_no = str(guest.get("room_no", "321"))

    # Bill number: default 6 digit, e.g. 127211 / 1
    bill_no = guest.get("bill_no") or guest.get("folio_no")
    if not bill_no:
        rand_bill = random.randint(127200, 127299)
        bill_no = f"{rand_bill} / 1"
    elif not "/" in str(bill_no):
        bill_no = f"{bill_no} / 1"

    # Rates
    rate = guest.get("rate", hotel_cfg.get("default_rate", 550000))
    total_amount = rate * nights
    rate_str = f"{float(rate):,.2f}"
    total_str = f"{float(total_amount):,.2f}"

    desc_room = guest.get("description", hotel_cfg.get("default_room_desc", "ROOM CHARGE"))

    # 1. Insert Guest Name & Agency
    page.insert_text(pymupdf.Point(41.90, 167.62), guest_name_val, fontfile=font_path_arial, fontsize=10.0, color=(0, 0, 0))
    try:
        ag_w = font_obj_arial.text_length(agency_name, fontsize=11.0)
        ag_x = 553.58 - ag_w
    except Exception:
        ag_x = 455.88
    page.insert_text(pymupdf.Point(ag_x, 168.52), agency_name, fontfile=font_path_arial, fontsize=11.0, color=(0, 0, 0))

    # 2. Insert Room & Reservation Values
    page.insert_text(pymupdf.Point(293.05, 193.72), room_no, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(288.05, 214.42), f": {arr_str}", fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(293.05, 224.72), dep_str, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(288.05, 235.12), f": {bill_no}", fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))

    # 3. Dynamic Transaction Table Rows
    ROW_DY = 11.80
    cols = [43.30, 107.22, 270.25, 326.95, 447.48, 546.68]

    shape = page.new_shape()
    for i in range(nights):
        cur_night_dt = checkin_dt + datetime.timedelta(days=i)
        cur_night_str = cur_night_dt.strftime("%d/%m/%y")
        row_y = 291.42 + (i * ROW_DY)
        top_y = 282.27 + (i * ROW_DY)
        bot_y = top_y + ROW_DY

        # Text
        page.insert_text(pymupdf.Point(58.00, row_y), cur_night_str, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(112.82, row_y), desc_room, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(296.25, row_y), "1", fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(379.85, row_y), room_no, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_amount(rate_str), row_y), rate_str, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))

        # Bottom horizontal line of this row
        shape.draw_line(pymupdf.Point(43.30, bot_y), pymupdf.Point(546.68, bot_y))
        # Vertical column dividers
        for x in cols:
            shape.draw_line(pymupdf.Point(x, top_y), pymupdf.Point(x, bot_y))

    # 4. Balance Row
    dy_balance = (nights - 1) * ROW_DY
    bal_top_y = 294.07 + dy_balance
    bal_bot_y = 305.87 + dy_balance
    bal_text_y = 303.22 + dy_balance

    # Text Balance
    page.insert_text(pymupdf.Point(409.75, bal_text_y), "Balance", fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(right_align_amount(total_str), bal_text_y), total_str, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))

    # Balance row borders
    shape.draw_line(pymupdf.Point(43.30, bal_bot_y), pymupdf.Point(546.68, bal_bot_y))
    shape.draw_line(pymupdf.Point(43.30, bal_top_y), pymupdf.Point(43.30, bal_bot_y))
    shape.draw_line(pymupdf.Point(447.48, bal_top_y), pymupdf.Point(447.48, bal_bot_y))
    shape.draw_line(pymupdf.Point(546.68, bal_top_y), pymupdf.Point(546.68, bal_bot_y))

    shape.finish(color=(0, 0, 0), width=0.5)
    shape.commit()

    # 5. Stempel Digital Cap Basah Organik
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        stamp_file = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp.png"))
        if os.path.exists(stamp_file):
            base_stamp_rect = cfg.get("stamp_rect", [466.85, 411.65, 550.10, 584.15])
            insert_realistic_stamp(
                page,
                stamp_file,
                base_stamp_rect,
                dx_range=(-2.5, 2.5),
                dy_range=(-2.0, 2.0),
                angle_range=(-1.5, 1.5),
                opacity_range=(0.85, 0.95),
                overlay=True
            )

    return doc

def render_wisata_niaga_banyumas_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Hotel Wisata Niaga Purwokerto (Banyumas).
    Mendukung format resmi PMS Wisata Niaga Purwokerto dengan:
    - Logo Hotel Wisata Niaga (emas & hijau) di pojok kiri atas persis sesuai aslinya
    - QR Code resmi hotel di pojok kanan atas persis sesuai aslinya
    - Header judul HOTEL WISATA NIAGA PURWOKERTO & kontak lengkap
    - Kotak judul dokumen GUEST BILLING INFORMATION
    - Rincian tamu, instansi (default KEMENTERIAN PU), kamar, tanggal arrival/departure, dan folio
    - Tabel transaksi multi-malam (1 malam, 2 malam, dst.) dengan open horizontal grid
    - Baris TOTAL dinamis proporsional
    - Kolom print info & disclaimers (ID & EN)
    - Kolom tanda tangan dengan paraf otentik JAKA dan stempel cap basah hijau otentik.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "banyumas_wisata_niaga"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    footer_block_path = os.path.join(tmpl_folder, "footer_block.png")
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]

    font_path_arial = r"C:\Windows\Fonts\arial.ttf"
    font_path_arial_bold = r"C:\Windows\Fonts\arialbd.ttf"
    font_path_times = r"C:\Windows\Fonts\times.ttf"

    try:
        font_obj_arial = pymupdf.Font(fontfile=font_path_arial) if os.path.exists(font_path_arial) else pymupdf.Font("helv")
    except Exception:
        font_obj_arial = pymupdf.Font("helv")

    try:
        font_obj_bold = pymupdf.Font(fontfile=font_path_arial_bold) if os.path.exists(font_path_arial_bold) else pymupdf.Font("helv")
    except Exception:
        font_obj_bold = pymupdf.Font("helv")

    def right_align_x(text, target_right_x=387.79, font_obj=font_obj_arial, fontsize=8.0):
        try:
            w = font_obj.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 4.6
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    # Format dates
    arr_str = f"{checkin_dt.day} {ID_MONTHS[checkin_dt.month]} {checkin_dt.year}"
    dep_str = f"{checkout_dt.day} {ID_MONTHS[checkout_dt.month]} {checkout_dt.year}"

    # Nama Tamu
    guest_name_val = guest.get("name", "").strip().upper()

    # Instansi (Company)
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "KEMENTERIAN PU")
    if not raw_agency or any(k in raw_agency.upper() for k in ["PU", "PUPR", "BPPW", "KEMENTERIAN PU", "KEMENTRIAN PU"]):
        agency_val = default_agency.strip()
    else:
        agency_val = raw_agency.strip()

    city_val = guest.get("city", "").strip()

    # Room info
    room_no = str(guest.get("room_no", "401"))
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "PRDX"))
    room_desc = guest.get("description", hotel_cfg.get("default_room_desc", "PREMIUM DELUXE RBF"))

    # Folio No: MSAQ902026
    folio_no = guest.get("folio_no")
    if not folio_no:
        rand_fol = random.randint(902000, 902999)
        folio_no = f"MSAQ{rand_fol}"
    elif not str(folio_no).startswith("MSAQ"):
        folio_no = f"MSAQ{folio_no}"

    # Reff No: NAAQ903258
    reff_no = guest.get("reff_no")
    if not reff_no:
        rand_ref = random.randint(903200, 903299)
        reff_no = f"NAAQ{rand_ref}"

    staff_name = cfg.get("staff_name", "TEGUH")
    checker_name = cfg.get("checker_name", "JAKA")

    rate = guest.get("rate", hotel_cfg.get("default_rate", 455000))
    total_amount = rate * nights
    rate_str = f"{rate:,}"
    total_str = f"{total_amount:,}"

    # 1. Insert Guest & Reservation Info Values
    page.insert_text(pymupdf.Point(90.78, 130.5), f":    {guest_name_val}", fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(90.78, 147.5), f":    {agency_val}", fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))
    addr_txt = f":    {city_val}" if city_val else ":"
    page.insert_text(pymupdf.Point(90.78, 164.5), addr_txt, fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))

    page.insert_text(pymupdf.Point(448.38, 130.5), f":      {room_no} -  ( {room_suffix} )", fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(448.38, 147.5), f":      {arr_str}", fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(448.38, 164.5), f":      {dep_str}", fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))
    page.insert_text(pymupdf.Point(448.38, 181.5), f":      {folio_no}", fontfile=font_path_arial, fontsize=8.3, color=(0, 0, 0))

    # 2. Table Rows
    ROW_DY = 17.0
    table_start_y = 207.5

    # Print info
    print_dt = trip.get("print_dt") or datetime.datetime.now()
    print_time_str = print_dt.strftime("%H:%M")
    print_date_str = f"{print_dt.day:02d}-{EN_MONTHS_SHORT[print_dt.month]}-{str(print_dt.year)[-2:]}"

    if nights == 2:
        # Standard 2 nights: matches original reference layout 100%
        # Row 1 (i=0)
        dt_0 = (checkin_dt).strftime("%d/%m/%Y")
        page.insert_text(pymupdf.Point(30.84, 219.0), "1.", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(48.04, 219.0), dt_0, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(92.04, 219.0), "PCKG", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(128.84, 219.0), reff_no, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(189.67, 219.0), f"RM# {room_no} {room_desc}", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 387.79), 219.0), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(443.72, 219.0), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 504.59), 219.0), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(517.95, 219.0), staff_name, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

        # Row 2 (i=1)
        dt_1 = (checkin_dt + datetime.timedelta(days=1)).strftime("%d/%m/%Y")
        page.insert_text(pymupdf.Point(30.84, 236.0), "2.", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(48.04, 236.0), dt_1, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(92.04, 236.0), "PCKG", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(128.84, 236.0), reff_no, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(189.67, 236.0), f"RM# {room_no} {room_desc}", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 387.79), 236.0), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(443.72, 236.0), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 504.59), 236.0), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(517.95, 236.0), staff_name, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

        # Total numbers
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 387.79), 253.5), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(443.72, 253.5), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 504.59), 253.5), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

        # Print Info values
        page.insert_text(pymupdf.Point(100.90, 273.5), print_time_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(100.83, 284.5), print_date_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

    elif nights == 1:
        # 1 Night: Render Row 1, mask Row 2, move TOTAL line up
        dt_0 = (checkin_dt).strftime("%d/%m/%Y")
        page.insert_text(pymupdf.Point(30.84, 219.0), "1.", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(48.04, 219.0), dt_0, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(92.04, 219.0), "PCKG", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(128.84, 219.0), reff_no, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(189.67, 219.0), f"RM# {room_no} {room_desc}", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 387.79), 219.0), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(443.72, 219.0), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 504.59), 219.0), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(517.95, 219.0), staff_name, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

        # Mask Row 2 and original TOTAL line
        page.draw_rect(pymupdf.Rect(30.0, 225.0, 555.0, 263.0), color=(1, 1, 1), fill=(1, 1, 1))

        # Draw closing line for row 1
        shape1 = page.new_shape()
        shape1.draw_line(pymupdf.Point(30.8, 224.5), pymupdf.Point(552.0, 224.5))
        shape1.finish(color=(0, 0, 0), width=1.44)
        shape1.commit()

        # New TOTAL row
        y_tot1 = 236.5
        page.insert_text(pymupdf.Point(214.44, y_tot1), "TOTAL", fontfile=font_path_arial_bold, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 387.79), y_tot1), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(443.72, y_tot1), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(rate_str, 504.59), y_tot1), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

        shape_tot1 = page.new_shape()
        shape_tot1.draw_line(pymupdf.Point(198.2, y_tot1 + 6.8), pymupdf.Point(504.6, y_tot1 + 6.8))
        shape_tot1.finish(color=(0, 0, 0), width=1.44)
        shape_tot1.commit()

        # Print Info
        page.insert_text(pymupdf.Point(100.90, 273.5), print_time_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(100.83, 284.5), print_date_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

    else:
        # Multi-night (> 2 nights): Expand dynamic rows downwards
        # 1. Bersihkan area dari garis bawah row 2 (y=241.5) sampai footer bawah (y=445.0)
        page.draw_rect(pymupdf.Rect(30.0, 241.5, 565.0, 445.0), color=(1, 1, 1), fill=(1, 1, 1))

        # 2. Render seluruh baris malam inap
        sh_lines = page.new_shape()
        for i in range(nights):
            cur_night_dt = checkin_dt + datetime.timedelta(days=i)
            cur_night_str = cur_night_dt.strftime("%d/%m/%Y")
            y_base = 219.0 + i * ROW_DY

            page.insert_text(pymupdf.Point(30.84, y_base), f"{i+1}.", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(48.04, y_base), cur_night_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(92.04, y_base), "PCKG", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(128.84, y_base), reff_no, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(189.67, y_base), f"RM# {room_no} {room_desc}", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(right_align_x(rate_str, 387.79), y_base), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(443.72, y_base), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(right_align_x(rate_str, 504.59), y_base), rate_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
            page.insert_text(pymupdf.Point(517.95, y_base), staff_name, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

            # Bottom horizontal divider
            line_y = table_start_y + (i + 1) * ROW_DY
            if i < nights - 1:
                sh_lines.draw_line(pymupdf.Point(30.8, line_y), pymupdf.Point(552.0, line_y))
            else:
                sh_lines.draw_line(pymupdf.Point(30.8, line_y), pymupdf.Point(552.0, line_y))

        sh_lines.finish(color=(0, 0, 0), width=1.20)
        sh_lines.commit()

        # 3. Baris TOTAL Dinamis
        y_tot_dyn = table_start_y + nights * ROW_DY + 14.0
        page.insert_text(pymupdf.Point(214.44, y_tot_dyn), "TOTAL", fontfile=font_path_arial_bold, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(total_str, 387.79), y_tot_dyn), total_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(443.72, y_tot_dyn), "0", fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(right_align_x(total_str, 504.59), y_tot_dyn), total_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

        sh_tot = page.new_shape()
        sh_tot.draw_line(pymupdf.Point(198.2, y_tot_dyn + 6.8), pymupdf.Point(504.6, y_tot_dyn + 6.8))
        sh_tot.finish(color=(0, 0, 0), width=1.44)
        sh_tot.commit()

        # 4. Tempelkan Footer Asli yang bergeser secara proporsional ke bawah
        footer_top_y = y_tot_dyn + 8.0
        footer_rect = pymupdf.Rect(30.0, footer_top_y, 30.0 + 530.0, footer_top_y + 166.0)
        if os.path.exists(footer_block_path):
            page.insert_image(footer_rect, filename=footer_block_path)

        # 5. Nilai Waktu dan Tanggal Cetak dinamis pada blok footer
        page.insert_text(pymupdf.Point(100.90, footer_top_y + 11.5), print_time_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))
        page.insert_text(pymupdf.Point(100.83, footer_top_y + 22.5), print_date_str, fontfile=font_path_arial, fontsize=8.0, color=(0, 0, 0))

    # 4. Handle Stempel Cap Basah jika apply_stamp == False
    if not apply_stamp:
        dy_stamp = (nights - 2) * ROW_DY if nights > 2 else 0.0
        page.draw_rect(pymupdf.Rect(420.0, 355.0 + dy_stamp, 535.0, 417.0 + dy_stamp), color=(1, 1, 1), fill=(1, 1, 1))
        sh_cl = page.new_shape()
        sh_cl.draw_line(pymupdf.Point(397.4, 417.4 + dy_stamp), pymupdf.Point(533.8, 417.4 + dy_stamp))
        sh_cl.finish(color=(0, 0, 0), width=1.0)
        sh_cl.commit()
        paraf_file = os.path.join(tmpl_folder, cfg.get("paraf_file", "paraf.png"))
        if os.path.exists(paraf_file):
            page.insert_image(pymupdf.Rect(424.0, 393.0 + dy_stamp, 460.0, 417.0 + dy_stamp), filename=paraf_file)
        page.insert_text(pymupdf.Point(461.0, 414.0 + dy_stamp), checker_name, fontfile=font_path_arial, fontsize=9.0, color=(0, 0, 0))

    return doc

def render_braling_purbalingga_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = True) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Braling Grand Hotel Purbalingga (Azana PMS / Braling Format).
    Mendukung format resmi Braling Grand Hotel:
    - Logo Vektor Murni Braling Grand Hotel di header
    - Rincian reservasi & tamu (~ INDIVIDUAL RSV ~ / Instansi, Nama Tamu, Kota)
    - Metadata kamar, folio FL.2600xxxx / 0, arrival, departure, room night
    - Tabel transaksi dinamis multi-malam (1 malam, 2 malam, dst.) dengan garis pembatas presisi
    - Pergeseran proporsional blok bawah (Total, Balance merah, disclaimers, signature, printed)
    - 6 variasi stempel tanda tangan kasir resmi (sig1.png - sig6.png) dari dokumen master asli
    - Garis footer lengkap dengan alamat & kontak www.bralinggrandhotel.com
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "purbalingga_braling"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]

    font_path_arial = r"C:\Windows\Fonts\arial.ttf"
    try:
        font_obj_arial = pymupdf.Font(fontfile=font_path_arial) if os.path.exists(font_path_arial) else pymupdf.Font("helv")
    except Exception:
        font_obj_arial = pymupdf.Font("helv")

    font_path_const_it = r"C:\Windows\Fonts\constani.ttf"
    font_const_it = font_path_const_it if os.path.exists(font_path_const_it) else font_path_arial

    def right_align_x(text, target_right_x=478.28, fontsize=8.0):
        try:
            w = font_obj_arial.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * 4.6
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    arr_str = f"{checkin_dt.day:02d}-{EN_MONTHS_SHORT[checkin_dt.month]}-{checkin_dt.year}"
    dep_str = f"{checkout_dt.day:02d}-{EN_MONTHS_SHORT[checkout_dt.month]}-{checkout_dt.year}"

    # Print timestamp
    print_dt = guest.get("print_dt") or trip.get("print_dt")
    if not print_dt:
        print_dt = checkout_dt.replace(hour=random.randint(7, 10), minute=random.randint(5, 55), second=random.randint(10, 50))
    printed_user = hotel_cfg.get("printed_user", cfg.get("printed_user", "IVANA"))
    printed_str = f"Printed : {printed_user} on {print_dt.strftime('%d-%m-%Y %H:%M:%S')}"

    # Room & Folio
    room_no = guest.get("room_no", "508")
    room_suffix = guest.get("room_suffix", hotel_cfg.get("room_suffix", "DLXT"))
    room_full = f":   {room_no} - {room_suffix}"

    folio_no = guest.get("folio_no")
    if not folio_no:
        yr_short = str(checkin_dt.year)[-2:]
        rand_fol = random.randint(3000, 3099)
        folio_no = f"FL.{yr_short}00{rand_fol}  /  0"
    if not folio_no.startswith(":"):
        folio_full = f":   {folio_no}"
    else:
        folio_full = folio_no

    rate = guest.get("rate", hotel_cfg.get("default_rate", 600000))
    total_amount = rate * nights
    rate_str = format_rupiah_comma(rate)
    total_str = format_rupiah_comma(total_amount)

    font_color = (3/255, 4/255, 5/255) # #030405
    red_color = (237/255, 33/255, 39/255) # #ED2127
    line_color = (0.135, 0.121, 0.124) # #221F20

    # 1. Left Header: Agency / RSV Header, Name, City (baseline origin persis master)
    raw_agency = guest.get("agency")
    default_agency = hotel_cfg.get("default_agency", "KEMENTERIAN PU")
    if raw_agency and raw_agency.strip() and raw_agency.upper() not in ["INDIVIDUAL", "~ INDIVIDUAL RSV ~"]:
        agency_txt = raw_agency.upper()
    else:
        agency_txt = default_agency.upper() if default_agency != "KEMENTERIAN PU" else "~ INDIVIDUAL RSV ~"

    guest_name_txt = guest.get("name", "").upper()
    city_txt = guest.get("city", hotel_cfg.get("default_city", "PURBALINGGA")).upper()

    page.insert_text(pymupdf.Point(62.06, 101.92), agency_txt, fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(62.06, 112.92), guest_name_txt, fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(62.06, 123.92), city_txt, fontfile=font_path_arial, fontsize=8.0, color=font_color)

    # 2. Right Header Labels & Values (baseline origin persis master)
    page.insert_text(pymupdf.Point(334.19, 101.92), "Room", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(334.19, 113.73), "Folio", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(334.19, 125.54), "Arrival", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(334.19, 137.34), "Departure", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(334.19, 149.15), "Room Night", fontfile=font_path_arial, fontsize=8.0, color=font_color)

    page.insert_text(pymupdf.Point(404.66, 101.93), room_full, fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(404.66, 113.74), folio_full, fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(404.66, 125.54), f":   {arr_str}", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(404.66, 137.35), f":   {dep_str}", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(404.66, 149.16), f":   {nights}", fontfile=font_path_arial, fontsize=8.0, color=font_color)

    # 3. Table Header Lines & Column Names
    shape = page.new_shape()
    shape.draw_line(pymupdf.Point(54.60, 163.01), pymupdf.Point(557.64, 163.01))
    shape.draw_line(pymupdf.Point(54.60, 182.11), pymupdf.Point(557.64, 182.11))
    shape.finish(color=line_color, width=0.5)
    shape.commit()

    page.insert_text(pymupdf.Point(83.14, 180.42), "Date", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(137.66, 180.42), "Room", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(255.88, 180.42), "Description", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(389.83, 180.42), "Qty", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(439.05, 180.42), "Debit", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(508.31, 180.42), "Credit", fontfile=font_path_arial, fontsize=8.0, color=font_color)

    # 4. Transaction Rows (Dinamis bertambah ke bawah per malam, Qty tiap malam selalu 1)
    ROW_DY = 13.93
    for i in range(nights):
        cur_night_dt = checkin_dt + datetime.timedelta(days=i)
        cur_night_str = f"{cur_night_dt.day:02d}-{EN_MONTHS_SHORT[cur_night_dt.month]}-{cur_night_dt.year}"
        row_y = 192.56 + (i * ROW_DY)

        page.insert_text(pymupdf.Point(69.38, row_y), cur_night_str, fontfile=font_path_arial, fontsize=8.0, color=font_color)
        page.insert_text(pymupdf.Point(141.04, row_y), str(room_no), fontfile=font_path_arial, fontsize=8.0, color=font_color)
        page.insert_text(pymupdf.Point(176.66, row_y), hotel_cfg.get("default_room_desc", "ROOM CHARGE"), fontfile=font_path_arial, fontsize=8.0, color=font_color)
        page.insert_text(pymupdf.Point(393.39, row_y), "1", fontfile=font_path_arial, fontsize=8.0, color=font_color)
        page.insert_text(pymupdf.Point(right_align_x(rate_str), row_y), rate_str, fontfile=font_path_arial, fontsize=8.0, color=font_color)

        # Garis pembatas horizontal tiap baris transaksi
        line_y = 196.04 + (i * ROW_DY)
        shape_row = page.new_shape()
        shape_row.draw_line(pymupdf.Point(54.60, line_y), pymupdf.Point(557.64, line_y))
        shape_row.finish(color=line_color, width=0.5)
        shape_row.commit()

    # Pergeseran dinamis untuk seluruh blok bawah
    dy = (nights - 1) * ROW_DY

    # 5. Total & Balance
    total_y = 209.98 + dy
    bal_y = 221.98 + dy
    page.insert_text(pymupdf.Point(389.36, total_y), "Total :", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(right_align_x(total_str), total_y), total_str, fontfile=font_path_arial, fontsize=8.0, color=font_color)

    page.insert_text(pymupdf.Point(377.35, bal_y), "Balance :", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    page.insert_text(pymupdf.Point(right_align_x(total_str), bal_y), total_str, fontfile=font_path_arial, fontsize=8.0, color=red_color)

    # 6. Disclaimers
    page.insert_text(pymupdf.Point(54.60, 240.41 + dy), "Please check that you have not left any valuables in the room personal safe.", fontfile=font_const_it, fontsize=7.5, color=font_color)
    page.insert_text(pymupdf.Point(54.60, 252.41 + dy), "Thank you for choosing to stay with us and we wish you pleasant onward journey.", fontfile=font_const_it, fontsize=7.5, color=font_color)

    # 7. Signature & Garis Tanda Tangan
    page.insert_text(pymupdf.Point(419.47, 271.49 + dy), "Signature", fontfile=font_path_arial, fontsize=8.0, color=font_color)
    shape_sig = page.new_shape()
    shape_sig.draw_line(pymupdf.Point(457.59, 271.49 + dy), pymupdf.Point(553.51, 271.49 + dy))
    shape_sig.finish(color=line_color, width=0.5)
    shape_sig.commit()

    # 8. Stempel Tanda Tangan Kasir Otentik Braling (Variasi PNG Alami)
    if apply_stamp and hotel_cfg.get("has_stamp", True):
        sig_configs = cfg.get("signature_configs", {})
        stamp_candidates = cfg.get("stamp_files", ["stamp1.png", "stamp2.png", "stamp3.png", "stamp4.png", "stamp5.png"])
        # Kombinasikan seluruh variasi PNG yang terdaftar di konfigurasi
        all_variations = list(sig_configs.keys()) if sig_configs else [f.replace(".png", "") for f in stamp_candidates]
        selected_key = random.choice(all_variations)

        sig_path = os.path.join(tmpl_folder, f"{selected_key}.png")
        if not os.path.exists(sig_path):
            sig_path = os.path.join(tmpl_folder, cfg.get("stamp_file", "stamp1.png"))

        if os.path.exists(sig_path):
            raw_rect = sig_configs.get(selected_key, {}).get("rect", [461.96, 193.00, 526.04, 289.00])
            base_sig_rect = [raw_rect[0], raw_rect[1] + dy, raw_rect[2], raw_rect[3] + dy]
            insert_realistic_stamp(
                page,
                sig_path,
                base_sig_rect,
                dx_range=(-0.5, 0.5),
                dy_range=(-0.5, 0.5),
                angle_range=(-0.4, 0.4),
                opacity_range=(0.94, 1.0),
                overlay=True
            )

    # 9. Printed Timestamp
    page.insert_text(pymupdf.Point(55.55, 282.94 + dy), printed_str, fontfile=font_path_arial, fontsize=8.0, color=font_color)

    # 10. Footer Bawah (Jl. Letjen S Parman, Telp, Website, Page 1 of 1)
    shape_foot = page.new_shape()
    shape_foot.draw_line(pymupdf.Point(46.12, 765.56), pymupdf.Point(549.16, 765.56))
    shape_foot.finish(color=line_color, width=0.5)
    shape_foot.commit()

    page.insert_text(pymupdf.Point(132.89, 778.92), "Jl. Letjen S Parman No. 50, Kedung Menjengan, Kec, Purbalingga, Kab. Purbalingga, Jawa Tengah 53315", fontfile=font_path_arial, fontsize=7.0, color=font_color)
    page.insert_text(pymupdf.Point(204.38, 790.92), "Telp : 0281-8901010 | Website : www.bralinggrandhotel.com", fontfile=font_path_arial, fontsize=7.0, color=font_color)
    page.insert_text(pymupdf.Point(525.29, 805.58), "Page 1 of 1", fontfile=font_path_arial, fontsize=7.0, color=font_color)

    return doc

def safe_save_pdf(doc: pymupdf.Document, target_path: str, max_retries: int = 3, retry_delay: float = 0.5) -> str:
    """
    Menyimpan dokumen PDF secara aman ke target_path.
    Menangani locking dari Windows Explorer preview, Google Drive sync, atau PDF viewer.
    """
    last_err = None
    for _ in range(max_retries):
        try:
            if os.path.exists(target_path):
                try:
                    with open(target_path, "r+b"):
                        pass
                except (PermissionError, OSError) as pe:
                    last_err = pe
                    time.sleep(retry_delay)
                    continue

            doc.save(target_path, garbage=4, deflate=True, clean=True)
            return target_path
        except Exception as e:
            last_err = e
            time.sleep(retry_delay)

    fname = os.path.basename(target_path)
    err_str = str(last_err).lower()
    if "permission denied" in err_str or "code=2" in err_str or "sharing violation" in err_str or isinstance(last_err, PermissionError):
        raise PermissionError(
            f"File '{fname}' tidak dapat disimpan karena sedang dibuka atau dikunci oleh program lain "
            f"(seperti Adobe Acrobat Reader, Browser, atau Preview Windows Explorer). "
            f"Silakan tutup file PDF tersebut terlebih dahulu, lalu klik Buat Nota kembali."
        )
    raise last_err

def render_aliyana_temanggung_receipt(guest: dict, trip: dict, hotel_cfg: dict, apply_stamp: bool = False) -> pymupdf.Document:
    """
    Menghasilkan 1 lembar PDF untuk Hotel Aliyana Temanggung.
    Berdasarkan format resmi Aliyana 2026 (vektor murni tajam, tanpa pixelation).
    Mendukung field dinamis nomor bill 8 digit, rincian tamu, durasi menginap (nights),
    tabel transaksi kamar checkout, dan perataan nominal Debet & Balance Due yang presisi.
    """
    tmpl_folder = os.path.join(TEMPLATES_DIR, hotel_cfg.get("template_folder", "temanggung_aliyana"))
    with open(os.path.join(tmpl_folder, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)

    master_pdf_path = os.path.join(tmpl_folder, cfg.get("master_pdf", "master_base.pdf"))
    doc = pymupdf.open(master_pdf_path)
    page = doc[0]
    register_fonts(page, ("arial", "arial_bold", "calibri", "calibri_bold"))

    font_path_arial_bold = r"C:\Windows\Fonts\arialbd.ttf"
    try:
        font_obj_arial_bold = pymupdf.Font(fontfile=font_path_arial_bold) if os.path.exists(font_path_arial_bold) else pymupdf.Font("helv")
    except Exception:
        font_obj_arial_bold = pymupdf.Font("helv")

    def right_align_x(text: str, target_right_x: float = 480.66, fontsize: float = 9.0) -> float:
        try:
            w = font_obj_arial_bold.text_length(text, fontsize=fontsize)
        except Exception:
            w = len(text) * (fontsize * 0.55)
        return target_right_x - w

    checkin_dt = trip["checkin_dt"]
    checkout_dt = trip["checkout_dt"]
    nights = max(1, trip.get("nights", 1))

    # Format tanggal
    arr_str = f"{checkin_dt.month}/{checkin_dt.day}/{checkin_dt.year}"
    dep_str = f"{checkout_dt.month}/{checkout_dt.day}/{checkout_dt.year}"
    table_date_str = f"{checkout_dt.day:02d} {EN_MONTHS_SHORT[checkout_dt.month]} {checkout_dt.year}"

    # Print Date
    print_dt = trip.get("print_dt")
    if not print_dt:
        print_dt = checkout_dt.replace(hour=8, minute=random.randint(15, 25))
    am_pm = "am" if print_dt.hour < 12 else "pm"
    hour_12 = print_dt.hour % 12
    if hour_12 == 0:
        hour_12 = 12
    print_dt_str = f"{print_dt.day:02d} {EN_MONTHS_SHORT[print_dt.month]} {print_dt.year}  {hour_12:02d}:{print_dt.minute:02d} {am_pm}"

    # Room & Type
    room_no = str(guest.get("room_no", "114"))
    room_type = str(guest.get("room_type", hotel_cfg.get("default_room_type", "SDLX"))).strip()

    # Rate & Totals
    rate = guest.get("rate", hotel_cfg.get("default_rate", 550000))
    total_amount = rate * nights
    total_str = format_rupiah_comma(total_amount)

    # Bill No (Folio) - Pojok kiri atas 8 digit
    folio_no = guest.get("folio_no") or guest.get("bill_no")
    if not folio_no:
        rand_bill = random.randint(70000, 89999)
        bill_no_str = f"{rand_bill:08d}"
    else:
        digits = re.sub(r"\D", "", str(folio_no))
        bill_no_str = digits.zfill(8) if digits else f"{random.randint(70000, 89999):08d}"

    # Ref No (Tabel Transaksi) - contoh PC-00089212
    ref_no = guest.get("ref_no")
    if not ref_no:
        rand_ref = random.randint(70000, 95000)
        ref_no = f"PC-{rand_ref:08d}"

    text_color = (3/255, 4/255, 4/255)

    # 1. Nomor Bill kiri atas
    page.insert_text(pymupdf.Point(35.07, 55.95), bill_no_str, fontname="calibri", fontsize=9.0, color=text_color)

    # 2. Guest Info (Kolom Kiri)
    guest_name = guest.get("name", "").strip().upper().replace("\xa0", " ")
    pref = ":   "
    page.insert_text(pymupdf.Point(109.14, 208.51), f"{pref}{guest_name}", fontname="calibri", fontsize=10.0, color=text_color)
    page.insert_text(pymupdf.Point(109.14, 222.51), f"{pref}{arr_str}", fontname="calibri", fontsize=10.0, color=text_color)
    page.insert_text(pymupdf.Point(109.15, 236.51), f"{pref}{dep_str}", fontname="calibri", fontsize=10.0, color=text_color)
    page.insert_text(pymupdf.Point(109.17, 250.51), f"{pref}{room_type}", fontname="calibri", fontsize=10.0, color=text_color)
    page.insert_text(pymupdf.Point(109.17, 264.51), f"{pref}{room_no}", fontname="calibri", fontsize=10.0, color=text_color)
    page.insert_text(pymupdf.Point(109.16, 292.51), f"{pref}{print_dt_str}", fontname="calibri", fontsize=10.0, color=text_color)

    # 3. Guest Info (Kolom Kanan)
    page.insert_text(pymupdf.Point(453.34, 221.83), f":  {nights}", fontname="calibri", fontsize=9.0, color=text_color)

    # 4. Tabel Transaksi
    # Date (D Mon YYYY)
    page.insert_text(pymupdf.Point(35.07, 336.85), table_date_str, fontname="arial_bold", fontsize=9.0, color=text_color)
    # Ref No
    page.insert_text(pymupdf.Point(92.54, 336.85), ref_no, fontname="arial_bold", fontsize=9.0, color=text_color)
    # Description
    page.insert_text(pymupdf.Point(232.77, 336.85), f"Room {room_no}", fontname="arial_bold", fontsize=8.0, color=text_color)
    # Debet (Right-aligned ke target_right_x = 480.66)
    debet_x = right_align_x(total_str, target_right_x=480.66, fontsize=9.0)
    page.insert_text(pymupdf.Point(debet_x, 336.85), total_str, fontname="arial_bold", fontsize=9.0, color=text_color)
    # Credit (0)
    page.insert_text(pymupdf.Point(537.92, 336.85), "0", fontname="arial_bold", fontsize=9.0, color=text_color)

    # 5. Balance Due (Right-aligned ke target_right_x = 512.05)
    bal_x = right_align_x(total_str, target_right_x=512.05, fontsize=10.0)
    page.insert_text(pymupdf.Point(bal_x, 498.22), total_str, fontname="arial_bold", fontsize=10.0, color=text_color)

    return doc

def generate_receipts(hotel_id: str, guests: list, checkin_str: str, checkout_str: str, apply_stamp: bool = True) -> dict:
    """
    Fungsi Utama Generator:
    - hotel_id: e.g. 'karanganyar_facade' atau 'wonogiri_golden'
    - guests: list of dicts [{'name': '...', 'room_no': '...', 'rate': 678000, 'folio_no': '...'}]
    - checkin_str: 'YYYY-MM-DD'
    - checkout_str: 'YYYY-MM-DD'
    """
    # Load hotel info
    with open(os.path.join(DATA_DIR, "hotels.json"), "r", encoding="utf-8") as f:
        hotels = json.load(f)
    
    hotel_cfg = next((h for h in hotels if h["id"] == hotel_id), None)
    if not hotel_cfg:
        raise ValueError(f"Hotel with ID '{hotel_id}' not found.")

    checkin_dt = datetime.datetime.strptime(checkin_str, "%Y-%m-%d")
    checkout_dt = datetime.datetime.strptime(checkout_str, "%Y-%m-%d")
    nights = max(1, (checkout_dt - checkin_dt).days)

    trip_info = {
        "checkin_dt": checkin_dt,
        "checkout_dt": checkout_dt,
        "nights": nights
    }

    # Buat subfolder output untuk trip ini
    hotel_clean_name = hotel_cfg["name"].replace(" ", "_").replace("&", "dan").replace("/", "-")
    trip_folder_name = f"{checkin_str}_{hotel_clean_name}"
    target_dir = os.path.join(OUTPUT_DIR, trip_folder_name)
    indiv_dir = os.path.join(target_dir, "Individu")
    os.makedirs(indiv_dir, exist_ok=True)

    merged_doc = pymupdf.open()
    indiv_files = []

    # Waktu cetak batch berurutan secara logis & realistis (checkout pagi, selisih 0-15 detik antar lembar)
    batch_base_print_dt = checkout_dt.replace(
        hour=random.randint(5, 6),
        minute=random.randint(2, 45),
        second=random.randint(5, 35)
    )
    current_batch_dt = batch_base_print_dt

    try:
        for i, guest in enumerate(guests):
            if i > 0:
                # Selisih cetak realistis antar lembar nota dalam batch yang sama (0 s.d. 15 detik)
                step_seconds = random.choice([0, 2, 4, 6, 8, 11, 14, 18])
                current_batch_dt += datetime.timedelta(seconds=step_seconds)

            guest_trip_info = {
                **trip_info,
                "print_dt": guest.get("print_dt", current_batch_dt)
            }

            single_doc = None
            try:
                # Render single page
                if hotel_cfg.get("format_type") == "golden_bill":
                    single_doc = render_golden_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "golden_invoice_v2":
                    single_doc = render_golden_v2_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "azana_trio":
                    single_doc = render_trio_azana_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "frontone_sragen":
                    single_doc = render_frontone_sragen_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "ardiana_purworejo":
                    single_doc = render_ardiana_purworejo_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "surya_yudha":
                    single_doc = render_surya_yudha_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "magelang_artos":
                    single_doc = render_artos_magelang_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "atrium_cilacap":
                    single_doc = render_atrium_cilacap_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "wisata_niaga_banyumas":
                    single_doc = render_wisata_niaga_banyumas_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "braling_purbalingga":
                    single_doc = render_braling_purbalingga_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                elif hotel_cfg.get("format_type") == "temanggung_aliyana":
                    single_doc = render_aliyana_temanggung_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)
                else: # default azana_pms
                    single_doc = render_facade_receipt(guest, guest_trip_info, hotel_cfg, apply_stamp)

                # Simpan file individu
                clean_guest_name = guest["name"].replace(" ", "_").replace(".", "").replace(",", "")
                indiv_filename = f"{i+1:02d}_{clean_guest_name}_{hotel_id}.pdf"
                indiv_path = os.path.join(indiv_dir, indiv_filename)
                safe_save_pdf(single_doc, indiv_path)
                indiv_files.append(indiv_path)

                # Gabungkan ke master document
                merged_doc.insert_pdf(single_doc)
            finally:
                if single_doc:
                    single_doc.close()

        # Simpan file gabungan multi-page
        merged_filename = f"Nota_{hotel_clean_name}_{checkin_str}_Gabungan.pdf"
        merged_path = os.path.join(target_dir, merged_filename)
        safe_save_pdf(merged_doc, merged_path)
    finally:
        merged_doc.close()

    return {
        "status": "success",
        "hotel_name": hotel_cfg["name"],
        "checkin": checkin_str,
        "checkout": checkout_str,
        "nights": nights,
        "guest_count": len(guests),
        "merged_pdf": merged_path,
        "output_folder": target_dir,
        "individual_pdfs": indiv_files
    }
