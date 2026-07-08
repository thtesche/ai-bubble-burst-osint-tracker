# AI-Bubble-Burst-OSINT-Tracker

Ein hochgradig robuster, modularer Tracker zur Identifizierung von Anzeichen einer KI-Blase durch die Kombination von News-Sentiment und Marktdaten.

## 🚀 Kernkonzept
Der Tracker berechnet einen **"Bubble Burst Score" (0-100%)** basierend auf zwei Dimensionen:
1.  **Sentiment (Qualitativ):** Analyse von News-Inhalten auf Hype-Keywords vs. technische Substanz (via LLM & Snippet-Parsing).
2.  **Market Action (Quantitativ):** Analyse von Kursbewegungen relevanter Tech-Indizes und Aktien.

## 🛠 Architektur & Resilienz
Das System wurde nach dem Prinzip der **"Graceful Degradation"** entwickelt, um auch gegen aggressive Bot-Schutzmechanismen (z.B. auf Yahoo Finance oder Reuters) stabil zu bleiben:

*   **Hybrid-Execution:** Das System nutzt eine lokale Python-Umgebung (`venv`) für schwere Berechnungen und die Hermes-Runtime für die Web-Interaktion.
*   **Cascade-Extraction Strategy:** 
    *   *Level 1 (Fast):* Extraktion direkt aus Such-Snippets (extrem schnell & bot-resistent).
    *   *Level 2 (Deep):* Falls Snippet fehlschlägt $\rightarrow$ Vollständige Seiten-Extraktion via `web_extract`.
    *   *Level 3 (Fallback):* Falls alles fehlschlägt $\rightarrow$ Nutzung neutraler Werte, um die Pipeline stabil zu halten.
*   **Modularität:** Klare Trennung zwischen `core` (Logik), `fetchers` (Daten) und `delivery` (Output).

## 📂 Projektstruktur
```text
src/
├── core/
│   ├── engine.py          # Scoring-Logik & mathematische Formel
│   └── test_full_pipeline_live.py # E2E-Test (Hybrid Mode)
├── fetchers/
│   ├── news.py            # News-Suche & Snippet/Deep Extraction
│   └── market.py          # Markt-Suche & Preis-Extraktion (Search-basiert)
└── delivery/              # (Geplant: Telegram/Discord Integration)
```

## 🛠 Installation & Setup (Lokal)

### 1. Umgebung vorbereiten
Erstelle ein lokales Virtual Environment direkt im Projektverzeichnis:
```bash
python3 -m venv venv
source venv/bin/activate
pip install yfinance pandas
```

### 2. Konfiguration (.env)
Das Projekt nutzt eine `.env` Datei für lokale Pfade und Geheimnisse. Kopiere die Beispiel-Datei und passe den Pfad an deine Umgebung an:
```bash
cp .env.example .env
# Bearbeite die .env Datei und setze PROJECT_ROOT auf deinen absoluten Pfad
nano .env 
```

### 3. Ausführung (Manuell)
Um den gesamten Prozess inklusive echter Daten zu testen, nutze die Hermes-Runtime (da diese die `hermes_tools` bereitstellt):
```bash
execute_code "import sys; sys.path.append('/path/to/your/project'); from src.core.full_pipeline_live import e2e_test; e2e_test()"
```

### 4. Automatisierung (Cronjob)
Für den täglichen automatisierten Lauf ohne Hermes-Runtime wird das lokale Skript `daily_report.sh` verwendet. Dieses nutzt das lokale `venv` und bricht bei fehlenden Daten oder Tools sauber ab (Fail-Fast).

**Cronjob Setup:**
1. Stelle sicher, dass das Skript ausführbar ist: `chmod +x daily_report.sh`
2. Öffne die Crontab: `crontab -e`
3. Füge folgenden Eintrag hinzu (Beispiel für täglicher Lauf um 08:00 Uhr):
```cron
0 8 * * * /path/to/your/project/daily_report.sh >> /path/to/your/project/cron_output.log 2>&1
```

*Hinweis: Das Skript loggt alle Details zusätzlich in `logs/runs/`.*

## 📈 Roadmap (V2)
- [ ] **Echte API-Anbindung:** Ersetzung des Scrapings durch professionelle Finanz-APIs (z.B. *Alpha Vantage* oder *Polygon.io*).
- [ ] **Erweiterte Datenquellen:** Integration von Krypto-Daten und VC-Funding-News.
- [ ] **Visualisierung:** Dashboard zur Darstellung der Score-Historie.

```cron
0 8 * * * /path/to/your/project/daily_report.sh >> /path/to/your/project/cron_output.log 2>&1
```

*Hinweis: Das Skript loggt alle Details zusätzlich in `logs/runs/`.*

## 📈 Roadmap (V2)
- [ ] **Echte API-Anbindung:** Ersetzung des Scrapings durch professionelle Finanz-APIs (z.B. *Alpha Vantage* oder *Polygon.io*).
- [ ] **Erweiterte Datenquellen:** Integration von Krypto-Daten und VC-Funding-News.
- [ ] **Visualisierung:** Dashboard zur Darstellung der Score-Historie.

---
*Developed with Hermes Agent (by Nous Research)*
