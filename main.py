from flask import Flask, request, send_file
import yt_dlp
import os
import uuid

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Flux Music Online</h1><p>Use /download?url=LINK</p>"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return "Informe ?url=link"

    file_id = str(uuid.uuid4()) + ".mp3"
    output_path = f"/tmp/{file_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return f"Erro ao baixar: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
