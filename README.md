# AI-Bubble-OSINT-Tracker 🫧📉

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Framework](https://img.shields.io/badge/framework-Astro-ff5d01.svg)
![Agent](https://img.shields.io/badge/agent-pi.dev-green.svg)

## 👁️ Vision
Der **AI-Bubble-OSINT-Tracker** ist ein autonomes Analyse-System, das die Frage stellt: *Wann platzt die KI-Blase?* 

Anstatt auf menschliche Analysen zu warten, nutzt das Projekt eine spezialisierte Agenten-Architektur, um täglich Open Source Intelligence (OSINT) zu sammeln. Durch die Korrelation von Cloud-Infrastruktur-Ausgaben (CapEx), Startup-Finanzierungszyklen und technologischen Durchbrüchen berechnet das System eine tägliche "Bubble Probability Score".

## 🏗️ Architektur: Der "Lean Agent" Ansatz
Im Gegensatz zu schwerfälligen Frameworks (wie LangChain oder CrewAI) setzt dieses Projekt auf maximale Effizienz und lokale Kontrolle:

* **Orchestrierung:** Ein schlankes Bash-Skript steuert den Workflow.
* **Agentic Engine:** Nutzung des `pi.dev` CLI-Tools im Print-Modus (`-p`). Dies ermöglicht eine präzise Steuerung der Agenten-Logik ohne unnötigen Overhead.
* **Local Intelligence:** Die Inferenz erfolgt vollständig lokal über einen Inferenz-Server, der ein **Gemma 4 (31B)** Modell hostet. Dies garantiert Datenschutz und Unabhängigkeit von Cloud-Providern.
* **Data Pipeline:** Der Agent generiert strukturierte Markdown-Dateien, die als "Single Source of Truth" dienen.
* **Frontend:** Eine hochperformante, statische Webseite auf Basis von **Astro**, die die Markdown-Daten via *Content Collections* konsumiert.

## 🛠️ Tech Stack
- **Agent Engine:** `pi.dev` (CLI)
- **LLM:** Gemma 4 (31B) via Local Inference Server
- **Frontend:** [Astro](https://astro.build/) (i18n ready, Static Site Generation)
- **Deployment:** GitHub Actions -> GitHub Pages
- **Automation:** Cronjobs (Bash/Git)

## 🚀 Installation & Setup

### Voraussetzungen
- `pi.dev` CLI installiert und im PATH.
- Ein laufender lokaler Inferenz-Server (kompatibel mit `pi.dev` Konfiguration).
- Git & Node.js (für das Astro Frontend).

### Lokale Entwicklung
1. **Repository klonen:**
   ```bash
   git clone https://github.com/your-repo/ai-bubble-osint-tracker.git
   cd ai-bubble-osint-tracker
   ```

2. **Agenten testen:**
   Führen Sie das Bootstrap-Skript manuell aus, um die erste Analyse zu triggern:
   ```bash
   chmod +x scripts/run_agent.sh
   ./scripts/run_agent.sh
   ```

3. **Frontend starten:**
   ```bash
   cd web/
   npm install
   npm run dev
   ```

## 📅 Workflow & Deployment
Der Prozess ist vollautomatisiert:
1. **Trigger:** Ein täglicher Cronjob startet `scripts/run_agent.sh`.
2. **Analysis:** Der Agent führt Web-Scraping durch und schreibt eine neue `.md` Datei in `web/src/content/reports/`.
3. **Commit:** Das Skript committet die neue Datei automatisch in das Repository.
4. **Build:** GitHub Actions erkennt den Push, baut das Astro-Projekt und deployt es auf GitHub Pages.
