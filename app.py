"""
AURORA - Main Web Server
Tool suite with aurora borealis interface.
"""
import os
import sys
import json
import base64
import threading
import webbrowser
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# ─── STATIC ROUTES ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


# ─── API: QR ─────────────────────────────────────────────────────────────────

@app.route("/api/qr/generate", methods=["POST"])
def api_qr_generate():
    try:
        from modules.qr_module import generate_qr_base64
        body = request.get_json()
        data = body.get("data", "").strip()
        color_fill = body.get("color_fill", "#00FFB2")
        color_back = body.get("color_back", "#0A0E1A")

        if not data:
            return jsonify({"error": "You must enter text or URL for the QR."}), 400

        result = generate_qr_base64(data, color_fill, color_back)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── API: CRYPTO ──────────────────────────────────────────────────────────────

@app.route("/api/crypto/encrypt", methods=["POST"])
def api_encrypt():
    try:
        from modules.crypto_module import encrypt_message
        body = request.get_json()
        message = body.get("message", "")
        password = body.get("password", "")

        if not message or not password:
            return jsonify({"error": "Message and password are required."}), 400

        token = encrypt_message(message, password)
        return jsonify({"token": token, "length": len(token)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/crypto/decrypt", methods=["POST"])
def api_decrypt():
    try:
        from modules.crypto_module import decrypt_message
        body = request.get_json()
        token = body.get("token", "")
        password = body.get("password", "")

        if not token or not password:
            return jsonify({"error": "Token and password are required."}), 400

        message = decrypt_message(token, password)
        return jsonify({"message": message})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── API: DOWNLOADER ─────────────────────────────────────────────────────────

@app.route("/api/downloader/info", methods=["POST"])
def api_video_info():
    try:
        from modules.downloader_module import get_info
        body = request.get_json()
        url = body.get("url", "")

        if not url:
            return jsonify({"error": "URL required."}), 400

        info = get_info(url)
        return jsonify(info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Shared download status between threads
_download_status = {"progress": 0, "status": "idle", "result": None, "error": None}
_lock = threading.Lock()


@app.route("/api/downloader/download", methods=["POST"])
def api_download():
    from modules.downloader_module import download

    body = request.get_json()
    url = body.get("url", "")
    mode = body.get("mode", "video")

    if not url:
        return jsonify({"error": "URL required."}), 400

    def task():
        with _lock:
            _download_status.update({"progress": 0, "status": "downloading", 
                                      "result": None, "error": None})
        try:
            def progress_cb(pct):
                with _lock:
                    _download_status["progress"] = pct

            result = download(url, mode, progress_callback=progress_cb)
            with _lock:
                _download_status.update({"status": "completed", "result": result, 
                                          "progress": 100})
        except Exception as e:
            with _lock:
                _download_status.update({"status": "error", "error": str(e)})

    t = threading.Thread(target=task, daemon=True)
    t.start()
    return jsonify({"message": "Download started."})


@app.route("/api/downloader/status", methods=["GET"])
def api_download_status():
    with _lock:
        return jsonify(_download_status.copy())


# ─── STARTUP ────────────────────────────────────────────────────────────────

def open_browser():
    import time
    time.sleep(1.2)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  ✦  AURORA SUITE  —  Starting server...")
    print("  ✦  Opening at: http://localhost:5000")
    print("=" * 50 + "\n")

    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5000, debug=False)
