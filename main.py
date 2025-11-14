import os
import yt_dlp
from flask import Flask, render_template_string, request, send_file

app = Flask(__name__)

# Criar pasta de downloads
if not os.path.exists("downloads"):
    os.mkdir("downloads")

# ---- TEMPLATE HTML COM INTERFACE BONITA ---- #
HTML = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>FluxMusic Downloader</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background:#111;
            color:white;
            text-align:center;
            padding:40px;
        }
        input {
            width:70%;
            padding:10px;
            font-size:17px;
            border-radius:8px;
            border:none;
            margin-bottom:20px;
        }
        button {
            padding:12px 20px;
            font-size:17px;
            border:none;
            border-radius:8px;
            background:#0a84ff;
            color:white;
            cursor:pointer;
        }
        .video-box {
            margin-top:30px;
            padding:20px;
            background:#222;
            border-radius:10px;
            display:inline-block;
        }
        img {
            width:320px;
            border-radius:10px;
            margin-bottom:10px;
        }
    </style>
</head>
<body>

<h1>FluxMusic Downloader</h1>
<p>Cole o link do YouTube abaixo:</p>

<form method="POST">
    <input name="url" placeholder="https://youtu.be/..." required>
    <br>
    <button type="submit">Buscar</button>
</form>

{% if title %}
<div class="video-box">
    <img src="{{ thumbnail }}">
    <h2>{{ title }}</h2>
    <a href="/download?url={{ url }}">
        <button>Baixar MP3</button>
    </a>
</div>
{% endif %}

</body>
</html>
"""

# ------------------------ LOGICA ------------------------ #

def get_info(url):
    """Pega capa e título SEM baixar."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["title"], info["thumbnail"]


@app.route("/", methods=["GET", "POST"])
def index():
    title = None
    thumbnail = None
    url = None

    if request.method == "POST":
        url = request.form["url"].strip()

        try:
            title, thumbnail = get_info(url)
        except Exception:
            title = "Erro ao carregar vídeo."
            thumbnail = "https://i.imgur.com/HyfXNxw.png"

    return render_template_string(HTML, title=title, thumbnail=thumbnail, url=url)


@app.route("/download")
def download():
    url = request.args.get("url")

    if not url:
        return "URL inválida."

    # Caminho final
    output_path = "downloads/%(title)s.%(ext)s"

    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": output_path,
        "quiet": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
        ]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Erro ao baixar: {e}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
