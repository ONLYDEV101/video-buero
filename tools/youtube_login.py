# -*- coding: utf-8 -*-
r"""Einmalige YouTube-Anmeldung. Holt den Refresh-Token und speichert alles direkt als GitHub-Secrets
(nichts wird angezeigt oder auf die Platte geschrieben).

    python tools/youtube_login.py C:\Pfad\zur\client_secret_XXXX.json
"""
import http.server, json, os, secrets, subprocess, sys, urllib.parse, urllib.request, webbrowser

GH = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin\gh.exe")
REPO = "ONLYDEV101/video-buero"
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
cfg = cfg.get("installed") or cfg.get("web")
PORT = 8765
redirect = f"http://127.0.0.1:{PORT}"
state = secrets.token_urlsafe(16)
url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
    "client_id": cfg["client_id"], "redirect_uri": redirect, "response_type": "code", "state": state,
    "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly",
    "access_type": "offline", "prompt": "consent"})
code = {}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if q.get("state", [""])[0] == state and "code" in q:
            code["c"] = q["code"][0]
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers()
        self.wfile.write("<h2>Fertig – du kannst das Fenster schließen.</h2>".encode())

    def log_message(self, *a):
        pass


webbrowser.open(url)
srv = http.server.HTTPServer(("127.0.0.1", PORT), H)
while "c" not in code:
    srv.handle_request()
daten = urllib.parse.urlencode({"code": code["c"], "client_id": cfg["client_id"], "client_secret": cfg["client_secret"],
                                "redirect_uri": redirect, "grant_type": "authorization_code"}).encode()
tok = json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", daten))
kanal = json.load(urllib.request.urlopen(urllib.request.Request(
    "https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", headers={"Authorization": "Bearer " + tok["access_token"]})))
print("Kanal:", ", ".join(i["snippet"]["title"] for i in kanal.get("items", [])) or "keiner gefunden!")
for name, wert in (("YT_CLIENT_ID", cfg["client_id"]), ("YT_CLIENT_SECRET", cfg["client_secret"]), ("YT_REFRESH_TOKEN", tok["refresh_token"])):
    subprocess.run([GH, "secret", "set", name, "-R", REPO, "--body", wert], check=True, capture_output=True)
    print("Secret gesetzt:", name)
