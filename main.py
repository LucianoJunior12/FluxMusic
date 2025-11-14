import os
import subprocess
import sys

# ---------------------------
# Instala pacotes se faltar
# ---------------------------
def instalar_pacotes():
    try:
        import flask
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])
    try:
        import yt_dlp
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])

instalar_pacotes()

# ---------------------------
# Imports reais
# ---------------------------
from flask import Flask, render_template_string, request, send_from_directory
import yt_dlp

# ---------------------------
# Configurações
# ---------------------------
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)  # cria pasta se não existir

app = Flask(__name__)

HTML = """
<!doctype html>
<title>FluxMusic Downloader</title>
<h2>Baixe seu vídeo do YouTube</h2>
<form method=post>
  <input type=text name=link placeholder="Cole o link aqui" style="width:300px">
  <input type=submit value="Baixar">
</form>
{% if filename %}
<p>Download pronto: <a href="/downloads/{{ filename }}">{{ filename }}</a></p>
{% endif %}
"""

# ---------------------------
# Função para baixar vídeo
# ---------------------------
def baixar_video(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(link, download=True)
        filename = ydl.prepare_filename(info)
        return os.path.basename(filename)

# ---------------------------
# Rotas Flask
# ---------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    filename = None
    if request.method == "POST":
        link = request.form.get("link")
        if link:
            filename = baixar_video(link)
    return render_template_string(HTML, filename=filename)

@app.route("/downloads/<path:filename>")
def download_file(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename, as_attachment=True)

# ---------------------------
# Rodar app
# ---------------------------
if __name__ == "__main__":
    print("Acesse: http://127.0.0.1:5000")
    app.run(debug=True)
