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

# Atualiza yt-dlp automaticamente no startup
def update_yt_dlp():
    try:
        subprocess.check_call(['pip', 'install', '--upgrade', 'yt-dlp'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log.info("yt-dlp atualizado com sucesso!")
    except Exception as e:
        log.warning(f"Falha ao atualizar yt-dlp: {e}")

update_yt_dlp()

# Lista de user agents reais (mobile + desktop)
USER_AGENTS = [
    'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Configs de bypass (ordem otimizada: android > ios > web)
BYPASS_CONFIGS = [
    {'client': 'android', 'ua': USER_AGENTS[0]},
    {'client': 'ios',      'ua': USER_AGENTS[1]},
    {'client': 'web',      'ua': USER_AGENTS[3]},
]

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

    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,
        'extract_flat': False,
        'user_agent': random.choice(USER_AGENTS),
        'extractor_args': {'youtube': {'player_client': 'android'}},
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Vídeo não encontrado."})
            entries = info.get('entries') or [info]
            entries = [e for e in entries if e]
    except Exception as e:
        log.exception("Erro ao extrair info")
        return jsonify({"error": f"Erro: {str(e)[:100]}"})

    result = []
    for e in entries:
        result.append({
            "title": e.get("title", "Sem título"),
            "thumbnail": e.get("thumbnail", ""),
            "webpage_url": e.get("webpage_url") or e.get("url"),
            "uploader": e.get("uploader", "")
        })
    return jsonify(result)

def try_download_with_bypass(url, outtmpl):
    base_name = uuid.uuid4().hex
    mp3_path = os.path.join(DOWNLOAD_DIR, f"{base_name}.mp3")

    for i, config in enumerate(BYPASS_CONFIGS):
        log.info(f"Tentativa {i+1}/3 com client: {config['client']}")
        time.sleep(random.uniform(1, 3))  # Delay humano

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
            'user_agent': config['ua'],
            'http_headers': {'User-Agent': config['ua']},
            'extractor_args': {
                'youtube': {
                    'player_client': config['client'],
                    'skip': ['hls', 'dash'],
                    'player_skip': ['configs', 'webpage'],
                }
            },
            'cachedir': False,
            'sleep_interval': random.uniform(0.5, 2),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            time.sleep(0.5)
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1024:
                log.info(f"Sucesso com {config['client']}! Tamanho: {os.path.getsize(mp3_path)} bytes")
                return mp3_path
        except Exception as e:
            log.warning(f"Falha com {config['client']}: {str(e)[:80]}")
            continue

    return None

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return "URL necessária!", 400

    base = uuid.uuid4().hex
    outtmpl = os.path.join(DOWNLOAD_DIR, f"{base}.%(ext)s")
    mp3_path = try_download_with_bypass(url, outtmpl)

    if not mp3_path or not os.path.exists(mp3_path):
        return "Falha ao baixar. Tente novamente em 1 minuto.", 500

    @after_this_request
    def remove_file(response):
        try:
            time.sleep(1)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
                log.info("Arquivo temporário removido.")
        except Exception as e:
            log.error(f"Erro ao remover: {e}")
        return response

    return send_file(mp3_path, as_attachment=True, download_name="musica.mp3")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
