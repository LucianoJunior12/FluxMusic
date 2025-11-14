import os
import tempfile
import shutil
import uuid
import glob
import threading
from flask import Flask, request, render_template_string, send_file, flash, redirect, url_for

# --- App
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "flux-secret-key")

# porta dinâmica (PaaS fornece PORT)
PORT = int(os.environ.get("PORT", 8080))

# -------- HTML (interface limpa e moderna)
HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Flux Music</title>
<style>
:root{--bg:#0f1115;--card:#101217;--accent:#1DB954;--muted:#9aa3b2}
body{margin:0;font-family:Inter,Segoe UI,Arial;background:linear-gradient(180deg,#0b0c0f 0%,#111217 100%);color:#fff;display:flex;align-items:center;justify-content:center;height:100vh}
.container{width:96%;max-width:820px;padding:28px;background:linear-gradient(180deg,rgba(255,255,255,0.02),rgba(255,255,255,0.01));border-radius:16px;box-shadow:0 10px 40px rgba(2,6,23,.6)}
.header{display:flex;align-items:center;gap:16px}
.logo{width:56px;height:56px;border-radius:12px;background:linear-gradient(135deg,#00e0a3,#00d6ff);display:flex;align-items:center;justify-content:center;font-weight:bold;color:#000}
h1{margin:0;font-size:22px}
form{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap}
.input{flex:1;min-width:220px}
input[type="text"]{width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,0.06);background:rgba(255,255,255,0.02);color:#fff;font-size:15px}
button{background:var(--accent);border:none;padding:12px 18px;border-radius:10px;color:#001;font-weight:700;cursor:pointer}
.note{margin-top:12px;color:var(--muted);font-size:13px}
.result{margin-top:18px;padding:14px;border-radius:10px;background:rgba(255,255,255,0.02);display:flex;align-items:center;justify-content:space-between;gap:12px}
a.link{color:#001;background:linear-gradient(90deg,#fff,#fff);padding:8px 12px;border-radius:8px;text-decoration:none;font-weight:700}
.error{color:#ff7b7b;margin-top:12px}
.footer{margin-top:18px;color:var(--muted);font-size:13px;text-align:center}
@media(max-width:540px){.header{flex-direction:column;align-items:flex-start}.logo{width:48px;height:48px}}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">FM</div>
    <div>
      <h1>Flux Music</h1>
      <div class="note">Cole o link do YouTube (qualquer formato) e baixe o MP3.</div>
    </div>
  </div>

  <form method="post">
    <div class="input"><input type="text" name="url" placeholder="https://youtu.be/xxxxx  ou  https://www.youtube.com/watch?v=xxxxx" required></div>
    <div><button type="submit">Baixar MP3</button></div>
  </form>

  {% if error %}
    <div class="error">{{ error }}</div>
  {% endif %}

  {% if file_url %}
    <div class="result">
      <div>Pronto: <strong>{{ title }}</strong></div>
      <a class="link" href="{{ file_url }}" download>Baixar agora</a>
    </div>
  {% endif %}

  <div class="footer">Observação: alguns vídeos restritos podem não ser baixáveis. Se houver erro, tente outro link.</div>
</div>
</body>
</html>
"""

# -------- Utility: apagar temp dir depois de X segundos
def schedule_remove(path, delay=60):
    def _rm():
        try:
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass
    t = threading.Timer(delay, _rm)
    t.daemon = True
    t.start()

# -------- Route principal
@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    file_url = None
    title = None

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            error = "Cole um link válido."
            return render_template_string(HTML, error=error)

        # cria pasta temporária única por job
        tmpdir = os.path.join(tempfile.gettempdir(), "flux_"+uuid.uuid4().hex)
        os.makedirs(tmpdir, exist_ok=True)

        # opções do yt-dlp
        # tenta extrair áudio e converter para mp3 (requer ffmpeg no sistema)
        ytdl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        # import dinamicamente (evita crash se library ausente)
        try:
            from yt_dlp import YoutubeDL
        except Exception as e:
            error = "Dependência faltando: yt-dlp. Verifique requirements.txt."
            schedule_remove(tmpdir, 5)
            return render_template_string(HTML, error=error)

        try:
            with YoutubeDL(ytdl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # info pode ser dict ou raise erro
        except Exception as e:
            # tenta fallback simples: talvez conversão falhou por falta de ffmpeg.
            # tenta baixar sem postprocessor (apenas áudio no formato original)
            try:
                ytdl_opts_fallback = dict(ytdl_opts)
                ytdl_opts_fallback.pop("postprocessors", None)
                with YoutubeDL(ytdl_opts_fallback) as ydl:
                    info = ydl.extract_info(url, download=True)
            except Exception as e2:
                error = f"Erro ao baixar/converter: {e2}"
                schedule_remove(tmpdir, 5)
                return render_template_string(HTML, error=error)

        # localizar arquivo gerado (pega primeiro arquivo dentro do tmpdir)
        files = glob.glob(os.path.join(tmpdir, "*"))
        if not files:
            error = "Não foi possível encontrar o arquivo baixado."
            schedule_remove(tmpdir, 5)
            return render_template_string(HTML, error=error)

        # preferir .mp3 se existir
        mp3s = [f for f in files if f.lower().endswith(".mp3")]
        if mp3s:
            out_path = mp3s[0]
            out_ext = ".mp3"
        else:
            # pega o primeiro arquivo disponível e usa sua extensão
            out_path = files[0]
            out_ext = os.path.splitext(out_path)[1]

        # nome amigável para download
        # tenta extrair title de info
        try:
            title = info.get("title") or os.path.basename(out_path)
            safe_name = "".join(c for c in title if c.isalnum() or c in " _-()[]{}.,").strip()
            download_name = safe_name + out_ext
        except Exception:
            download_name = os.path.basename(out_path)

        # cria rota de download temporária (link direto para o arquivo)
        # para servir via send_file usamos URL relativo ao servidor: /tmpfile/<uuid>
        token = uuid.uuid4().hex
        token_path = os.path.join(tempfile.gettempdir(), "flux_tokens")
        os.makedirs(token_path, exist_ok=True)
        token_file = os.path.join(token_path, token)
        # armazena mapeamento simples: token -> real path
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(out_path + "||" + download_name)
        file_url = url_for("download_token", token=token, _external=True)

        # agendar remoção do tmpdir e token em 3 minutos
        schedule_remove(tmpdir, delay=180)
        def remove_token(path=token_file):
            try:
                os.remove(path)
            except Exception:
                pass
        threading.Timer(180, remove_token).start()

    return render_template_string(HTML, error=error, file_url=file_url, title=title)

# rota para download via token
@app.route("/d/<token>")
def download_token(token):
    token_path = os.path.join(tempfile.gettempdir(), "flux_tokens")
    token_file = os.path.join(token_path, token)
    if not os.path.isfile(token_file):
        return "Link expirado ou inválido.", 404
    try:
        content = open(token_file, "r", encoding="utf-8").read()
        out_path, download_name = content.split("||", 1)
        if not os.path.isfile(out_path):
            return "Arquivo não encontrado.", 404
        return send_file(out_path, as_attachment=True, download_name=download_name)
    except Exception as e:
        return f"Erro no download: {e}", 500

# start
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
