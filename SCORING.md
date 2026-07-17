# Bubble Score Calculation — Complete Documentation

## 1. Overview

The **AI Bubble Burst OSINT Tracker** computes a **Bubble Probability Score** in the range **0–100%**, indicating the probability of an imminent correction or crash in AI market valuations.

The score is composed of three independent sub-scoring modules that are combined linearly:

```
final_bubble_score = ((1.0 - mean_sentiment_score) × 0.4)
                   + (market_score             × 0.2)
                   + (capex_score              × 0.4)
```

### Weighting

| Component  | Weight | Description                                    |
|------------|--------|------------------------------------------------|
| Sentiment  | 40 %   | LLM-based sentiment analysis of news articles  |
| Market     | 20 %   | Price data: SMA-200 distance + YTD performance |
| CapEx      | 40 %   | Quarterly CapEx growth of hyperscalers         |

> **Weighting logic:** News sentiment and infrastructure investments (CapEx) are considered the two most important early indicators (each 40 %). Market prices are treated as a secondary, macro-stable indicator (SMA 200 + YTD) with 20 %.

---

## 2. Sentiment Score

### Source
- **Data source:** Google News RSS → Firecrawl scraping of article text
- **Analysis:** An LLM (OpenAI-compatible) analyzes *each* article individually in the context of the AI bubble.

### LLM Scoring Rubric (per article, scale 0.0–1.0)

| Score Range | Meaning for AI Market | Bubble-Risk Interpretation |
|-------------|-----------------------|----------------------------|
| **0.0**     | Strongly bearish — warns of bubble, overvaluation, crash | **High** risk: warning signals |
| **0.5**     | Neutral — balanced reporting | **Moderate** risk: no clear signals |
| **1.0**     | Strongly bullish — praises AI as revolutionary, explosive growth | **High** risk: euphoria = classic bubble signal |

### Aggregation
The **mean_sentiment_score** is the arithmetic mean of all article sentiment scores.

```
mean_sentiment_score = Σ(article_sentiment_score_i) / n
```

### Inversion in the Final Formula

The sentiment score is **0.0 = bearish, 1.0 = bullish**. However, since *both* extreme euphoria (1.0) *and* panicked warnings (0.0) are bubble signals, the value is **inverted** in the main formula:

```
(1.0 - mean_sentiment_score) × 0.4
```

This means:
- **Strongly bearish news (0.0):** `1.0 - 0.0 = 1.0` → **maximum contribution to bubble score** (crash risk)
- **Strongly bullish news (1.0):** `1.0 - 1.0 = 0.0` → **no contribution to bubble score**
- **Neutral news (0.5):** `1.0 - 0.5 = 0.5` → moderate contribution

> **Note:** This inversion was introduced after the original bug was identified: bearish sentiment incorrectly pushed the overall score downward, contradicting the intended risk model.

---

## 3. Market Score

### Source
- **Data source:** yfinance — stock prices for 12 AI-relevant tickers (MSFT, GOOGL, AMZN, META, NVDA, AMD, ASML, AVGO, MU, DELL, SMCI, HPE).

### Highlighted Metrics (per ticker)
1. **Distance from 200-day SMA** — percentage by which the current price is above or below the simple moving average of the last 200 trading days.
2. **Year-to-Date (YTD) Performance** — price development since January 1 of the current year.

### Score Calculation (scale 0.0–1.0)

The `market_score` aggregates the scores of both metrics per ticker, then averages across all tickers.

#### SMA 200 Distance Score

| Distance to SMA 200 | Score | Reasoning |
|---------------------|-------|-----------|
| ≤ 20 % above SMA    | 0.0   | Fairly valued / undervalued |
| 20–50 % above SMA   | 0.0 – 1.0 (linear interpolation) | Bubble zone — progressive overvaluation |
| ≥ 50 % above SMA    | 1.0   | Extreme overshooting |
| Below SMA 200       | 0.0   | Price in healthy range |

Formula:
```
sma_score = 0.0                               if dist ≤ 20
sma_score = (dist - 20.0) / 30.0              if 20 < dist < 50
sma_score = 1.0                               if dist ≥ 50
```

#### YTD Performance Score

| YTD Performance | Score | Reasoning |
|-----------------|-------|-----------|
| ≤ 30 %          | 0.0   | Healthy development |
| 30–70 %         | 0.0 – 1.0 (linear interpolation) | Overheating zone |
| ≥ 70 %          | 1.0   | Extreme YTD surge |

Formula:
```
ytd_score = 0.0                               if ytd ≤ 30
ytd_score = (ytd - 30.0) / 40.0               if 30 < ytd < 70
ytd_score = 1.0                               if ytd ≥ 70
```

#### Aggregation

```
ticker_market_score = (sma_score + ytd_score) / 2
final_market_score  = Σ(ticker_market_score_i) / n
```

### U-shaped Correction

