# -*- coding: utf-8 -*-
"""Baut eine lange Doku (1920x1080) aus dokus/<datei>.json.

    python scripts/doku.py dokus/warteschlange/wirecard_en.json

JSON:
{ "id": "...", "sprache": "en", "stimme": "en-US-AndrewMultilingualNeural", "rate": "-4%",
  "titel": "...", "beschreibung": "...", "tags": [...], "quellen": [...],
  "abschnitte": [
     {"kapitel": "CHAPTER 1", "untertitel": "The Rise"},
     {"text": "Gesprochener Absatz ...", "bilder": [
         {"archiv": "File:....jpg", "hinweis": "Real photo, 2018"},
         {"suche": ["stock term", "other term"]},
         {"karte": "€1.9 BILLION", "unter": "that never existed"},
         {"zitat": "Text eines Dokuments", "quelle": "EY, 18 June 2020"} ]} ] }
"""
import asyncio, json, os, random, re, shutil, sys, tempfile, textwrap, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import run, dauer, gruenschirm, klangteppich  # noqa: E402

W, H, FPS = 1920, 1080, 30
BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANTON = os.path.join(BASIS, "fonts", "Anton-Regular.ttf").replace("\\", "/")
MONO = next((p for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "C:/Windows/Fonts/consola.ttf") if os.path.exists(p)), ANTON)
GELB, PAPIER = "0xFFE500", "0xE9E4D6"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]


def pfad(p):
    return "'" + p.replace("\\", "/").replace(":", "\\:") + "'"


def textdatei(tmp, name, text):
    p = os.path.join(tmp, name)
    open(p, "w", encoding="utf-8").write(text)
    return pfad(p)


# ------------------------------------------------------------------ Stimme (Edge, wie Probe Nr. 6)
def sprechen(text, stimme, rate, ziel):
    import edge_tts
    mp3 = ziel[:-4] + ".mp3"
    for versuch in range(4):
        try:
            asyncio.run(edge_tts.Communicate(text, stimme, rate=rate).save(mp3))
            break
        except Exception as e:
            print("  Stimme Versuch", versuch + 1, "ging nicht:", str(e)[:150])
            if versuch == 3:
                raise
    run(["ffmpeg", "-y", "-i", mp3, "-ar", "44100", "-ac", "2", ziel])


# ------------------------------------------------------------------ Stockclips (Querformat)
class Stock:
    def __init__(self, zufall):
        self.zufall, self.benutzt, self.cache = zufall, set(), {}

    def suche(self, q):
        if q in self.cache:
            return self.cache[q]
        treffer = []
        key = os.environ.get("PEXELS_API_KEY")
        if key:
            try:
                url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": q, "orientation": "landscape", "per_page": 15})
                d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "video-buero/2"}), timeout=30))
                for v in d.get("videos", []):
                    f = sorted([f for f in v.get("video_files", []) if f.get("width", 0) >= 1280 and f.get("height", 0) < f.get("width", 0)],
                               key=lambda f: abs(f["width"] - 1920))
                    if f:
                        treffer.append((v["id"], f[0]["link"]))
            except Exception as e:
                print(f"  Pexels '{q}':", str(e)[:120])
        pix = os.environ.get("PIXABAY_API_KEY")
        if pix and len(treffer) < 4:
            try:
                url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": pix, "q": q, "per_page": 20, "safesearch": "true", "video_type": "film"})
                d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "video-buero/2"}), timeout=30))
                for v in d.get("hits", []):
                    if re.search(r"cartoon|animat|illustration|infographic|green ?screen|chroma|fantasy|anime", v.get("tags", "").lower()):
                        continue
                    g = sorted([f for f in v.get("videos", {}).values() if f.get("url") and f.get("width", 0) >= 1280], key=lambda f: abs(f["width"] - 1920))
                    if g:
                        treffer.append(("pb%s" % v["id"], g[0]["url"]))
            except Exception as e:
                print(f"  Pixabay '{q}':", str(e)[:120])
        self.zufall.shuffle(treffer)
        self.cache[q] = treffer
        return treffer

    def clip(self, anfragen, ziel):
        for q in anfragen:
            for vid, link in self.suche(q):
                if vid in self.benutzt:
                    continue
                self.benutzt.add(vid)
                try:
                    with urllib.request.urlopen(urllib.request.Request(link, headers={"User-Agent": "video-buero/2"}), timeout=90) as r, open(ziel, "wb") as f:
                        shutil.copyfileobj(r, f)
                    if not gruenschirm(ziel):
                        return True
                except Exception as e:
                    print("  Clip-Download:", str(e)[:120])
        return False


