# Kanal-Leitfaden (für den täglichen Agenten)

Kanal: englischsprachige Kurzvideos (Instagram Reels / TikTok) über **Verschwörungen, die sich als wahr herausgestellt haben**, und **echte ungelöste Rätsel/Mysterien**. Label oben im Video: `Conspiracy that was TRUE` oder `Unsolved Mystery`.

## Eiserne Regeln
- Nur **belegte Fakten** (freigegebene Akten, Gerichtsurteile, Parlaments-/Senatsberichte, seriöse Historiker). Jede Folge braucht im Feld `quellen` mindestens eine echte Quelle (Name des Berichts/Dokuments, Jahr). Im Zweifel: Thema weglassen.
- Bei Mysterien klar sagen, was bekannt ist und was **nicht** bekannt ist – keine erfundenen Details.
- **Tabu:** Gesundheits-/Impf-Falschinfos, Wahlbetrugs-Behauptungen, Hetze gegen Gruppen (Religion, Herkunft …), Anschuldigungen gegen lebende Privatpersonen, aktuelle Tragödien/Anschläge, Flat Earth/Fake-Wissenschaft.
- Keine Wiederholung: vorher `episoden/gepostet/` und `episoden/warteschlange/` prüfen.

## Aufbau einer Folge (25–40 Sekunden, 7–10 Szenen)
1. **Hook in Szene 1** (max. ~10 Wörter): Neugier + Fallhöhe. Muster: „This sounds like a conspiracy theory. But it's *100% real.*“, „The U.S. government once planned to …“, „Nobody can explain what happened on …“
2. Szenen 2–7: Fakten in kurzen Sätzen (max. ~14 Wörter pro Szene), jede Szene bringt etwas Neues. Zahlen und Jahreszahlen machen es glaubwürdig.
3. Wendepunkt/Beweis: „In 1997, the documents were *declassified.*“
4. Schluss: Frage oder Cliffhanger + Follow-Aufruf („Follow for part two.“ / „Which one should I cover next?“)
- Wichtige Wörter mit `*Sternchen*` markieren (werden gelb). Pro Szene höchstens 1–2 Markierungen.
- `suche`: 2–3 kurze englische Stock-Footage-Begriffe je Szene (z. B. „old documents“, „dark corridor“, „military jet“). Keine Personennamen (Stockvideos zeigen keine echten Personen).

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
  "quellen": ["…"]
}
```
