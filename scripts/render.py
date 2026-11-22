# -*- coding: utf-8 -*-
"""Baut aus einer Episoden-Datei (episoden/*.json) ein virales Hochkant-Video 1080x1920.

    python scripts/render.py episoden/<datei>.json [weitere.json ...]

Stil: schnelle Schnitte (Pexels-Clips, alle ~2,5 s neu), dunkler Film-Look mit Körnung,
große Wort-für-Wort-Untertitel (Anton, Schlagwörter gelb – im Text mit *Wort* markieren),
Fortschrittsbalken oben, Label-Banner, düsterer Klangteppich mit Einschlägen bei Szenenwechseln.
Ergebnis: out/<id>.mp4 und out/<id>.txt (Caption + Hashtags).
"""
import json, math, os, random, re, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request, wave

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASIS, "out")
W, H, FPS = 1080, 1920, 30
SCHNITT = 2.6            # max. Sekunden pro Einstellung
PAUSE = 0.22             # Pause nach jeder Szene
STIMMEN = {"de": "voices/de.onnx", "en": "voices/en.onnx"}
GELB = "&H0000E6FF&"     # ASS-Farbe (BGR)
LOOK = ("eq=contrast=1.15:saturation=0.70:brightness=-0.06,colorbalance=rs=-0.04:bs=0.07:bm=0.03,"
        "vignette=PI/4.2,noise=alls=9:allf=t")


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"Fehler bei {cmd[0]}: {r.stderr[-2000:]}")
    return r.stdout


def dauer(datei):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", datei]).strip())


def sauber(text):
    return text.replace("*", "")


# ------------------------------------------------------------------ Stimme
_KOKORO = []


def kokoro(text, sprache, ziel, stimme_name, tempo):
    """Kokoro-82M (Apache 2.0): sehr natürliche Stimme, läuft auf CPU."""
    modell, stimmen = os.path.join(BASIS, "voices/kokoro.onnx"), os.path.join(BASIS, "voices/kokoro-voices.bin")
    if not (os.path.exists(modell) and os.path.exists(stimmen)):
        return False
    try:
        if not _KOKORO:
            from kokoro_onnx import Kokoro
            _KOKORO.append(Kokoro(modell, stimmen))
        import soundfile
        proben, rate = _KOKORO[0].create(text, voice=stimme_name, speed=tempo, lang="en-us" if sprache == "en" else sprache)
        soundfile.write(ziel, proben, rate)
        return os.path.getsize(ziel) > 1000
    except Exception as e:
        print("  Kokoro ging nicht:", str(e)[:300])
        return False


