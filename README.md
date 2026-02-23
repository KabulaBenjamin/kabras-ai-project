# Kabras Speech Translator: Research on Low-Resource ASR

## Abstract
This project investigates automatic speech recognition (ASR) for Kabras, a low-resource dialect spoken in Western Kenya. By integrating Google Speech Recognition (Swahili + English fallback) with a community-curated Kabras–English lexicon, the system demonstrates how speech technology can support dialect preservation, agritech applications, and educational contexts. The research emphasizes fuzzy matching, confidence scoring, and structured logging to enable dataset growth and evaluation.

## Problem Statement
Mainstream ASR systems rarely support low-resource dialects. Kabras, despite its cultural significance, lacks digital tools for speech recognition and translation. This project addresses the gap by combining existing ASR models with lexicon-driven translation and logging, creating a foundation for future fine-tuning and dataset expansion.

## Methodology
- **Speech Recognition**: Google Speech Recognition API, configured for Swahili with English fallback.
- **Lexicon Expansion**: JSON-based Kabras–English dictionary, editable via Gradio interface.
- **Fuzzy Matching**: Implemented with `difflib`, cutoff set to 1.0 to ensure closest matches are always accepted.
- **Confidence Scoring**: SequenceMatcher ratio converted to percentage for evaluation.
- **Structured Logging**: Captures recognized text, matched phrase, translation, confidence, and timestamp.
- **Interface**: Gradio tabs for translation, lexicon expansion, history, and export.

## Experiments & Metrics
1. **Transcription Evaluation**
   - Word Error Rate (WER) calculated for recognized vs. reference text.
   - Comparison of Swahili vs. English fallback performance.

2. **Confidence Analysis**
   - Correlation between confidence scores and transcription accuracy.
   - Statistical visualization planned with Matplotlib/Seaborn.

3. **Dataset Analysis**
   - Count of unique Kabras phrases logged.
   - Distribution of unmatched phrases.
   - Frequency of fuzzy matches.

4. **Comparative Study**
   - Whisper small vs. base models (future work).
   - Google ASR vs. Whisper performance comparison.

## Results (Preliminary)
- Swahili recognition provides reliable transcription for common phrases.
- English fallback ensures robustness when Swahili fails.
- Fuzzy matching with cutoff=1.0 prevents rejection of near matches (e.g., *mulembe* → “hello/peace”).
- Logs demonstrate potential for dataset growth and fine-tuning.

## Discussion
The system highlights the feasibility of combining mainstream ASR with community-driven lexicon building. While Google ASR provides strong baseline transcription, the Kabras lexicon ensures cultural and linguistic relevance. Limitations include dependency on internet connectivity and lack of purely offline support. Future work involves fine-tuning Whisper with collected datasets and expanding lexicon coverage.

## Conclusion
This project contributes to research on speech technology for under-resourced dialects. By integrating Swahili recognition with Kabras lexicon expansion, it provides a reproducible framework for sustainable language technology development in agritech and education.

## References
- Jurafsky, D., & Martin, J. H. (2023). *Speech and Language Processing*. Pearson.
- Google Cloud. (2025). *Speech-to-Text API Documentation*. Retrieved from https://cloud.google.com/speech-to-text
- Python Software Foundation. (2026). *SpeechRecognition Library*. Retrieved from https://pypi.org/project/SpeechRecognition/

## Appendix
### Installation
```bash
git clone https://github.com/YOUR_USERNAME/kabras-speech-translator.git
cd kabras-speech-translator
pip install -r requirements.txt
