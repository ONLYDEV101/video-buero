# Kanal-Leitfaden (für den täglichen Agenten)

Kanal: englischsprachige Kurzvideos (Instagram Reels / TikTok) über **Verschwörungen, die sich als wahr herausgestellt haben**, und **echte ungelöste Rätsel/Mysterien**. Label oben im Video (eins davon): `Conspiracy that was TRUE`, `State Secret`, `Declassified`, `Unsolved Mystery`, `Cold War Files`.

## Themen-Mix (pro Tag abwechseln, nie 2× dieselbe Kategorie hintereinander)
1. **Verschwörungen, die wahr waren** (MKUltra, Northwoods, COINTELPRO, Tuskegee …)
2. **Staatsgeheimnisse** – geheime Bunker/Basen, geheime Programme, die jahrzehntelang geleugnet wurden (Area 51 offiziell bestätigt 2013, Project Greek Island, Operation Mockingbird, Project Azorian, Stargate-Programm …)
3. **Freigegebene Akten / Spionage** – echte Spionage-Operationen, Doppelagenten, Abhörprogramme (Operation Gold, Crypto AG, Venona, Snowden-Enthüllungen als belegte Fakten)
4. **Kalter Krieg** – Beinahe-Atomkriege, verlorene Atombomben (Broken Arrows), Projekte wie A119 (Mond-Atombombe)
5. **Ungelöste Mysterien** – Dyatlov Pass, D. B. Cooper, Wow!-Signal, Mary Celeste, Voynich-Manuskript …
Von jeder Kategorie mindestens 1 Folge pro Tag (8 Folgen = Mix).

## Eiserne Regeln
- Nur **belegte Fakten** (freigegebene Akten, Gerichtsurteile, Parlaments-/Senatsberichte, seriöse Historiker). Jede Folge braucht im Feld `quellen` mindestens eine echte Quelle (Name des Berichts/Dokuments, Jahr). Im Zweifel: Thema weglassen.
- Bei Mysterien klar sagen, was bekannt ist und was **nicht** bekannt ist – keine erfundenen Details.
- **Tabu:** Gesundheits-/Impf-Falschinfos, Wahlbetrugs-Behauptungen, Hetze gegen Gruppen (Religion, Herkunft …), Anschuldigungen gegen lebende Privatpersonen, aktuelle Tragödien/Anschläge, Flat Earth/Fake-Wissenschaft.
- Keine Wiederholung: vorher `episoden/gepostet/` und `episoden/warteschlange/` prüfen. Ein Thema nur in Ausnahmefällen erneut – dann mit klar neuem Blickwinkel ("Part 2") und frühestens nach 30 Tagen.

## Aufbau einer Folge (25–32 Sekunden, 7–9 Szenen) – Ziel: Zuschauer bis zum Ende halten
Messwerte (24.11.): Reels werden im Schnitt nur 10–14 s von 35 s geschaut, Likes/Shares fast 0. Deshalb:
1. **Hook in Szene 1** (max. 8 Wörter): Sofort die **konkreteste, schockierendste Tatsache** – keine Floskel wie „This sounds like fiction“. Gut: „The CIA secretly owned the world's top *encryption* company.“, „A U.S. bomber dropped *two nukes* on North Carolina.“ Schlecht: „This sounds like a conspiracy theory.“
2. **`titel` = Hook-Titel auf dem Bildschirm** (erscheint gross in den ersten 2–3 s): max. 6 Wörter, Neugier-Lücke, verrät nicht alles. Z. B. „They Hid It Under A Hotel“, „The Ship That Wasn't A Ship“.
3. Szenen 2–6: Fakten in kurzen Sätzen (max. ~12 Wörter pro Szene), jede Szene bringt etwas Neues. Zahlen und Jahreszahlen machen es glaubwürdig. Ab Szene 3 eine **offene Schleife**: „But the strangest part came later.“
4. Wendepunkt/Beweis: „In 1997, the documents were *declassified.*“
5. Schluss: **eine Frage, auf die man kommentieren will** (Meinung, kein Ja/Nein-Wissen): „Would you have believed it in 1975?“, „What do you think they're hiding today?“ – dann „Follow for more files.“
- **caption**: 1. Zeile = neuer Mini-Hook (nicht der Videotext). Danach 1–2 Sätze, dann dieselbe Kommentar-Frage. Bei 2–3 Folgen pro Tag zusätzlich: „Send this to someone who doesn't believe it.“ (Shares sind das stärkste Signal.) Max. 5 passende Hashtags.
- Wichtige Wörter mit `*Sternchen*` markieren (werden gelb). Pro Szene höchstens 1–2 Markierungen.
- `suche`: 2–3 kurze, **konkrete, sichtbare** englische Stock-Footage-Begriffe je Szene (Dinge, die man filmen kann: „submarine underwater“, „cia headquarters“, „old typewriter“, „radar screen“ – keine abstrakten Wörter wie „secret“, „mystery“, „truth“) (z. B. „old documents“, „dark corridor“, „military jet“). Keine Personennamen (Stockvideos zeigen keine echten Personen).

## Echte Archivfotos (wichtig: wirkt deutlich stärker als Stockclips)
- Je Folge 3–8 echte Fotos, vor allem in Szene 1 und beim Beweis. Themen mit guten Fotos bevorzugen (U.S.-Regierung, NARA, NASA, Militär).
- Suchen: `python3 scripts/archiv_suche.py bitmap "Soviet submarine B-59"` (macht absichtlich Pausen; bei Fehler 429 aufhören und später weitermachen). Klappt das Netz nicht, Folge ohne Archivfotos schreiben.
- Nur **Public domain oder CC0**, nur wenn Beschreibung auf Commons eindeutig zum Satz passt. Bei Filmfiguren, unklarer Herkunft oder Zweifel an der Lizenz: weglassen. Keine Leichen/Verletzten, keine lebenden Privatpersonen.
- Je Szene 1–2 Fotos: `"archiv": [{"datei": "File:Soviet b-59 submarine.jpg", "hinweis": "The real B-59"}], "nur_archiv": true`
- `hinweis` (max. 26 Zeichen) muss stimmen: „Real photo, 1962“ nur beim echten Ereignis, sonst „Archive: …“, „Replica“, „Painting, 1861“.
- Auf Folgenebene `"klang": "voll"` setzen. Mit Archivfotos endet die caption auf: `AI voice & edit. Footage: Pixabay/Pexels. Archive images: Wikimedia Commons (public domain/CC0).`
- `suche` bleibt in jeder Szene Pflicht (Ersatz, falls ein Foto nicht lädt).

## Dateiformat
Dateiname: `episoden/warteschlange/JJJJMMTT-NN_stichwort.json` (NN = 01..08, bestimmt die Reihenfolge).
```json
{
  "id": "20261123-01_northwoods",
  "sprache": "en",
  "label": "Conspiracy that was TRUE",
  "titel": "…",
  "szenen": [ { "text": "…", "suche": ["…", "…"] } ],
  "caption": "1–2 Sätze + Frage an die Zuschauer. Endet mit: AI voice & edit. Footage: Pixabay/Pexels.",
  "hashtags": ["#conspiracy", "#declassified", "…max 10"],
  "quellen": ["…"],
  "story_frage": "Kurze TRUE-or-FAKE-Behauptung für die Story, max. 12 Wörter, z. B. \"The CIA once tried to bug a cat.\""
}
```
