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
    print(f"Instagram: {len(offen)} unbeantwortete Kommentare")
    return offen


def yt_anfrage(pfad, daten=None, **p):
    import urllib.request
    from post_youtube import token
    if not hasattr(yt_anfrage, "at"):
        yt_anfrage.at = token()
    kopf = {"Authorization": "Bearer " + yt_anfrage.at, "Content-Type": "application/json"}
    url = "https://www.googleapis.com/youtube/v3/" + pfad + "?" + urllib.parse.urlencode(p)
    req = urllib.request.Request(url, json.dumps(daten).encode() if daten else None, kopf, method="POST" if daten else "GET")
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"YouTube {e.code}: {e.read().decode(errors='replace')[:300]}")


def yt_holen():
    erledigt = set(lesen(ERLEDIGT, []))
    kanal = yt_anfrage("channels", part="id", mine="true")["items"][0]["id"]
    offen = []
    d = yt_anfrage("commentThreads", part="snippet", allThreadsRelatedToChannelId=kanal, maxResults=100, order="time")
    for th in d.get("items", []):
        s = th["snippet"]["topLevelComment"]["snippet"]
        cid = th["snippet"]["topLevelComment"]["id"]
        if cid in erledigt or s.get("authorChannelId", {}).get("value") == kanal or th["snippet"].get("totalReplyCount"):
            continue
        offen.append({"plattform": "youtube", "comment_id": "yt:" + cid, "von": s.get("authorDisplayName"),
                      "text": s.get("textOriginal", ""), "reel": s.get("videoId"), "zeit": s.get("publishedAt")})
    print(f"YouTube: {len(offen)} unbeantwortete Kommentare")
    return offen


def tt_senden(pfad, daten, methode="POST"):
    import urllib.request
    kopf = {"Authorization": "Bearer " + os.environ["ZERNIO_API_KEY"], "Content-Type": "application/json"}
    req = urllib.request.Request("https://zernio.com/api/v1" + pfad, json.dumps(daten).encode(), kopf, method=methode)
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Zernio {e.code} {pfad}: {e.read().decode(errors='replace')[:300]}")


def tt_antworten(a):
    """Antwort + Herz auf TikTok über Zernio. Fehlende Felder (post_id/account_id) kommen aus offen.json."""
    k = {x["comment_id"]: x for x in lesen(os.path.join(ORDNER, "offen.json"), [])}.get(a["comment_id"], {})
    post, konto, cid = a.get("post_id") or k.get("post_id"), a.get("account_id") or k.get("account_id"), a["comment_id"][3:]
    r = tt_senden(f"/inbox/comments/{post}", {"accountId": konto, "message": a["text"][:150], "commentId": cid})
    print("TikTok-Antwort:", json.dumps(r)[:200])
    if a.get("herz", True):
        for pfad in (f"/inbox/comments/{post}/{cid}/like", f"/inbox/comments/{post}/like"):
            try:
                print("TikTok-Herz:", json.dumps(tt_senden(pfad, {"accountId": konto, "commentId": cid}))[:200]); break
            except RuntimeError as e:
                print("Herz ging nicht:", str(e)[:200])


def tt_holen():
    """TikTok über Zernio-Inbox: Posts mit Kommentaren, dann deren Kommentare."""
    import urllib.request
    kopf = {"Authorization": "Bearer " + os.environ["ZERNIO_API_KEY"]}
    z = lambda pfad: json.load(urllib.request.urlopen(urllib.request.Request("https://zernio.com/api/v1" + pfad, headers=kopf), timeout=60))
    erledigt = set(lesen(ERLEDIGT, []))
    posts = z("/inbox/comments?platform=tiktok").get("data", [])
    if posts:
        print("TikTok Felder:", sorted(posts[0].keys()))
    offen = []
    for p in posts:
        n = p.get("commentCount") or p.get("commentsCount") or p.get("comments") or 0
        if not n:
            continue
        print(f"TikTok {n} Kommentar(e): {(p.get('content') or '')[:60]!r}")
        try:
            d = z(f"/inbox/comments/{p['id']}?accountId={p['accountId']}")
        except Exception as e:
            print("  Kommentare laden ging nicht:", str(e)[:200]); continue
        liste = d.get("data") or d.get("comments") or []
        if liste:
            print("  Felder:", sorted(liste[0].keys()))
        for c in liste:
            cid = "tt:" + str(c.get("id"))
            if cid in erledigt or c.get("isOwner") or c.get("fromMe"):
                continue
            offen.append({"plattform": "tiktok", "comment_id": cid, "post_id": p["id"], "account_id": p["accountId"],
                          "von": (c.get("from") or {}).get("username") if isinstance(c.get("from"), dict) else c.get("username"),
                          "text": c.get("text") or c.get("message") or c.get("content", ""),
                          "reel": (p.get("content") or "")[:120], "zeit": c.get("createdTime")})
    print(f"TikTok: {len(offen)} Kommentare")
    return offen


def antworten():
    liste = lesen(os.path.join(ORDNER, "antworten.json"), [])
    erledigt = lesen(ERLEDIGT, [])
    for a in liste:
        if a.get("comment_id") in erledigt or not a.get("text"):
            continue
        try:
            if str(a["comment_id"]).startswith("tt:"):
                tt_antworten(a)
            elif str(a["comment_id"]).startswith("yt:"):
                yt_anfrage("comments", {"snippet": {"parentId": a["comment_id"][3:], "textOriginal": a["text"][:500]}}, part="snippet")
            else:
                anfrage(f"{GRAPH}/{a['comment_id']}/replies",
                        urllib.parse.urlencode({"message": a["text"][:300], "access_token": TOKEN}).encode())
            print("Antwort gesendet:", a["comment_id"])
        except RuntimeError as e:
            print("Antwort fehlgeschlagen:", str(e)[:200])
        erledigt.append(a["comment_id"])
    schreiben(ERLEDIGT, erledigt[-2000:])
    schreiben(os.path.join(ORDNER, "antworten.json"), [])


if __name__ == "__main__":
    if "antworten" in sys.argv:
        antworten()
    if "holen" in sys.argv:
        alle = []
        teile = [("Instagram", lambda: holen(os.environ.get("IG_USER_ID") or konto_finden(TOKEN)) if TOKEN else []),
                 ("YouTube", lambda: yt_holen() if os.environ.get("YT_REFRESH_TOKEN") else []),
                 ("TikTok", lambda: tt_holen() if os.environ.get("ZERNIO_API_KEY") else [])]
        for name, f in teile:
            try:
                alle += f()
            except Exception as e:
                print(name, "ging nicht:", str(e)[:300])
        for k in alle:
            print("  ", k.get("plattform", "instagram"), "|", k.get("von"), "|", (k.get("text") or "")[:120])
        schreiben(os.path.join(ORDNER, "offen.json"), alle)
