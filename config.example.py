# config.example.py — Copy this file to config.py and edit LOG_PATH
# config.py itself is NOT tracked by git (it has your local machine path)

import os

# ── EDIT THIS LINE ONLY ───────────────────────────────────────────────────
LOG_PATH = r"C:\Users\YOUR_USERNAME\MyProjects\kabras-ai-project\app\datasets\translations_log.csv"
# ─────────────────────────────────────────────────────────────────────────

RESEARCH_DIR = os.path.dirname(os.path.abspath(__file__))
DATASETS_DIR = os.path.join(RESEARCH_DIR, "datasets")
PLOTS_DIR    = os.path.join(RESEARCH_DIR, "analysis", "plots")

LOG_PATH = os.environ.get("KABRAS_LOG_PATH", LOG_PATH)

os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(PLOTS_DIR, exist_ok=True)


def check_log_exists():
    if not os.path.exists(LOG_PATH):
        raise FileNotFoundError(
            f"\n\nLog file not found:\n  {LOG_PATH}\n\n"
            "Fix: edit LOG_PATH in config.py to the correct path on your machine.\n"
        )
    return True
