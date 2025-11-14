from flask import Flask, request, render_template_string, send_file
from pytube import YouTube
from pydub import AudioSegment
import os

app = Flask(__name__)
download_folder = "downloads"
os.makedirs(download_folder, exist_ok=True)

# HTML simples para receber o link
HTML = """
<!doctype html>
<title>Baixar MP3</title>
<h2>Coloque o link do YouTube:</h2>
<form method=post>
  <input type=text name=link style="width:400px">
  <input type=submit value=Baixar>
</form>
{% if file %}
  <p>Download pronto: <a href="{{ file }}">{{ file }}</a></p>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    file_path = None
    if request.method == "POST":
        url = request.form.get("link")
        try:
            yt = YouTube(url)
            stream = yt.streams.filter(only_audio=True).first()
            mp4_file = stream.download(output_path=download_folder)
            mp3_file = mp4_file.replace(".mp4", ".mp3")
            AudioSegment.from_file(mp4_file).export(mp3_file, format="mp3")
            os.remove(mp4_file)
            file_path = mp3_file
        except Exception as e:
            return f"Erro: {e}"
    return render_template_string(HTML, file=file_path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
