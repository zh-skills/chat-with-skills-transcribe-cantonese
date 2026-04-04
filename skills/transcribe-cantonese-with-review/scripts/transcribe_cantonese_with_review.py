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


def load_corrections(corrections_file: str) -> dict:
    """Load word corrections from file. Format: wrong，correct (one per line)."""
    corrections = {}
    if not os.path.isfile(corrections_file):
        return corrections
    with open(corrections_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Support both ，(full-width) and ,(half-width) as separator
            parts = line.replace('，', ',').split(',', 1)
            if len(parts) == 2:
                wrong, correct = parts[0].strip(), parts[1].strip()
                if wrong and correct:
                    corrections[wrong] = correct
    return corrections


def apply_corrections(text: str, corrections: dict) -> str:
    """Apply word-level corrections to text."""
    for wrong, correct in corrections.items():
        text = text.replace(wrong, correct)
    return text


def review_with_llm(text: str, llm_fn, ref_file: str = None, corrections_file: str = None) -> str:
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
        import re as _re

        # Try to split text into segments matching reference sentence lengths
        # First try punctuation splits
        segments = _re.split(r'[，,。！？\n]+', text)
        segments = [s.strip() for s in segments if s.strip()]

        # If only one segment (no punctuation), try to split by matching reference boundaries
        if len(segments) == 1 and len(matched) > 1:
            remaining = text
            new_segments = []
            for ref in matched:
                # Find where this reference best fits in remaining text
                best_pos = 0
                best_score = 0
                for i in range(len(remaining)):
                    window = remaining[i:i+len(ref)+5]
                    score = sum(c in window for c in ref) / max(len(ref), 1)
                    if score > best_score:
                        best_score = score
                        best_pos = i
                if best_score >= 0.5:
                    if best_pos > 0:
                        new_segments.append(remaining[:best_pos])
                    new_segments.append(remaining[best_pos:best_pos+len(ref)+2])
                    remaining = remaining[best_pos+len(ref)+2:]
            if remaining:
                new_segments.append(remaining)
            if len(new_segments) > 1:
                segments = [s.strip() for s in new_segments if s.strip()]

        corrected_lines = []
        for seg in segments:
            best = max(matched, key=lambda s: sum(c in seg for c in s) / max(len(s), 1))
            score = sum(c in seg for c in best) / max(len(best), 1)
            if score >= 0.5:
                corrected_lines.append(best)
            else:
                corrected_lines.append(seg)
        result = "\n".join(corrected_lines)
        # Apply word corrections on top of reference matching
        if corrections_file:
            corrections = load_corrections(corrections_file)
            result = apply_corrections(result, corrections)
        return result

    # Fallback: ask LLM to correct without reference
    try:
        prompt = f"粵語校對，只糾正明顯錯誤，只返回更正後文本：\n{text}"
        corrected = llm_fn([{"role": "user", "content": prompt}]).strip()
        if corrections_file:
            corrections = load_corrections(corrections_file)
            corrected = apply_corrections(corrected, corrections)
        return corrected
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
        # Look for Cantonese-sentences.txt in assets/ next to the script, then fallback locations
        ref_file = None
        corrections_file = None
        script_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(script_dir, '..', 'assets')
        for search_dir in [assets_dir, os.path.dirname(audio_path), os.getcwd()]:
            if ref_file is None:
                candidate = os.path.join(search_dir, "Cantonese-sentences.txt")
                if os.path.isfile(candidate):
                    ref_file = candidate
            if corrections_file is None:
                candidate = os.path.join(search_dir, "Cantonese-corrections.txt")
                if os.path.isfile(candidate):
                    corrections_file = candidate
        corrected = review_with_llm(raw, llm_fn, ref_file=ref_file, corrections_file=corrections_file)
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
