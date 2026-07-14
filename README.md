# AI-Bubble-Burst-OSINT-Tracker

A highly robust, modular tracker for identifying signs of an AI bubble through the combination of news sentiment and market data.

## 🚀 Core Concept
The tracker calculates a **"Bubble Burst Score" (0-100%)** based on two dimensions:
1.  **Sentiment (Qualitative):** Analysis of news content for hype keywords vs. technical substance (via LLM & snippet parsing).
2.  **Market Action (Quantitative):** Analysis of price movements of relevant tech indices and stocks.

## 🛠 Architecture & Resilience
The system was designed according to the principle of **"Graceful Degradation"** to remain stable even against aggressive bot protection mechanisms (e.g., on Yahoo Finance or Reuters):

*   **Hybrid-Execution:** The system uses a local Python environment (`venv`) for heavy computations and the Hermes runtime for web interaction.
*   **Cascade-Extraction Strategy:** 
    *   *Level 1 (Fast):* Extraction directly from search snippets (extremely fast & bot-resistant).
    *   *Level 2 (Deep):* If snippet fails → Full page extraction via `web_extract`.
    *   *Level 3 (Fallback):* If everything fails → Use neutral values to keep the pipeline stable.
*   **Modularity:** Clear separation between `core` (logic), `fetchers` (data) and `delivery` (output).

## 📂 Project Structure
```text
src/
├── core/
│   ├── engine.py          # Scoring logic & mathematical formula
│   └── test_full_pipeline_live.py # E2E test (Hybrid Mode)
├── fetchers/
│   ├── news.py            # News search & snippet/deep extraction
│   └── market.py          # Market search & price extraction (search-based)
└── delivery/              # (Planned: Telegram/Discord integration)
```

## 🛠 Installation & Setup (Local)

### 1. Prepare Environment
Create a local virtual environment directly in the project directory:
```bash
python3 -m venv venv
source venv/bin/activate
pip install yfinance pandas
```

### 2. Configuration (.env)
The project uses a `.env` file for local paths and secrets. Copy the example file and adjust the path to your environment:
```bash
cp .env.example .env
# Edit the .env file and set PROJECT_ROOT to your absolute path
nano .env 
```

### 3. Execution (Manual)
To test the entire process with real data, use the Hermes runtime (as it provides the `hermes_tools`):
```bash
execute_code "import sys; sys.path.append('/path/to/your/project'); from src.core.full_pipeline_live import e2e_test; e2e_test()"
```

### 4. Automation (Cronjob)
For the daily automated run without the Hermes runtime, the local script `daily_report.sh` is used. This uses the local `venv` and exits cleanly on missing data or tools (Fail-Fast).

**Cronjob Setup:**
1. Ensure the script is executable: `chmod +x daily_report.sh`
2. Open crontab: `crontab -e`
3. Add the following entry (example for daily run at 08:00):
```cron
0 8 * * * /path/to/your/project/daily_report.sh >> /path/to/your/project/cron_output.log 2>&1
```

*Note: The script logs all details additionally in `logs/runs/`.*

## 📈 Roadmap (V2)
- [ ] **Real API Integration:** Replace scraping with professional financial APIs (e.g., *Alpha Vantage* or *Polygon.io*).
- [ ] **Extended Data Sources:** Integration of crypto data and VC funding news.
- [ ] **Visualization:** Dashboard for displaying the score history.

---
*Developed with Hermes Agent (by Nous Research)*
