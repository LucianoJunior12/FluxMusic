import os
import sys
import subprocess
from flask import Flask, render_template_string, request, send_file
from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO

# Instala dependências se faltarem
try:
    import yt_dlp
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    import yt_dlp

try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
    from PIL import Image

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>FluxMusic Downloader</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-5">
  <h1 class="mb-4">FluxMusic Downloader</h1>
  <form method="POST">
    <input type="text" name="url" class="form-control mb-3" placeholder="Cole o link do YouTube" required>
    <button type="submit" class="btn btn-primary">Processar</button>
  </form>
  {% if video %}
  <div class="card mt-4" style="width: 18rem;">
    <img src="{{ video['thumbnail'] }}" class="card-img-top" alt="Thumbnail">
    <div class="card-body">
      <h5 class="card-title">{{ video['title'] }}</h5>
      <a href="/download/{{ video['filename'] }}" class="btn btn-success">Baixar</a>
    </div>
  </div>
  {% endif %}
</div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    video = None
    if request.method == "POST":
        url = request.form.get("url")
        try:
            info = download_video_info(url)
            video = info
        except Exception as e:
            print("Erro:", e)
    return render_template_string(HTML_PAGE, video=video)

def download_video_info(url):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception:
        # Tenta apenas áudio se tiver bloqueio
        ydl_opts["format"] = "bestaudio"
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

    filename = ydl.prepare_filename(info)
    # Reduz para apenas audio se bloqueado
    if not os.path.exists(filename):
        filename = filename.rsplit(".", 1)[0] + ".webm"

    return {
        "title": info.get("title", "Sem título"),
        "thumbnail": info.get("thumbnail", ""),
        "filename": os.path.basename(filename)
    }

@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "Arquivo não encontrado!", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
