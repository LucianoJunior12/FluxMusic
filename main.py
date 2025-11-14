from flask import Flask, request, render_template_string, send_file
import yt_dlp
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Buscar e Baixar Música</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial; padding: 40px; background: #111; color: #fff; }
        input, button { padding: 12px; font-size: 18px; width: 100%; margin-top: 10px; border-radius: 8px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); grid-gap: 20px; margin-top: 30px; }
        .card { background: #222; padding: 18px; border-radius: 12px; }
        img { width: 100%; border-radius: 10px; }
        .btn { background: #4CAF50; color: #fff; border: none; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>Buscar Música</h1>
    <form method="POST" action="/search">
        <input type="text" name="query" placeholder="Digite nome da música ou artista..." required>
        <button class="btn" type="submit">Pesquisar</button>
    </form>

    {% if results %}
    <h2>Resultados:</h2>
    <div class="grid">
        {% for item in results %}
        <div class="card">
            <img src="{{ item.thumbnail }}">
            <h3>{{ item.title }}</h3>
            <form method="POST" action="/download">
                <input type="hidden" name="id" value="{{ item.id }}">
                <input type="hidden" name="title" value="{{ item.title }}">
                <button class="btn" type="submit">Baixar MP3</button>
            </form>
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>
"""

def youtube_search(q):
    """Retorna lista de vídeos do YouTube para uma pesquisa."""
    opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": "ytsearch10",  # pega até 10 resultados
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        data = ydl.extract_info(q, download=False)

    results = []
    for item in data["entries"]:
        results.append(type("Video", (), {
            "id": item["id"],
            "title": item["title"],
            "thumbnail": f"https://i.ytimg.com/vi/{item['id']}/hqdefault.jpg"
        }))

    return results

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/search", methods=["POST"])
def search():
    query = request.form["query"]
    results = youtube_search(query)
    return render_template_string(HTML, results=results)

@app.route("/download", methods=["POST"])
def download():
    vid = request.form["id"]
    title = request.form["title"].replace("/", "-").replace("\\", "-")
    filename = f"{title}.mp3"

    opts = {
        "format": "bestaudio/best",
        "outtmpl": filename,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)

    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
