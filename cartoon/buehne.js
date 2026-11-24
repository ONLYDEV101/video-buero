/* Ronny & Mandy – krakelige Cartoon-Bühne. zeichne(t) malt das Bild zum Zeitpunkt t (Sekunden).
 * Die Timeline (window.TL) kommt aus tts.py: Zeilen mit start, dauer, huelle (Lautstärke pro Bild).
 */
"use strict";
const C = document.getElementById("c"), X = C.getContext("2d");
const W = 1080, H = 1920, BODEN = 1430;
let T = 0, SEED = 0;

// ---------- Wackel-Linien (Handzeichnungs-Look)
function hash(a, b) { let h = (a * 374761393 + b * 668265263) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; }
let nJ = 0;
const j = (amp = 3) => (hash(SEED, nJ++) - .5) * 2 * amp;
function linie(pts, farbe = "#111", breite = 7, fuell = null, zu = false, amp = 2.4) {
  X.beginPath();
  pts.forEach(([x, y], i) => { const px = x + j(amp), py = y + j(amp); i ? X.lineTo(px, py) : X.moveTo(px, py); });
  if (zu) X.closePath();
  if (fuell) { X.fillStyle = fuell; X.fill(); }
  if (breite) { X.lineWidth = breite; X.strokeStyle = farbe; X.lineJoin = X.lineCap = "round"; X.stroke(); }
}
function kreisPts(cx, cy, rx, ry, n = 22, rot = 0) {
  const p = []; for (let i = 0; i < n; i++) { const a = i / n * Math.PI * 2 + rot; p.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); } return p;
}
function ellipse(cx, cy, rx, ry, fuell, breite = 7, farbe = "#111") { linie(kreisPts(cx, cy, rx, ry), farbe, breite, fuell, true); }
function rechteck(x, y, w, h, fuell, breite = 6) { linie([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], "#111", breite, fuell, true); }
function kurve(x1, y1, cx, cy, x2, y2, farbe = "#111", breite = 7) {
  const p = []; for (let i = 0; i <= 10; i++) { const t = i / 10; p.push([(1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t * t * x2, (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t * t * y2]); }
  linie(p, farbe, breite);
}
function text(s, x, y, groesse, farbe = "#fff", rand = "#111", align = "center", font = "Anton") {
  X.font = `${groesse}px ${font}, Impact, sans-serif`; X.textAlign = align; X.textBaseline = "middle";
  X.lineWidth = groesse * .22; X.strokeStyle = rand; X.lineJoin = "round"; X.strokeText(s, x, y); X.fillStyle = farbe; X.fillText(s, x, y);
}

// ---------- Hintergründe
function wohnzimmer() {
  X.fillStyle = "#d8c48a"; X.fillRect(0, 0, W, H);
  for (let x = 30; x < W; x += 90) linie([[x, 300], [x, BODEN - 230]], "#c4ad6c", 10, null, false, 3);
  // Fenster mit Gardine
  rechteck(640, 420, 330, 300, "#9fd3ff"); linie([[805, 420], [805, 720]], "#111", 6); linie([[640, 570], [970, 570]], "#111", 6);
  linie([[620, 400], [990, 400]], "#111", 8);
  linie([[625, 405], [700, 405], [690, 740], [640, 760]], "#111", 5, "#f2e6c8", true);
  linie([[985, 405], [910, 405], [920, 740], [970, 760]], "#111", 5, "#f2e6c8", true);
  // Poster
  linie([[90, 430], [330, 410], [340, 640], [100, 655]], "#111", 6, "#ff9a3c", true);
  text("MALLE", 215, 500, 70, "#fff", "#111"); text("2009", 218, 590, 56, "#ffe14a", "#111");
  // Boden
  X.fillStyle = "#8a5a3a"; X.fillRect(0, BODEN - 230, W, H);
  linie([[0, BODEN - 230], [W, BODEN - 230]], "#111", 8);
  ellipse(540, BODEN + 40, 470, 70, "#a33a3a", 6);
  // Sofa hinter den Figuren
  linie([[80, BODEN - 420], [1000, BODEN - 420], [1010, BODEN - 200], [70, BODEN - 200]], "#111", 8, "#6b4f8a", true);
  linie([[60, BODEN - 330], [150, BODEN - 340], [150, BODEN - 180], [55, BODEN - 180]], "#111", 8, "#5a3f78", true);
  linie([[930, BODEN - 340], [1020, BODEN - 330], [1025, BODEN - 180], [930, BODEN - 180]], "#111", 8, "#5a3f78", true);
  // leere Dosen auf dem Boden
  [[160, BODEN + 60, 8], [880, BODEN + 80, -20], [930, BODEN + 40, 70]].forEach(([x, y, r]) => dose(x, y, r * Math.PI / 180, .8));
}
function kueche() {
  X.fillStyle = "#e9e3d0"; X.fillRect(0, 0, W, H);
  for (let y = 320; y < BODEN - 230; y += 80) linie([[0, y], [W, y]], "#cfc6a8", 5, null, false, 2);
  for (let x = 0; x < W; x += 80) linie([[x, 320], [x, BODEN - 230]], "#cfc6a8", 5, null, false, 2);
  // Kühlschrank
  rechteck(790, 420, 230, 720, "#f4f4f4", 8); linie([[790, 640], [1020, 640]], "#111", 6); linie([[820, 500], [820, 590]], "#111", 8); linie([[820, 690], [820, 800]], "#111", 8);
  rechteck(850, 700, 70, 60, "#ffe14a", 4); // Magnet-Zettel
  // Fenster
  rechteck(120, 430, 300, 260, "#9fd3ff"); linie([[270, 430], [270, 690]], "#111", 6);
  X.fillStyle = "#7a7a7a"; X.fillRect(0, BODEN - 230, W, H); linie([[0, BODEN - 230], [W, BODEN - 230]], "#111", 8);
  for (let x = 0; x < W; x += 120) linie([[x, BODEN - 230], [x - 60, H]], "#666", 4);
  // Tisch mit Sekt
  linie([[260, BODEN - 120], [820, BODEN - 120], [800, BODEN - 70], [280, BODEN - 70]], "#111", 7, "#b57a45", true);
  flasche(700, BODEN - 175);
}
function dose(x, y, rot = 0, s = 1) {
  X.save(); X.translate(x, y); X.rotate(rot); X.scale(s, s);
  rechteck(-26, -55, 52, 110, "#c8d4dc", 6); rechteck(-26, -20, 52, 40, "#2e8b3d", 0); linie([[-26, -20], [26, -20]], "#111", 4); linie([[-26, 20], [26, 20]], "#111", 4);
  X.restore();
}
function flasche(x, y) {
  linie([[x - 20, y + 55], [x - 20, y - 10], [x - 8, y - 40], [x - 8, y - 75], [x + 8, y - 75], [x + 8, y - 40], [x + 20, y - 10], [x + 20, y + 55]], "#111", 6, "#2f6b2a", true);
  rechteck(x - 12, y - 88, 24, 16, "#e6c04a", 4);
}

// ---------- Figuren
const FIG = {
  ronny: { haut: "#f0c08a", hemd: "#f6f6ee", hose: "#7d7d86", name: "RONNY", farbe: "#ffe14a", s: 1.0 },
  mandy: { haut: "#f6c9a6", hemd: "#ff5fa8", hose: "#222", name: "MANDY", farbe: "#ff7cc0", s: .94 },
  kevin: { haut: "#efc7a0", hemd: "#3b6fd8", hose: "#2a2a3a", name: "KEVIN", farbe: "#7ec8ff", s: .8 },
};
function figur(id, x, blick, zustand) {
  const f = FIG[id], s = f.s, sp = zustand.spricht, akt = zustand.aktion, mund = zustand.mund;
  const wackel = akt === "schreit" ? 7 : 0;
  X.save(); X.translate(x + j(wackel), BODEN + j(wackel)); X.scale(s * (zustand.flip ? -1 : 1), s);
  const atem = Math.sin(T * 2.2 + x) * 6;
  const kopfY = -560 + atem, kopfR = 105;
  // Beine
  const hb = id === "ronny" ? 70 : 52;
  linie([[-hb + 10, -230], [-hb + 5, 0]], "#111", 52); linie([[-hb + 10, -230], [-hb + 5, 0]], f.hose, 40);
  linie([[hb - 10, -230], [hb - 5, 0]], "#111", 52); linie([[hb - 10, -230], [hb - 5, 0]], f.hose, 40);
  if (id === "ronny") { linie([[-hb - 13, -220], [-hb - 15, -10]], "#fff", 6); linie([[hb + 13, -220], [hb + 15, -10]], "#fff", 6); }
  ellipse(-hb - 15, 8, 50, 22, id === "mandy" ? "#fff" : "#f2f2f2", 6); ellipse(hb + 15, 8, 50, 22, id === "mandy" ? "#fff" : "#f2f2f2", 6);
  // Körper
  if (id === "ronny") {
    linie([[-110, -470 + atem], [110, -470 + atem], [175, -330], [150, -210], [-150, -210], [-175, -330]], "#111", 8, f.hemd, true);
    ellipse(40, -300, 26, 18, "#e8d27a", 0); ellipse(-60, -360, 14, 10, "#e8d27a", 0); // Flecken
    linie([[-70, -470 + atem], [-60, -380]], "#111", 5); linie([[70, -470 + atem], [60, -380]], "#111", 5);
  } else if (id === "mandy") {
    linie([[-80, -470 + atem], [80, -470 + atem], [95, -330], [-95, -330]], "#111", 8, f.hemd, true);
    linie([[-95, -330], [95, -330], [80, -220], [-80, -220]], "#111", 8, f.haut, true);
    text("QUEEN", 0, -400 + atem, 44, "#fff", "#c21a6a");
  } else {
    linie([[-115, -470 + atem], [115, -470 + atem], [130, -220], [-130, -220]], "#111", 8, f.hemd, true);
    linie([[-50, -330], [50, -330], [45, -270], [-45, -270]], "#111", 5, "#2a52a8", true);
  }
  // Arme
  const sx = id === "ronny" ? 135 : 100, sy = -440 + atem;
  const arm = (seite, hx, hy) => { const ex = seite * sx + (hx - seite * sx) * .5 + seite * 18, ey = sy + (hy - sy) * .5 + 20;
    linie([[seite * sx, sy], [ex, ey], [hx, hy]], "#111", 40); linie([[seite * sx, sy], [ex, ey], [hx, hy]], id === "kevin" ? f.hemd : f.haut, 28); ellipse(hx, hy, 24, 24, f.haut, 6); };
  const sw = Math.sin(T * 3 + x) * 10;
  let links = [-sx - 30, -250 + sw], rechts = [sx + 30, -250 - sw];
  let doseHand = id === "ronny" ? "r" : null, kopfNeig = 0;
  if (sp && akt === "trinkt") { rechts = [70, kopfY + 70]; doseHand = "r"; kopfNeig = -.18; }
  else if (id === "ronny") rechts = [sx + 40, -300 - sw];
  if (sp && akt === "zeigt") rechts = [sx + 230, sy - 40 + Math.sin(T * 9) * 12];
  if (sp && akt === "schreit") { links = [-sx - 90, sy - 230 + j(10)]; rechts = [sx + 90, sy - 230 + j(10)]; doseHand = id === "ronny" ? "r" : null; }
  if (zustand.schock) { links = [-60, kopfY + 60]; rechts = [60, kopfY + 60]; doseHand = null; }
  arm(-1, links[0], links[1]); arm(1, rechts[0], rechts[1]);
  if (doseHand) dose(rechts[0] + 6, rechts[1] - 30, sp && akt === "trinkt" ? -2.3 : .15, .9);
  // Kopf
  X.save(); X.translate(0, kopfY); X.rotate(kopfNeig + (sp ? Math.sin(T * 7) * .03 : 0));
  const rot = sp && akt === "schreit";
  if (id === "mandy") { ellipse(0, -kopfR - 40, 62, 55, "#ffe27a", 7); for (let i = 0; i < 5; i++) linie([[-40 + i * 20, -kopfR - 70], [-30 + i * 18, -kopfR - 15]], "#d9b23c", 4); }
  ellipse(0, 0, kopfR, kopfR * 1.05, rot ? "#ff8f7a" : f.haut, 8);
  if (id === "ronny") { // Halbglatze, Haarkranz, Bartstoppeln, Schnauzer
    linie([[-kopfR + 5, -10], [-kopfR + 20, -60], [-kopfR + 45, -75]], "#5a3b1e", 14); linie([[kopfR - 5, -10], [kopfR - 20, -60], [kopfR - 45, -75]], "#5a3b1e", 14);
    linie([[-20, -kopfR + 2], [-5, -kopfR - 30]], "#5a3b1e", 5); linie([[10, -kopfR + 2], [25, -kopfR - 25]], "#5a3b1e", 5);
    for (let i = 0; i < 16; i++) { const a = .3 + i * .16; X.fillStyle = "#6b5a4a"; X.fillRect(Math.cos(a) * 75 - 2 + j(2), Math.sin(a) * 70 + 10 + j(2), 5, 5); }
    linie([[-48, 38], [-15, 28], [15, 28], [48, 38]], "#5a3b1e", 16);
  }
  if (id === "mandy") { ellipse(-kopfR + 2, 30, 18, 26, null, 6, "#e3b23c"); ellipse(kopfR - 2, 30, 18, 26, null, 6, "#e3b23c"); }
  if (id === "kevin") { // Cap verkehrt herum
    linie([[-kopfR, -30], [-kopfR + 10, -kopfR + 10], [kopfR - 10, -kopfR + 10], [kopfR, -30]], "#111", 7, "#d83b3b", true);
    linie([[-kopfR + 10, -60], [-kopfR - 70, -50], [-kopfR - 65, -30], [-kopfR, -35]], "#111", 6, "#b82424", true);
  }
  // Augen
  const zu = ((T + x * .01) % 3.4) < .12 && !zustand.schock;
  const ag = zustand.schock ? 30 : id === "ronny" ? 20 : 24;
  const bx = blick * 8;
  [-40, 40].forEach((ax, i) => {
    if (zu) { linie([[ax - 22, -18], [ax + 22, -18]], "#111", 6); return; }
    ellipse(ax, -20, ag + 6, ag + 10, "#fff", 6);
    ellipse(ax + bx, -16, 9, 10, "#111", 0);
    if (id === "ronny" && !zustand.schock) linie([[ax - 28, -38], [ax + 28, -30 + (i ? -6 : 6)]], "#111", 7); // halb geschlossene Lider
    if (id === "mandy") { linie([[ax - 20, -46], [ax - 30, -60]], "#111", 4); linie([[ax, -50], [ax, -66]], "#111", 4); linie([[ax + 20, -46], [ax + 30, -60]], "#111", 4); }
  });
  if (rot) { linie([[-70, -62], [-15, -42]], "#111", 9); linie([[70, -62], [15, -42]], "#111", 9); }
  // Nase
  kurve(5, -10, 30, 25, 0, 30, "#111", 6);
  if (id === "ronny") ellipse(8, 20, 20, 14, "#f08a7a", 0);
  // Mund
  const my = 62, offen = Math.min(1, mund * 1.6);
  if (offen > .08) {
    ellipse(0, my, 22 + offen * 22, 6 + offen * (rot ? 46 : 32), "#5a0f1a", 6);
    if (offen > .4) ellipse(0, my + offen * 12, 14, 8, "#ff6f7f", 0);
  } else if (zustand.schock) ellipse(0, my, 16, 22, "#5a0f1a", 6);
  else kurve(-30, my, 0, my + (id === "ronny" ? 14 : 10), 30, my - 6, id === "mandy" ? "#d0103a" : "#111", id === "mandy" ? 9 : 6);
  if (zustand.schock) linie([[kopfR - 10, -60], [kopfR + 5, -30], [kopfR - 15, -30]], "#5ab4ff", 4, "#a8dcff", true);
  X.restore();
  if (rot) { text("!", kopfR + 70, kopfY - 110, 110, "#ff3b3b"); text("!", kopfR + 125, kopfY - 70, 80, "#ff3b3b"); }
  if (sp && akt === "trinkt" && (T * 4 | 0) % 2) { text("gluck", 0, kopfY - 190, 46, "#fff"); }
  X.restore();
}

// ---------- Zustand zum Zeitpunkt t
function aktuelleZeile(t) {
  return TL.zeilen.find(z => t >= z.start && t < z.start + z.dauer + .25) || null;
}
function mundWert(id, t) {
  const z = TL.zeilen.find(z => z.wer === id && t >= z.start && t < z.start + z.dauer);
  if (!z) return 0;
  const i = Math.floor((t - z.start) * TL.fps);
  return z.huelle[Math.min(i, z.huelle.length - 1)] || 0;
}

function zeichne(t) {
  T = t; SEED = Math.floor(t * 8); nJ = 0;
  const z = aktuelleZeile(t);
  const figs = TL.figuren;
  const pos = figs.length === 2 ? [300, 780] : [220, 540, 860];
  // Kamera: leichter Zoom auf den Sprecher, Ruck bei Geschrei
  const si = z ? figs.indexOf(z.wer) : -1;
  let zoom = 1, cx = W / 2;
  if (si >= 0) { const p = Math.min(1, (t - z.start) / .5); zoom = 1 + .07 * p; cx = W / 2 + (pos[si] - W / 2) * .35 * p; if (z.aktion === "schreit") zoom += .05; }
  if (z && z.wer === "geraeusch") zoom = 1.02 + Math.sin(t * 40) * .01;
  const halb = W / 2 / zoom; cx = Math.max(halb + 12, Math.min(W - halb - 12, cx));
  X.save();
  X.translate(W / 2, BODEN - 300); X.scale(zoom, zoom); X.translate(-cx, -(BODEN - 300));
  if (z && (z.aktion === "schreit" || z.wer === "geraeusch")) X.translate(j(8), j(8));
  (TL.ort === "kueche" ? kueche : wohnzimmer)();
  figs.forEach((id, i) => {
    const andere = si >= 0 && si !== i ? pos[si] : pos[1 - Math.min(i, 1)];
    const spricht = z && z.wer === id;
    figur(id, pos[i], Math.sign(andere - pos[i]), {
      spricht, aktion: spricht ? z.aktion : null, mund: mundWert(id, t),
      schock: spricht && z.aktion === "schock" || (z && z.wer === "geraeusch" && i === 0 && false),
      flip: false,
    });
  });
  if (z && z.wer === "geraeusch") text(z.text.replace(/\*/g, ""), W / 2, 560, 120, "#ffe14a", "#111");
  X.restore();
  // Titel-Banner
  X.fillStyle = "#111"; X.fillRect(0, 0, W, 300);
  const fr = t < .6 ? 1 + (1 - t / .6) * .4 : 1;
  X.save(); X.translate(W / 2, 120); X.scale(fr, fr); X.rotate(-.03);
  text("RONNY & MANDY", 0, 0, 104, "#ffe14a", "#c21a6a"); X.restore();
  text(TL.titel.toUpperCase(), W / 2, 228, 54, "#fff", "#111");
  // Untertitel
  X.fillStyle = "#111"; X.fillRect(0, 1560, W, H - 1560);
  if (z && z.wer !== "geraeusch") {
    const f = FIG[z.wer];
    text(f.name, W / 2, 1625, 46, f.farbe, "#111");
    const woerter = z.text.split(" "), zeilen = []; let akt = "";
    woerter.forEach(w => { if ((akt + " " + w).trim().length > 24) { zeilen.push(akt.trim()); akt = w; } else akt += " " + w; });
    zeilen.push(akt.trim());
    zeilen.slice(0, 3).forEach((zl, i) => text(zl, W / 2, 1712 + i * 80, 70, "#fff", "#000"));
  }
  // Ende: Folgen-Hinweis
  if (t > TL.dauer - 1.1) { X.fillStyle = "rgba(0,0,0,.55)"; X.fillRect(0, 300, W, 1260); text("FOLGEN FÜR MEHR", W / 2, 900, 110, "#ffe14a", "#c21a6a"); text("RONNY & MANDY", W / 2, 1030, 70, "#fff"); }
}
window.zeichne = zeichne;
