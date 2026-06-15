"""
AURORA - Módulo Descargador
Descarga video/audio desde YouTube, Twitter, Reddit, Vimeo y más vía yt-dlp.
"""
import os
import re
import yt_dlp


CARPETA_DEFAULT = os.path.join(os.path.expanduser("~"), "Aurora_Downloads")


def _sanitize_url(url: str) -> str:
    url = url.strip().strip('"').strip("'")
    if not re.match(r"^https?://", url):
        raise ValueError("La URL debe comenzar con http:// o https://")
    return url


def obtener_info(url: str) -> dict:
    """
    Obtiene metadatos del video sin descargar.
    Útil para mostrar preview al usuario.
    """
    url = _sanitize_url(url)
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    duracion = info.get("duration", 0)
    minutos, segundos = divmod(int(duracion), 60)
    
    return {
        "titulo": info.get("title", "Sin título"),
        "canal": info.get("uploader", "Desconocido"),
        "duracion": f"{minutos}:{segundos:02d}",
        "plataforma": info.get("extractor_key", "Desconocida"),
        "miniatura": info.get("thumbnail", ""),
        "url": url,
    }


def descargar(url: str, modo: str = "video", carpeta: str = CARPETA_DEFAULT, 
              progreso_callback=None) -> dict:
    """
    Descarga un video o solo el audio.
    
    Args:
        url: URL del contenido
        modo: 'video' para video+audio, 'audio' para solo MP3
        carpeta: carpeta de destino
        progreso_callback: función opcional que recibe % de progreso (0-100)
    
    Returns:
        dict con 'ruta', 'titulo', 'tamanio_mb'
    """
    url = _sanitize_url(url)
    os.makedirs(carpeta, exist_ok=True)

    resultado = {}

    def hook_progreso(d):
        if progreso_callback and d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            descargado = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int((descargado / total) * 100)
                progreso_callback(pct)
        elif d["status"] == "finished":
            resultado["ruta_temp"] = d["filename"]

    plantilla = os.path.join(carpeta, "%(title)s.%(ext)s")

    if modo == "audio":
        opts = {
            "format": "bestaudio/best",
            "outtmpl": plantilla,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook_progreso],
            "restrictfilenames": True,
        }
    else:
        opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": plantilla,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [hook_progreso],
            "restrictfilenames": True,
            "merge_output_format": "mp4",
        }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        titulo = info.get("title", "archivo")

    # Buscar el archivo descargado más reciente
    archivos = sorted(
        [os.path.join(carpeta, f) for f in os.listdir(carpeta)],
        key=os.path.getmtime,
        reverse=True,
    )
    ruta_final = archivos[0] if archivos else ""
    tamanio = os.path.getsize(ruta_final) / (1024 * 1024) if ruta_final else 0

    return {
        "titulo": titulo,
        "ruta": ruta_final,
        "tamanio_mb": round(tamanio, 2),
        "modo": modo,
        "carpeta": carpeta,
    }
