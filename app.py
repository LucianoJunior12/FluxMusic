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

    # Try extraction with standard args (full extract)
    ydl_opts = {'quiet': True, 'ignoreerrors': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # entries handling for playlist or single
            if info is None:
                return {"error": "Não foi possível extrair informações do URL."}
            entries = info.get('entries') if isinstance(info, dict) and info.get('entries') else None
            if entries:
                entries = [e for e in entries if e]  # filter None
            else:
                entries = [info]
    except Exception as e:
        log.exception("Erro em info.extract_info")
        return {"error": f"Erro ao extrair info: {e}"}

    result = []
    for entry in entries:
        # attempt to get webpage_url, thumbnail, title
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

def try_download_to_path(url, out_path, extractor_args=None):
    """Tenta baixar e converter para MP3 usando yt-dlp. Retorna (ok, error_msg)."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_path,   # yt-dlp will replace extension, postprocessor will create mp3
        'quiet': True,
        'no_warnings': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cachedir': False,
    }
    if extractor_args:
        ydl_opts['extractor_args'] = extractor_args

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True, None
    except Exception as e:
        log.exception("Erro no download (tentativa):")
        return False, str(e)

@app.route("/download")
def download():
    # Accept either id (not used here) or url param
    url = request.args.get("url")
    if not url:
        return "Parâmetro 'url' necessário. Ex: /download?url=<video_url>", 400

    # Make unique base name; yt-dlp will create file like <base>.mp3
    base = uuid.uuid4().hex
    outtmpl = os.path.join(DOWNLOAD_DIR, base + ".%(ext)s")
    mp3_path = os.path.join(DOWNLOAD_DIR, base + ".mp3")

    # Try sequence of extractor args to handle SABR / client variations
    extractor_clients = [
        {'youtube': {'player_client': 'default'}},
        {'youtube': {'player_client': 'web'}},
        {'youtube': {'player_client': 'android'}},
        None
    ]

    last_error = None
    ok = False
    for args in extractor_clients:
        log.info("Tentando baixar com extractor_args=%s", args)
        ok, err = try_download_to_path(url, outtmpl, extractor_args=args)
        if ok:
            # small delay to allow filesystem write flush
            time.sleep(0.2)
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                log.info("Arquivo criado: %s (%d bytes)", mp3_path, os.path.getsize(mp3_path))
                break
            else:
                ok = False
                err = "Arquivo MP3 não encontrado após conversão."
        last_error = err

    if not ok:
        log.error("Falha ao baixar/converter: %s", last_error)
        return f"Falha ao gerar MP3: {last_error}", 500

    # Ensure file will be deleted AFTER response is sent
    @after_this_request
    def remove_file(response):
        try:
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
                log.info("Arquivo temporário removido: %s", mp3_path)
        except Exception as e:
            log.exception("Erro ao apagar arquivo temporário")
        return response

    # send_file will raise if file doesn't exist; we've checked above
    return send_file(mp3_path, as_attachment=True, download_name="musica.mp3")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

