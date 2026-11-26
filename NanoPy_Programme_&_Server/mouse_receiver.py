#!/usr/bin/env python3
# Steuert die PC-Maus aus den Gesten des Oxocard Connect tof-Sensors.
# Start:  python3 mouse_receiver.py     (Windows/macOS/Linux)

import http.server
import socketserver
import urllib.parse
import socket
import sys

PORT = 8765
KEY = "geheim123"

# --- Maus-Backend waehlen -----------------------------------------------
try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0

    def move(dx, dy):
        pyautogui.moveRel(dx, dy)

    def click():
        pyautogui.click()

    BACKEND = "pyautogui"

except ImportError:
    try:
        import ctypes
        user32 = ctypes.windll.user32

        def move(dx, dy):
            user32.mouse_event(0x0001, int(dx), int(dy), 0, 0)

        def click():
            user32.mouse_event(0x0002, 0, 0, 0, 0)
            user32.mouse_event(0x0004, 0, 0, 0, 0)

        BACKEND = "win32"

    except Exception:
        print("Bitte pyautogui installieren:  pip install pyautogui")
        sys.exit(1)


def local_ips():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return [ip]
    except Exception:
        return ["127.0.0.1"]


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path != "/mouse":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"mouse receiver ready\n")
            return

        if params.get("key", [""])[0] != KEY:
            self.send_response(403)
            self.end_headers()
            return

        dx = int(params.get("dx", ["0"])[0])
        dy = int(params.get("dy", ["0"])[0])
        btn = int(params.get("b", ["0"])[0])

        if dx != 0 or dy != 0:
            move(dx, dy)
        if btn == 1:
            click()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    print("Maus-Empfaenger auf Port %d (Backend: %s)" % (PORT, BACKEND))
    for ip in local_ips():
        print("  NanoPy pcBase -> http://%s:%d/mouse?key=%s" % (ip, PORT, KEY))
    with socketserver.TCPServer(("", PORT), Handler) as srv:
        srv.serve_forever()