# Video-Büro

Baut automatisch kurze Hochkant-Videos (1080×1920) für Instagram Reels und TikTok und postet sie auf Instagram.

## So läuft es
1. **Episode schreiben:** Eine Datei in `episoden/` (JSON) mit Szenen-Texten, Suchbegriffen für Hintergrundvideos, Caption und Hashtags. Das übernimmt später ein geplanter Claude-Agent jeden Tag.
2. **Video bauen:** Sobald eine Episode im Projekt landet, baut GitHub Actions das Video. Dazu kommen eine kostenlose KI-Stimme (Piper), Hintergründe von Pexels (kostenlos, kommerziell nutzbar) oder Farbverläufe und eingebrannte Untertitel.
3. **Posten:** Wenn `IG_TOKEN`/`IG_USER_ID` hinterlegt sind und die Variable `AUTO_POST` auf `true` steht, geht das Reel automatisch auf Instagram.

Die fertigen Videos liegen 14 Tage unter *Actions → Lauf → Artifacts → videos* zum Herunterladen, zum Beispiel für TikTok.

## Geheimnisse (Settings → Secrets and variables → Actions)
| Name | Wofür | Pflicht |
|---|---|---|
| `PEXELS_API_KEY` | echte Hintergrundvideos statt Farbverlauf | nein |
| `IG_TOKEN` | Instagram-Zugriffstoken (langlebig) | zum Posten |
| `IG_USER_ID` | ID des Instagram-Creator-Kontos | zum Posten |
| Variable `AUTO_POST` = `true` | automatisch posten | nein |

## Episode-Format
```json
{
  "id": "2026-11-23_thema",
  "sprache": "de",
  "titel": "…",
  "szenen": [ { "text": "gesprochener Satz", "suche": "english stock search", "einblendung": "optional kürzerer Bildtext" } ],
  "caption": "…",
  "hashtags": ["#…"]
}
```

## Regeln
- Nur eigene Inhalte und frei lizenziertes Material. Keine Ausschnitte aus Filmen, Serien oder von Creatorn.
- KI-Videos werden in der Caption gekennzeichnet (#KIgeneriert).
