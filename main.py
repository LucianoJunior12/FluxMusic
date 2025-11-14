from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Downloader Local</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; padding: 40px; background: #111; color: #fff; }
        input, button { padding: 10px; font-size: 18px; width: 100%; margin-top: 10px; }
        .video-card { margin-top: 20px; background: #222; padding: 20px; border-radius: 10px; }
        img { width: 100%; border-radius: 10px; margin-top: 15px; }
        .btn { background: #4CAF50; color: #fff; border: none; padding: 10px; margin-top: 20px; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Baixar Música (Local)</h1>

    <form method="POST" action="/info">
        <input type="text" name="query" placeholder="Cole o link ou escreva o nome da música" required>
        <button class="btn" type="submit">Buscar</button>
    </form>

    {% if video %}
    <div class="video-card">
        <h2>{{ video['title'] }}</h2>
        <img src="{{ video['thumbnail'] }}">
        <form method="POST" action="/download">
            <input type="hidden" name="id" value="{{ video['id'] }}">
            <button class="btn" type="submit">Baixar MP3</button>
        </form>
    </div>
    {% endif %}
</body>
</html>
"""

def search_youtube(query):
    """Busca no YouTube quando link está bloqueado."""
    ydl_opts = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "skip_download": True,
        "default_search": "ytsearch1",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)

    item = info['entries'][0]
    return item['id'], item['title'], f"https://i.ytimg.com/vi/{item['id']}/hqdefault.jpg"

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML)

@app.route("/info", methods=["POST"])
def info():
    query = request.form["query"].strip()

    try:
        # Tentativa direta pelo link
        ydl = yt_dlp.YoutubeDL({"quiet": True, "skip_download": True})
        data = ydl.extract_info(query, download=False)

        video = {
            "id": data["id"],
            "title": data["title"],
            "thumbnail": data.get("thumbnail", "")
        }

    except Exception as e:
        if "Sign in to confirm you're not a bot" in str(e):
            # Procurar pelo nome automaticamente
            vid, title, thumb = search_youtube(query)
            video = {"id": vid, "title": title, "thumbnail": thumb}
        else:
            return f"<h1>Erro inesperado: {e}</h1>"

    return render_template_string(HTML, video=video)

@app.route("/download", methods=["POST"])
def download():
    vid = request.form["id"]
    out = f"{vid}.mp3"

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": out,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)

    return send_file(out, as_attachment=True)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
