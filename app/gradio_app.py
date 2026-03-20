import asyncio
import sys
import gradio as gr
import json
import csv
import os
import speech_recognition as sr
from difflib import SequenceMatcher, get_close_matches
from datetime import datetime
from collections import Counter

# --- Fix Windows asyncio event loop issues ---
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

LEXICON_PATH = os.path.join("lexicon", "kabras_lexicon.json")
LOG_PATH = "translations_log.json"

# --- Load lexicon ---
def load_lexicon():
    with open(LEXICON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "phrases" in data:
        lexicon = data["phrases"]
    else:
        lexicon = data
    lexicon_dict = {}
    for entry in lexicon:
        kabras_word = entry.get("kabras") or entry.get("Kabras") or entry.get("word")
        english_word = entry.get("english") or entry.get("translation")
        if kabras_word and english_word:
            lexicon_dict[kabras_word.lower()] = english_word
    return lexicon_dict

translation_dict = load_lexicon()


# ─────────────────────────────────────────────
# LOGGING (JSON + CSV)
# ─────────────────────────────────────────────
def log_translation(recognized_text, matched_phrase, translation, confidence):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "recognized_text": recognized_text,
        "matched_phrase": matched_phrase,
        "translation": translation,
        "confidence": confidence,
    }

    # JSON log
    try:
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                log_data = json.load(f)
        except FileNotFoundError:
            log_data = []
        log_data.append(entry)
        with open(LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    except Exception as err:
        print("Logging error (JSON):", err)

    # CSV log
    try:
        os.makedirs("datasets", exist_ok=True)
        csv_path = os.path.join("datasets", "translations_log.csv")
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "recognized_text", "matched_phrase", "translation", "confidence"])
            writer.writerow([
                entry["timestamp"], recognized_text,
                matched_phrase, translation, confidence
            ])
    except Exception as err:
        print("Logging error (CSV):", err)


# ─────────────────────────────────────────────
# TRANSLATION  (FIX 1: returns captured text via tuple for State)
# ─────────────────────────────────────────────
def kabras_to_english(audio_file):
    """
    Returns (result_text, captured_text) so Gradio State can carry
    the recognised phrase over to the Expand-Lexicon tab.
    """
    if not audio_file or not os.path.exists(audio_file):
        return "Error: No audio file received.", ""

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        # Try Swahili first, fallback to English
        try:
            recognized_text = recognizer.recognize_google(audio, language="sw")
        except sr.UnknownValueError:
            recognized_text = recognizer.recognize_google(audio, language="en")

        recognized_text = recognized_text.strip()
        print("Recognized:", recognized_text)

        output = f"Captured speech: {recognized_text}\n"

        # --- Exact match ---
        if recognized_text.lower() in translation_dict:
            translation = translation_dict[recognized_text.lower()]
            confidence = 100
            output += (
                f"Match type:    Exact\n"
                f"Matched phrase: {recognized_text}\n"
                f"Translation:   {translation}\n"
                f"Confidence:    {confidence}%"
            )
            log_translation(recognized_text, recognized_text, translation, confidence)
            return output, recognized_text

        # --- Fuzzy match  (FIX 2: cutoff lowered from 0.8 → 0.62) ---
        matches = get_close_matches(
            recognized_text.lower(),
            translation_dict.keys(),
            n=3,           # return top 3 candidates
            cutoff=0.62,
        )
        if matches:
            best_match = matches[0]
            confidence = int(
                SequenceMatcher(None, recognized_text.lower(), best_match).ratio() * 100
            )
            translation = translation_dict[best_match]

            # Show top alternatives if there are more
            alt_lines = ""
            for alt in matches[1:]:
                alt_conf = int(SequenceMatcher(None, recognized_text.lower(), alt).ratio() * 100)
                alt_lines += f"  • {alt} → {translation_dict[alt]}  ({alt_conf}%)\n"

            output += (
                f"Match type:    Fuzzy\n"
                f"Matched phrase: {best_match}\n"
                f"Translation:   {translation}\n"
                f"Confidence:    {confidence}%\n"
            )
            if alt_lines:
                output += f"Alternatives:\n{alt_lines}"

            log_translation(recognized_text, best_match, translation, confidence)
            return output, recognized_text

        # --- No match ---
        output += (
            "No translation found.\n"
            "Suggestion: Switch to the 'Expand Lexicon' tab to add this phrase.\n"
            "(The phrase has been pre-filled for you.)"
        )
        log_translation(recognized_text, None, None, 0)
        return output, recognized_text

    except sr.RequestError as err:
        return f"Error: Google Speech Recognition request failed: {err}", ""
    except Exception as err:
        return f"Error processing audio: {err}", ""


