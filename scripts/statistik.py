# -*- coding: utf-8 -*-
"""Zeigt Reichweite der letzten Reels + Kontodaten (Instagram Graph API)."""
import json, os, sys, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
from post_instagram import anfrage, konto_finden, GRAPH, TOKEN

nutzer = os.environ.get("IG_USER_ID") or konto_finden(TOKEN)
q = lambda pfad, **p: anfrage(f"{GRAPH}/{pfad}?" + urllib.parse.urlencode({**p, "access_token": TOKEN}))
k = q(nutzer, fields="username,followers_count,follows_count,media_count")
print(f"KONTO @{k.get('username')}: {k.get('followers_count')} Follower, {k.get('media_count')} Beiträge")
medien = q(f"{nutzer}/media", fields="id,caption,media_type,timestamp,like_count,comments_count,permalink", limit=30).get("data", [])
zeilen = []
for m in medien:
    werte = {}
    for metrik in ("views,reach,saved,shares,total_interactions", "ig_reels_avg_watch_time,ig_reels_video_view_total_time"):
        try:
            for d in q(f"{m['id']}/insights", metric=metrik).get("data", []):
                werte[d["name"]] = d["values"][0]["value"]
        except RuntimeError as e:
            werte.setdefault("fehler", str(e)[:120])
    titel = (m.get("caption") or "").split("\n")[0][:60]
    zeilen.append({"zeit": m["timestamp"][:16], "typ": m["media_type"], "titel": titel, "likes": m.get("like_count"),
                   "kommentare": m.get("comments_count"), **werte})
for z in zeilen:
    print(json.dumps(z, ensure_ascii=False))


# ------------------------------------------------------------------ YouTube
def youtube():
    from post_youtube import token
    import urllib.request
    kopf = {"Authorization": "Bearer " + token()}
    yt = lambda pfad, **p: json.load(urllib.request.urlopen(urllib.request.Request(
        "https://www.googleapis.com/youtube/v3/" + pfad + "?" + urllib.parse.urlencode(p), headers=kopf), timeout=60))
    kanal = yt("channels", part="statistics,contentDetails,snippet", mine="true")["items"][0]
    s = kanal["statistics"]
    print(f"YOUTUBE {kanal['snippet']['title']}: {s.get('subscriberCount')} Abos, {s.get('viewCount')} Aufrufe, {s.get('videoCount')} Videos")
    liste = kanal["contentDetails"]["relatedPlaylists"]["uploads"]
    ids = [i["contentDetails"]["videoId"] for i in yt("playlistItems", part="contentDetails", playlistId=liste, maxResults=50)["items"]]
    for v in yt("videos", part="snippet,statistics", id=",".join(ids))["items"]:
        st = v["statistics"]
        print("YT", json.dumps({"zeit": v["snippet"]["publishedAt"][:16], "titel": v["snippet"]["title"][:50],
                                "views": st.get("viewCount"), "likes": st.get("likeCount"), "kommentare": st.get("commentCount")}, ensure_ascii=False))


# ------------------------------------------------------------------ TikTok (Zernio)
def tiktok():
    import urllib.request
    kopf = {"Authorization": "Bearer " + os.environ["ZERNIO_API_KEY"]}
    for pfad in ("/analytics?platform=tiktok&limit=50", "/posts?platform=tiktok&status=published&limit=50"):
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request("https://zernio.com/api/v1" + pfad, headers=kopf), timeout=60))
        except Exception as e:
            print("TT", pfad, "ging nicht:", str(e)[:150]); continue
        posten = d.get("posts") or d.get("data") or d.get("analytics") or (d if isinstance(d, list) else [])
        print("TT", pfad, "Felder:", sorted(d.keys()) if isinstance(d, dict) else "liste", "Anzahl:", len(posten))
        for p in posten[:40]:
            a = {k: v for k, v in p.items() if k in ("publishedAt", "scheduledFor", "status", "analytics", "metrics", "stats")}
            for pl in p.get("platforms", []):
                a.update({k: pl[k] for k in ("analytics", "metrics", "status", "platformPostUrl") if k in pl})
            print("TT", json.dumps({"text": (p.get("content") or "")[:45], **a}, ensure_ascii=False)[:400])


for teil in (youtube, tiktok):
    try:
        teil()
    except Exception as e:
        print(teil.__name__, "ging nicht:", str(e)[:300])
