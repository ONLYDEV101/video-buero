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
