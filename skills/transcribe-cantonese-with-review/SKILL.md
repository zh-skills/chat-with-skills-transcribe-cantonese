---
name: transcribe-cantonese-with-review
description: Transcribe a Cantonese audio file to text using Faster Whisper, then review and correct using reference sentences from assets/Cantonese-sentences.txt. Use ONLY when the user explicitly says "use skill transcribe-cantonese-with-review" followed by an audio filename.
---

# Transcribe Cantonese with Review

Transcribe a Cantonese audio file, then automatically correct the transcription by matching against a reference sentence library.

## Workflow

1. Extract the audio filename from the user's message
2. Run `scripts/transcribe_cantonese_with_review.py {filename}` to transcribe and review
3. The script matches each transcribed segment against `assets/Cantonese-sentences.txt`
4. If a reference sentence has >50% similarity, it replaces the transcribed segment
5. The corrected transcription is saved as `{filename}_transcription.txt`

## Trigger Examples

- `use skill transcribe-cantonese-with-review speech-Cantonese.mp3`
- `用技能转录粤语并校对 speech-Cantonese.mp3`

## Important

- Run `scripts/transcribe_cantonese_with_review.py` only once per request
- Reference sentences are in `assets/Cantonese-sentences.txt` — add your own sentences there

## Setup

```bash
pip install faster-whisper
```

## Reference

The `assets/Cantonese-sentences.txt` file contains reference sentences used for correction.
