# Plan: Robustere Sentiment-Berechnung mit Relevanz-Filterung

## Problem

Aktuelle Sentiment-Berechnung (`_analyze_sentiment_by_article`, `full_pipeline_live.py`) bewertet **jeden** Artikel, unabhängig vom Thema. Ein Artikel über "KI in der Medizin" wird als "bullish" gewertet und verfälscht den Mean Sentiment Score, der 40% in den finalen Bubble Score eingeht.

Zudem ist der System-Prompt zu allgemein ("stance toward AI market/tech sector") – er berücksichtigt nicht explizit den Bubble-Kontext.

## Lösung: Zwei-Stufen-Ansatz mit separatem Relevanz-Check

### Architektur-Änderung

**Vorher:** 1 LLM-Aufruf pro Artikel → Sentiment-Score (0.0–1.0)
**Nachher:** 2 LLM-Aufrufe pro Artikel → (1) Relevanz-Check → (2) Sentiment-Score (nur bei Relevanz)

```
Artikel
  ├─ LLM: "Ist dieser Artikel relevant für KI-Marktblase?"
  │       → relevant: true/false + Grund
  ├─ NEIN → Artikel wird aus Sentiment-Mittelwert ausgeschlossen
  └─ JA   → LLM: Sentiment-Score (0.0–1.0) zum Bubble-Aspekt
            → Sentiment-Wert wird in Mittelwert aufgenommen
```

### Betroffene Datei

- **`src/core/full_pipeline_live.py`** – Alle Änderungen an einer Datei

### Detaillierte Änderungen

---

### 1. Neue System-Prompts (Zeilen 76–90 → ersetzen)

**Relevanz-System-Prompt** (neu, ca. Zeile 76):
```
You are a content classification assistant. Given a news article, determine
whether it is RELEVANT or NOT RELEVANT to the topic of the AI market
bubble / technology sector valuation concerns.

An article is RELEVANT if it discusses ANY of the following:
- AI/technology market valuation, speculation, or bubble concerns
- Technology stock overvaluation, market mania, or hype
- AI investment spending, data center buildout, or CapEx concerns
- Tech/AI stock price risks, corrections, or crashes
- Tech/AI sector growth debates (bullish or bearish perspectives)
- Specific AI companies' stock valuations or market positioning

An article is NOT RELEVANT if it discusses:
- AI applications in non-financial contexts (healthcare, education, etc.)
- General technology product reviews or launches
- AI ethics, regulation, or policy without market/valuation angle
- Purely technical AI research without market implications
- Unrelated topics entirely

Output ONLY a JSON object — no explanations:
{"relevant": <true/false>, "reason": "<short 1-sentence explanation>"}
```

**Sentiment-System-Prompt** (aktualisiert, Zeile 91):
```
You are a sentiment analysis expert. Given a news article,
assign a sentiment score between 0.0 and 1.0 based on the article's
stance toward the AI market bubble risk.\n\n
Scoring rubric (directed at AI bubble risk):\n
- 0.0 = strongly bearish: article warns of AI bubble, describes
speculative mania, overvaluation, impending crash\n
- 0.5 = neutral: balanced reporting, no clear bullish or bearish bias\n
- 1.0 = strongly bullish: article praises AI growth, calls it
revolutionary, discusses explosive growth\n\n
Output ONLY a JSON object — no explanations:
{'sentiment_score': <float 0-1>, 'reason': '<short 1-2 sentence reasoning>'}
```

---

### 2. Neue Funktion: `_classify_relevance(article, llm_engine)`

**Position:** Nach `_build_sentiment_user_prompt` (ca. Zeile 101)

**Rückgabewert:**
```python
{
    "url": str,
    "title": str,
    "relevant": bool,
    "reason": str,
}
```

**Logik:**
- Ruft `_SENTIMENT_SYSTEM_PROMPT` (neu: Relevanz-Prompt) + User-Prompt auf
- Parst JSON → extrahiert `relevant` (bool) und `reason` (str)
- Fallback bei LLM-Fehler: `relevant = True` (konservativ: lieber falsch positiv als falsch negativ)
- Bei JSON-Parse-Fehler: `relevant = True`

