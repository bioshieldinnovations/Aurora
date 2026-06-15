"""
AURORA - Downloader Module
Downloads video/audio from YouTube, Twitter, Reddit, Vimeo and more via yt-dlp.
"""
import os
import re
import yt_dlp


DEFAULT_FOLDER = os.path.join(os.path.expanduser("~"), "Aurora_Downloads")


def _sanitize_url(url: str) -> str:
    url = url.strip().strip('"').strip("'")
    if not re.match(r"^https?://", url):
        raise ValueError("The URL must start with http:// or https://")
    return url


def get_info(url: str) -> dict:
    """
    Gets video metadata without downloading.
    Useful for showing a preview to the user.
    """
    url = _sanitize_url(url)
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    
    duration = info.get("duration", 0)
    minutes, seconds = divmod(int(duration), 60)
    
    return {
        "title": info.get("title", "No title"),
        "channel": info.get("uploader", "Unknown"),
        "duration": f"{minutes}:{seconds:02d}",
        "platform": info.get("extractor_key", "Unknown"),
        "thumbnail": info.get("thumbnail", ""),
        "url": url,
    }


def download(url: str, mode: str = "video", folder: str = DEFAULT_FOLDER, 
             progress_callback=None) -> dict:
    """
    Downloads a video or just the audio.
    
    Args:
        url: Content URL
        mode: 'video' for video+audio, 'audio' for MP3 only
        folder: destination folder
        progress_callback: optional function that receives % progress (0-100)
    
    Returns:
        dict with 'path', 'title', 'size_mb'
    """
    url = _sanitize_url(url)
    os.makedirs(folder, exist_ok=True)

    result = {}

    def progress_hook(d):
        if progress_callback and d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                pct = int((downloaded / total) * 100)
                progress_callback(pct)
        elif d["status"] == "finished":
            result["temp_path"] = d["filename"]

    template = os.path.join(folder, "%(title)s.%(ext)s")

    if mode == "audio":
        opts = {
            "format": "bestaudio/best",
            "outtmpl": template,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "restrictfilenames": True,
        }
    else:
        opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "restrictfilenames": True,
            "merge_output_format": "mp4",
        }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title", "file")

    # Find the most recent downloaded file
    files = sorted(
        [os.path.join(folder, f) for f in os.listdir(folder)],
        key=os.path.getmtime,
        reverse=True,
    )
    final_path = files[0] if files else ""
    size = os.path.getsize(final_path) / (1024 * 1024) if final_path else 0

    return {
        "title": title,
        "path": final_path,
        "size_mb": round(size, 2),
        "mode": mode,
        "folder": folder,
    }
