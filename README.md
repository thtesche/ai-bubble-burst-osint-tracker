# AI Bubble Burst OSINT Tracker

A modular tracker that calculates a **Bubble Probability Score (0–100%)** by correlating news sentiment, market performance, and cloud infrastructure investment (CapEx) trends.

## 🚀 Core Concept

The tracker evaluates three dimensions:

1. **Sentiment (Qualitative):** Keyword-density analysis of 24-hour Google News articles for hype markers (revolution, bubble, crash, etc.).
2. **Market Action (Quantitative):** 5-day price momentum of 12 AI-relevant stock tickers via yfinance.
3. **CapEx Trends (Quantitative):** Capital expenditure growth of hyperscalers (Microsoft, Google, Amazon, Meta, NVIDIA, etc.) as a proxy for infrastructure overinvestment.

Weights: 40% Sentiment · 20% Market · 40% CapEx.

> **Fail-Fast Philosophy:** When data cannot be fetched, the pipeline raises a `PipelineError` rather than returning fabricated results. The market-only fallback is a comment in the logs — there is no silent neutral-score fallback.

## 🛠 Architecture

| Module | Responsibility |
|--------|----------------|
| `src/fetchers/googlenews.py` | Google News RSS + URL decoding (googlenewsdecoder) + Firecrawl scraping |
| `src/fetchers/market.py` | yfinance — prices + CapEx (cash flow statements) |
| `src/core/engine.py` | Keyword-density sentiment + weighted final score |
| `src/core/logger.py` | RunLogger — saves every run to `logs/runs/<timestamp>/` |
| `src/inference/llm_engine.py` | OpenAI-compatible LLM calls (non-streaming + streaming) |
| `src/inference/bubble_risk_prompt.py` | Structured prompt templates for LLM evaluation |
| `src/delivery/telegram.py` | Structured Telegram delivery (LLM first, market/news second) |
| `src/main.py` | Entry point: loads `.env`, runs pipeline, delivers to Telegram |

## 📂 Project Structure

```text
src/
├── core/
│   ├── __init__.py
│   ├── analyzer.py          # Legacy qualitative/quantitative scorer (not used by pipeline)
│   ├── engine.py            # Keyword-density sentiment + final score calculation
│   ├── full_pipeline_live.py# E2E pipeline: news → market → CapEx → scores → LLM
│   └── logger.py            # RunLogger — saves all data to logs/runs/<timestamp>/
├── fetchers/
│   ├── __init__.py
│   ├── firecrawl_engine.py  # Local Firecrawl/Atlantis /scrape endpoint (cache mode)
│   ├── googlenews.py        # Google News RSS + URL decoding + Firecrawl scraping
│   ├── market.py            # yfinance — prices + CapEx (no fake fallback)
│   └── market_fetcher.py    # Legacy mock (do not use — kept for reference)
├── delivery/
│   ├── __init__.py
│   └── telegram.py          # Structured Telegram delivery (LLM first, chunks)
└── inference/
    ├── __init__.py
    ├── llm_engine.py        # OpenAI-compatible API (non-streaming + streaming)
    └── bubble_risk_prompt.py# System + user prompt builders

tests/
├── test_pipeline_integration.py  # Mock-based integration tests
└── test_scoring_engine.py        # Unit tests (no external deps)

.env.example                    # Configuration template (copy to .env)
daily_report.sh                 # Standalone cron runner
```

## 🛠 Installation & Setup

### 1. Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Required packages (managed in `venv/`): `googlenewsdecoder`, `yfinance`, `httpx`, `selectolax`, `pandas`, `numpy`. No explicit `pip install` is needed — the provided `venv/` directory contains all dependencies.

### 2. Configuration (.env)

Copy the example file and fill in your settings:

```bash
cp .env.example .env
```

| Variable | Description | Default |
|----------|-------------|---------|
| `SEARCH_QUERY` | Google News search query | `"AI market bubble burst risk analysis 2025 2026"` |
| `PIPELINE_LIMIT` | Number of news articles to analyze | `5` |
| `MARKET_TICKERS` | Comma-separated stock tickers | `MSFT,GOOGL,AMZN,META,NVDA,AMD,ASML,AVGO,MU,DELL,SMCI,HPE` |
| `TELEGRAM_BOT_TOKEN` | Bot token for Telegram delivery | *(empty — optional)* |
| `TELEGRAM_CHAT_ID` | Target chat ID | *(empty — optional)* |
| `LLM_API_KEY` | API key for OpenAI-compatible endpoint | *(empty — optional)* |
| `LLM_API_BASE_URL` | API base URL | `https://api.openai.com/v1` |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |

### 3. Run Locally (Standalone)

```bash
# Via the shell script (recommended for cron):
./daily_report.sh

# Directly with Python:
python src/main.py
```

The script loads `.env`, runs the full pipeline (news + market + CapEx + optional LLM), and delivers the report to Telegram if credentials are configured. All data is saved to `logs/runs/<timestamp>/`.

### 4. Cronjob Setup

```bash
chmod +x daily_report.sh
crontab -e
```

Add a daily entry (example: 08:00):

```cron
0 8 * * * /path/to/your/project/daily_report.sh >> /path/to/your/project/cron_output.log 2>&1
```

> **Note:** The script clears `PYTHONPATH` before execution to prevent Hermes-Agent virtualenv leakage.

## 📈 Roadmap (V2)

- [ ] **Extended Data Sources:** Crypto data and VC funding news integration.
- [ ] **Visualization Dashboard:** Score history display.

---
*Developed with Hermes Agent (by Nous Research)*
