# -*- coding: utf-8 -*-
"""Lädt ein Video über Zernio zu TikTok (REST-API, nur Standardbibliothek).

    python scripts/post_tiktok.py out/<id>.mp4

ZERNIO_API_KEY     Secret. Fehlt es, wird TikTok übersprungen.
TIKTOK_ACCOUNT_ID  Zernio-Konto-ID
TIKTOK_MODUS       entwurf (Standard: landet im TikTok-Posteingang, Veröffentlichen per Hand in der App) | oeffentlich
TIKTOK_ZUSTIMMUNG  "ja" nur, wenn der Kontoinhaber dem Posten zugestimmt hat (TikTok verlangt Vorschau + Zustimmung).
"""
import json, os, sys, urllib.error, urllib.request

API = "https://zernio.com/api/v1"


def anfrage(pfad, daten):
    req = urllib.request.Request(API + pfad, json.dumps(daten).encode(), {
        "Authorization": "Bearer " + os.environ["ZERNIO_API_KEY"], "Content-Type": "application/json"}, method="POST")
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Zernio-Fehler {e.code}: {e.read().decode(errors='replace')[:600]}")


def posten(video):
    basis = os.path.splitext(video)[0]
    caption = open(basis + ".txt", encoding="utf-8").read() if os.path.exists(basis + ".txt") else ""
    p = anfrage("/media/presign", {"filename": os.path.basename(video), "contentType": "video/mp4", "size": os.path.getsize(video)})
    with open(video, "rb") as f:
        urllib.request.urlopen(urllib.request.Request(p["uploadUrl"], f.read(), {"Content-Type": "video/mp4"}, method="PUT"), timeout=600)
    einst = {"allow_comment": True, "allow_duet": True, "allow_stitch": True,
             "content_preview_confirmed": True, "express_consent_given": True}
    if os.environ.get("TIKTOK_MODUS", "entwurf") == "oeffentlich":
        einst["privacy_level"] = "PUBLIC_TO_EVERYONE"
        einst["video_made_with_ai"] = True  # KI-Label (Stimme ist KI)
    else:
        einst["draft"] = True
    r = anfrage("/posts", {"content": caption[:2200], "mediaItems": [{"type": "video", "url": p["publicUrl"]}],
                           "platforms": [{"platform": "tiktok", "accountId": os.environ["TIKTOK_ACCOUNT_ID"]}],
                           "tiktokSettings": einst, "publishNow": True})
    post = r.get("post", r)
    print("TikTok:", post.get("_id"), post.get("status"), [x.get("status") for x in post.get("platforms", [])])


if __name__ == "__main__":
    if not os.environ.get("ZERNIO_API_KEY"):
        sys.exit("Kein ZERNIO_API_KEY – TikTok übersprungen.")
    if os.environ.get("TIKTOK_ZUSTIMMUNG") != "ja":
        sys.exit("TIKTOK_ZUSTIMMUNG fehlt – nichts hochgeladen.")
    for v in sys.argv[1:]:
        if not v.endswith("_story.mp4"):
            posten(v)
