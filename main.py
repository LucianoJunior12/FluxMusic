import http.server
import socketserver
import os
from urllib.parse import unquote

PORT = 8080

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Spotfi Lite</title>
<style>
body { background:#111; color:#fff; font-family:Arial; text-align:center; }
h1 { margin-top:40px; }
.container { width:80%; margin:auto; }
.song {
    background:#222; padding:12px; margin:10px;
    border-radius:8px; cursor:pointer;
}
audio { width:100%; margin-top:20px; }
input { margin:20px; }
button { padding:8px 20px; }
</style>
</head>
<body>

<h1>Spotfi Lite</h1>
<p>Envie e toque músicas diretamente do navegador</p>

<form method="POST" enctype="multipart/form-data">
<input type="file" name="file">
<button type="submit">Enviar Música</button>
</form>

<h2>Suas músicas</h2>
<div id="songs">
{songs}
</div>

<audio id="player" controls autoplay></audio>

<script>
function playSong(file) {
    const audio = document.getElementById("player");
    audio.src = file;
    audio.play();
}
</script>

</body>
</html>
"""

class Server(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            mp3s = [f for f in os.listdir() if f.endswith(".mp3") or f.endswith(".wav")]

            list_html = ""
            for s in mp3s:
                list_html += f'<div class="song" onclick="playSong(\'{s}\')">{s}</div>'

            page = HTML.replace("{songs}", list_html)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(page.encode("utf-8"))
        else:
            return super().do_GET()

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length)

        boundary = self.headers.get('Content-Type').split("boundary=")[1].encode()
        sections = data.split(boundary)

        for section in sections:
            if b"filename=" in section:
                header_end = section.find(b"\r\n\r\n")
                header = section[:header_end].decode()
                file_start = header_end + 4
                file_data = section[file_start:-4]  # remove \r\n--

                filename = header.split("filename=")[1].split('"')[1]

                with open(filename, "wb") as f:
                    f.write(file_data)

        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

with socketserver.TCPServer(("", PORT), Server) as httpd:
    print(f"Servidor iniciado na porta {PORT}")
    print("Acesse assim no navegador:")
    print(f" http://SEU_IP_PUBLICO:{PORT}")
    httpd.serve_forever()
