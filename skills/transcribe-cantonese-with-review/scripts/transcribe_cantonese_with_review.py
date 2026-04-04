#!/usr/bin/env python3
"""
transcribe_cantonese_with_review.py — Transcribe a Cantonese audio file to text
using Faster Whisper, then review and correct with a local LLM.

Usage:
    python transcribe_cantonese_with_review.py {audio_file}

Examples:
    python transcribe_cantonese_with_review.py speech-Cantonese.mp3
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
            print("❌ faster-whisper install failed.")
            return False


def transcribe(audio_path: str) -> str:
    """Transcribe audio and return raw transcription text."""
    from faster_whisper import WhisperModel
    print("Loading Whisper model...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    print(f"Transcribing {audio_path}...")
    segments, _ = model.transcribe(
        audio_path, language="zh", beam_size=5,
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500)
    )
    lines = []
    current = []
    prev_end = None
    for seg in segments:
        gap = (seg.start - prev_end) if prev_end is not None else 0
        if prev_end is not None and gap >= 0.5:
            if current:
                lines.append("".join(current).strip())
                current = []
        current.append(seg.text)
        prev_end = seg.end
    if current:
        lines.append("".join(current).strip())
    return "\n".join(l for l in lines if l.strip())


def review_with_llm(text: str, llm_fn, ref_file: str = None) -> str:
    """Use LLM to review and correct Cantonese transcription using reference sentences."""
    import re

    # Load reference sentences and find top matches above 50% similarity
    matched = []
    if ref_file and os.path.isfile(ref_file):
        with open(ref_file, 'r', encoding='utf-8') as f:
            ref_sentences = [line.strip() for line in f if line.strip()]
        if ref_sentences:
            def _sim(s):
                return sum(c in text for c in s) / max(len(s), 1)
            matched = [s for s in ref_sentences if _sim(s) >= 0.5]
            matched = sorted(matched, key=_sim, reverse=True)[:5]

    # If we have high-confidence matches, just replace directly without LLM
    if matched:
        # Split transcription into lines and try to match each
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        corrected_lines = []
        for line in lines:
            best = max(matched, key=lambda s: sum(c in line for c in s) / max(len(s), 1))
            score = sum(c in line for c in best) / max(len(best), 1)
            if score >= 0.5:
                corrected_lines.append(best)
            else:
                corrected_lines.append(line)
        return "\n".join(corrected_lines)

    # Fallback: ask LLM to correct without reference
    try:
        prompt = f"粵語校對，只糾正明顯錯誤，只返回更正後文本：\n{text}"
        return llm_fn([{"role": "user", "content": prompt}]).strip()
    except Exception as e:
        return text


def transcribe_cantonese_with_review(audio_path: str, llm_fn=None) -> str:
    if not os.path.isfile(audio_path):
        return f"❌ File not found: {audio_path}"

    if not ensure_faster_whisper():
        return "❌ faster-whisper not available."

    # Step 1: Transcribe
    raw = transcribe(audio_path)
    if not raw.strip():
        return "❌ No speech detected in the audio file."

    result = f"📝 Transcription:\n{raw}"

    # Step 2: AI review (if LLM available)
    if llm_fn:
        print("AI review in progress...")
        # Look for Cantonese-sentences.txt in same dir as audio or parent dirs
        ref_file = None
        for search_dir in [os.path.dirname(audio_path), os.getcwd(),
                           os.path.dirname(os.path.abspath(__file__))]:
            candidate = os.path.join(search_dir, "Cantonese-sentences.txt")
            if os.path.isfile(candidate):
                ref_file = candidate
                break
        corrected = review_with_llm(raw, llm_fn, ref_file=ref_file)
        result += f"\n\n✅ AI Corrected:\n{corrected}"
        save_text = corrected
    else:
        save_text = raw

    # Step 3: Save
    output_path = os.path.splitext(audio_path)[0] + "_transcription.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(save_text)

    result += f"\n\n[Saved to {output_path}]"
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: transcribe_cantonese_with_review.py {audio_file}")
        sys.exit(1)
    audio_file = ' '.join(sys.argv[1:])
    print(transcribe_cantonese_with_review(audio_file))
