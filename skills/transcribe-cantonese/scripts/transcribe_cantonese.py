#!/usr/bin/env python3
"""
transcribe_cantonese.py — Transcribe a Cantonese audio file to text using Faster Whisper.
Saves transcription as a .txt file next to the audio file.

Setup (first time only):
    pip install faster-whisper

Usage:
    python transcribe_cantonese.py {audio_file}

Examples:
    python transcribe_cantonese.py speech-Cantonese.mp3
    python transcribe_cantonese.py voice.mp3
"""

import sys
import os
import re
import subprocess


def ensure_faster_whisper():
    try:
        from faster_whisper import WhisperModel  # noqa
        return True
    except ImportError:
        print("⚠️ faster-whisper not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'faster-whisper'],
                       capture_output=True)
        try:
            from faster_whisper import WhisperModel  # noqa
            return True
        except ImportError:
            print("❌ faster-whisper install failed. Run: pip install faster-whisper")
            return False


def transcribe_cantonese(audio_path: str) -> str:
    if not os.path.isfile(audio_path):
        return f"❌ File not found: {audio_path}"

    if not ensure_faster_whisper():
        return "❌ faster-whisper not available."

    from faster_whisper import WhisperModel

    try:
        print(f"Loading Whisper model...")
        model = WhisperModel("small", device="cpu", compute_type="int8")

        print(f"Transcribing {audio_path} (Cantonese/Chinese)...")
        segments, info = model.transcribe(
            audio_path, language="zh", beam_size=5,
            vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500)
        )

        lines = []
        current_line = []
        prev_end = None
        PAUSE_THRESHOLD = 0.5

        for seg in segments:
            gap = (seg.start - prev_end) if prev_end is not None else 0
            if prev_end is not None and gap >= PAUSE_THRESHOLD:
                if current_line:
                    lines.append("".join(current_line).strip())
                    current_line = []
            current_line.append(seg.text)
            prev_end = seg.end
        if current_line:
            lines.append("".join(current_line).strip())

        if not lines or not any(l.strip() for l in lines):
            return "❌ No speech detected in the audio file."

        transcription = "\n".join(l for l in lines if l.strip())

        # Save to txt file next to audio
        output_path = os.path.splitext(audio_path)[0] + "_transcription.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcription)

        return f"📝 Transcription:\n{transcription}\n\n[Saved to {output_path}]"

    except Exception as e:
        return f"❌ Transcription failed: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: transcribe_cantonese.py {audio_file}")
        sys.exit(1)
    audio_file = ' '.join(sys.argv[1:])
    print(transcribe_cantonese(audio_file))