The original market score only treated *price increases* as a bubble signal — which was a fundamental flaw: a bubble is characterized by *price surges* before it bursts, not by the post-burst decline.

The U-shaped correction now treats **extreme price gains AND extreme price losses** as high bubble risk:

- **Strong gains** (far above SMA 200 / high YTD): indicate *euphoria* = classic bubble signal.
- **Strong losses** (price below SMA 200, strongly negative YTD): indicate *panic/correction* = possible stage *after* bubble formation.

Both extremes are thus penalized in the `market_score` with a high value (near 1.0).

---

## 4. CapEx Score

### Source
- **Data source:** yfinance — cash flow statements (annual and quarterly) for the 12 tickers.
- **Metric:** Capital Expenditure (CapEx) as a proxy for infrastructure overinvestment.

### Score Calculation (scale 0.0–1.0)

For each ticker, the quarterly CapEx growth is calculated:

1. Absolute values of the last 4 quarters are extracted (negative CapEx values are converted to positive absolute amounts).
2. The percentage change between consecutive quarters is computed.
3. The average of these changes is the mean change.

```
changes_i = (capex_i - capex_{i-1}) / |capex_{i-1}|
avg_change = Σ(changes_i) / n
```

4. The `avg_change` is mapped to the score range 0.0–1.0:

| Quarterly CapEx Growth (avg) | Score | Meaning |
|------------------------------|-------|---------|
| -20 % or more (decline)      | 0.0   | Less investment = low bubble signal |
| 0 %                          | 0.5   | Stagnation = neutral risk |
| +20 % or more (growth)       | 1.0   | Aggressive infrastructure buildout = high bubble signal |

Formula:
```
score = 0.5 + (avg_change / 0.20)
score = max(0.0, min(1.0, score))  # Clamping
```

#### Aggregation

```
final_capex_score = Σ(ticker_capex_score_i) / n
```

### Fallback Behavior

- **No CapEx data available:** Score stays **0.5** (neutral).
- **Fewer than 2 quarters:** Score stays **0.5** (neutral).

---

## 5. Final Bubble Score Formula

```
final_bubble_score = ((1.0 - mean_sentiment_score) × 0.4)
                   + (market_score             × 0.2)
                   + (capex_score              × 0.4)
```

The final score is scaled to the percentage range 0–100 % by multiplying by 100.

### Example Calculation (fictional)

Assume:
- `mean_sentiment_score` = 0.35 (panicking, warning-laden news)
- `market_score` = 0.60 (prices well above SMA 200, strong YTD)
- `capex_score` = 0.85 (massive infrastructure buildout)

```
Inverted Sentiment:  (1.0 - 0.35) × 0.4 = 0.65 × 0.4 = 0.26
Market Contribution: 0.60 × 0.2 = 0.12
CapEx Contribution:  0.85 × 0.4 = 0.34

final_bubble_score = 0.26 + 0.12 + 0.34 = 0.72 (72.0 %) → Critical risk zone 🔴
```

---

## 6. Score Interpretation (LLM Prompt)

The score is interpreted by the LLM prompt and the Telegram output as follows:

### Bubble Score (0–100 %)

| Range | Risk Level | Emoji | Description |
|-------|------------|-------|-------------|
| **0 – 40 %** | LOW RISK | 🟢 | Market appears stable or consolidated |
| **40 – 70 %** | MODERATE RISK | 🟡 | Mixed signals, some tension present |
| **70 – 100 %** | CRITICAL RISK | 🔴 | Extreme overheating, speculative mania |

### Component Scale

| Component | 0.0 | 0.5 | 1.0 |
|-----------|-----|-----|-----|
| **Sentiment** | Panicking warnings | Balanced reporting | Euphoric posts |
| **Market** | Stable / undervalued | Moderately elevated | Extreme overvaluation |
| **CapEx** | Stagnation / decline | Moderate growth | Aggressive infrastructure buildout |

---

## 7. Code Reference

| File | Function | Line | Responsibility |
|------|----------|------|----------------|
| `src/fetchers/market.py` | `calculate_capex_score()` | 301–361 | Quarterly CapEx growth |
| `src/fetchers/market.py` | `calculate_market_score()` | 363–411 | SMA 200 + YTD |
| `src/core/full_pipeline_live.py` | `run_pipeline()` | 393 | Final score formula |
| `src/inference/bubble_risk_prompt.py` | `build_user_prompt()` | 34–125 | LLM prompt with score reference |

---

## 8. Design Principles

1. **Fail-Fast:** When data cannot be fetched, a `PipelineError` is raised — no silent fallback values.
2. **No Fake Data:** Missing data means no scoring, not a fictional neutral score (except for justified fallbacks like CapEx score 0.5 for missing quarterly data).
3. **Transparency:** Each component is clearly and linearly scalable 0.0–1.0 and traceable.
4. **Inversion as Feature:** Inverting the sentiment score (bearish news → higher bubble score) was introduced after the bug was explicitly identified.
