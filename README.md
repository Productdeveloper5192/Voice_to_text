# Multilingual Voice to Text

A Streamlit app that listens to your microphone in any of 13 languages, transcribes it, auto-translates non-English speech to English, and accumulates everything into a downloadable note — with live microphone diagnostics so a noisy mic doesn't just silently fail.

## What It Does

- **Speech-to-text** in 13 languages (English, 8 Indian languages, Spanish, French, German, Japanese) via Google's speech recognition.
- **Auto-translation to English** for any non-English capture, so the working note is always in one language regardless of what was spoken.
- **Accumulating note** — each successful capture is appended to a running note, editable inline, and downloadable as a `.txt` file.
- **Mic diagnostics built in** — background-noise calibration, an adjustable energy/pause threshold, a live sensitivity readout, and specific on-screen troubleshooting tips when recognition fails (e.g. "your noise floor is high, uncheck auto-adjust and lower the slider").

## End-to-End Flow

```
 User picks a microphone + speaking language, clicks "Start Recording"
        │
        ▼
 SpeechRecognition opens the selected mic
   - if "Auto-Adjust for Noise" is on: samples 1s of ambient noise to
     set the energy threshold, then nudges it down 20% to catch
     quieter speech
   - "🔴 SPEAK NOW" cue shown once calibration completes
        │
        ▼
 r.listen() captures audio (10s timeout to start, 15s max phrase length)
        │
        ▼
 Captured audio is played back in the UI immediately, so the user can
 confirm their voice was actually picked up
        │
        ▼
 r.recognize_google(audio, language=<selected>) -> raw transcript
        │
        ├── selected language == English -> used as-is
        │
        └── selected language != English
                    │
                    ▼
             googletrans translates the transcript to English
        │
        ▼
 Result appended to the running note (session state), and the
 original + translated text shown as a persistent "Last Capture" card
        │
        ▼
 User can keep recording (each capture appends), edit the note text
 area directly, or download the accumulated note as voice_note.txt
```

If recognition fails, the app doesn't just show a generic error — it inspects the current energy threshold and gives a targeted suggestion (e.g. lower the noise slider, or that the mic likely didn't pick up any audio at all), since silent/garbled captures are the most common failure mode with browser/OS microphone permissions.

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Speech capture & recognition | `SpeechRecognition` (Google Web Speech API) |
| Translation | `googletrans` |
| Audio I/O | `PyAudio` (microphone access) |

## Setup

```bash
pip install -r requirements.txt
```

`PyAudio` (required for microphone access) needs system audio libraries on some platforms:
- **Windows**: usually installs cleanly via pip.
- **macOS**: `brew install portaudio` before `pip install pyaudio`.
- **Linux**: `sudo apt-get install portaudio19-dev` before `pip install pyaudio`.

## Run

```bash
streamlit run voice_to_text.py
```
Open the URL Streamlit prints (typically `http://localhost:8501`), grant microphone access when prompted, pick your language and mic in the sidebar, and click **Start Recording**.

## Known Limitations

- `recognize_google` and `googletrans` both call free, unofficial/undocumented Google endpoints (not a paid API key) — they can rate-limit or break without notice if Google changes the underlying web service. For production use, swapping in the paid Google Cloud Speech-to-Text and Cloud Translation APIs would be the reliable path.
- Recognition accuracy depends heavily on mic quality and ambient noise; the built-in calibration and threshold sliders exist specifically to compensate for this.