def stimme(text, sprache, ziel, tempo, stimme_name="am_michael"):
    if sprache == "en" and kokoro(text, sprache, ziel, stimme_name, 1.0 / tempo):
        return "kokoro"
    modell = os.path.join(BASIS, STIMMEN.get(sprache, STIMMEN["en"]))
    if os.path.exists(modell):
        for extra in (["--length-scale", str(tempo)], []):
            try:
                subprocess.run([sys.executable, "-m", "piper", "-m", modell, "-f", ziel, *extra], input=text, text=True,
                               capture_output=True, check=True, timeout=180)
                if os.path.getsize(ziel) > 1000:
                    return "piper"
            except Exception as e:
                print("  Piper ging nicht:", str(e)[:200])
    if shutil.which("espeak-ng"):
        run(["espeak-ng", "-v", "de" if sprache == "de" else "en-us", "-s", "170", "-w", ziel, text])
        return "espeak"
    sek = max(2.0, len(text.split()) / 2.8)
    with wave.open(ziel, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(b"\0\0" * int(22050 * sek))
    return "stille"


# ------------------------------------------------------------------ Pexels
class Pexels:
    def __init__(self, zufall):
        self.key = os.environ.get("PEXELS_API_KEY")
        self.cache, self.benutzt, self.zufall = {}, set(), zufall

    def suche(self, q):
        if q in self.cache:
            return self.cache[q]
        treffer = []
        if self.key:
            try:
                url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode(
                    {"query": q, "orientation": "portrait", "per_page": 15, "size": "medium"})
                daten = json.load(urllib.request.urlopen(urllib.request.Request(
                    url, headers={"Authorization": self.key, "User-Agent": "video-buero/2"}), timeout=30))
                for v in daten.get("videos", []):
                    dateien = [f for f in v.get("video_files", []) if f.get("width") and f.get("height")]
                    hoch = [f for f in dateien if f["height"] > f["width"] and 1280 <= f["height"] <= 2560]
                    wahl = sorted(hoch or [f for f in dateien if f["width"] >= 1080], key=lambda f: abs(f["height"] - 1920))
                    if wahl:
                        treffer.append((v["id"], wahl[0]["link"], float(v.get("duration") or 5)))
                self.zufall.shuffle(treffer)
                print(f"  Pexels '{q}': {len(treffer)} Clips")
            except Exception as e:
                print(f"  Pexels '{q}' ging nicht:", str(e)[:200])
        pix = os.environ.get("PIXABAY_API_KEY")
        if pix and len(treffer) < 4:
            try:
                url = "https://pixabay.com/api/videos/?" + urllib.parse.urlencode({"key": pix, "q": q, "per_page": 15, "safesearch": "true"})
                daten = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "video-buero/2"}), timeout=30))
                extra = []
                for v in daten.get("hits", []):
                    if re.search(r"green ?screen|chroma|blue ?screen|alpha", v.get("tags", ""), re.I):
                        continue
                    groessen = [f for f in v.get("videos", {}).values() if f.get("url") and f.get("width", 0) >= 960]
                    wahl = sorted(groessen, key=lambda f: abs(f["width"] - 1920))
                    if wahl:
                        extra.append(("pb%s" % v["id"], wahl[0]["url"], float(v.get("duration") or 5)))
                self.zufall.shuffle(extra)
                treffer += extra
                print(f"  Pixabay '{q}': {len(extra)} Clips")
            except Exception as e:
                print(f"  Pixabay '{q}' ging nicht:", str(e)[:200])
        self.cache[q] = treffer
        return treffer

    def clip(self, anfragen, ziel):
        for q in anfragen:
            for vid, link, lang in self.suche(q):
                if vid in self.benutzt:
                    continue
                self.benutzt.add(vid)
                try:
                    req = urllib.request.Request(link, headers={"User-Agent": "video-buero/2 (+https://github.com/ONLYDEV101/video-buero)"})
                    with urllib.request.urlopen(req, timeout=60) as r, open(ziel, "wb") as f:
                        shutil.copyfileobj(r, f)
                    return lang
                except Exception as e:
                    print("  Download ging nicht:", str(e)[:150])
        return None


