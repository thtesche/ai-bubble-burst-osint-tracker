# AI-Bubble-Burst-OSINT-Tracker 🫧📉

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Framework](https://img.shields.io/badge/framework-Astro-ff5d01.svg)
![Agent](https://img.shields.io/badge/agent-pi.dev-green.svg)

## 👁️ Vision
The **AI-Bubble-Burst-OSINT-Tracker** is an autonomous analysis system that asks the question: *When will the AI bubble burst?* 

Instead of waiting for human analysis, this project uses a specialized agent architecture to collect Open Source Intelligence (OSINT) daily. By correlating cloud infrastructure spending (CapEx), startup funding cycles, and technological breakthroughs, the system calculates a daily "Bubble Probability Score".

## 🏗️ Architecture: The "Lean Agent" Approach
Unlike heavy frameworks (such as LangChain or CrewAI), this project focuses on maximum efficiency and local control:

* **Orchestration:** A lightweight Bash script controls the workflow.
* **Agentic Engine:** Uses the `pi.dev` CLI tool in print mode (`-p`). This allows for precise control of the agent logic without unnecessary overhead.
* **Local Intelligence:** Inference is performed entirely locally via an inference server hosting a **Gemma 4 (31B)** model. This guarantees data privacy and independence from cloud providers.
* **Data Pipeline:** The agent generates structured Markdown files that serve as the "Single Source of Truth".
* **Frontend:** A high-performance, static website based on **Astro**, which consumes the Markdown data via *Content Collections*.

## 🛠️ Tech Stack
- **Agent Engine:** `pi.dev` (CLI)
- **LLM:** Gemma 4 (31B) via Local Inference Server
- **Frontend:** [Astro](https://astro.build/) (i18n ready, Static Site Generation)
- **Deployment:** GitHub Actions -> GitHub Pages
- **Automation:** Cronjobs (Bash/Git)

## 🚀 Installation & Setup

### Prerequisites
- `pi.dev` CLI installed and in your PATH.
- A running local inference server (compatible with `pi.dev` configuration).
- Git & Node.js (for the Astro frontend).

### Local Development
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-repo/ai-bubble-burst-osint-tracker.git
   cd ai-bubble-burst-osint-tracker
   ```

2. **Test the agent:**
   Run the bootstrap script manually to trigger the first analysis:
   ```bash
   chmod +x scripts/run_agent.sh
   ./scripts/run_agent.sh
   ```

3. **Start the frontend:**
   ```bash
   cd web/
   npm install
   npm run dev
   ```

## 📅 Workflow & Deployment
The process is fully automated:
1. **Trigger:** A daily cronjob starts `scripts/run_agent.sh`.
2. **Analysis:** The agent performs web scraping and writes a new `.md` file to `web/src/content/reports/`.
3. **Commit:** The script automatically commits the new file to the repository.
4. **Build:** GitHub Actions detects the push, builds the Astro project, and deploys it to GitHub Pages.
