# -*- coding: utf-8 -*-
"""Baut aus fertigen Shorts ein langes Video (>3 Min., zählt bei YouTube für die Watch-Time).

    python scripts/kompilation.py "6 COLD WAR SECRETS" "THAT WERE TRUE" out/a.mp4 out/b.mp4 ... -o out/kompilation.mp4

Nur bauen, kein Upload.
"""
import os, subprocess, sys


def main():
    args = sys.argv[1:]
    ziel = args[args.index("-o") + 1] if "-o" in args else "out/kompilation.mp4"
    if "-o" in args:
        i = args.index("-o"); del args[i:i + 2]
    zeile1, zeile2, videos = args[0], args[1], args[2:]
    schrift = "fonts/Anton-Regular.ttf"
    intro = os.path.join(os.path.dirname(ziel) or ".", "intro.mp4")
    esc = lambda t: t.replace("'", "’").replace(":", "\\:")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=0x0b0b0b:s=1080x1920:d=3.5:r=30",
                    "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "3.5", "-vf",
                    f"drawtext=fontfile={schrift}:text='{esc(zeile1)}':fontsize=110:fontcolor=white:x=(w-tw)/2:y=760,"
                    f"drawtext=fontfile={schrift}:text='{esc(zeile2)}':fontsize=110:fontcolor=0xFFE500:x=(w-tw)/2:y=900,"
                    f"drawtext=fontfile={schrift}:text='DECLASSIFIED FILES':fontsize=48:fontcolor=white@0.7:x=(w-tw)/2:y=1080,"
                    "fade=t=in:d=0.4,fade=t=out:st=3.1:d=0.4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", intro], check=True)
    alle = [intro] + videos
    eing, filt = [], ""
    for n, v in enumerate(alle):
        eing += ["-i", v]
        filt += f"[{n}:v]scale=1080:1920,fps=30,format=yuv420p,setsar=1[v{n}];[{n}:a]aresample=44100,aformat=channel_layouts=stereo[a{n}];"
    filt += "".join(f"[v{n}][a{n}]" for n in range(len(alle))) + f"concat=n={len(alle)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *eing, "-filter_complex", filt, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-c:a", "aac", "-b:a", "160k", ziel], check=True)
    print("Kompilation:", ziel)


if __name__ == "__main__":
    main()
