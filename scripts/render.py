# -*- coding: utf-8 -*-
"""Baut aus einer Episoden-Datei (episoden/*.json) ein Hochkant-Video 1080x1920.

    python scripts/render.py episoden/2026-11-22_beispiel.json [weitere.json ...]

Ablauf je Szene: Stimme (Piper -> espeak-ng -> Stille) -> Hintergrund (Pexels-Video
oder Farbverlauf) -> Untertitel einbrennen. Danach alle Szenen aneinanderhängen.
Ergebnis: out/<id>.mp4 und out/<id>.txt (Caption + Hashtags).
"""
import json, os, shutil, subprocess, sys, tempfile, textwrap, urllib.parse, urllib.request, wave

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASIS, "out")
W, H, FPS = 1080, 1920, 30
STIMMEN = {"de": "voices/de.onnx", "en": "voices/en.onnx"}
SCHRIFTEN = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]
VERLAEUFE = [("0x1b0f2e", "0x3a1d63"), ("0x0b2a3a", "0x0f6b6b"), ("0x2a0f14", "0x6b1f2e"), ("0x10202a", "0x2f4f6f")]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"Fehler bei {cmd[0]}: {r.stderr[-1500:]}")
    return r.stdout


def dauer(datei):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", datei]).strip())


# ------------------------------------------------------------------ Stimme
def stimme(text, sprache, ziel):
    modell = os.path.join(BASIS, STIMMEN.get(sprache, STIMMEN["en"]))
    if os.path.exists(modell):
        try:
            subprocess.run([sys.executable, "-m", "piper", "-m", modell, "-f", ziel], input=text, text=True,
                           capture_output=True, check=True, timeout=180)
            if os.path.getsize(ziel) > 1000:
                return "piper"
        except Exception as e:
            print("  Piper ging nicht:", str(e)[:200])
    if shutil.which("espeak-ng"):
        run(["espeak-ng", "-v", "de" if sprache == "de" else "en-us", "-s", "165", "-w", ziel, text])
        return "espeak"
    sek = max(2.5, len(text.split()) / 2.6)          # keine Stimme verfügbar: Stille in Lesedauer
    with wave.open(ziel, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050); w.writeframes(b"\0\0" * int(22050 * sek))
    return "stille"


# ------------------------------------------------------------------ Hintergrund
def pexels(suche, sek, ziel):
    key = os.environ.get("PEXELS_API_KEY")
    if not key or not suche:
        return False
    try:
        url = "https://api.pexels.com/videos/search?" + urllib.parse.urlencode({"query": suche, "orientation": "portrait", "per_page": 8})
        daten = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": key, "User-Agent": "video-buero"}), timeout=30))
        kandidaten = []
        for v in daten.get("videos", []):
            if v.get("duration", 0) < min(sek, 4):
                continue
            for f in v.get("video_files", []):
                if f.get("height") and f.get("width") and f["height"] > f["width"] and f["height"] >= 1280:
                    kandidaten.append((abs(f["height"] - 1920), f["link"]))
        if not kandidaten:
            return False
        kandidaten.sort()
        urllib.request.urlretrieve(kandidaten[0][1], ziel)
        return True
    except Exception as e:
        print("  Pexels ging nicht:", str(e)[:200])
        return False


def schrift():
    eigene = os.environ.get("SCHRIFT")
    for s in ([eigene] if eigene else []) + SCHRIFTEN:
        if s and os.path.exists(s):
            return s.replace("\\", "/").replace(":", "\\:")
    raise RuntimeError("Keine Schrift gefunden – Umgebungsvariable SCHRIFT setzen")


# ------------------------------------------------------------------ Szene
def szene(nr, sz, sprache, tmp, akzent):
    wav = os.path.join(tmp, f"s{nr}.wav")
    art = stimme(sz["text"], sprache, wav)
    sek = dauer(wav) + 0.35
    bg = os.path.join(tmp, f"bg{nr}.mp4")
    hat_video = pexels(sz.get("suche"), sek, bg)
    txt = os.path.join(tmp, f"t{nr}.txt")
    zeilen = textwrap.wrap(sz.get("einblendung") or sz["text"], 20)[:6]
    open(txt, "w", encoding="utf-8").write("\n".join(zeilen))
    f = schrift()
    tf = txt.replace("\\", "/").replace(":", "\\:")
    groesse = 74 if len(zeilen) <= 3 else 62
    text = (f"drawtext=fontfile='{f}':textfile='{tf}':fontsize={groesse}:fontcolor=white:line_spacing=8:text_align=C:"
            f"box=1:boxcolor=black@0.55:boxborderw=28:x=(w-text_w)/2:y=h*0.62-text_h/2:"
            f"alpha='if(lt(t,0.25),t/0.25,1)'")
    if hat_video:
        quelle = ["-stream_loop", "-1", "-i", bg]
        vf = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},eq=brightness=-0.06,{text}[v]"
    else:
        c0, c1 = VERLAEUFE[(nr + akzent) % len(VERLAEUFE)]
        quelle = ["-f", "lavfi", "-i", f"gradients=s={W}x{H}:c0={c0}:c1={c1}:speed=0.015:r={FPS}"]
        vf = f"[0:v]{text}[v]"
    ziel = os.path.join(tmp, f"szene{nr}.mp4")
    run(["ffmpeg", "-y", *quelle, "-i", wav, "-filter_complex", vf, "-map", "[v]", "-map", "1:a", "-t", f"{sek:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", str(FPS),
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-af", "apad", "-shortest", ziel])
    print(f"  Szene {nr + 1}: {sek:.1f}s, Stimme={art}, Hintergrund={'Pexels' if hat_video else 'Verlauf'}")
    return ziel


def episode(pfad):
    ep = json.load(open(pfad, encoding="utf-8"))
    eid = ep.get("id") or os.path.splitext(os.path.basename(pfad))[0]
    print(f"Episode {eid}: {ep.get('titel', '')}")
    os.makedirs(OUT, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        teile = [szene(i, sz, ep.get("sprache", "de"), tmp, hash(eid) % 4) for i, sz in enumerate(ep["szenen"])]
        liste = os.path.join(tmp, "liste.txt")
        open(liste, "w", encoding="utf-8").write("".join(f"file '{t.replace(chr(92), '/')}'\n" for t in teile))
        ziel = os.path.join(OUT, f"{eid}.mp4")
        run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", liste, "-c", "copy", "-movflags", "+faststart", ziel])
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