# ------------------------------------------------------------------ Fotos (gemeinfrei, CC0, CC BY, CC BY-SA mit Namensnennung)
def bild_laden(titel, ziel):
    kopf = {"User-Agent": "video-buero/2 (automated video tool)"}
    try:
        url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
            "action": "query", "format": "json", "titles": titel, "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1920})
        seite = next(iter(json.load(urllib.request.urlopen(urllib.request.Request(url, headers=kopf), timeout=30))["query"]["pages"].values()))
        info = seite["imageinfo"][0]
        m = info["extmetadata"]
        lizenz = m.get("LicenseShortName", {}).get("value", "").strip()
        if not re.match(r"(public domain|cc0|pd|cc by(-sa)? [234])", lizenz.lower()):
            print(f"  Foto abgelehnt ({lizenz}): {titel}")
            return None
        with urllib.request.urlopen(urllib.request.Request(info.get("thumburl") or info["url"], headers=kopf), timeout=60) as r, open(ziel, "wb") as f:
            shutil.copyfileobj(r, f)
        autor = re.sub(r"<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip()[:60] or "unknown"
        print(f"  Foto: {titel} ({lizenz}, {autor})")
        return "" if re.match(r"(public domain|cc0|pd)", lizenz.lower()) else f"{titel[5:]} by {autor} ({lizenz}), Wikimedia Commons"
    except Exception as e:
        print(f"  Foto ging nicht: {titel}: {str(e)[:150]}")
        return None


# ------------------------------------------------------------------ Einstellungen
def e_clip(datei, sek, ziel):
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", datei, "-t", f"{sek:.3f}", "-vf",
         f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},eq=brightness=-0.06:saturation=0.85:contrast=1.05,"
         f"vignette=PI/5,fps={FPS},fade=t=in:d=0.3", *ENC, ziel])


def e_foto(foto, sek, hinweis, nr, tmp, ziel):
    z = f"(1+0.07*t/{sek:.3f})" if nr % 2 else f"(1.07-0.07*t/{sek:.3f})"
    filt = (f"[0:v]format=yuv420p,split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:2,"
            f"eq=brightness=-0.25:saturation=0.4[h];[b]scale=1400:860:force_original_aspect_ratio=decrease,pad=iw+28:ih+28:14:14:{PAPIER},"
            f"scale=w='trunc(iw*{z}/2)*2':h='trunc(ih*{z}/2)*2':eval=frame[f];[h][f]overlay=x='(W-w)/2':y='(H-h)/2-10',vignette=PI/5")
    if hinweis:
        filt += (f",drawtext=fontfile={pfad(ANTON)}:textfile={textdatei(tmp, f'h{nr}.txt', hinweis.upper())}:fontsize=34:fontcolor=black:"
                 f"box=1:boxcolor={GELB}:boxborderw=12:x=80:y=h-110")
    filt += f",fps={FPS},fade=t=in:d=0.3[v]"
    run(["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-i", foto, "-filter_complex", filt, "-map", "[v]", "-t", f"{sek:.3f}", *ENC, ziel])


def e_karte(gross, klein, sek, nr, tmp, ziel, farbe=GELB):
    filt = (f"noise=alls=8:allf=t,vignette=PI/4,drawtext=fontfile={pfad(ANTON)}:textfile={textdatei(tmp, f'g{nr}.txt', gross.upper())}:"
            f"fontsize=150:fontcolor={farbe}:x=(w-tw)/2:y=(h-th)/2-60:alpha='min(1,t/0.5)'")
    if klein:
        filt += (f",drawtext=fontfile={pfad(ANTON)}:textfile={textdatei(tmp, f'k{nr}.txt', klein.upper())}:fontsize=54:fontcolor=white:"
                 f"x=(w-tw)/2:y=(h/2)+70:alpha='min(1,max(0,(t-0.5)/0.5))'")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0c0c0c:s={W}x{H}:r={FPS}:d={sek:.3f}", "-vf", filt, *ENC, ziel])


def e_zitat(text, quelle, sek, nr, tmp, ziel):
    zeilen = "\n".join(textwrap.wrap(text, 44))
    filt = (f"drawbox=x=260:y=120:w=1400:h=840:color={PAPIER}:t=fill,noise=alls=6:allf=t,"
            f"drawtext=fontfile={pfad(MONO)}:textfile={textdatei(tmp, f'z{nr}.txt', zeilen)}:fontsize=46:line_spacing=10:fontcolor=0x1a1a1a:"
            f"x=340:y=220:alpha='min(1,t/0.6)'")
    if quelle:
        filt += (f",drawtext=fontfile={pfad(ANTON)}:textfile={textdatei(tmp, f'q{nr}.txt', '— ' + quelle.upper())}:fontsize=40:fontcolor=0xB00000:"
                 f"x=340:y=860")
    filt += ",vignette=PI/5"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x151515:s={W}x{H}:r={FPS}:d={sek:.3f}", "-vf", filt, *ENC, ziel])


def e_kapitel(titel, unter, sek, nr, tmp, ziel):
    filt = (f"drawbox=x=(iw-160)/2:y=430:w=160:h=8:color=0xD01010:t=fill,"
            f"drawtext=fontfile={pfad(ANTON)}:textfile={textdatei(tmp, f'c{nr}.txt', titel.upper())}:fontsize=64:fontcolor=0xD01010:x=(w-tw)/2:y=330,"
            f"drawtext=fontfile={pfad(ANTON)}:textfile={textdatei(tmp, f'u{nr}.txt', (unter or '').upper())}:fontsize=120:fontcolor=white:"
            f"x=(w-tw)/2:y=480:alpha='min(1,t/0.6)',fade=t=out:st={sek - 0.4:.2f}:d=0.4")
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={sek:.3f}", "-vf", filt, *ENC, ziel])


