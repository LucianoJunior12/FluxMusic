import os
from flask import Flask, render_template_string, request, send_file, redirect, url_for, flash
from youtube_explode_dart import YoutubeExplode, AudioOnlyStream
import tempfile

app = Flask(__name__)
app.secret_key = "flux_music_secret"  # necessário para flash messages

# Porta fornecida pelo ambiente PaaS
PORT = int(os.environ.get("PORT", 8080))

# HTML da interface
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flux Music</title>
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(to right, #4e54c8, #8f94fb); color: #fff; text-align: center; padding: 50px; }
        h1 { font-size: 3em; margin-bottom: 20px; }
        form { margin-top: 20px; }
        input[type="text"] { width: 60%; padding: 10px; border-radius: 5px; border: none; }
        input[type="submit"] { padding: 10px 20px; border-radius: 5px; border: none; background-color: #ff4b2b; color: #fff; font-weight: bold; cursor: pointer; margin-left: 10px; }
        .flash { margin: 20px; color: yellow; }
        footer { margin-top: 50px; font-size: 0.8em; color: #ccc; }
    </style>
</head>
<body>
    <h1>Flux Music</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="flash">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}
    <form method="post">
        <input type="text" name="url" placeholder="Cole o link do YouTube aqui" required>
        <input type="submit" value="Baixar MP3">
    </form>
    <footer>Desenvolvido por Junior</footer>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            flash("Insira um link válido!")
            return redirect(url_for("index"))

        try:
            yt = YoutubeExplode()
            video = yt.videos.get(url)
            audio_stream = yt.streams.filter(audio_only=True).get_best()

            # Cria arquivo temporário
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp_file.close()

            # Faz download do áudio
            yt.streams.get(audio_stream.id).download(filename=tmp_file.name)

            return send_file(tmp_file.name, as_attachment=True, download_name=f"{video.title}.mp3")
        except Exception as e:
            print(e)
            flash("Erro ao baixar o vídeo. Verifique o link.")
            return redirect(url_for("index"))

    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
