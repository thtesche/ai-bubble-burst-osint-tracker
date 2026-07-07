import os
import json
import re
from datetime import datetime

class RunLogger:
    """
    Verantwortlich für das Speichern des gesamten Datenflusses eines Runs.
    Nutzt einen absoluten Pfad zum Projekt-Root, um sicherzustellen, 
    dass Logs im lokalen Dateisystem des Nutzers landen.
    """
    def __init__(self, base_dir="logs/runs"):
        # Wir versuchen den Projekt-Root zu finden oder nutzen das aktuelle CWD
        # In der Hermes-Runtime ist das CWD meist der Projekt-Root.
        self.project_root = os.environ.get("PROJECT_ROOT", os.getcwd())
        
        # Wir bauen den Pfad absolut auf
        self.base_dir = os.path.abspath(os.path.join(self.project_root, base_dir))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(self.base_dir, self.timestamp)
        self.content_dir = os.path.join(self.run_dir, "extracted_content")
        self._setup_dirs()

    def _setup_dirs(self):
        os.makedirs(self.content_dir, exist_ok=True)
        print(f"[*] Run logger initialized. Logs will be saved to: {self.run_dir}")

    def save_search_results(self, stage: str, data: dict):
        """Speichert die rohen Suchergebnisse."""
        file_path = os.path.join(self.run_dir, f"{stage}_search_results.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"[LOG] Saved search results for {stage} to {file_path}")

    def save_content(self, stage: str, identifier: str, content: str):
        """Speichert extrahierten Text in einer Datei."""
        # Sicherstellen, dass der Dateiname keine ungültigen Zeichen enthält
        safe_id = re.sub(r'[^\w\-]', '_', identifier)
        file_path = os.path.join(self.content_dir, f"{stage}_{safe_id}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_summary(self, summary: dict):
        """Speichert die Zusammenfassung des Runs."""
        file_path = os.path.join(self.run_dir, "run_summary.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4)
        print(f"[LOG] Run summary saved to {file_path}")
