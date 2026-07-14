import os
import json
import re
from datetime import datetime

class RunLogger:
    """
    Responsible for saving the entire data flow of a Run.
    Uses an absolute path to the project root to ensure
    that logs end up in the user's local file system.
    """
    def __init__(self, base_dir="logs/runs"):
        # We attempt to find the project root or use the current CWD
        # In the Hermes runtime, the CWD is usually the project root.
        self.project_root = os.environ.get("PROJECT_ROOT", os.getcwd())
        
        # Build the path absolutely
        self.base_dir = os.path.abspath(os.path.join(self.project_root, base_dir))
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(self.base_dir, self.timestamp)
        self.content_dir = os.path.join(self.run_dir, "extracted_content")
        self._setup_dirs()

    def _setup_dirs(self):
        os.makedirs(self.content_dir, exist_ok=True)
        print(f"[*] Run logger initialized. Logs will be saved to: {self.run_dir}")

    def save_search_results(self, stage: str, data: dict):
        """Saves the raw search results."""
        file_path = os.path.join(self.run_dir, f"{stage}_search_results.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        print(f"[LOG] Saved search results for {stage} to {file_path}")

    def save_content(self, stage: str, identifier: str, content: str):
        """Saves extracted text to a file."""
        # Ensure the filename doesn't contain invalid characters
        safe_id = re.sub(r'[^\w\-]', '_', identifier)
        file_path = os.path.join(self.content_dir, f"{stage}_{safe_id}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def save_summary(self, summary: dict):
        """Saves the run summary."""
        file_path = os.path.join(self.run_dir, "run_summary.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4)
        print(f"[LOG] Run summary saved to {file_path}")