# ─────────────────────────────────────────────
# ADD NEW PHRASE
# ─────────────────────────────────────────────
def add_phrase(kabras_phrase, english_translation):
    kabras_phrase = kabras_phrase.strip()
    english_translation = english_translation.strip()
    if not kabras_phrase or not english_translation:
        return "Error: Both fields are required."
    try:
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Avoid duplicates
        existing = [e.get("kabras", "").lower() for e in data.get("phrases", [])]
        if kabras_phrase.lower() in existing:
            return f"'{kabras_phrase}' already exists in the lexicon."
        data["phrases"].append({"kabras": kabras_phrase, "english": english_translation})
        with open(LEXICON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        global translation_dict
        translation_dict = load_lexicon()
        return f"✓ Added: {kabras_phrase} → {english_translation}\nLexicon now has {len(translation_dict)} entries."
    except Exception as err:
        return f"Error adding phrase: {err}"


# ─────────────────────────────────────────────
# VIEW HISTORY
# ─────────────────────────────────────────────
def view_history():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        formatted = ""
        for entry in reversed(log_data[-20:]):
            formatted += (
                f"[{entry['timestamp']}]\n"
                f"  Captured:    {entry['recognized_text']}\n"
                f"  Matched:     {entry['matched_phrase']}\n"
                f"  Translation: {entry['translation']}\n"
                f"  Confidence:  {entry['confidence']}%\n\n"
            )
        return formatted if formatted else "No history yet."
    except FileNotFoundError:
        return "No history log found."
    except Exception as err:
        return f"Error reading history: {err}"


# ─────────────────────────────────────────────
# ADMIN: UNMATCHED PHRASES  (NEW)
# ─────────────────────────────────────────────
def view_unmatched():
    """
    Surfaces all phrases that had no match, sorted by frequency.
    This tells you exactly which gaps to fill in the lexicon first.
    """
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
    except FileNotFoundError:
        return "No log file found yet."

    unmatched = [
        e["recognized_text"]
        for e in log_data
        if e.get("matched_phrase") is None and e.get("recognized_text")
    ]

    if not unmatched:
        return "No unmatched phrases yet — great coverage!"

    counts = Counter(unmatched)
    lines = [f"{'Count':>5}  Phrase\n" + "─" * 40]
    for phrase, count in counts.most_common():
        lines.append(f"{count:>5}  {phrase}")

    summary = (
        f"Total unmatched attempts: {len(unmatched)}\n"
        f"Unique unmatched phrases: {len(counts)}\n\n"
    )
    return summary + "\n".join(lines)


# ─────────────────────────────────────────────
# EXPORT HISTORY
# ─────────────────────────────────────────────
def export_history_file(format_choice):
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        os.makedirs("datasets", exist_ok=True)

        if format_choice == "JSON":
            filename = os.path.join("datasets", "exported_history.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            return filename

        elif format_choice == "CSV":
            filename = os.path.join("datasets", "exported_history.csv")
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "recognized_text", "matched_phrase", "translation", "confidence"])
                for entry in log_data:
                    writer.writerow([
                        entry["timestamp"], entry["recognized_text"],
                        entry["matched_phrase"], entry["translation"], entry["confidence"]
                    ])
            return filename

        return None
    except FileNotFoundError:
        return None
    except Exception as err:
        print("Export error:", err)
        return None


# ─────────────────────────────────────────────
# GRADIO UI  (FIX 3: proper State for captured text)
# ─────────────────────────────────────────────
with gr.Blocks(title="Kabras AI Translator") as demo:
    gr.Markdown("# 🗣️ Kabras AI Translator\nSpeech translation for the Kabras language (Luhya dialect, Western Kenya)")

    # Shared state: carries the last recognised phrase across tabs
    captured_state = gr.State("")

    with gr.Tabs():

        # ── Tab 1: Translate ──────────────────────────
        with gr.TabItem("Translate"):
            gr.Markdown("Record or upload Kabras speech to translate it to English.")
            audio_input = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Kabras audio")
            translate_btn = gr.Button("Translate", variant="primary")
            translation_output = gr.Textbox(label="Result", lines=8, interactive=False)

            translate_btn.click(
                fn=kabras_to_english,
                inputs=[audio_input],
                outputs=[translation_output, captured_state],
            )

        # ── Tab 2: Expand Lexicon ─────────────────────
        with gr.TabItem("Expand Lexicon"):
            gr.Markdown(
                "Add a new phrase to the lexicon. "
                "If you just translated and got 'no match', the phrase is pre-filled below."
            )
            kabras_input = gr.Textbox(label="Kabras phrase")
            english_input = gr.Textbox(label="English translation")
            add_btn = gr.Button("Add to lexicon", variant="primary")
            add_output = gr.Textbox(label="Result", interactive=False)

            # FIX: when the tab becomes active, copy captured_state into the textbox
            # Gradio 4.x approach: use a load trigger on the tab via a helper button,
            # or wire the state update via a separate invisible component.
            # Cleanest reliable method: a "Load last capture" button.
            load_btn = gr.Button("↙ Load last captured phrase", size="sm")
            load_btn.click(fn=lambda s: s, inputs=[captured_state], outputs=[kabras_input])

            add_btn.click(
                fn=add_phrase,
                inputs=[kabras_input, english_input],
                outputs=[add_output],
            )

        # ── Tab 3: History ────────────────────────────
        with gr.TabItem("History"):
            gr.Markdown("Last 20 translation attempts (newest first).")
            refresh_btn = gr.Button("Refresh")
            history_output = gr.Textbox(label="History", lines=20, interactive=False)
            refresh_btn.click(fn=view_history, inputs=[], outputs=[history_output])

        # ── Tab 4: Admin — Unmatched Phrases (NEW) ───
        with gr.TabItem("Admin: Gaps"):
            gr.Markdown(
                "### Lexicon gap analysis\n"
                "Shows every phrase with no translation match, sorted by frequency. "
                "Use this to prioritise which phrases to add next."
            )
            gaps_btn = gr.Button("Analyse gaps")
            gaps_output = gr.Textbox(label="Unmatched phrases (most frequent first)", lines=20, interactive=False)
            gaps_btn.click(fn=view_unmatched, inputs=[], outputs=[gaps_output])

        # ── Tab 5: Export ─────────────────────────────
        with gr.TabItem("Export"):
            gr.Markdown("Download the full translation log as JSON or CSV.")
            format_radio = gr.Radio(choices=["JSON", "CSV"], label="Export format", value="CSV")
            export_btn = gr.Button("Export")
            export_output = gr.File(label="Download")
            export_btn.click(fn=export_history_file, inputs=[format_radio], outputs=[export_output])


if __name__ == "__main__":
    demo.launch()