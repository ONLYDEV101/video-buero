# -*- coding: utf-8 -*-
"""Stimmen für eine Cartoon-Folge erzeugen (Piper, kostenlos) + Lippen-Hüllkurve.

    python cartoon/tts.py cartoon/folgen/01_pizza.json build/01_pizza

Ergebnis: <ziel>/audio.wav und <ziel>/timeline.json
"""
import json, os, struct, subprocess, sys, wave, array, math

BASIS = os.path.dirname(os.path.abspath(__file__))
STIMMEN = os.path.join(os.path.dirname(BASIS), "voices")
FPS = 30
# Stimme je Figur: Modell, Sprecher (bei Mehrsprecher-Modellen), Tonhöhe, Tempo
FIGUREN = {
    "ronny": {"modell": "de_thorsten_emotional", "sprecher": "drunk", "pitch": 0.94, "tempo": 1.0},
    "mandy": {"modell": "de_kerstin", "sprecher": None, "pitch": 1.12, "tempo": 1.06},
    "kevin": {"modell": "de_karlsson", "sprecher": None, "pitch": 1.22, "tempo": 1.05},
    "erzaehler": {"modell": "de_thorsten", "sprecher": None, "pitch": 1.0, "tempo": 1.0},
}
RATE = 22050


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]}: {r.stderr.decode(errors='replace')[-800:]}")
    return r


# Edge-Neuralstimmen (STIMMEN_ENGINE=edge). Fällt bei Fehlern automatisch auf Piper zurück.
EDGE = {
    "ronny": {"stimme": "de-DE-ChristophNeural", "rate": "-6%", "pitch": "-14Hz", "filter": "lowpass=f=6500,acompressor=threshold=-20dB:ratio=3"},
    "mandy": {"stimme": "de-DE-TanjaNeural", "rate": "+10%", "pitch": "+22Hz", "filter": ""},
    "kevin": {"stimme": "de-DE-ChristophNeural", "rate": "+8%", "pitch": "+60Hz", "filter": ""},
    "erzaehler": {"stimme": "de-DE-ChristophNeural", "rate": "+0%", "pitch": "+0Hz", "filter": ""},
}
ENGINE = os.environ.get("STIMMEN_ENGINE", "piper")


def sprich_edge(text, fig, stimmung, ziel):
    e = EDGE[fig]
    rate = e["rate"]
    if stimmung == "angry": rate = f"{int(rate.rstrip('%')) + 8:+d}%"
    if stimmung == "drunk": rate = f"{int(rate.rstrip('%')) - 10:+d}%"
    mp3 = ziel + ".mp3"
    run([sys.executable, "-m", "edge_tts", "--voice", e["stimme"], f"--rate={rate}", f"--pitch={e['pitch']}", "--text", text, "--write-media", mp3], timeout=120)
    filt = ",".join(x for x in [e["filter"], "highpass=f=70", "loudnorm=I=-16:TP=-1.5"] if x)
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-af", filt, "-ac", "1", "-ar", str(RATE), ziel])
    os.remove(mp3)


def sprich(text, fig, stimmung, ziel):
    if ENGINE == "edge":
        try:
            return sprich_edge(text, fig, stimmung, ziel)
        except Exception as ex:
            print("Edge-TTS fehlgeschlagen, nehme Piper:", str(ex)[:200])
    cfg = FIGUREN[fig]
    modell = os.path.join(STIMMEN, cfg["modell"] + ".onnx")
    roh = ziel + ".roh.wav"
    cmd = [sys.executable, "-m", "piper", "-m", modell, "-f", roh]
    sprecher = stimmung or cfg["sprecher"]
    if sprecher:
        ids = json.load(open(modell + ".json", encoding="utf-8")).get("speaker_id_map", {})
        if sprecher in ids:
            cmd += ["--speaker", str(ids[sprecher])]
        elif cfg["sprecher"] in ids:
            cmd += ["--speaker", str(ids[cfg["sprecher"]])]
    run(cmd, input=text.encode("utf-8"), timeout=180)
    p, t = cfg["pitch"], cfg["tempo"]
    filt = f"asetrate={RATE}*{p},aresample={RATE},atempo={t / p:.4f},highpass=f=70,loudnorm=I=-16:TP=-1.5"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", roh, "-af", filt, "-ac", "1", "-ar", str(RATE), ziel])
    os.remove(roh)


def geraeusch(text, ziel):
    """Türklingel o. ä. synthetisch."""
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "sine=f=880:d=0.45", "-f", "lavfi", "-i", "sine=f=660:d=0.7",
         "-filter_complex", "[0]afade=t=out:st=0.3:d=0.15[a];[1]adelay=450,afade=t=out:st=0.5:d=0.6[b];[a][b]amix=2:normalize=0,volume=0.5",
         "-ac", "1", "-ar", str(RATE), ziel])


def lesen(datei):
    with wave.open(datei) as w:
        n = w.getnframes(); daten = array.array("h", w.readframes(n))
    return daten


def huelle(daten):
    """Lautstärke pro Videobild (0..1) für die Mundbewegung."""
    pro = RATE // FPS; werte = []
    for i in range(0, len(daten), pro):
        stueck = daten[i:i + pro]
        rms = math.sqrt(sum(x * x for x in stueck) / max(1, len(stueck))) / 32768
        werte.append(round(min(1.0, rms * 6), 3))
    return werte


def main(folge_datei, ziel):
    folge = json.load(open(folge_datei, encoding="utf-8"))
    os.makedirs(ziel, exist_ok=True)
    zeit, zeilen, gesamt = 0.6, [], array.array("h")
    gesamt.extend([0] * int(RATE * zeit))
    for i, z in enumerate(folge["zeilen"]):
        wav = os.path.join(ziel, f"z{i}.wav")
        if z["wer"] == "geraeusch":
            geraeusch(z["text"], wav)
        else:
            sprich(z["text"], z["wer"], z.get("stimmung"), wav)
        d = lesen(wav)
        dauer = len(d) / RATE
        zeilen.append({**z, "start": round(zeit, 3), "dauer": round(dauer, 3), "huelle": huelle(d)})
        pause = 0.25 if i < len(folge["zeilen"]) - 1 else 1.2
        gesamt.extend(d); gesamt.extend([0] * int(RATE * pause))
        zeit += dauer + pause
    with wave.open(os.path.join(ziel, "audio.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(gesamt.tobytes())
    tl = {**folge, "zeilen": zeilen, "dauer": round(zeit, 3), "fps": FPS}
    json.dump(tl, open(os.path.join(ziel, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{folge['id']}: {len(zeilen)} Zeilen, {zeit:.1f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
