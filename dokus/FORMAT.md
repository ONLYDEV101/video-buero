# Doku-JSON – Format & Qualitätsregeln

Vorlage: `dokus/gepostet/doku_wirecard_en.json` (bzw. `dokus/warteschlange/…` falls noch nicht verschoben). Genau so aufbauen.

## Felder
```json
{
  "id": "doku_<thema>_en",                 // = Dateiname ohne .json, nur a-z0-9_
  "sprache": "en",
  "stimme": "en-US-AndrewMultilingualNeural",
  "rate": "-4%",
  "titel": "<Thema>: <Hook> | Documentary",   // max. 90 Zeichen
  "beschreibung": "2–3 Sätze Hook.\n\nChapters:\n0:00 ...\n...\n\n<Unschuldsvermutung falls lebende Personen angeklagt>",
  "hashtags": ["#documentary", ...],        // max. 5
  "quellen": ["Gericht/Bericht/Medium, Datum", ...],   // 6–10 echte, prüfbare Quellen
  "hinweis": "Narration: AI voice. Footage: Pexels/Pixabay. Archive images: Wikimedia Commons.",
  "abschnitte": [
    {"kapitel": "Chapter 1", "untertitel": "The Rise"},
    {"text": "Gesprochener Absatz, 30–70 Wörter.",
     "bilder": [
       {"suche": ["konkrete englische stock suche", "alternative"]},
       {"archiv": "File:<exakter Commons-Dateiname>.jpg", "hinweis": "kurze Bildunterschrift"},
       {"karte": "€1.9 BILLION", "unter": "kurzer Untertitel"},
       {"zitat": "Wörtliches, belegtes Zitat.", "quelle": "Wer, Datum"}
     ]}
  ]
}
```

## Pflicht
- Länge: 2000–2300 gesprochene Wörter (≈ 14–16 Min.), 40–55 Abschnitte, 6–8 Kapitel.
- Aufbau: Cold Open (Hook, 3 Absätze, endet mit offener Frage) → Kapitel → Epilog mit Frage an die Zuschauer ("Tell me in the comments ...").
- Pro Textabschnitt 1–3 Bilder (die Sprechzeit wird gleichmäßig aufgeteilt).
- Mindestens 10 `archiv`-Bilder: echte Fotos von Wikimedia Commons, nur Public Domain, CC0, CC BY oder CC BY-SA.
  Dateinamen VORHER per API prüfen, z. B.
  `https://commons.wikimedia.org/w/api.php?action=query&titles=File:X.jpg&prop=imageinfo&iiprop=extmetadata&format=json`
  (LicenseShortName muss passen). Nicht prüfbar → weglassen. Keine Logos, keine Fotos lebender Privatpersonen.
- `suche`: konkret und zum Satz passend ("trading floor screens", "police car night"), keine Natur/Landschaft/Tiere.
- `karte` für Zahlen/Daten (max. ~14 Zeichen groß), `zitat` nur wörtlich belegt mit Quelle.
- Zahlen ausschreiben, wie sie gesprochen werden ("one point nine billion euros"). Keine Abkürzungen, die die TTS falsch liest.
- Deutsche Themen: für internationales Publikum erklären, Begriffe übersetzen.

## Inhaltlich (siehe auch STIL.md)
- Jede Tatsachenbehauptung muss belegbar sein (Urteil, Untersuchungsbericht, Parlament, seriöse Presse). Vorher per WebFetch prüfen.
- Polarisierend im Ton, sauber im Inhalt. Meinung als Frage formulieren, nicht als Fakt.
- Lebende Personen: nur Belegtes; laufende Verfahren → Unschuldsvermutung in Text UND Beschreibung.
- Tabu: Wahlbetrugs-Behauptungen, Gesundheits-Falschinfos, Hetze, aktuelle Anschläge/Tragödien, Vorwürfe gegen Privatpersonen.
