# app.py
from flask import Flask, render_template_string, request, send_file
import os
import yt_dlp

app = Flask(__name__)

# Pasta para salvar downloads
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Template HTML simples
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>FluxMusic Downloader</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f0f0f0; }
        .video { display: flex; align-items: center; margin-bottom: 15px; background: #fff; padding: 10px; border-radius: 8px; }
        img { width: 120px; height: 90px; margin-right: 15px; }
        .info { flex: 1; }
        button { padding: 5px 10px; }
    </style>
</head>
<body>
    <h1>FluxMusic Downloader</h1>
    <form method="POST" action="/search">
        <input type="text" name="query" placeholder="Nome da música ou cantor" required>
        <button type="submit">Pesquisar</button>
    </form>
    <hr>
    {% if results %}
        {% for video in results %}
        <div class="video">
            <img src="{{ video.thumbnail }}" alt="thumbnail">
            <div class="info">
                <b>{{ video.title }}</b><br>
                <form method="POST" action="/download">
                    <input type="hidden" name="url" value="{{ video.url }}">
                    <button type="submit">Baixar</button>
                </form>
            </div>
        </div>
        {% endfor %}
    {% elif message %}
        <p>{{ message }}</p>
    {% endif %}
</body>
</html>
"""

# Função de busca
def youtube_search(query):
    results = []
    try:
        ydl_opts = {"quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = data.get("entries", [])
            for item in entries:
                results.append({
                    "title": item.get("title"),
                    "url": item.get("webpage_url"),
                    "thumbnail": item.get("thumbnail")
                })
    except Exception as e:
        print("Erro na busca:", e)
    return results

# Função de download
def download_video(url):
    try:
        ydl_opts = {
            "outtmpl": os.path.join(DOWNLOAD_FOLDER, "%(title)s.%(ext)s"),
            "format": "bestaudio/best",
            "quiet": True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
        return filename
    except Exception as e:
        print("Erro no download:", e)
        return None

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")
    results = youtube_search(query)
    if not results:
        return render_template_string(HTML_TEMPLATE, results=None, message="Nenhum vídeo encontrado.")
    return render_template_string(HTML_TEMPLATE, results=results)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    file_path = download_video(url)
    if not file_path or not os.path.exists(file_path):
        return "Erro ao baixar o vídeo."
    return send_file(file_path, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