# ------------------------------------------------------------------ Doku
def doku(pfad_json):
    d = json.load(open(pfad_json, encoding="utf-8"))
    did = d["id"]
    zufall = random.Random(did)
    stock = Stock(zufall)
    stimme, rate = d.get("stimme", "en-US-AndrewMultilingualNeural"), d.get("rate", "-4%")
    os.makedirs("out", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        teile, sprache, t, schlaege, nr, credits = [], [], 0.0, [], 0, []
        for i, ab in enumerate(d["abschnitte"]):
            if "kapitel" in ab:
                sek = 3.2
                ziel = os.path.join(tmp, f"v{nr:04d}.mp4"); nr += 1
                e_kapitel(ab["kapitel"], ab.get("untertitel", ""), sek, nr, tmp, ziel)
                teile.append(ziel); schlaege.append(t)
                stille = os.path.join(tmp, f"a{i}.wav")
                run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", f"{sek:.3f}", stille])
                sprache.append(stille); t += sek
                continue
            wav = os.path.join(tmp, f"a{i}.wav")
            sprechen(re.sub(r"\*", "", ab["text"]), stimme, rate, wav)
            laenge = dauer(wav) + 0.45
            gepolstert = os.path.join(tmp, f"p{i}.wav")
            run(["ffmpeg", "-y", "-i", wav, "-af", f"apad=whole_dur={laenge:.3f}", gepolstert])
            sprache.append(gepolstert)
            bilder = ab.get("bilder") or [{"suche": ["dark city night"]}]
            stueck = laenge / len(bilder)
            for b in bilder:
                ziel = os.path.join(tmp, f"v{nr:04d}.mp4"); nr += 1
                ok = False
                if "archiv" in b:
                    foto = os.path.join(tmp, f"f{nr}.img")
                    nachweis = bild_laden(b["archiv"], foto)
                    if nachweis is not None:
                        if nachweis and nachweis not in credits:
                            credits.append(nachweis)
                        e_foto(foto, stueck, b.get("hinweis", ""), nr, tmp, ziel); ok = True
                elif "karte" in b:
                    e_karte(b["karte"], b.get("unter", ""), stueck, nr, tmp, ziel); ok = True
                elif "zitat" in b:
                    e_zitat(b["zitat"], b.get("quelle", ""), stueck, nr, tmp, ziel); ok = True
                if not ok:
                    roh = os.path.join(tmp, f"r{nr}.mp4")
                    if stock.clip(b.get("suche") or ab.get("suche") or ["dark office night", "city skyline night"], roh):
                        e_clip(roh, stueck, ziel)
                    else:
                        e_karte("", "", stueck, nr, tmp, ziel)
                teile.append(ziel)
            t += laenge
            print(f"  Abschnitt {i + 1}/{len(d['abschnitte'])}: {laenge:.1f} s, {len(bilder)} Bilder")
        liste = os.path.join(tmp, "liste.txt")
        open(liste, "w").write("".join(f"file '{p.replace(os.sep, '/')}'\n" for p in teile))
        bild = os.path.join(tmp, "bild.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", bild])
        sl = os.path.join(tmp, "sprache.txt")
        open(sl, "w").write("".join(f"file '{p.replace(os.sep, '/')}'\n" for p in sprache))
        stimme_wav = os.path.join(tmp, "stimme.wav")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", sl, "-c:a", "pcm_s16le", stimme_wav])
        gesamt = dauer(stimme_wav)
        musik = os.path.join(tmp, "musik.wav")
        klangteppich(gesamt, schlaege, musik)
        ziel = os.path.join("out", f"{did}.mp4")
        run(["ffmpeg", "-y", "-i", bild, "-i", stimme_wav, "-i", musik, "-filter_complex",
             "[2:a]volume=0.55[m];[1:a][m]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-16:TP=-1.5[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", ziel])
        beschreibung = d.get("beschreibung", "") + "\n\nSources:\n" + "\n".join("- " + q for q in d.get("quellen", []))
        beschreibung += "\n\n" + d.get("hinweis", "AI voice. Footage: Pexels/Pixabay. Archive images: Wikimedia Commons (public domain/CC0).")
        if credits:
            beschreibung += "\nPhoto credits: " + "; ".join(credits)
        beschreibung += "\n" + " ".join(d.get("hashtags", []))
        open(os.path.join("out", f"{did}.txt"), "w", encoding="utf-8").write(d["titel"] + "\n\n" + beschreibung)
        print(f"Fertig: {ziel} ({gesamt / 60:.1f} Min., {len(teile)} Einstellungen)")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        doku(p)