---

### 3. Modifizierte Funktion: `_analyze_sentiment_by_article(article, llm_engine)`

**Position:** Zeile 103–174

**Neue Logik:**
```python
# Schritt 1: Relevanz-Check
relevance = _classify_relevance(article, llm_engine)

if not relevance["relevant"]:
    return {
        "url": relevance["url"],
        "title": relevance["title"],
        "content": content,
        "sentiment_score": 0.5,  # neutral – zählt nicht in Mittelwert
        "relevant": False,
        "reason": f"IRRELEVANT: {relevance['reason']}",
    }

# Schritt 2: Sentiment-Check (nur wenn relevant)
response = await llm_engine.generate_async(
    prompt=_build_sentiment_user_prompt(title, content),
    system_prompt=_SENTIMENT_SYSTEM_PROMPT,  # aktualisierter Prompt
)
# ... wie bisher, aber mit zusätzlichem "relevant": True Feld ...
```

---

### 4. Aktualisierte Mittelwert-Berechnung (Zeile 349–351)

**Vorher:**
```python
mean_sentiment_score = (
    sum(a["sentiment_score"] for a in article_sentiments) / len(article_sentiments)
    if article_sentiments else 0.5
)
```

**Nachher:**
```python
relevant_articles = [a for a in article_sentiments if a.get("relevant", True)]
mean_sentiment_score = (
    sum(a["sentiment_score"] for a in relevant_articles) / len(relevant_articles)
    if relevant_articles else 0.5
)
```

**Zusätzlich:** Log-Ausgabe um irrelevant Articles erweitern:
```python
for i, a in enumerate(article_sentiments, 1):
    status = "RELEVANT" if a.get("relevant", True) else "IRRELEVANT (excluded)"
    print(f"  [{i}] {a['title'][:60]}... → {a['sentiment_score']:.3f} [{status}]")
```

---

### 5. Aktualisierte JSON-Log-Ausgabe (Zeile 368–377)

Feld `"relevant"` zur JSON-Ausgabe hinzufügen:
```python
{
    "url": a["url"],
    "title": a["title"],
    "sentiment_score": a["sentiment_score"],
    "relevant": a.get("relevant", True),
    "reason": a["reason"],
    "content_length": len(a.get("content", "")),
}
```

---

### 6. PipelineResult – optional: Relevance-Info

Die `article_sentiments` Liste enthält bereits das neue `"relevant"` Feld. Keine Änderung am Dataclass-Interface nötig.

---

## Edge Cases

| Szenario | Behandlung |
|----------|-------------|
| Alle Artikel irrelevant | `mean_sentiment_score = 0.5` (neutral, wie bisher) |
| LLM bei Relevanz-Check fällt aus | Fallback: `relevant = True` (konservativ) |
| LLM bei Sentiment-Check fällt aus | Fallback: `sentiment_score = 0.5`, `relevant = True` |
| JSON-Parse-Fehler bei Relevanz | Fallback: `relevant = True` |
| JSON-Parse-Fehler bei Sentiment | Fallback: `sentiment_score = 0.5`, `relevant = True` |

## API-Kosten

- Vorher: 1 LLM-Aufruf pro Artikel (z.B. 5 Artikel = 5 Aufrufe)
- Nachher: 2 LLM-Aufrufe pro Artikel (z.B. 5 Artikel = 10 Aufrufe)
- Wenn 40% der Artikel als irrelevant klassifiziert werden: 10 Aufrufe statt 10 (gleiche Anzahl, da irrelevante Artikel keinen 2. Aufruf bekommen)
- **Netto:** Ca. gleicher oder weniger Aufrufe, da irrelevante Artikel den 2. Aufruf sparen. Aber jeder Artikel kostet mindestens 1 zusätzlichen Aufruf.

## Test-Validierung

1. Manuelle Tests mit bekannten relevanten/irrelevanten Artikeln prüfen
2. Prüfen dass `mean_sentiment_score` sich korrekt verhält wenn Artikel ausgeschlossen werden
3. Prüfen dass JSON-Logs das `relevant` Feld korrekt enthalten
