/* Ronny & Mandy – Cartoon-Bühne v2. zeichne(t) malt das Bild zum Zeitpunkt t (Sekunden).
 * Timeline (window.TL) aus tts.py: zeilen[{wer,text,aktion,start,dauer,huelle}], figuren, ort, titel, dauer, fps.
 * v2: Cel-Shading, weiche Konturen, Kamera-Schnitte (Totale/Nah/Groß), Licht & Vignette,
 *     detailreiche Räume, Mimik je Stimmung, Karaoke-Untertitel.
 */
"use strict";
const C = document.getElementById("c"), X = C.getContext("2d");
const W = 1080, H = 1920, BODEN = 1470, OUT = "#1d1426";
let T = 0, SEED = 0, nJ = 0;

// ---------------------------------------------------------------- Grundwerkzeuge
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; }
const j = (amp = 1.6) => (hash(SEED, nJ++) - .5) * 2 * amp;
const fest = (i) => hash(9173, i);               // zeitlich stabile Zufallswerte (Deko)
const mix = (a, b, t) => a + (b - a) * t;
const ease = t => t < .5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2;

function pfad(p, zu, rund) {
  X.beginPath();
  if (!rund || p.length < 3) { p.forEach(([x, y], i) => i ? X.lineTo(x, y) : X.moveTo(x, y)); if (zu) X.closePath(); return; }
  if (zu) {
    const m = (a, b) => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], n = p.length, s = m(p[n - 1], p[0]);
    X.moveTo(s[0], s[1]);
    for (let i = 0; i < n; i++) { const q = m(p[i], p[(i + 1) % n]); X.quadraticCurveTo(p[i][0], p[i][1], q[0], q[1]); }
    X.closePath();
  } else {
    X.moveTo(p[0][0], p[0][1]);
    for (let i = 1; i < p.length - 1; i++) { const q = [(p[i][0] + p[i + 1][0]) / 2, (p[i][1] + p[i + 1][1]) / 2]; X.quadraticCurveTo(p[i][0], p[i][1], q[0], q[1]); }
    X.lineTo(p[p.length - 1][0], p[p.length - 1][1]);
  }
}
function schattieren(p, seite = 1, stark = .24) {
  const xs = p.map(q => q[0]), ys = p.map(q => q[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  X.save(); X.clip();
  const g = X.createLinearGradient(seite > 0 ? x0 : x1, 0, seite > 0 ? x1 : x0, 0);
  g.addColorStop(0, "rgba(255,250,230,.16)"); g.addColorStop(.3, "rgba(255,250,230,0)");
  g.addColorStop(.6, "rgba(60,20,80,0)"); g.addColorStop(.66, `rgba(60,20,80,${stark})`); g.addColorStop(1, `rgba(60,20,80,${stark + .06})`);
  X.fillStyle = g; X.fillRect(x0 - 2, y0 - 2, x1 - x0 + 4, y1 - y0 + 4);
  X.restore();
}
// Form: gefüllt, optional cel-schattiert, weiche Kontur
function form(pts, fuell, o = {}) {
  const { breite = 7, farbe = OUT, amp = 1.6, rund = true, schatten = true, zu = true } = o;
  const p = pts.map(([x, y]) => [x + j(amp), y + j(amp)]);
  pfad(p, zu, rund);
  if (fuell) { X.fillStyle = fuell; X.fill(); if (schatten && zu) schattieren(p, o.seite || 1, o.stark ?? .24); pfad(p, zu, rund); }
  if (breite) { X.lineWidth = breite; X.strokeStyle = farbe; X.lineJoin = X.lineCap = "round"; X.stroke(); }
}
const strich = (pts, farbe = OUT, breite = 7, amp = 1.4) => form(pts, null, { farbe, breite, amp, zu: false });
function kreisPts(cx, cy, rx, ry, n = 18, rot = 0) { const p = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2 + rot; p.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); } return p; }
const oval = (cx, cy, rx, ry, fuell, o = {}) => form(kreisPts(cx, cy, rx, ry, o.n || 18), fuell, { amp: 1.2, ...o });
function eck(x, y, w, h, fuell, o = {}) { form([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], fuell, { rund: false, ...o }); }
function kurve(x1, y1, cx, cy, x2, y2, farbe = OUT, breite = 7) { const p = []; for (let i = 0; i <= 10; i++) { const t = i / 10; p.push([(1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2]); } strich(p, farbe, breite, .8); }
function text(s, x, y, groesse, farbe = "#fff", rand = OUT, align = "center", font = "Anton") {
  X.font = `${groesse}px ${font}, Impact, sans-serif`; X.textAlign = align; X.textBaseline = "middle";
  X.lineWidth = groesse * .22; X.strokeStyle = rand; X.lineJoin = "round"; X.strokeText(s, x, y); X.fillStyle = farbe; X.fillText(s, x, y);
}
function weicherSchatten(x, y, rx, ry, a = .35) {
  const g = X.createRadialGradient(x, y, 0, x, y, rx); g.addColorStop(0, `rgba(20,5,30,${a})`); g.addColorStop(1, "rgba(20,5,30,0)");
  X.save(); X.translate(x, y); X.scale(1, ry / rx); X.translate(-x, -y); X.fillStyle = g; X.beginPath(); X.arc(x, y, rx, 0, 7); X.fill(); X.restore();
}

// ---------------------------------------------------------------- Requisiten
function dose(x, y, rot = 0, s = 1, farbe = "#2e8b3d") {
  X.save(); X.translate(x, y); X.rotate(rot); X.scale(s, s);
  eck(-26, -55, 52, 110, "#c9d3da", { breite: 6 }); eck(-26, -24, 52, 46, farbe, { breite: 0, schatten: false });
  strich([[-26, -24], [26, -24]], OUT, 4); strich([[-26, 22], [26, 22]], OUT, 4);
  text("B", 0, -1, 30, "#ffe14a", OUT); X.fillStyle = "rgba(255,255,255,.5)"; X.fillRect(-16, -50, 7, 98);
  X.restore();
}
function flasche(x, y, farbe = "#2f6b2a", etikett = "SEKT") {
  form([[x - 22, y + 60], [x - 22, y - 10], [x - 9, y - 42], [x - 9, y - 80], [x + 9, y - 80], [x + 9, y - 42], [x + 22, y - 10], [x + 22, y + 60]], farbe, { breite: 6, rund: false });
  eck(x - 12, y - 94, 24, 16, "#e6c04a", { breite: 4 }); eck(x - 20, y + 5, 40, 34, "#f3ead0", { breite: 4, schatten: false });
  X.fillStyle = "rgba(255,255,255,.35)"; X.fillRect(x - 15, y - 5, 6, 60);
}
function pizzakarton(x, y, n = 3, s = 1) {
  for (let i = 0; i < n; i++) { const yy = y - i * 34 * s, d = (fest(i + x) - .5) * 18; form([[x - 120 * s + d, yy], [x + 120 * s + d, yy], [x + 120 * s + d, yy - 30 * s], [x - 120 * s + d, yy - 30 * s]], "#d9b27a", { breite: 5, rund: false }); }
  text("PIZZA", x, y - (n - 1) * 34 * s - 15 * s, 22 * s, "#c8312b", "#d9b27a");
}

// ---------------------------------------------------------------- Räume
function licht(x0, y0, breite, farbe = "255,236,170") { // Lichtkegel vom Fenster
  X.save(); X.globalCompositeOperation = "lighter";
  const g = X.createLinearGradient(x0, y0, x0 - 260, BODEN + 120); g.addColorStop(0, `rgba(${farbe},.20)`); g.addColorStop(1, `rgba(${farbe},0)`);
  X.fillStyle = g; X.beginPath(); X.moveTo(x0, y0); X.lineTo(x0 + breite, y0); X.lineTo(x0 + breite - 380, BODEN + 120); X.lineTo(x0 - 420, BODEN + 120); X.closePath(); X.fill();
  for (let i = 0; i < 18; i++) { // Staubkörner
    const px = x0 - 300 + fest(i) * (breite + 300) + Math.sin(T * .6 + i) * 20, py = y0 + 80 + ((fest(i + 50) * 900 + T * 18) % 900);
    X.fillStyle = `rgba(255,250,220,${.25 + .25 * Math.sin(T * 2 + i)})`; X.beginPath(); X.arc(px, py, 2.5 + fest(i + 9) * 2.5, 0, 7); X.fill();
  }
  X.restore();
}
function boden(farbe1, farbe2, fugen) {
  const g = X.createLinearGradient(0, BODEN - 260, 0, H); g.addColorStop(0, farbe1); g.addColorStop(1, farbe2);
  X.fillStyle = g; X.fillRect(0, BODEN - 260, W, H);
  X.strokeStyle = fugen; X.lineWidth = 4;
  for (let i = -6; i < 14; i++) { X.beginPath(); X.moveTo(W / 2 + i * 70, BODEN - 260); X.lineTo(W / 2 + i * 230, H); X.stroke(); }
  for (let y = BODEN - 200, k = 0; y < H; y += 60 + k * 18, k++) { X.globalAlpha = .5; X.beginPath(); X.moveTo(0, y); X.lineTo(W, y); X.stroke(); X.globalAlpha = 1; }
  strich([[0, BODEN - 260], [W, BODEN - 260]], OUT, 8);
  eck(0, BODEN - 290, W, 30, "#efe6cf", { breite: 5 }); // Fußleiste
}
function wohnzimmer() {
  const g = X.createLinearGradient(0, 0, 0, BODEN - 260); g.addColorStop(0, "#c9b07a"); g.addColorStop(1, "#e3cf98");
  X.fillStyle = g; X.fillRect(0, 0, W, BODEN);
  for (let x = 20; x < W; x += 72) { X.fillStyle = "rgba(150,110,50,.13)"; X.fillRect(x, 0, 26, BODEN - 260); }
  X.fillStyle = "rgba(120,90,40,.18)"; X.beginPath(); X.ellipse(170, 760, 60, 34, .3, 0, 7); X.fill(); // Fleck an der Wand
  // Deckenlampe
  const sw = Math.sin(T * 1.3) * .05;
  X.save(); X.translate(540, 0); X.rotate(sw); strich([[0, 0], [0, 230]], OUT, 5); form([[-80, 300], [80, 300], [40, 225], [-40, 225]], "#e86a3a", { breite: 6 }); oval(0, 305, 22, 14, "#fff7c0", { breite: 4, schatten: false }); X.restore();
  // Fenster + Gardinen
  eck(640, 440, 330, 320, "#8fd0ff", { breite: 8, schatten: false });
  const himmel = X.createLinearGradient(0, 440, 0, 760); himmel.addColorStop(0, "#6ec2ff"); himmel.addColorStop(1, "#d8f0ff"); X.fillStyle = himmel; X.fillRect(646, 446, 318, 308);
  oval(720, 520, 50, 22, "#fff", { breite: 0, schatten: false }); oval(880, 600, 60, 24, "#fff", { breite: 0, schatten: false });
  form([[640, 690], [700, 640], [760, 700], [830, 620], [900, 690], [970, 650], [970, 760], [640, 760]], "#6c8a5a", { breite: 0, schatten: false }); // Plattenbauten
  for (let i = 0; i < 6; i++) eck(660 + i * 50, 700, 18, 22, "#ffe58a", { breite: 0, schatten: false });
  strich([[805, 440], [805, 760]], OUT, 7); strich([[640, 600], [970, 600]], OUT, 7); eck(630, 760, 350, 24, "#f2ead6", { breite: 6 });
  strich([[610, 420], [1000, 420]], OUT, 9);
  form([[618, 424], [705, 424], [690, 700], [712, 800], [630, 815]], "#f4e7c4", { breite: 5, seite: -1 });
  form([[992, 424], [905, 424], [920, 700], [898, 800], [985, 815]], "#f4e7c4", { breite: 5 });
  // Poster + Regal
  form([[90, 420], [330, 400], [342, 640], [100, 656]], "#ff8f3c", { breite: 6, rund: false });
  text("MALLE", 216, 495, 72, "#fff"); text("2009", 220, 588, 58, "#ffe14a");
  eck(80, 820, 290, 22, "#8a5a36", { breite: 5 });
  form([[130, 820], [120, 760], [180, 760], [170, 820]], "#e8c04a", { breite: 5 }); oval(150, 745, 30, 18, "#e8c04a", { breite: 5 }); text("NR.1", 150, 790, 22, "#fff");
  dose(260, 787, 0, .55, "#c8312b"); dose(320, 787, .1, .55);
  // Fernseher (flackert)
  eck(20, 1000, 230, 190, "#3a3a44", { breite: 7 });
  const fl = .55 + .45 * Math.abs(Math.sin(T * 7) * Math.sin(T * 2.3));
  X.fillStyle = `rgba(120,190,255,${fl})`; X.fillRect(38, 1018, 194, 140);
  eck(60, 1190, 150, 18, "#3a3a44", { breite: 5 });
  boden("#9a6440", "#6e4129", "rgba(50,25,10,.35)");
  // Teppich, Sofa
  oval(540, BODEN + 40, 500, 82, "#a8343c", { breite: 6, seite: 1, stark: .18 });
  oval(540, BODEN + 40, 430, 60, null, { breite: 4, farbe: "#e0a23c" });
  weicherSchatten(540, BODEN - 175, 520, 50, .3);
  form([[70, BODEN - 450], [1010, BODEN - 450], [1020, BODEN - 210], [60, BODEN - 210]], "#6b4f8a", { breite: 8 });
  form([[100, BODEN - 330], [980, BODEN - 330], [990, BODEN - 200], [90, BODEN - 200]], "#5d4379", { breite: 7 });
  oval(820, BODEN - 380, 40, 22, "#f1ead2", { breite: 5, schatten: false }); // Loch mit Füllung
  form([[40, BODEN - 360], [150, BODEN - 372], [155, BODEN - 175], [35, BODEN - 175]], "#55396f", { breite: 8 });
  form([[930, BODEN - 372], [1040, BODEN - 360], [1045, BODEN - 175], [925, BODEN - 175]], "#55396f", { breite: 8 });
  licht(700, 445, 270);
  // Kram auf dem Boden
  pizzakarton(880, BODEN + 110, 3, .8);
  [[150, BODEN + 70, 8], [300, BODEN + 120, -70], [700, BODEN + 130, 85]].forEach(([x, y, r], i) => dose(x, y, r * Math.PI / 180, .75, i === 1 ? "#c8312b" : "#2e8b3d"));
  oval(420, BODEN + 125, 40, 14, "#9aa", { breite: 4 }); // Aschenbecher
}
function kueche() {
  const g = X.createLinearGradient(0, 0, 0, BODEN); g.addColorStop(0, "#d8d2bd"); g.addColorStop(1, "#efe9d6"); X.fillStyle = g; X.fillRect(0, 0, W, BODEN);
  // Fliesenspiegel
  for (let y = 760; y < BODEN - 400; y += 64) for (let x = 0; x < W; x += 64) { X.fillStyle = (x / 64 + y / 64) % 2 ? "#cfe3e0" : "#bcd6d2"; X.fillRect(x, y, 62, 62); }
  // Oberschränke
  for (let i = 0; i < 2; i++) { eck(40 + i * 210, 330, 200, 300, "#e9c98f", { breite: 7 }); oval(200 + i * 210, 590, 10, 10, "#9a8", { breite: 4, schatten: false }); }
  // Kühlschrank
  eck(790, 420, 240, 840, "#f4f4f4", { breite: 8 }); strich([[790, 700], [1030, 700]], OUT, 6);
  strich([[820, 500], [820, 640]], OUT, 9); strich([[820, 760], [820, 900]], OUT, 9);
  eck(870, 760, 80, 64, "#ffe14a", { breite: 4 }); text("BIER!", 910, 792, 22, "#c8312b", "#ffe14a");
  oval(980, 520, 16, 16, "#ff5fa8", { breite: 4, schatten: false }); oval(940, 470, 14, 14, "#7ec8ff", { breite: 4, schatten: false });
  // Fenster
  eck(90, 700, 280, 0, null, { breite: 0 });
  // Arbeitsplatte + Spüle mit Geschirrberg
  eck(0, BODEN - 520, 780, 36, "#9c9c9c", { breite: 7 }); eck(0, BODEN - 484, 780, 230, "#e9c98f", { breite: 7 });
  for (let i = 0; i < 4; i++) strich([[190 + i * 190, BODEN - 470], [190 + i * 190, BODEN - 270]], OUT, 5);
  for (let i = 0; i < 6; i++) oval(330 + (i % 3) * 18, BODEN - 540 - i * 16, 70, 12, i % 2 ? "#fff" : "#f0e0c0", { breite: 4, schatten: false });
  oval(150, BODEN - 560, 34, 40, "#d23", { breite: 5 }); strich([[150, BODEN - 600], [160, BODEN - 640]], OUT, 5); // Kaffeekanne rot
  // Kalender
  eck(470, 380, 140, 170, "#fff", { breite: 5 }); eck(470, 380, 140, 40, "#c8312b", { breite: 5, schatten: false }); text("HARTZ", 540, 400, 22, "#fff", "#c8312b");
  for (let i = 0; i < 9; i++) { X.fillStyle = "#555"; X.fillRect(484 + (i % 3) * 42, 440 + ((i / 3) | 0) * 34, 24, 18); }
  boden("#8d8d8d", "#5f5f5f", "rgba(40,40,40,.4)");
  for (let y = BODEN - 260; y < H; y += 90) for (let x = ((y / 90) % 2) * 45; x < W; x += 90) { X.fillStyle = "rgba(255,255,255,.06)"; X.fillRect(x, y, 45, 45); }
  // Tisch
  weicherSchatten(540, BODEN - 40, 330, 30, .35);
  form([[250, BODEN - 140], [830, BODEN - 140], [810, BODEN - 88], [270, BODEN - 88]], "#b57a45", { breite: 7 });
  strich([[300, BODEN - 88], [300, BODEN]], OUT, 12); strich([[780, BODEN - 88], [780, BODEN]], OUT, 12);
  flasche(690, BODEN - 200); dose(380, BODEN - 195, 0, .7); pizzakarton(520, BODEN - 142, 2, .7);
  licht(860, 430, 90, "255,255,235");
}
function balkon() {
  const g = X.createLinearGradient(0, 0, 0, BODEN); g.addColorStop(0, "#4b6fb5"); g.addColorStop(.6, "#f0a26a"); g.addColorStop(1, "#ffd08a"); X.fillStyle = g; X.fillRect(0, 0, W, BODEN);
  oval(780, 560, 110, 110, "#fff1a8", { breite: 0, schatten: false });
  for (let i = 0; i < 7; i++) { const hx = i * 160 - 20, hh = 380 + fest(i) * 300; eck(hx, BODEN - 300 - hh, 150, hh, "#6b6f8a", { breite: 6 }); for (let k = 0; k < 10; k++) if (fest(i * 20 + k) > .45) eck(hx + 20 + (k % 3) * 42, BODEN - 260 - hh + 40 + ((k / 3) | 0) * 70, 22, 30, "#ffe58a", { breite: 0, schatten: false }); }
  boden("#a9a39a", "#7a756c", "rgba(40,40,40,.3)");
  for (let x = 20; x < W; x += 60) strich([[x, BODEN - 480], [x, BODEN - 260]], OUT, 6);
  eck(0, BODEN - 500, W, 26, "#d0d0d0", { breite: 6 });
  form([[880, BODEN - 40], [1000, BODEN - 40], [990, BODEN + 60], [890, BODEN + 60]], "#3b8f4a", { breite: 6 }); // Bierkasten
  for (let i = 0; i < 3; i++) flasche(905 + i * 40, BODEN - 70, "#6b3d14", "");
}
const ORTE = { wohnzimmer, kueche, balkon };

// ---------------------------------------------------------------- Figuren
const FIG = {
  ronny: { haut: "#f1bf8c", hemd: "#f7f5ea", hose: "#8a8a95", name: "RONNY", farbe: "#ffe14a", s: 1.0 },
  mandy: { haut: "#e9a978", hemd: "#ff5fa8", hose: "#24202b", name: "MANDY", farbe: "#ff7cc0", s: .95 },
  kevin: { haut: "#efc7a0", hemd: "#3b6fd8", hose: "#2a2a3a", name: "KEVIN", farbe: "#7ec8ff", s: .8 },
};
function hand(x, y, haut, r = 26, nagel = null) {
  oval(x, y, r, r * .9, haut, { breite: 6, stark: .2 });
  strich([[x - r * .2, y - r * .5], [x - r * .2, y + r * .1]], OUT, 3); strich([[x + r * .2, y - r * .5], [x + r * .2, y + r * .1]], OUT, 3);
  if (nagel) for (let i = -1; i <= 1; i++) oval(x + i * r * .4, y - r * .75, 5, 7, nagel, { breite: 2, schatten: false });
}
function figur(id, x, blick, z) {
  const f = FIG[id], s = f.s, sp = z.spricht, akt = z.aktion, mund = z.mund;
  const wackel = sp && akt === "schreit" ? 6 : 0;
  // Sprech-Rhythmus: leichtes Wippen & Stauchen
  const bob = sp ? Math.abs(Math.sin(T * 9)) * mund * 10 : 0;
  const stauch = 1 + (sp ? mund * .025 : 0);
  weicherSchatten(x, BODEN + 10, 190 * s, 34 * s, .4);
  X.save(); X.translate(x + j(wackel), BODEN + j(wackel)); X.scale(s * (z.flip ? -1 : 1), s / stauch); X.scale(1, stauch * stauch);
  const atem = Math.sin(T * 2.2 + x) * 5 - bob;
  const kopfY = -585 + atem, kopfR = 108;
  const L = blick >= 0 ? 1 : -1; // Lichtseite folgt nicht dem Blick; Schatten immer rechts
  // --- Beine & Schuhe
  const hb = id === "ronny" ? 66 : 50;
  [-1, 1].forEach(sd => {
    form([[sd * hb - 34, -250], [sd * hb + 34, -250], [sd * hb + 30, -10], [sd * hb - 30, -10]], f.hose, { breite: 7, rund: false });
    if (id === "ronny") { strich([[sd * (hb + 31), -240], [sd * (hb + 29), -20]], "#fff", 6); }
    if (id === "ronny") { eck(sd * hb - 30, -30, 60, 26, "#fff", { breite: 5, schatten: false }); oval(sd * (hb + 14), 6, 54, 20, "#2b5fd8", { breite: 6 }); } // Socken + Latschen
    else if (id === "mandy") { form([[sd * hb - 40, -90], [sd * hb + 36, -90], [sd * hb + 50, 14], [sd * hb - 44, 14]], "#d9b48a", { breite: 6 }); } // Fellboots
    else oval(sd * (hb + 12), 4, 52, 22, "#f2f2f2", { breite: 6 });
  });
  // --- Körper
  if (id === "ronny") {
    form([[-150, -250], [150, -250], [140, -170], [-140, -170]], f.hose, { breite: 7, rund: false }); // Bund (unter dem Bauch)
    form([[-118, -480 + atem], [118, -480 + atem], [190, -330], [175, -205], [-175, -205], [-190, -330]], f.hemd, { breite: 8 }); // Feinripp
    for (let i = -4; i <= 4; i++) strich([[i * 34, -455 + atem], [i * 40, -215]], "rgba(0,0,0,.08)", 3, .5);
    oval(50, -300, 28, 18, "#e2c46a", { breite: 0, schatten: false }); oval(-70, -380, 15, 10, "#d6b95a", { breite: 0, schatten: false }); oval(-20, -250, 10, 7, "#c87a5a", { breite: 0, schatten: false });
    form([[-118, -480 + atem], [-60, -480 + atem], [-70, -400], [-112, -410]], f.haut, { breite: 6 }); form([[118, -480 + atem], [60, -480 + atem], [70, -400], [112, -410]], f.haut, { breite: 6 });
    kurve(-55, -470 + atem, 0, -420 + atem, 55, -470 + atem, "#e0b13c", 6); // Goldkette
    oval(0, -425 + atem, 12, 14, "#e0b13c", { breite: 4, schatten: false });
  } else if (id === "mandy") {
    form([[-86, -480 + atem], [86, -480 + atem], [100, -340], [-100, -340]], f.hemd, { breite: 8 });
    form([[-100, -340], [100, -340], [86, -222], [-86, -222]], f.haut, { breite: 8 });
    oval(0, -290, 7, 9, "#7a3a2a", { breite: 3, schatten: false }); // Bauchnabel-Piercing
    oval(0, -272, 6, 6, "#e0e0e0", { breite: 2, schatten: false });
    text("QUEEN", 0, -410 + atem, 44, "#fff", "#c21a6a");
    form([[-90, -230], [90, -230], [86, -200], [-86, -200]], f.hose, { breite: 6, rund: false });
  } else {
    form([[-120, -480 + atem], [120, -480 + atem], [138, -210], [-138, -210]], f.hemd, { breite: 8 });
    form([[-55, -330], [55, -330], [48, -262], [-48, -262]], "#2a52a8", { breite: 5 });
    strich([[-30, -480 + atem], [-26, -400]], "#ddd", 5); strich([[30, -480 + atem], [26, -400]], "#ddd", 5);
  }
  // --- Arme
  const sx = id === "ronny" ? 140 : 100, sy = -448 + atem;
  const armFarbe = id === "kevin" ? f.hemd : f.haut;
  const arm = (seite, hx, hy) => {
    const ex = seite * sx + (hx - seite * sx) * .5 + seite * 22, ey = sy + (hy - sy) * .5 + 24;
    strich([[seite * sx, sy], [ex, ey], [hx, hy]], OUT, 44, .6); strich([[seite * sx, sy], [ex, ey], [hx, hy]], armFarbe, 31, .6);
    if (id === "ronny") for (let k = 0; k < 4; k++) strich([[ex + j(14) - 6, ey + j(14)], [ex + j(14) + 4, ey + j(14) - 8]], "#6b4a2a", 2, .3); // Armhaare
    hand(hx, hy, f.haut, 27, id === "mandy" ? "#ff3b8f" : null);
  };
  const sw = Math.sin(T * 3 + x) * 10;
  let links = [-sx - 34, -255 + sw], rechts = [sx + 34, -255 - sw];
  let inHand = id === "ronny" ? "dose" : id === "mandy" ? "handy" : null, kopfNeig = 0;
  if (sp && akt === "trinkt") { rechts = [72, kopfY + 72]; inHand = "dose"; kopfNeig = -.2; }
  else if (id === "ronny") rechts = [sx + 44, -305 - sw];
  else if (id === "mandy") rechts = [sx + 30, -300 - sw];
  if (sp && akt === "zeigt") rechts = [sx + 240, sy - 50 + Math.sin(T * 9) * 12];
  if (sp && akt === "schreit") { links = [-sx - 95, sy - 230 + j(9)]; rechts = [sx + 95, sy - 230 + j(9)]; inHand = null; }
  if (z.schock) { links = [-64, kopfY + 66]; rechts = [64, kopfY + 66]; inHand = null; }
  arm(-1, links[0], links[1]); arm(1, rechts[0], rechts[1]);
  if (inHand === "dose") dose(rechts[0] + 6, rechts[1] - 32, sp && akt === "trinkt" ? -2.3 : .15, .9);
  if (inHand === "handy") { X.save(); X.translate(rechts[0] + 4, rechts[1] - 40); X.rotate(.2); eck(-22, -40, 44, 78, "#222", { breite: 5, schatten: false }); X.fillStyle = `rgba(140,200,255,${.6 + .3 * Math.sin(T * 5)})`; X.fillRect(-15, -32, 30, 58); X.restore(); }
  // --- Hals & Kopf
  form([[-36, kopfY + 80], [36, kopfY + 80], [42, sy + 8], [-42, sy + 8]], f.haut, { breite: 6 });
  X.save(); X.translate(0, kopfY); X.rotate(kopfNeig + (sp ? Math.sin(T * 7) * .035 : Math.sin(T * .9 + x) * .02));
  const rot = sp && akt === "schreit";
  // Hinterkopf-Haare
  if (id === "mandy") {
    form([[-kopfR - 6, 10], [-kopfR + 4, -kopfR * .8], [0, -kopfR - 22], [kopfR - 4, -kopfR * .8], [kopfR + 6, 10], [kopfR - 10, 70], [-kopfR + 10, 70]], "#f6d36a", { breite: 7 });
    oval(0, -kopfR - 52, 62, 54, "#f6d36a", { breite: 7 }); oval(0, -kopfR - 52, 30, 26, "#8a6a2a", { breite: 0, schatten: false }); // Dutt mit Ansatz
    for (let i = 0; i < 4; i++) strich([[-40 + i * 26, -kopfR - 88], [-30 + i * 22, -kopfR - 20]], "#d6a83a", 4);
  }
  // Ohren
  oval(-kopfR + 4, 10, 22, 30, rot ? "#ff8f7a" : f.haut, { breite: 6, schatten: false }); oval(kopfR - 4, 10, 22, 30, rot ? "#ff8f7a" : f.haut, { breite: 6 });
  // Gesicht
  form(id === "ronny" ? [[-kopfR, -20], [-kopfR + 14, -kopfR + 4], [0, -kopfR - 10], [kopfR - 14, -kopfR + 4], [kopfR, -20], [kopfR - 4, 70], [50, kopfR + 18], [-50, kopfR + 18], [-kopfR + 4, 70]]
                      : kreisPts(0, 0, kopfR, kopfR * 1.05, 18), rot ? "#ff8a74" : f.haut, { breite: 8, stark: .2 });
  if (rot) { X.fillStyle = "rgba(255,40,40,.25)"; X.beginPath(); X.arc(0, 0, kopfR, 0, 7); X.fill(); }
  if (id === "ronny") {
    X.fillStyle = "rgba(255,255,255,.45)"; X.beginPath(); X.ellipse(-30, -kopfR + 26, 34, 14, -.3, 0, 7); X.fill(); // Glatzenglanz
    form([[-kopfR - 4, 20], [-kopfR + 8, -50], [-kopfR + 46, -78], [-kopfR + 30, -30], [-kopfR + 12, 30]], "#5a3b1e", { breite: 5, schatten: false });
    form([[kopfR + 4, 20], [kopfR - 8, -50], [kopfR - 46, -78], [kopfR - 30, -30], [kopfR - 12, 30]], "#5a3b1e", { breite: 5, schatten: false });
    strich([[-14, -kopfR - 6], [-4, -kopfR - 36]], "#5a3b1e", 5); strich([[12, -kopfR - 6], [24, -kopfR - 30]], "#5a3b1e", 5);
    for (let i = 0; i < 22; i++) { const a = .25 + i * .12; X.fillStyle = "rgba(70,50,35,.75)"; X.fillRect(Math.cos(a) * 78 + j(1.5), Math.sin(a) * 74 + 14 + j(1.5), 4, 4); }
  }
  if (id === "mandy") { // Pony-Strähnen + Kreolen
    form([[-kopfR + 4, -30], [-60, -kopfR + 4], [10, -kopfR - 8], [-20, -60]], "#f6d36a", { breite: 6, schatten: false });
    oval(-kopfR - 2, 64, 22, 30, null, { breite: 6, farbe: "#e3b23c" }); oval(kopfR + 2, 64, 22, 30, null, { breite: 6, farbe: "#e3b23c" });
    X.fillStyle = "rgba(255,90,120,.28)"; X.beginPath(); X.arc(-58, 36, 22, 0, 7); X.arc(58, 36, 22, 0, 7); X.fill(); // Rouge
  }
  if (id === "kevin") {
    form([[-kopfR, -26], [-kopfR + 8, -kopfR + 6], [kopfR - 8, -kopfR + 6], [kopfR, -26]], "#d83b3b", { breite: 7 });
    form([[-kopfR + 10, -60], [-kopfR - 76, -50], [-kopfR - 70, -28], [-kopfR, -34]], "#b82424", { breite: 6 });
    for (let i = 0; i < 5; i++) oval(-50 + fest(i) * 100, 40 + fest(i + 7) * 40, 5, 5, "#e0705a", { breite: 0, schatten: false }); // Pickel
  }
  // Augen
  const blinzel = ((T + x * .013) % 3.6) < .12 && !z.schock;
  const genuss = sp && akt === "trinkt";
  const ag = z.schock ? 32 : id === "ronny" ? 21 : 25;
  const bx = blick * 8 + Math.sin(T * .7 + x) * 2;
  [-40, 40].forEach((ax, i) => {
    if (blinzel || genuss) { kurve(ax - 22, -20, ax, genuss ? -8 : -14, ax + 22, -20, OUT, 6); return; }
    oval(ax, -20, ag + 6, ag + 11, "#fff", { breite: 6, schatten: false });
    oval(ax + bx, -15, 11, 12, "#3a2a1a", { breite: 0, schatten: false }); oval(ax + bx, -15, 6, 7, "#111", { breite: 0, schatten: false });
    X.fillStyle = "#fff"; X.beginPath(); X.arc(ax + bx + 4, -20, 3.5, 0, 7); X.fill();
    if (id === "ronny" && !z.schock && !rot) form([[ax - 29, -50], [ax + 29, -50], [ax + 29, -30 + (i ? -4 : 4)], [ax - 29, -30 + (i ? 4 : -4)]], f.haut, { breite: 6, rund: false, schatten: false }); // schwere Lider
    if (id === "ronny") kurve(ax - 20, 12, ax, 22, ax + 20, 12, "rgba(90,50,40,.6)", 4); // Tränensäcke
    if (id === "mandy") { strich([[ax - 26, -38], [ax - 38, -52]], OUT, 5); strich([[ax - 6, -44], [ax - 8, -62]], OUT, 5); strich([[ax + 16, -42], [ax + 26, -58]], OUT, 5); strich([[ax - 28, -32], [ax + 30, -38]], OUT, 6); }
  });
  // Augenbrauen nach Stimmung
  const br = (ax, s1, s2) => strich([[ax - 28, s1], [ax + 28, s2]], id === "mandy" ? "#8a6a2a" : "#4a2f18", 9);
  if (rot) { br(-40, -72, -50); br(40, -50, -72); }
  else if (z.schock) { br(-40, -82, -90); br(40, -90, -82); }
  else if (sp && akt === "zeigt") { br(-40, -66, -62); br(40, -76, -86); }
  else { br(-40, -64 + (sp ? -mund * 6 : 0), -66); br(40, -66, -64 + (sp ? -mund * 6 : 0)); }
  // Nase
  kurve(6, -10, 34, 26, 0, 32, OUT, 6);
  if (id === "ronny") oval(10, 22, 22, 15, "#f08a7a", { breite: 0, schatten: false });
  // Mund (Lippensync)
  const my = 66, offen = Math.min(1, mund * 1.6);
  if (id === "ronny") form([[-52, 40], [-16, 30], [16, 30], [52, 40], [40, 50], [-40, 50]], "#5a3b1e", { breite: 0, schatten: false }); // Schnauzer
  if (offen > .08) {
    const mw = 22 + offen * 24, mh = 6 + offen * (rot ? 48 : 34);
    oval(0, my, mw, mh, "#5a0f1a", { breite: 6, schatten: false });
    X.save(); X.beginPath(); X.ellipse(0, my, mw - 3, mh - 3, 0, 0, 7); X.clip();
    X.fillStyle = "#fff"; X.fillRect(-mw, my - mh, mw * 2, mh * .45); if (id === "ronny") { X.fillStyle = "#5a0f1a"; X.fillRect(6, my - mh, 12, mh * .45); } // Zahnlücke
    X.fillStyle = "#ff6f7f"; X.beginPath(); X.ellipse(0, my + mh * .7, mw * .6, mh * .45, 0, 0, 7); X.fill(); X.restore();
  } else if (z.schock) oval(0, my, 16, 24, "#5a0f1a", { breite: 6, schatten: false });
  else if (genuss) kurve(-30, my, 0, my + 22, 30, my, OUT, 6);
  else kurve(-30, my, 0, my + (id === "ronny" ? 12 : 10), 30, my - 6, id === "mandy" ? "#d0103a" : OUT, id === "mandy" ? 10 : 6);
  if (z.schock) form([[kopfR - 8, -64], [kopfR + 8, -30], [kopfR - 18, -30]], "#a8dcff", { breite: 4, farbe: "#3a8ad8", schatten: false });
  X.restore();
  if (rot) { text("!", kopfR + 70, kopfY - 120, 120, "#ff3b3b"); text("!", kopfR + 130, kopfY - 75, 84, "#ff3b3b"); }
  if (genuss && (T * 4 | 0) % 2) text("gluck", 0, kopfY - 200, 48, "#fff");
  X.restore();
}

// ---------------------------------------------------------------- Zeitachse
function aktuelleZeile(t) { return TL.zeilen.find(z => t >= z.start && t < z.start + z.dauer + .25) || null; }
function mundWert(id, t) {
  const z = TL.zeilen.find(z => z.wer === id && t >= z.start && t < z.start + z.dauer);
  if (!z) return 0; const i = Math.floor((t - z.start) * TL.fps); return z.huelle[Math.min(i, z.huelle.length - 1)] || 0;
}
// Kamera-Einstellung je Zeile: Totale, Nah (Kopf + Oberkörper) oder Groß (Gesicht)
function einstellung(idx, zeile) {
  if (!zeile || zeile.wer === "geraeusch" || idx === 0) return "total";
  if (zeile.aktion === "schreit" || zeile.aktion === "schock") return "gross";
  return idx % 3 === 2 ? "total" : "nah";
}

function zeichne(t) {
  T = t; SEED = Math.floor(t * 6); nJ = 0;
  const z = aktuelleZeile(t), idx = z ? TL.zeilen.indexOf(z) : -1;
  const figs = TL.figuren, pos = figs.length === 2 ? [300, 780] : [175, 520, 890];
  const si = z ? figs.indexOf(z.wer) : -1;
  // Kamera
  const art = einstellung(idx, z);
  let zoom = 1, fx = W / 2, fy = H / 2;
  if (si >= 0 && art !== "total") {
    const kopf = BODEN + (-585) * FIG[z.wer].s;
    zoom = art === "gross" ? 1.9 : 1.5; fx = pos[si]; fy = kopf - ((art === "gross" ? 820 : 760) - H / 2) / zoom;
  }
  const p = z ? Math.min(1, (t - z.start) / Math.max(1, z.dauer)) : 0;
  zoom *= 1 + .035 * ease(p);                                  // langsames Heranfahren
  const hw = W / 2 / zoom, hh = H / 2 / zoom;
  fx = Math.max(hw, Math.min(W - hw, fx)); fy = Math.max(hh, Math.min(H - hh, fy));
  X.save(); X.translate(W / 2, H / 2); X.scale(zoom, zoom); X.translate(-fx, -fy);
  if (z && (z.aktion === "schreit" || z.wer === "geraeusch")) X.translate(j(7), j(7));
  (ORTE[TL.ort] || wohnzimmer)();
  figs.forEach((id, i) => {
    const andere = si >= 0 && si !== i ? pos[si] : pos[i === 0 ? 1 : 0];
    const spricht = !!(z && z.wer === id);
    figur(id, pos[i], Math.sign(andere - pos[i]), { spricht, aktion: spricht ? z.aktion : null, mund: mundWert(id, t), schock: spricht && z.aktion === "schock", flip: false });
  });
  X.restore();
  if (z && z.wer === "geraeusch") { const k = 1 + Math.sin(t * 30) * .04; X.save(); X.translate(W / 2, 700); X.scale(k, k); X.rotate(-.06); text(z.text.replace(/\*/g, ""), 0, 0, 150, "#ffe14a", "#c21a6a"); X.restore(); }
  // Farbe & Vignette (Bildschirmraum)
  X.save(); X.globalCompositeOperation = "multiply"; X.fillStyle = "rgba(255,236,215,1)"; X.fillRect(0, 0, W, H); X.restore();
  const v = X.createRadialGradient(W / 2, H * .48, H * .3, W / 2, H * .5, H * .78); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(15,5,25,.55)");
  X.fillStyle = v; X.fillRect(0, 0, W, H);
  // Schnitt-Blitz beim Einstellungswechsel
  if (z && t - z.start < .06 && idx > 0) { X.fillStyle = "rgba(255,255,255,.18)"; X.fillRect(0, 0, W, H); }
  // Titel-Plakette
  const fr = t < .7 ? 1 + (1 - t / .7) * .5 : 1;
  X.save(); X.translate(W / 2, 128); X.scale(fr, fr); X.rotate(-.035);
  X.fillStyle = "rgba(20,8,30,.78)"; X.beginPath(); X.roundRect(-330, -78, 660, 156, 34); X.fill();
  text("RONNY & MANDY", 0, -14, 96, "#ffe14a", "#c21a6a"); X.restore();
  text(TL.titel.toUpperCase(), W / 2, 238, 50, "#fff", OUT);
  // Karaoke-Untertitel
  if (z && z.wer !== "geraeusch") {
    const f = FIG[z.wer], woerter = z.text.split(" "), zeilen = []; let akt = [];
    woerter.forEach(w => { if ((akt.join(" ") + " " + w).trim().length > 22) { zeilen.push(akt); akt = [w]; } else akt.push(w); }); zeilen.push(akt);
    const sicht = zeilen.slice(0, 3), boxH = 92 + sicht.length * 84, y0 = 1890 - boxH;
    X.fillStyle = "rgba(20,8,30,.80)"; X.beginPath(); X.roundRect(50, y0, W - 100, boxH, 36); X.fill();
    X.fillStyle = f.farbe; X.beginPath(); X.roundRect(W / 2 - 110, y0 - 30, 220, 62, 30); X.fill();
    text(f.name, W / 2, y0 + 1, 44, "#1d1426", f.farbe);
    const gesamt = woerter.reduce((a, w) => a + w.length + 2, 0), fort = (t - z.start) / Math.max(.3, z.dauer) * gesamt;
    let lauf = 0;
    sicht.forEach((zl, zi) => {
      X.font = "72px Anton, Impact, sans-serif"; const breiten = zl.map(w => X.measureText(w + " ").width), ges = breiten.reduce((a, b) => a + b, 0);
      let xx = W / 2 - ges / 2;
      zl.forEach((w, wi) => {
        const an = lauf, aus = lauf + w.length + 2; lauf = aus;
        const farbe = fort >= aus ? "#ffffff" : fort >= an ? "#ffe14a" : "rgba(255,255,255,.55)";
        const gr = fort >= an && fort < aus ? 78 : 72;
        text(w, xx + breiten[wi] / 2 - X.measureText(" ").width / 2, y0 + 98 + zi * 84, gr, farbe, "#000");
        X.font = "72px Anton, Impact, sans-serif";
        xx += breiten[wi];
      });
    });
  }
  // Ende
  if (t > TL.dauer - 1.2) { X.fillStyle = "rgba(20,8,30,.6)"; X.fillRect(0, 0, W, H); const k = 1 + Math.sin(t * 8) * .03; X.save(); X.translate(W / 2, 880); X.scale(k, k); text("FOLGEN FÜR MEHR", 0, 0, 112, "#ffe14a", "#c21a6a"); X.restore(); text("RONNY & MANDY", W / 2, 1010, 72, "#fff"); }
}
window.zeichne = zeichne;
