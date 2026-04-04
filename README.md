# Chat with transcribe-cantonese skill

A local AI chat app with a built-in Cantonese audio transcription skill using Faster Whisper.

> 本地 AI 聊天应用，内置粤语音频转录技能，使用 Faster Whisper。

---

## Skills

| Skill | Trigger | Description |
|-------|---------|-------------|
| Chat with Local Model | any question | Chat using a local GGUF model (Qwen2.5) |
| Transcribe Cantonese | `use skill transcribe-cantonese {audio_file}` | Transcribe a Cantonese audio file to text |

---

## Quick Start

**Step 1 — Install uv (one-time, choose one):**
```bash
pip install uv                                                    # if pip works
pipx install uv                                                   # if pip is blocked (macOS Homebrew)
curl -LsSf https://astral.sh/uv/install.sh | sh                  # macOS / Linux (no pip needed)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"       # Windows (no pip needed)
```

**Step 2 — Clone and run:**
```bash
git clone https://github.com/zh-skills/chat-with-skills-transcribe-cantonese
cd chat-with-skills-transcribe-cantonese
uv run server.py
```

`uv run` automatically creates a virtual environment, installs all dependencies, and starts the server.

The browser opens automatically at `http://localhost:8115/transcribe01_index.html`.

---

## Example Usage

```
What is artificial intelligence?
use skill transcribe-cantonese speech-Cantonese.mp3
use skill transcribe-cantonese voice.mp3
用技能转录粤语 speech-Cantonese.mp3
```

Place your audio file in the same folder as `transcribe01_server.py`, then use the trigger above.
The transcription is saved as `{audio_filename}_transcription.txt` in the same folder.

---

## Requirements

- Python 3.10+
- macOS or Windows
- Internet connection for first model download

---

## File Structure

```
transcribe01_server.py      — Flask API server
transcribe01_app.js         — Frontend JavaScript
transcribe01_index.html     — UI
transcribe01_marked.min.js  — Markdown renderer
requirements.txt
skills/
  transcribe-cantonese/scripts/transcribe_cantonese.py
models/                     — GGUF model files (downloaded on first use)
```

---

## License

MIT
