---
name: transcribe-cantonese
description: Transcribe a Cantonese audio file to text using Faster Whisper. Use ONLY when the user explicitly says "use skill transcribe-cantonese" followed by an audio filename. Saves transcription as a .txt file next to the audio file.
---

# Transcribe Cantonese

Transcribe a Cantonese audio file to text using Faster Whisper (local, no API key needed).

## Workflow

1. Extract the audio filename from the user's message
2. Run `scripts/transcribe_cantonese.py {filename}` to transcribe
3. The transcription is saved as `{filename}_transcription.txt`
4. Present the transcription to the user

## Trigger Examples

- `use skill transcribe-cantonese speech-Cantonese.mp3`
- `用技能转录粤语 speech-Cantonese.mp3`

## Important

- Run `scripts/transcribe_cantonese.py` only once per request
- Do NOT retry if the script exits with code 0

## Setup

```bash
pip install faster-whisper
```
