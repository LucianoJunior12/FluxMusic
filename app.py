#!/usr/bin/env python3
from flask import Flask, request, send_file, render_template_string, jsonify, after_this_request
import yt_dlp
import os
import uuid
import time
import logging
import random
import subprocess

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FluxMusic")

app = Flask("FluxMusic")
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# === SEU PROXY FUNCIONAL (FIXO + ROTATIVO) ===
PROXIES = [
    "http://104.167.25.186:3129",  # O SEU QUE FUNCIONA
    # Adicione mais se quiser rotacionar (opcional)
]

# === USER AGENTS REAIS ===
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
]

# === BYPASS DO YOUTUBE (ANDROID CLIENT) ===
BYPASS_CONFIG = {
    'youtube': {
        'player_client': ['android'],
        'skip': ['hls', 'dash', 'configs'],
        'player_skip': ['webpage', 'js']
    }
}

# === ATUALIZA yt-dlp NO STARTUP ===
def update_yt_dlp():
    try:
        subprocess.check_call(['pip', 'install', '--upgrade', 'yt-dlp'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("yt-dlp atualizado com sucesso!")
    except:
        log.warning("Falha ao atualizar yt-dlp")

update_yt_dlp()

# === HTML (igual ao seu) ===
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Flux Music</title>
<style>
body { background: #0f0f0f; color: #fff; font-family: Arial, sans-serif; margin:0; padding:0;}
header { padding: 20px; text-align: center; font-size: 28px; font-weight: bold; color: #00eaff; letter-spacing: 1px; }
.container { padding: 20px; max-width: 720px; margin: auto; }
.row { display:flex; gap:12px; }
input { flex:1; padding: 12px; margin-top: 10px; border-radius: 8px; border: none; background: #1d1d1d; color: #fff; font-size: 16px; }
button { padding: 12px 16px; margin-top: 10px; border: none; border-radius: 8px; background: #00eaff; color: #000; font-size: 16px; font-weight: bold; cursor: pointer;}
.card { margin-top: 20px; background: #1b1b1b; border-radius: 12px; padding: 12px; text-align: left; display:flex; gap:12px; align-items:center; }
.card img { width: 120px; height: 68px; object-fit: cover; border-radius:8px; }
.title { font-size: 16px; font-weight: bold; color: #fff; }
.small { color:#ccc; font-size:13px; }
.center { text-align:center; }
@media (max-width:720px){ .row{flex-direction:column;} .card{flex-direction:column; align-items:flex-start;} .card img{width:100%; height:auto;} }
</style>
</head>
<body>
<header>Flux Music</header>
<div class="container">
    <div class="row">
        <input id="url" placeholder="Cole o link do YouTube (vídeo ou playlist)">
        <button onclick="buscar()">Buscar</button>
    </div>
    <div id="videos"></div>
</div>
<script>
async function buscar(){
    let url = document.getElementById("url").value.trim();
    if(!url) return alert("Cole um link!");
    const res = await fetch("/info?url=" + encodeURIComponent(url));
    const data = await res.json();
    if(data.error) return alert(data.error);
    let html = "";
    data.forEach(v=>{
        let thumb = v.thumbnail || "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";
        html += `<div class="card">
            <img src="${thumb}" alt="thumb">
            <div style="flex:1">
                <div class="title">${v.title}</div>
                <div class="small">${v.uploader || ''}</div>
            </div>
            <div class="center">
                <a href="/download?url=${encodeURIComponent(v.webpage_url)}"><button>Baixar MP3</button></a>
            </div>
        </div>`;
    });
    document.getElementById("videos").innerHTML = html;
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/info")
def info():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL inválida!"})

    proxy = random.choice(PROXIES)
    ua = random.choice(USER_AGENTS)

    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,
        'extract_flat': False,
        'user_agent': ua,
        'http_headers': {'User-Agent': ua},
        'extractor_args': BYPASS_CONFIG,
        'proxy': proxy,
        'sleep_interval': random.uniform(1, 3),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Vídeo bloqueado ou proxy falhou. Tente novamente."})
            entries = info.get('entries') or [info]
            entries = [e for e in entries if e]
    except Exception as e:
        log.error(f"Erro info: {e}")
        return jsonify({"error": "Erro de conexão. Tente novamente em 10s."})

    result = []
    for e in entries:
        result.append({
            "title": e.get("title", "Sem título"),
            "thumbnail": e.get("thumbnail", ""),
            "webpage_url": e.get("webpage_url") or e.get("url"),
            "uploader": e.get("uploader", "")
        })
    return jsonify(result)

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return "URL necessária!", 400

    base = uuid.uuid4().hex
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{base}.%(ext)s")
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{base}.mp3")

    proxy = random.choice(PROXIES)
    ua = random.choice(USER_AGENTS)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'user_agent': ua,
        'http_headers': {'User-Agent': ua},
        'extractor_args': BYPASS_CONFIG,
        'proxy': proxy,
        'cachedir': False,
        'sleep_interval': random.uniform(1, 3),
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        time.sleep(1)

        if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1024:
            @after_this_request
            def remove(response):
                try: os.remove(mp3_path)
                except: pass
                return response
            return send_file(mp3_path, as_attachment=True, download_name="musica.mp3")
    except Exception as e:
        log.error(f"Download falhou: {e}")

    return "Falha no download. Tente novamente.", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
