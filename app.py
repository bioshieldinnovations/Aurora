"""
AURORA - Servidor Web Principal
Suite de herramientas con interfaz aurora boreal.
"""
import os
import sys
import json
import base64
import threading
import webbrowser
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Agregar módulos al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# ─── RUTAS ESTÁTICAS ─────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


# ─── API: QR ─────────────────────────────────────────────────────────────────

@app.route("/api/qr/generar", methods=["POST"])
def api_qr_generar():
    try:
        from modules.qr_module import generar_qr_base64
        body = request.get_json()
        datos = body.get("datos", "").strip()
        color_fill = body.get("color_fill", "#00FFB2")
        color_back = body.get("color_back", "#0A0E1A")

        if not datos:
            return jsonify({"error": "Debes ingresar texto o URL para el QR."}), 400

        resultado = generar_qr_base64(datos, color_fill, color_back)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── API: CRYPTO ──────────────────────────────────────────────────────────────

@app.route("/api/crypto/encriptar", methods=["POST"])
def api_encriptar():
    try:
        from modules.crypto_module import encriptar_mensaje
        body = request.get_json()
        mensaje = body.get("mensaje", "")
        password = body.get("password", "")

        if not mensaje or not password:
            return jsonify({"error": "Mensaje y contraseña son requeridos."}), 400

        token = encriptar_mensaje(mensaje, password)
        return jsonify({"token": token, "longitud": len(token)})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/crypto/desencriptar", methods=["POST"])
def api_desencriptar():
    try:
        from modules.crypto_module import desencriptar_mensaje
        body = request.get_json()
        token = body.get("token", "")
        password = body.get("password", "")

        if not token or not password:
            return jsonify({"error": "Token y contraseña son requeridos."}), 400

        mensaje = desencriptar_mensaje(token, password)
        return jsonify({"mensaje": mensaje})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── API: DOWNLOADER ─────────────────────────────────────────────────────────

@app.route("/api/downloader/info", methods=["POST"])
def api_video_info():
    try:
        from modules.downloader_module import obtener_info
        body = request.get_json()
        url = body.get("url", "")

        if not url:
            return jsonify({"error": "URL requerida."}), 400

        info = obtener_info(url)
        return jsonify(info)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Estado de descarga compartido entre threads
_estado_descarga = {"progreso": 0, "estado": "idle", "resultado": None, "error": None}
_lock = threading.Lock()


@app.route("/api/downloader/descargar", methods=["POST"])
def api_descargar():
    from modules.downloader_module import descargar

    body = request.get_json()
    url = body.get("url", "")
    modo = body.get("modo", "video")

    if not url:
        return jsonify({"error": "URL requerida."}), 400

    def tarea():
        with _lock:
            _estado_descarga.update({"progreso": 0, "estado": "descargando", 
                                      "resultado": None, "error": None})
        try:
            def progreso_cb(pct):
                with _lock:
                    _estado_descarga["progreso"] = pct

            resultado = descargar(url, modo, progreso_callback=progreso_cb)
            with _lock:
                _estado_descarga.update({"estado": "completado", "resultado": resultado, 
                                          "progreso": 100})
        except Exception as e:
            with _lock:
                _estado_descarga.update({"estado": "error", "error": str(e)})

    t = threading.Thread(target=tarea, daemon=True)
    t.start()
    return jsonify({"mensaje": "Descarga iniciada."})


@app.route("/api/downloader/estado", methods=["GET"])
def api_estado_descarga():
    with _lock:
        return jsonify(_estado_descarga.copy())


# ─── ARRANQUE ────────────────────────────────────────────────────────────────

def abrir_navegador():
    import time
    time.sleep(1.2)
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  ✦  AURORA SUITE  —  Iniciando servidor...")
    print("  ✦  Abriendo en: http://localhost:5000")
    print("=" * 50 + "\n")

    t = threading.Thread(target=abrir_navegador, daemon=True)
    t.start()

    app.run(host="0.0.0.0", port=5000, debug=False)
