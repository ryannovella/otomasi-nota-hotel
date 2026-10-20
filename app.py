"""
Backend Application & PyWebView Runner for Otomasi Nota Hotel
Author: BPPW Jateng / Antigravity
"""

import os
import sys
import json
import socket
import threading
import subprocess
import webbrowser
from bottle import Bottle, request, response, static_file, run

import generator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Bottle()

def get_app_port(preferred=54321):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('127.0.0.1', preferred))
        s.close()
        return preferred
    except OSError:
        s.bind(('', 0))
        port = s.getsockname()[1]
        s.close()
        return port

# --- Static Files & Index ---
@app.route('/')
def index():
    return static_file('index.html', root=STATIC_DIR)

@app.route('/static/<filepath:path>')
def server_static(filepath):
    return static_file(filepath, root=STATIC_DIR)

# --- APIs ---
@app.route('/api/hotels', method='GET')
def get_hotels():
    response.content_type = 'application/json'
    with open(os.path.join(DATA_DIR, "hotels.json"), "r", encoding="utf-8") as f:
        return f.read()

@app.route('/api/employees', method='GET')
def get_employees():
    response.content_type = 'application/json'
    with open(os.path.join(DATA_DIR, "employees.json"), "r", encoding="utf-8") as f:
        return f.read()

@app.route('/api/employees', method='POST')
def save_employees():
    response.content_type = 'application/json'
    try:
        data = request.json
        with open(os.path.join(DATA_DIR, "employees.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return json.dumps({"status": "success", "message": "Data pegawai berhasil diperbarui."})
    except Exception as e:
        response.status = 500
        return json.dumps({"status": "error", "message": str(e)})

@app.route('/api/generate', method='POST')
def handle_generate():
    response.content_type = 'application/json'
    try:
        payload = request.json
        hotel_id = payload.get("hotel_id")
        guests = payload.get("guests", [])
        checkin = payload.get("checkin")
        checkout = payload.get("checkout")
        apply_stamp = payload.get("apply_stamp", True)

        if not hotel_id or not guests or not checkin or not checkout:
            response.status = 400
            return json.dumps({"status": "error", "message": "Parameter tidak lengkap."})

        result = generator.generate_receipts(
            hotel_id=hotel_id,
            guests=guests,
            checkin_str=checkin,
            checkout_str=checkout,
            apply_stamp=apply_stamp
        )
        return json.dumps(result)
    except PermissionError as pe:
        response.status = 409
        return json.dumps({"status": "error", "message": str(pe)})
    except Exception as e:
        response.status = 500
        return json.dumps({"status": "error", "message": str(e)})

@app.route('/api/open_file', method='POST')
def open_file():
    response.content_type = 'application/json'
    try:
        payload = request.json
        file_path = payload.get("path")
        if file_path and os.path.exists(file_path):
            os.startfile(file_path)
            return json.dumps({"status": "success"})
        else:
            response.status = 404
            return json.dumps({"status": "error", "message": "File tidak ditemukan."})
    except Exception as e:
        response.status = 500
        return json.dumps({"status": "error", "message": str(e)})

@app.route('/api/open_folder', method='POST')
def open_folder():
    response.content_type = 'application/json'
    try:
        payload = request.json
        folder_path = payload.get("path")
        if folder_path and os.path.exists(folder_path):
            subprocess.Popen(f'explorer "{folder_path}"')
            return json.dumps({"status": "success"})
        else:
            response.status = 404
            return json.dumps({"status": "error", "message": "Folder tidak ditemukan."})
    except Exception as e:
        response.status = 500
        return json.dumps({"status": "error", "message": str(e)})

@app.route('/api/view_pdf', method='GET')
def view_pdf():
    file_path = request.query.get('path')
    if file_path and os.path.exists(file_path):
        return static_file(os.path.basename(file_path), root=os.path.dirname(file_path), mimetype='application/pdf')
    response.status = 404
    return "PDF tidak ditemukan"

@app.route('/api/history', method='GET')
def get_history():
    response.content_type = 'application/json'
    history = []
    if os.path.exists(OUTPUT_DIR):
        for entry in os.scandir(OUTPUT_DIR):
            if entry.is_dir():
                pdf_files = [f.path for f in os.scandir(entry.path) if f.name.endswith(".pdf") and "Gabungan" in f.name]
                if pdf_files:
                    merged = pdf_files[0]
                    stat = os.stat(merged)
                    history.append({
                        "folder_name": entry.name,
                        "folder_path": entry.path,
                        "merged_pdf": merged,
                        "created_time": stat.st_mtime
                    })
    history.sort(key=lambda x: x["created_time"], reverse=True)
    return json.dumps(history)

def start_server(port):
    run(app, host='127.0.0.1', port=port, quiet=True)

if __name__ == '__main__':
    port = get_app_port()
    t = threading.Thread(target=start_server, args=(port,), daemon=True)
    t.start()

    url = f"http://127.0.0.1:{port}"
    print(f"Otomasi Nota Hotel berjalan di: {url}")

    if "--browser" in sys.argv:
        webbrowser.open(url)
        t.join()
    else:
        try:
            import webview
            window = webview.create_window(
                title="Otomasi Nota Hotel - BPPW Jateng",
                url=url,
                width=1280,
                height=850,
                min_size=(1024, 700),
                text_select=True
            )
            webview.start()
        except Exception as e:
            print("Gagal membuka native window, fallback ke browser...", e)
            webbrowser.open(url)
            t.join()
