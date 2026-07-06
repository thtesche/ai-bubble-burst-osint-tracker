# Plan: AI Bubble Burst OSINT Tracker (MVP)

## Zielsetzung
Entwicklung eines automatisierten Trackers, der täglich einen "Bubble Burst Score" (0-100%) basierend auf News-Sentiment und Marktdaten berechnet und per Telegram an den User sendet.

## Kern-Indikatoren (Basierend auf Wikipedia & Marktlogik)
1. **Sentiment/Hype Index (Qualitativ):** Analyse von News auf "Marketing-Buzzwords" vs. "technische Substanz".
2. **Market Volatility/Trend (Quantitativ):** Kursbewegungen relevanter Tech-Indizes oder KI-bezogener Aktien.
3. **Investment/Funding Signal (Optional für MVP):** Trends in VC-News oder Hardware-Nachfrage.

## Phasen der Umsetzung

### Phase 1: Research & Definition (The "Logic")
- [ ] Wikipedia-Artikel analysieren (`web_extract`).
- [ ] Definition der Scoring-Formel (Gewichtung von Sentiment vs. Kursdaten).
- [ ] Festlegung der 20 primären News-Quellen/Suchbegriffe.

### Phase 2: Data Ingestion (The "Tools")
- [ ] Implementierung eines `NewsFetcher` (Python/Web Search).
- [ ] Implementierung eines `MarketDataFetcher` (Python/yfinance oder ähnliches).
- [ ] Erstellung eines Hermes-Skills für die Datenabfrage, falls nötig.

### Phase 3: Scoring Engine (The "Brain")
- [ ] Entwicklung der `ScoringEngine` in Python.
- [ ] Integration von LLM-Analysen zur Bewertung der News-Qualität (Hype vs. Substanz).
- [ ] Implementierung der Logik zur Zusammenführung von qualitativen und quantitativen Daten.

### Phase 4: Delivery & Automation (The "Action")
- [ ] Implementierung des Telegram-Senders (nutzt bereitgestellten Bot Token).
- [ ] Erstellung eines Hermes Cronjobs für den täglichen Lauf.
- [ ] Testlauf: Manuelle Triggerung des gesamten Flows und Verifizierung der Nachricht.

## Technische Details
- **Sprache:** Python 3.11
- **Deployment:** Hermes Cron (lokal)
- **Kommunikation:** Telegram Bot API
- **Bot Token:** `xxx`
- **Target User ID:** `xxx`

## Definition of Done (DoD)
- [ ] Der Tracker läuft täglich automatisch.
- [ ] Die Telegram-Nachricht enthält den Score (0-100%).
- [ ] Die Nachricht listet die analysierten Quellen auf.
- [ ] Der Score ist nachvollziehbar (Logik ist im Code dokumentiert).

