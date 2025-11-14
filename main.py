import os, subprocess, sys, random, yt_dlp
from flask import Flask, request, send_from_directory, render_template_string

# ---------- auto-instala dependências ----------
for pkg in ['flask', 'yt-dlp']:
    try: __import__(pkg)
    except: subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])

# ---------- configurações ----------
app = Flask(__name__)
DOWNLOAD_DIR = 'downloads'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- HTML ----------
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
    <p>Pronto! Clique abaixo para baixar:</p>
    <p><a href="/dl/{{ file }}" download>{{ file }}</a></p>
  </div>
  {% endif %}
</body>
</html>
"""

# ---------- função de download ----------
def baixar(url):
    ua = random.choice([
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Mozilla/5.0 (Linux; Android 10; SM-G973F)'
    ])

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'cookiefile': 'cookies.txt',       # ← cookie exportado do navegador
        'extractaudio': True,
        'audioformat': 'mp3',
        'audioquality': '192K',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'retries': 20,
        'fragment_retries': 20,
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_client': ['web_creator', 'android', 'ios'],
                'player_skip': ['configs'],
            }
        },
        'http_headers': {
            'User-Agent': ua,
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Referer': 'https://www.youtube.com/'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3 = os.path.splitext(filename)[0] + '.mp3'
            return os.path.basename(mp3), None
    except Exception as e:
        return None, str(e)

# ---------- rotas ----------
@app.route('/', methods=['GET', 'POST'])
def index():
    file = msg = None
    tipo = 'erro'
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if url and ('youtube.com' in url or 'youtu.be' in url):
            file, erro = baixar(url)
            if erro:
                msg = erro
            else:
                msg = 'Download concluído!'
                tipo = 'ok'
        else:
            msg = 'Link inválido. Use um do YouTube.'
    return render_template_string(HTML, file=file, msg=msg, tipo=tipo)

@app.route('/dl/<filename>')
def download(filename):
    try:
        return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)
    except FileNotFoundError:
        return 'Arquivo não encontrado.', 404

# ---------- início ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
