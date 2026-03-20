# Kabras AI Translator

A speech translation app for the **Kabras language** — a Luhya dialect spoken in Western Kenya. Built to support language preservation through accessible AI tooling.

## Features

- 🎙️ Live microphone recording or audio file upload
- 🔍 Exact and fuzzy matching against a growing Kabras lexicon
- 📊 Confidence scoring with top alternative matches
- 📝 Dual logging to JSON and CSV for research use
- ➕ In-app lexicon expansion with duplicate detection
- 🔎 Admin gap analysis — surfaces most-needed phrases by frequency
- 📤 Export translation history as JSON or CSV

## Project structure

```
kabras-ai-project/
├── app/
│   ├── gradio_app.py       # Main Gradio UI and all logic
│   ├── main.py             # Entry point — run this
│   ├── lexicon/
│   │   └── kabras_lexicon.json
│   ├── datasets/
│   │   └── translations_log.csv   # Auto-generated on first translation
│   └── config/
│       └── settings.yaml
├── docs/
│   └── README.md
└── requirements.txt
```

## Setup

```bash
git clone https://github.com/KabulaBenjamin/kabras-ai-project.git
cd kabras-ai-project
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Run

```bash
python app/main.py
```

Then open [http://127.0.0.1:7860](http://127.0.0.1:7860) in your browser.

## How it works

1. Audio is captured via microphone or file upload
2. Google Speech Recognition transcribes it (Swahili first, English fallback)
3. The transcription is matched against `kabras_lexicon.json`:
   - **Exact match** → 100% confidence
   - **Fuzzy match** (≥ 62% similarity) → confidence score + alternatives shown
   - **No match** → logged and flagged for lexicon expansion
4. Every attempt is logged to `datasets/translations_log.csv`

## Research companion

This app generates the dataset used by the
[kabras-asr-research](https://github.com/KabulaBenjamin/kabras-asr-research)
project for WER analysis and confidence visualisations.

## Contributing

To add new Kabras phrases, use the **Expand Lexicon** tab in the app,
or edit `lexicon/kabras_lexicon.json` directly following this format:

```json
{
  "phrases": [
    { "kabras": "mlembe", "english": "Hello" },
    { "kabras": "orienna", "english": "How are you?" }
  ]
}
```

## Author

**Benjamin Kabula Koikoi**
Evangelist, North West Kenya Conference — Seventh-day Adventist Church
Software Developer | [GitHub](https://github.com/KabulaBenjamin)
