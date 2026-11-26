from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
import ctypes
import hmac
import platform
import socket
import subprocess
import threading


HOST = "0.0.0.0"
PORT = 8765

# Derselbe Schlüssel muss auf der Oxocard stehen.
TOKEN = ""


def get_local_ip():
    """
    Ermittelt die IP-Adresse, über die der PC normalerweise
    Geräte im lokalen Netzwerk erreicht.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        # Es wird dabei keine echte Verbindung zu Google aufgebaut.
        # connect() bestimmt hier nur die passende lokale Netzwerkschnittstelle.
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = "UNBEKANNT"
    finally:
        s.close()

    return ip


def lock_pc():
    system = platform.system()

    if system == "Windows":
        ctypes.windll.user32.LockWorkStation()

    elif system == "Linux":
        subprocess.run(
            ["loginctl", "lock-session"],
            check=False
        )

    elif system == "Darwin":
        subprocess.run(
            ["pmset", "displaysleepnow"],
            check=False
        )

    else:
        print("Unbekanntes Betriebssystem:", system)


class Handler(BaseHTTPRequestHandler):

    def send_text(self, code, text):
        data = text.encode("utf-8")

        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

        self.wfile.write(data)

    def do_GET(self):
        client_ip = self.client_address[0]
        path = urlsplit(self.path).path

        print("Anfrage von:", client_ip, "Pfad:", path)

        if path != "/lock":
            self.send_text(404, "Not found")
            return

        supplied_token = self.headers.get("X-Oxocard-Key", "")

        if not hmac.compare_digest(supplied_token, TOKEN):
            print("Falscher oder fehlender Schlüssel von:", client_ip)
            self.send_text(403, "Forbidden")
            return

        self.send_text(200, "OK")

        print(">>> Sperren angefordert von:", client_ip)

        threading.Thread(
            target=lock_pc,
            daemon=True
        ).start()

    def log_message(self, format, *args):
        # Standard-HTTP-Logging ausschalten
        pass


if __name__ == "__main__":

    local_ip = get_local_ip()

    print()
    print("=" * 65)
    print(" OXOCARD PC LOCK SERVER")
    print("=" * 65)
    print()
    print("PC-IP:       ", local_ip)
    print("Port:        ", PORT)
    print("Schlüssel:   ", TOKEN)
    print()
    print("-" * 65)
    print("DIESE ZEILEN IN NANOPY EINTRAGEN:")
    print("-" * 65)
    print()

    print(
        'lockUrl:byte[80] = '
        f'"http://{local_ip}:{PORT}/lock"'
    )

    print(
        'lockToken:byte[80] = '
        f'"{TOKEN}"'
    )

    print()
    print("-" * 65)
    print()
    print("Server läuft.")
    print("Warte auf Oxocard ...")
    print()
    print("Zum Beenden: Strg+C")
    print()

    server = ThreadingHTTPServer((HOST, PORT), Handler)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print()
        print("Server beendet.")

    finally:
        server.server_close()