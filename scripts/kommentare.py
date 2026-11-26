# -*- coding: utf-8 -*-
"""Kommentare unter den eigenen Reels verwalten (offizielle Graph-API, nur eigene Beiträge).

    python scripts/kommentare.py antworten   # kommentare/antworten.json abschicken
    python scripts/kommentare.py holen       # unbeantwortete Kommentare -> kommentare/offen.json

Die Antworten schreibt der tägliche Claude-Agent in kommentare/antworten.json:
    [{"comment_id": "...", "text": "..."}]
"""
import json, os, sys, urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from post_instagram import GRAPH, TOKEN, anfrage, konto_finden  # noqa: E402

ORDNER = "kommentare"
ERLEDIGT = os.path.join(ORDNER, "erledigt.json")


def lesen(pfad, standard):
    try:
        return json.load(open(pfad, encoding="utf-8"))
    except (OSError, ValueError):
        return standard


def schreiben(pfad, daten):
    os.makedirs(ORDNER, exist_ok=True)
    json.dump(daten, open(pfad, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def holen(nutzer):
    q = lambda pfad, **p: anfrage(f"{GRAPH}/{pfad}?" + urllib.parse.urlencode({**p, "access_token": TOKEN}))
    ich = q(nutzer, fields="username").get("username", "")
    erledigt = set(lesen(ERLEDIGT, []))
    offen = []
    for m in q(f"{nutzer}/media", fields="id,caption,timestamp,comments_count", limit=60).get("data", []):
        if not m.get("comments_count"):
            continue
        print(f"{m['comments_count']} Kommentar(e): {(m.get('caption') or '')[:60]!r}")
        for c in q(f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50).get("data", []):
            antwortende = {r.get("username") for r in c.get("replies", {}).get("data", [])}
            if c["id"] in erledigt or c.get("username") == ich or ich in antwortende:
                continue
            offen.append({"comment_id": c["id"], "von": c.get("username"), "text": c.get("text", ""),
                          "reel": (m.get("caption") or "")[:120], "zeit": c.get("timestamp")})
    schreiben(os.path.join(ORDNER, "offen.json"), offen)
    print(f"{len(offen)} unbeantwortete Kommentare")


def antworten():
    liste = lesen(os.path.join(ORDNER, "antworten.json"), [])
    erledigt = lesen(ERLEDIGT, [])
    for a in liste:
        if a.get("comment_id") in erledigt or not a.get("text"):
            continue
        try:
            anfrage(f"{GRAPH}/{a['comment_id']}/replies",
                    urllib.parse.urlencode({"message": a["text"][:300], "access_token": TOKEN}).encode())
            print("Antwort gesendet:", a["comment_id"])
        except RuntimeError as e:
            print("Antwort fehlgeschlagen:", str(e)[:200])
        erledigt.append(a["comment_id"])
    schreiben(ERLEDIGT, erledigt[-2000:])
    schreiben(os.path.join(ORDNER, "antworten.json"), [])


if __name__ == "__main__":
    if not TOKEN:
        sys.exit("Kein IG_TOKEN")
    if "antworten" in sys.argv:
        antworten()
    if "holen" in sys.argv:
        holen(os.environ.get("IG_USER_ID") or konto_finden(TOKEN))
