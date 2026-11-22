# -*- coding: utf-8 -*-
"""Lädt ein fertiges Video als Reel auf Instagram hoch (offizielle Instagram-Graph-API).

    python scripts/post_instagram.py out/<id>.mp4

Braucht die Umgebungsvariablen IG_TOKEN (langlebiger Zugriffstoken) und IG_USER_ID
(ID des Instagram-Creator/Business-Kontos). Caption kommt aus out/<id>.txt.
API-Version über IG_API_VERSION änderbar (Standard v24.0).
"""
import json, os, sys, time, urllib.parse, urllib.request

VERSION = os.environ.get("IG_API_VERSION", "v24.0")
TOKEN = os.environ.get("IG_TOKEN", "")
# Token aus "Instagram-Login" (beginnt mit IG...) -> graph.instagram.com, sonst Facebook-Login -> graph.facebook.com
GRAPH = f"https://graph.{'instagram' if TOKEN.startswith('IG') else 'facebook'}.com/{VERSION}"


def anfrage(url, daten=None, kopf=None, methode=None):
    req = urllib.request.Request(url, data=daten, headers=kopf or {}, method=methode)
    try:
        return json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Instagram-Fehler {e.code}: {e.read().decode(errors='replace')[:800]}")


def konto_finden(token):
    """Instagram-Konto-ID selbst ermitteln (Instagram-Login-Token oder Systemnutzer-/Facebook-Token)."""
    q = lambda pfad, felder: anfrage(f"{GRAPH}/{pfad}?" + urllib.parse.urlencode({"fields": felder, "access_token": token}))
    if token.startswith("IG"):
        me = q("me", "user_id,username")
        print(f"Konto: @{me.get('username')}")
        return str(me.get("user_id") or me["id"])
    try:   # Facebook-Seiten mit verknüpftem Instagram-Konto
        for seite in q("me/accounts", "instagram_business_account{id,username}").get("data", []):
            ig = seite.get("instagram_business_account")
            if ig:
                print(f"Konto: @{ig.get('username')}")
                return ig["id"]
    except RuntimeError as e:
        print("me/accounts:", str(e)[:200])
    portfolios = [{"id": os.environ["IG_BUSINESS_ID"], "name": "IG_BUSINESS_ID"}] if os.environ.get("IG_BUSINESS_ID") else []
    try:
        portfolios += q("me/businesses", "id,name").get("data", [])
    except RuntimeError as e:
        print("me/businesses:", str(e)[:200])
    for b in portfolios:   # Business-Portfolio (Systemnutzer)
        for feld in ("instagram_accounts", "owned_instagram_accounts"):
            try:
                daten = q(f"{b['id']}/{feld}", "id,username").get("data", [])
            except RuntimeError:
                continue
            if daten:
                print(f"Konto: @{daten[0].get('username')} (Portfolio {b.get('name')})")
                return daten[0]["id"]
    raise RuntimeError("Kein Instagram-Konto zum Token gefunden – Secret IG_USER_ID setzen")


def posten(video):
    token, nutzer = TOKEN, os.environ.get("IG_USER_ID", "")
    if not nutzer:
        nutzer = konto_finden(token)
    caption = open(os.path.splitext(video)[0] + ".txt", encoding="utf-8").read() if os.path.exists(os.path.splitext(video)[0] + ".txt") else ""
    # 1) Container anlegen (Upload in Teilen über rupload)
    c = anfrage(f"{GRAPH}/{nutzer}/media", urllib.parse.urlencode({"media_type": "REELS", "upload_type": "resumable",
                "caption": caption[:2200], "share_to_feed": "true", "access_token": token}).encode())
    cid = c["id"]
    # 2) Datei hochladen
    groesse = os.path.getsize(video)
    with open(video, "rb") as f:
        r = anfrage(f"https://rupload.facebook.com/ig-api-upload/{VERSION}/{cid}", f.read(),
                    {"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(groesse),
                     "Content-Type": "application/octet-stream", "Content-Length": str(groesse)}, "POST")
    if not r.get("success", True):
        raise RuntimeError(f"Upload fehlgeschlagen: {r}")
    # 3) Warten bis Instagram das Video verarbeitet hat
    for _ in range(60):
        s = anfrage(f"{GRAPH}/{cid}?" + urllib.parse.urlencode({"fields": "status_code,status", "access_token": token}))
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram konnte das Video nicht verarbeiten: {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Zeitüberschreitung bei der Verarbeitung")
    # 4) Veröffentlichen
    p = anfrage(f"{GRAPH}/{nutzer}/media_publish", urllib.parse.urlencode({"creation_id": cid, "access_token": token}).encode())
    print(f"Veröffentlicht: {video} -> Medien-ID {p.get('id')}")


if __name__ == "__main__":
    for v in sys.argv[1:]:
        if v.endswith(".mp4"):
            posten(v)
