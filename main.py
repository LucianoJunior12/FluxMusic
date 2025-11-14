import os
import subprocess
import sys

# Instala Flask e yt-dlp se não existirem
def instalar():
    try:
        import flask
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    try:
        import yt_dlp
    except:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])

instalar()

from flask import Flask, request, send_from_directory, render_template_string
import yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# HTML responsivo e bonito no celular
HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FluxMusic</title>
  <style>
    body{font-family:Arial;background:#f0f0f0;padding:20px;text-align:center}
    input, button{padding:15px;font-size:18px;width:100%;max-width:500px;margin:10px 0;border:none;border-radius:10px}
    input{box-shadow:0 2px 5px #0002}
    button{background:#ff4500;color:white;cursor:pointer;font-weight:bold}
    button:hover{background:#cc3700}
    a{color:#ff4500;font-weight:bold;text-decoration:none}
    .msg{margin:20px;color:green;font-size:18px}
  </style>
</head>
<body>
  <h1>FluxMusic</h1>
  <p>Cole o link do YouTube e baixe a música!</p>
  <form method=post>
    <input name="url" placeholder="https://youtu.be/..." required>
    <button>Baixar Música</button>
  </form>
  {% if file %}
  <div class="msg">
    <p>Pronto! Clique para baixar:</p>
    <p><a href="/dl/{{ file }}" download>{{ file }}</a></p>
  </div>
  {% endif %}
</body>
</html>
"""

def baixar(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 3,
        'fragment_retries': 3,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['web', 'android']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.basename(filename)
    except Exception as e:
        print(f"[ERRO] {e}")
        return None

@app.route("/", methods=["GET", "POST"])
def index():
    file = None
    if request.method == "POST":
        url = request.form.get("url")
        if url and ("youtube.com" in url or "youtu.be" in url):
            file = baixar(url)
    return render_template_string(HTML, file=file)

@app.route("/dl/<filename>")
def download(filename):
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    except:
        return "Arquivo não encontrado.", 404

# Porta 8080 (OBRIGATÓRIA NO KOYEB)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Koyeb usa 8080
    app.run(host="0.0.0.0", port=port)
