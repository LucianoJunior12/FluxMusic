#!/usr/bin/env python3
from flask import Flask, request, send_file, render_template_string, jsonify, after_this_request
import yt_dlp
import os
import uuid
import time
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("FluxMusic")

app = Flask("FluxMusic")
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
        return {"error": "URL inválida!"}
    ydl_opts = {
        'quiet': True,
        'cookiefile': 'youtube.com_cookies.txt',
        'extractor_args': {'youtube': {'player_client': 'web'}},
        'ignoreerrors': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return {"error": "Não foi possível extrair informações do URL."}
            entries = info.get('entries') if isinstance(info, dict) and info.get('entries') else None
            if entries:
                entries = [e for e in entries if e]
            else:
                entries = [info]
    except Exception as e:
        log.exception("Erro em info.extract_info")
        return {"error": f"Erro ao extrair info: {e}"}
    result = []
    for entry in entries:
        webpage = entry.get("webpage_url") or entry.get("url")
        title = entry.get("title") or (entry.get("id") or "sem-titulo")
        thumb = entry.get("thumbnail") or ""
        uploader = entry.get("uploader") or ""
        result.append({
            "title": title,
            "thumbnail": thumb,
            "webpage_url": webpage,
            "uploader": uploader
        })
    return jsonify(result)

def try_download_to_path(url, out_path):
    ydl_opts = {
        'quiet': True,
        'cookiefile': 'youtube.com_cookies.txt',
        'extractor_args': {'youtube': {'player_client': 'web'}},
        'format': 'bestaudio/best',
        'outtmpl': out_path,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cachedir': False,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, None
    except Exception as e:
        log.exception("Erro no download")
        return False, str(e)

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return "Parâmetro 'url' necessário", 400
    base = uuid.uuid4().hex
    outtmpl = os.path.join(DOWNLOAD_DIR, base + ".%(ext)s")
    mp3_path = os.path.join(DOWNLOAD_DIR, base + ".mp3")
    ok, err = try_download_to_path(url, outtmpl)
    if not ok:
        return f"Falha ao gerar MP3: {err}", 500
    time.sleep(0.2)
    if not os.path.exists(mp3_path):
        return "Arquivo MP3 não encontrado após conversão", 500
    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception as e:
            log.exception("Erro ao apagar arquivo temporário")
        return response
    return send_file(mp3_path, as_attachment=True, download_name="musica.mp3")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
