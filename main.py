import os
import subprocess
import sys
import random

# Instala pacotes
def instalar():
    for pkg in ['flask', 'yt-dlp']:
        try: __import__(pkg)
        except: subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
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
    .msg{margin:20px;padding:15px;border-radius:10px;font-size:17px;line-height:1.5}
    .ok{background:#d4edda;color:#155724}
    .erro{background:#f8d7da;color:#721c24}
    a{color:#ff4500;font-weight:bold;text-decoration:none}
    .sugestao{color:#666;font-size:15px}
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
    <p>Download concluído!</p>
    <p><a href="/dl/{{ file }}" download>{{ file }}</a></p>
  </div>
  {% endif %}

  {% if sugestao %}
  <div class="sugestao">Dica: Tente este link alternativo: <a href="{{ sugestao }}" target="_blank">{{ sugestao }}</a></div>
  {% endif %}
</body>
</html>
"""

def baixar(url):
    # User-Agents rotativos pra simular humanos
    user_agents = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36'
    ]
    ua = random.choice(user_agents)
    
    ydl_opts = {
        'format': 'bestaudio/best[height<=480]/bestaudio',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 15,
        'fragment_retries': 15,
        'sleep_interval': random.uniform(1, 3),
        'max_sleep_interval': 10,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['web', 'android', 'ios', 'web_safari', 'mweb', 'android_webview'],
                'player_skip': ['configs', 'js'],
                'skip': ['webpage_archives']
            }
        },
        'http_headers': {
            'User-Agent': ua,
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Referer': 'https://www.youtube.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        },
        'sleep_subtitles': 1
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return os.path.basename(filename), None, None
    except Exception as e:
        erro = str(e).lower()
        if "sign in" in erro or "not a bot" in erro:
            # Sugestão automática: link com "audio" no título
            video_id = url.split('v=')[1].split('&')[0] if 'v=' in url else url.split('/')[-1]
            sugestao = f"https://www.youtube.com/results?search_query={video_id.replace('OqcHxX7DqKs', 'pablo+quem+ama+nao+machuca+audio')}"
            return None, "Bloqueado pelo YouTube (anti-bot). Tente outro link ou versão 'audio only'.", sugestao
        elif "private" in erro or "unavailable" in erro:
            return None, "Vídeo privado ou removido.", None
        else:
            return None, f"Erro: {str(e).split('ERROR:')[-1].strip() if 'ERROR:' in str(e) else str(e)}", None

@app.route("/", methods=["GET", "POST"])
def index():
    file = None
    msg = None
    tipo = "erro"
    sugestao = None
    
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if url and ("youtube.com" in url or "youtu.be" in url):
            file, erro, sug = baixar(url)
            if erro:
                msg = erro
                sugestao = sug
            else:
                msg = "Download concluído com sucesso!"
                tipo = "ok"
        else:
            msg = "Link inválido. Use um do YouTube."
    
    return render_template_string(HTML, file=file, msg=msg, tipo=tipo, sugestao=sugestao)

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
