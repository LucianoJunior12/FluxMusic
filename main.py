from flask import Flask, request, send_file, render_template_string
from pytube import YouTube
import os

app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<title>YouTube Downloader</title>
<h2>Baixe vídeos do YouTube em MP3</h2>
<form method="POST">
  <input name="url" placeholder="Cole o link do YouTube aqui" required>
  <button type="submit">Baixar</button>
</form>
{% if filename %}
  <p>Download pronto: <a href="{{ filename }}">{{ filename }}</a></p>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    filename = None
    if request.method == "POST":
        url = request.form["url"]
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        filename = yt.title + ".mp3"
        stream.download(filename=filename)
    return render_template_string(HTML_PAGE, filename=filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
