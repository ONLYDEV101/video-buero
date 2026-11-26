# -*- coding: utf-8 -*-
"""Lädt ein fertiges Video als YouTube Short hoch (YouTube Data API v3, nur Standardbibliothek).

    python scripts/post_youtube.py out/<id>.mp4

Braucht YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (einmalig mit tools/youtube_login.py erzeugt).
YT_PRIVACY: public | unlisted | private (Standard public; ungeprüfte API-Projekte erzwingt Google privat).
"""
import json, os, re, sys, urllib.parse, urllib.request


def token():
    daten = urllib.parse.urlencode({"client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
                                    "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}).encode()
    return json.load(urllib.request.urlopen("https://oauth2.googleapis.com/token", daten, timeout=60))["access_token"]


def metadaten(video):
    basis = os.path.splitext(video)[0]
    caption = open(basis + ".txt", encoding="utf-8").read() if os.path.exists(basis + ".txt") else ""
    ep = {}
    eid = os.path.basename(basis)
    for ordner in ("episoden/warteschlange", "episoden/gepostet", "episoden"):
        p = os.path.join(ordner, eid + ".json")
        if os.path.exists(p):
            ep = json.load(open(p, encoding="utf-8"))
            break
    titel = ep.get("titel") or caption.split("\n")[0]
    lang = os.path.basename(basis).startswith(("kompilation", "doku"))   # langes Video: kein #shorts
    titel = re.sub(r"[<>]", "", titel)[:90] + ("" if lang else " #shorts")
    tags = [t.lstrip("#") for t in re.findall(r"#\w+", caption)][:10]
    beschreibung = re.sub(r"[<>]", "", caption)[:4800]
    return {"snippet": {"title": titel, "description": beschreibung, "tags": tags, "categoryId": "27"},
            "status": {"privacyStatus": os.environ.get("YT_PRIVACY", "public"), "selfDeclaredMadeForKids": False}}


def hochladen(video):
    at = token()
    meta = json.dumps(metadaten(video)).encode()
    groesse = os.path.getsize(video)
    req = urllib.request.Request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                                 meta, {"Authorization": f"Bearer {at}", "Content-Type": "application/json; charset=UTF-8",
                                        "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(groesse)}, method="POST")
    ziel = urllib.request.urlopen(req, timeout=60).headers["Location"]
    with open(video, "rb") as f:
        req = urllib.request.Request(ziel, f.read(), {"Content-Type": "video/mp4", "Content-Length": str(groesse)}, method="PUT")
    try:
        r = json.load(urllib.request.urlopen(req, timeout=600))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"YouTube-Fehler {e.code}: {e.read().decode(errors='replace')[:600]}")
    print(f"YouTube: https://youtube.com/watch?v={r['id']} ({r['status']['privacyStatus']})")
    return r["id"]


if __name__ == "__main__":
    if not os.environ.get("YT_REFRESH_TOKEN"):
        sys.exit("Kein YT_REFRESH_TOKEN – YouTube übersprungen.")
    for v in sys.argv[1:]:
        if not v.endswith("_story.mp4"):
            hochladen(v)
