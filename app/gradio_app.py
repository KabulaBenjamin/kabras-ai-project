import asyncio
import sys
import gradio as gr
import json
import csv
import os
import speech_recognition as sr
from difflib import SequenceMatcher, get_close_matches
from datetime import datetime

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
last_captured = {"text": ""}

def log_translation(recognized_text, matched_phrase, translation, confidence):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "recognized_text": recognized_text,
        "matched_phrase": matched_phrase,
        "translation": translation,
        "confidence": confidence
    }
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
        print("Logging error:", err)

def kabras_to_english(audio_file):
    if not audio_file or not os.path.exists(audio_file):
        return "Error: No audio file received."

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

        last_captured["text"] = recognized_text
        output = f"Captured speech: {recognized_text}\n"

        # Exact match
        if recognized_text.lower() in translation_dict:
            translation = translation_dict[recognized_text.lower()]
            confidence = 100
            output += f"Matched phrase: {recognized_text}\nTranslation: {translation}\nConfidence: {confidence}%"
            log_translation(recognized_text, recognized_text, translation, confidence)
            return output

        # Fuzzy match with cutoff=1.0
        matches = get_close_matches(recognized_text.lower(), translation_dict.keys(), n=1, cutoff=1.0)
        if matches:
            best_match = matches[0]
            confidence = int(SequenceMatcher(None, recognized_text.lower(), best_match).ratio() * 100)
            translation = translation_dict[best_match]
            output += f"Matched phrase: {best_match}\nTranslation: {translation}\nConfidence: {confidence}%"
            log_translation(recognized_text, best_match, translation, confidence)
            return output

        # No match
        output += "No translation found.\nSuggestion: Add this phrase to the lexicon."
        log_translation(recognized_text, None, None, 0)
        return output

    except sr.RequestError as err:
        return f"Error: Google Speech Recognition request failed: {err}"
    except Exception as err:
        return f"Error processing audio: {err}"

def add_phrase(kabras_phrase, english_translation):
    try:
        with open(LEXICON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["phrases"].append({"kabras": kabras_phrase, "english": english_translation})
        with open(LEXICON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        global translation_dict
        translation_dict = load_lexicon()
        return f"Added new phrase: {kabras_phrase} → {english_translation}"
    except Exception as err:
        return f"Error adding phrase: {err}"

def view_history():
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        formatted = ""
        for entry in log_data[-20:]:
            formatted += (
                f"{entry['timestamp']}\n"
                f"Captured: {entry['recognized_text']}\n"
                f"Matched: {entry['matched_phrase']}\n"
                f"Translation: {entry['translation']}\n"
                f"Confidence: {entry['confidence']}%\n\n"
            )
        return formatted if formatted else "No history yet."
    except FileNotFoundError:
        return "No history log found."
    except Exception as err:
        return f"Error reading history: {err}"

def export_history_file(format_choice):
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            log_data = json.load(f)
        if format_choice == "JSON":
            filename = "exported_history.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            return filename
        elif format_choice == "CSV":
            filename = "exported_history.csv"
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "recognized_text", "matched_phrase", "translation", "confidence"])
                for entry in log_data:
                    writer.writerow([entry["timestamp"], entry["recognized_text"], entry["matched_phrase"], entry["translation"], entry["confidence"]])
            return filename
        return None
    except FileNotFoundError:
        return None
    except Exception as err:
        print("Export error:", err)
        return None

# --- Gradio interface ---
translate_tab = gr.Interface(
    fn=kabras_to_english,
    inputs=gr.Audio(sources=["microphone", "upload"], type="filepath"),
    outputs="text",
    title="Kabras Speech Translator (Google Speech Recognition, Swahili + English fallback)"
)

expand_tab = gr.Interface(
    fn=add_phrase,
    inputs=[
        gr.Textbox(label="Kabras phrase", value=lambda: last_captured["text"]),
        gr.Textbox(label="English translation")
    ],
    outputs="text",
    title="Add New Phrase"
)

history_tab = gr.Interface(
    fn=view_history,
    inputs=[],
    outputs="text",
    title="Translation History"
)

export_tab = gr.Interface(
    fn=export_history_file,
    inputs=gr.Radio(choices=["JSON", "CSV"], label="Export format"),
    outputs=gr.File(label="Download Exported History"),
    title="Export History Log"
)

demo = gr.TabbedInterface(
    [translate_tab, expand_tab, history_tab, export_tab],
    tab_names=["Translate", "Expand Lexicon", "History", "Export"]
)

if __name__ == "__main__":
    demo.launch()