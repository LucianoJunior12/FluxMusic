import http.server
import socketserver
import os

PORT = 8080

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Flux Music</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body { background:#121212; color:#fff; font-family: 'Segoe UI', sans-serif; margin:0; padding:0;}
header { background:#1DB954; padding:20px; text-align:center; font-size:2em; font-weight:bold;}
.container { width:90%; max-width:800px; margin:auto; padding:20px;}
h2 { margin-top:30px; }
.song {
    display:flex; justify-content:space-between; align-items:center;
    background:#222; padding:12px 20px; margin:10px 0; border-radius:10px;
    transition: 0.2s; cursor:pointer;
}
.song:hover { background:#333; }
button { background:#1DB954; border:none; color:#fff; padding:6px 14px; border-radius:6px; cursor:pointer; }
button:hover { background:#17a44d; }
audio { width:100%; margin-top:20px; border-radius:10px; }
input[type=file] { padding:10px; margin-top:20px; }
form { display:flex; justify-content:center; gap:10px; flex-wrap:wrap; }
</style>
</head>
<body>

<header>Flux Music</header>
<div class="container">

<form method="POST" enctype="multipart/form-data">
<input type="file" name="file">
<button type="submit">Enviar Música</button>
</form>

<h2>Suas músicas</h2>
<div id="songs">
{songs}
</div>

<audio id="player" controls autoplay></audio>

</div>
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
            files = [f for f in os.listdir() if f.endswith(".mp3") or f.endswith(".wav")]
            list_html = ""
            for f in files:
                list_html += f"""
<div class="song">
<span onclick="playSong('{f}')">{f}</span>
<a href="{f}" download><button>Download</button></a>
</div>
"""
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
                file_data = section[file_start:-4]
                filename = header.split("filename=")[1].split('"')[1]
                with open(filename, "wb") as f:
                    f.write(file_data)
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

with socketserver.TCPServer(("", PORT), Server) as httpd:
    print(f"Servidor iniciado na porta {PORT}")
    print(f"Acesse: http://SEU_IP_PUBLICO:{PORT}")
    httpd.serve_forever()