# ------------------------------------------------------------------ Bild
def einstellung(nr, sek, anfragen, px, tmp, zufall):
    roh, ziel = os.path.join(tmp, f"roh{nr}.mp4"), os.path.join(tmp, f"e{nr}.mp4")
    lang = px.clip(anfragen, roh)
    richtung = ["(iw-ow)*t/{d}", "(iw-ow)*(1-t/{d})"][nr % 2].format(d=f"{sek:.3f}")
    bewegung = f"scale={int(W*1.1)}:{int(H*1.1)}:force_original_aspect_ratio=increase,crop={int(W*1.1)}:{int(H*1.1)},crop={W}:{H}:x='{richtung}':y='(ih-oh)/2'"
    if lang:
        start = zufall.uniform(0, max(0.0, lang - sek - 0.5))
        quelle = ["-ss", f"{start:.2f}", "-stream_loop", "-1", "-i", roh]
    else:
        farben = [("0x050608", "0x1a2230"), ("0x0a0505", "0x301414"), ("0x050a08", "0x14302a")][nr % 3]
        quelle = ["-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0={farben[0]}:c1={farben[1]}:speed=0.03:r={FPS}"]
    run(["ffmpeg", "-y", *quelle, "-t", f"{sek:.3f}", "-vf", f"{bewegung},fps={FPS},{LOOK},format=yuv420p",
         "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS), ziel])
    return ziel, bool(lang)


# ------------------------------------------------------------------ Untertitel
def zeit(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


def bloecke(text):
    """Text in Häppchen à 1–3 Wörter, Satzzeichen beenden ein Häppchen."""
    woerter, teile, akt = text.split(), [], []
    for w in woerter:
        akt.append(w)
        laenge = len(sauber(" ".join(akt)))
        if len(akt) >= 3 or laenge >= 13 or re.search(r"[.,!?:;…]$", w.rstrip("*\"'")):
            teile.append(akt); akt = []
    if akt:
        teile.append(akt)
    return teile


def ass_text(woerter):
    aus = []
    for w in woerter:
        roh = w.upper()
        if "*" in roh:
            aus.append("{\\c" + GELB + "}" + roh.replace("*", "") + "{\\c&H00FFFFFF&}")
        else:
            aus.append(roh)
    return " ".join(aus)


def untertitel(szenen, gesamt, label, ziel):
    zeilen = ["[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 0",
              "ScaledBorderAndShadow: yes", "", "[V4+ Styles]",
              "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
              "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
              "Style: Cap,Anton,140,&H00FFFFFF,&H00FFFFFF,&H00000000,&H99000000,0,0,0,0,100,100,1,0,1,8,5,5,70,70,0,1",
              "Style: Label,Anton,62,&H00FFFFFF,&H00FFFFFF,&H001A1AD8,&H00000000,0,0,0,0,100,100,3,0,3,16,0,8,40,40,0,1",
              "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    if label:
        zeilen.append(f"Dialogue: 1,{zeit(0)},{zeit(gesamt)},Label,,0,0,0,,{{\\an8\\pos(540,120)}}{label.upper()}")
    for start, sprech, text in szenen:
        text = re.sub(r"\*([^*]+)\*", lambda m: " ".join("*" + w + "*" for w in m.group(1).split()), text)
        teile = bloecke(text)
        gewicht = [len(sauber(" ".join(t))) + (5 if re.search(r"[.,!?:;…]", t[-1]) else 1) for t in teile]
        summe, t = sum(gewicht), start + 0.05
        for teil, g in zip(teile, gewicht):
            d = (sprech - 0.1) * g / summe
            pop = "{\\an5\\pos(540,1180)\\fscx78\\fscy78\\t(0,110,\\fscx104\\fscy104)\\t(110,180,\\fscx100\\fscy100)}"
            zeilen.append(f"Dialogue: 0,{zeit(t)},{zeit(t + d)},Cap,,0,0,0,,{pop}{ass_text(teil)}")
            t += d
    open(ziel, "w", encoding="utf-8").write("\n".join(zeilen) + "\n")


# ------------------------------------------------------------------ Ton
def klangteppich(gesamt, schlaege, ziel):
    d = f"{gesamt:.3f}"
    eingaenge = ["-f", "lavfi", "-i", f"anoisesrc=c=brown:a=0.6:d={d}:r=44100",
                 "-f", "lavfi", "-i", f"sine=f=55:d={d}:r=44100",
                 "-f", "lavfi", "-i", f"sine=f=58.3:d={d}:r=44100",
                 "-f", "lavfi", "-i", f"sine=f=110.5:d={d}:r=44100"]
    filt = ["[0]lowpass=f=260,volume=0.5[n]", "[1]volume=0.35[a]", "[2]volume=0.30[b]", "[3]volume=0.06,tremolo=f=0.4:d=0.8[c]"]
    mix = ["[n]", "[a]", "[b]", "[c]"]
    for i, s in enumerate(schlaege):
        eingaenge += ["-f", "lavfi", "-i", "sine=f=42:d=1.4:r=44100"]
        ms = int(s * 1000)
        filt.append(f"[{4 + i}]afade=t=out:st=0.02:d=1.35,volume=1.6,adelay={ms}|{ms}[h{i}]")
        mix.append(f"[h{i}]")
    filt.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0,afade=t=in:d=0.4,afade=t=out:st={max(0, gesamt - 0.8):.2f}:d=0.8,volume=0.5[m]")
    run(["ffmpeg", "-y", *eingaenge, "-filter_complex", ";".join(filt), "-map", "[m]", "-ac", "2", "-t", d, ziel])


# ------------------------------------------------------------------ Episode
def episode(pfad):
    ep = json.load(open(pfad, encoding="utf-8"))
    eid = ep.get("id") or os.path.splitext(os.path.basename(pfad))[0]
    sprache = ep.get("sprache", "en")
    print(f"Episode {eid}: {ep.get('titel', '')}")
    os.makedirs(OUT, exist_ok=True)
    zufall = random.Random(eid)
    px = Pexels(zufall)
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(os.path.join(BASIS, "fonts"), os.path.join(tmp, "fonts"))
        # 1) Stimme je Szene
        wavs, laengen, zeitplan, t = [], [], [], 0.0
        for i, sz in enumerate(ep["szenen"]):
            wav = os.path.join(tmp, f"s{i}.wav")
            art = stimme(sauber(sz["text"]), sprache, wav, ep.get("tempo", 0.92), ep.get("stimme", "am_michael"))
            sprech = dauer(wav)
            wavs.append(wav); laengen.append(sprech + PAUSE)
            zeitplan.append((t, sprech, sz["text"]))
            print(f"  Szene {i + 1}: {sprech:.1f}s Stimme={art}")
            t += sprech + PAUSE
        gesamt = t + 0.4
        # 2) Stimmen aneinander
        stimme_wav = os.path.join(tmp, "stimme.wav")
        ein = sum([["-i", w] for w in wavs], [])
        f = "".join(f"[{i}]aresample=44100,apad=whole_dur={l:.3f}[a{i}];" for i, l in enumerate(laengen))
        f += "".join(f"[a{i}]" for i in range(len(wavs))) + f"concat=n={len(wavs)}:v=0:a=1,apad=whole_dur={gesamt:.3f}[s]"
        run(["ffmpeg", "-y", *ein, "-filter_complex", f, "-map", "[s]", "-ac", "2", stimme_wav])
        # 3) Bilder: mehrere Einstellungen je Szene
        teile, nr, pex = [], 0, 0
        for i, sz in enumerate(ep["szenen"]):
            anfragen = sz.get("suche") or ep.get("suche_standard") or ["dark night"]
            anfragen = [anfragen] if isinstance(anfragen, str) else list(anfragen)
            laenge = laengen[i] + (0.4 if i == len(ep["szenen"]) - 1 else 0)
            n = max(1, math.ceil(laenge / SCHNITT))
            for j in range(n):
                folge = anfragen[j % len(anfragen):] + anfragen[:j % len(anfragen)]
                datei, echt = einstellung(nr, laenge / n, folge, px, tmp, zufall)
                teile.append(datei); nr += 1; pex += echt
        liste = os.path.join(tmp, "liste.txt")
        open(liste, "w", encoding="utf-8").write("".join(f"file '{os.path.basename(x)}'\n" for x in teile))
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "liste.txt", "-c", "copy", "bild.mp4"], cwd=tmp)
        print(f"  {nr} Einstellungen, davon {pex} echte Clips (Pexels/Pixabay)")
        # 4) Untertitel + Klang
        untertitel(zeitplan, gesamt, ep.get("label", ""), os.path.join(tmp, "caps.ass"))
        klangteppich(gesamt, [z[0] for z in zeitplan], os.path.join(tmp, "musik.wav"))
        # 5) Alles zusammen
        ziel = os.path.join(OUT, f"{eid}.mp4")
        filt = (f"[0:v][3:v]overlay=x='-W+W*t/{gesamt:.3f}':y=0,subtitles=caps.ass:fontsdir=fonts[v];"
                "[1:a]asplit=2[s1][s2];[2:a][s1]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350[m];"
                "[s2][m]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        run(["ffmpeg", "-y", "-i", "bild.mp4", "-i", "stimme.wav", "-i", "musik.wav",
             "-f", "lavfi", "-i", f"color=c=0xD81A1A:s={W}x12:r={FPS}:d={gesamt:.3f}",
             "-filter_complex", filt, "-map", "[v]", "-map", "[a]", "-t", f"{gesamt:.3f}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
             "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", ziel], cwd=tmp)
    caption = (ep.get("caption", "").strip() + "\n\n" + " ".join(ep.get("hashtags", []))).strip()
    open(os.path.join(OUT, f"{eid}.txt"), "w", encoding="utf-8").write(caption)
    print(f"  fertig: {ziel} ({dauer(ziel):.1f}s)")
    return ziel


if __name__ == "__main__":
    dateien = [a for a in sys.argv[1:] if a.endswith(".json")]
    if not dateien:
        sys.exit("Keine Episode angegeben")
    for d in dateien:
        episode(d)
