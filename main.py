import os
import subprocess
import sys

# Instala pacotes
def instalar():
    for pkg in ['flask', 'yt-dlp']:
        try:
            __import__(pkg)
        except:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
instalar()

from flask import Flask, request, send_from_directory, render_template_string
import yt_dlp

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

HTML = """
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FluxMusic</title>
  <style>
    body{font-family:Arial;background:#f4f4f4;padding:20px;text-align:center}
    input,button{padding:16px;font-size:18px;width:100%;max-width:500px;margin:10px 0;border:none;border-radius:12px}
    input{box-shadow:0 2px 8px #0002}
    button{background:#ff4500;color:white;font-weight:bold;cursor:pointer}
    button:hover{background:#e03a00}
    .msg{margin:20px;padding:15px;border-radius:10px;font-size:17px}
    .ok{background:#d4edda;color:#155724}
    .erro{background:#f8d7da;color:#721c24}
    a{color:#ff4500;font-weight:bold;text-decoration:none}
  </style>
</head>
<body>
  <h1>FluxMusic</h1>
  <p>Cole o link do YouTube e baixe a música!</p>
  <form method=post>
    <input name="url" placeholder="https://youtu.be/..." required autofocus>
    <button>Baixar Música</button>
  </form>

  {% if msg %}
  <div class="msg {{ tipo }}">{{ msg }}</div>
  {% endif %}

  {% if file %}
  <div class="msg ok">
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
        'retries': 5,
        'fragment_retries': 5,
        'sleep_interval': 1,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['web', 'android', 'ios']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.basename(filename), None
    except Exception as e:
        erro = str(e)
        if "Sign in to confirm" in erro or "Private video" in erro or "age-restricted" in erro:
            return None, "Esse vídeo exige login no YouTube. Tente outro link público."
        elif "unavailable" in erro or "deleted" in erro:
            return None, "Vídeo não encontrado ou removido."
        else:
            return None, f"Erro: {erro.split(']')[-1].strip()}"

@app.route("/", methods=["GET", "POST"])
def index():
    file = None
    msg = None
    tipo = "erro"
    
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if url and ("youtube.com" in url or "youtu.be" in url):
            file, erro = baixar(url)
            if erro:
                msg = erro
            else:
                msg = "Download concluído com sucesso!"
                tipo = "ok"
        else:
            msg = "Link inválido. Use um link do YouTube."
    
    return render_template_string(HTML, file=file, msg=msg, tipo=tipo)

@app.route("/dl/<filename>")
def download(filename):
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    except:
        return "Arquivo não encontrado.", 404

# Porta 8080 (Koyeb)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
