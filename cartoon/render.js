// Rendert eine Cartoon-Folge: Bühne im Headless-Chrome Bild für Bild -> ffmpeg (+ Ton) -> MP4.
//   node cartoon/render.js build/01_pizza out/01_pizza.mp4 [nur-standbild-sekunde]
const puppeteer = require("puppeteer-core");
const path = require("path"), fs = require("fs"), { spawn } = require("child_process");
const CHROME = process.env.CHROME || ["/usr/bin/google-chrome", "C:/Program Files/Google/Chrome/Application/chrome.exe"].find(p => fs.existsSync(p));

(async () => {
  const [ordner, ziel, standbild] = process.argv.slice(2);
  const tl = JSON.parse(fs.readFileSync(path.join(ordner, "timeline.json"), "utf8"));
  const b = await puppeteer.launch({ executablePath: CHROME, headless: "new", args: ["--no-sandbox", "--allow-file-access-from-files"] });
  const p = await b.newPage();
  await p.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await p.goto("file://" + path.resolve(__dirname, "buehne.html").split(path.sep).join("/").replace(/^([A-Z]):/, "/$1:"));
  await p.evaluate(t => { window.TL = t; }, tl);
  await p.evaluate(() => document.fonts.load("70px Anton").then(() => document.fonts.ready));
  if (standbild !== undefined) {
    for (const s of standbild.split(",")) { await p.evaluate(t => zeichne(t), +s); await p.screenshot({ path: `${ziel}_${s}.png` }); }
    await b.close(); return;
  }
  const frames = Math.ceil(tl.dauer * tl.fps);
  const ff = spawn("ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(tl.fps), "-i", "-",
    "-i", path.join(ordner, "audio.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", ziel], { stdio: ["pipe", "inherit", "inherit"] });
  for (let f = 0; f < frames; f++) {
    await p.evaluate(t => zeichne(t), f / tl.fps);
    const buf = await p.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
    if (f % 150 === 0) console.log(`  Bild ${f}/${frames}`);
  }
  ff.stdin.end();
  await new Promise((r, e) => ff.on("close", c => c === 0 ? r() : e(new Error("ffmpeg " + c))));
  await b.close();
  console.log("fertig:", ziel);
})();
