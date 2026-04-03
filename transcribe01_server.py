# pip install python-dotenv requests flask flask-cors waitress llama-cpp-python faster-whisper
# Skills: chat, transcribe-cantonese
import os
import sys
import re
import time
import threading
import http.server
import webbrowser
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR   = os.path.join(BASE_DIR, "skills")
API_PORT     = 5075
STATIC_PORT  = 8115
INDEX_FILE   = "transcribe01_index.html"

# ── Import skills ─────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(SKILLS_DIR, "transcribe-cantonese", "scripts"))
from transcribe_cantonese import transcribe_cantonese

# ── Local GGUF model ──────────────────────────────────────────────────────────

active_model = 'Qwen2.5-0.5B-Instruct-Q4_K_M.gguf'

LOCAL_MODELS = {
    'Qwen2.5-0.5B-Instruct-Q4_K_M.gguf': 'https://huggingface.co/bartowski/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/Qwen2.5-0.5B-Instruct-Q4_K_M.gguf',
    'Qwen2.5-1.5B-Instruct-Q4_K_M.gguf': 'https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q4_K_M.gguf',
}
MODELS_DIR      = os.path.join(os.path.dirname(BASE_DIR), "models")
_llama_instance = None


def ensure_local_model(model_filename=None):
    model_filename = model_filename or active_model
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, model_filename)
    if os.path.exists(model_path):
        return model_path
    url = LOCAL_MODELS.get(model_filename)
    if not url:
        raise ValueError(f"Unknown model: {model_filename}")
    print(f"  Downloading {model_filename}...")
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    total = int(resp.headers.get('content-length', 0))
    downloaded = 0
    with open(model_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                print(f"  {downloaded * 100 // total}%", end='\r')
    print(f"  Downloaded: {model_path}")
    return model_path


def get_llama_instance(model_filename=None):
    global _llama_instance
    model_filename = model_filename or active_model
    model_path = ensure_local_model(model_filename)
    if _llama_instance is None:
        from llama_cpp import Llama
        print(f"  Loading {model_filename}...")
        _llama_instance = Llama(model_path=model_path, n_ctx=2048, verbose=False)
        print("  Model ready.")
    return _llama_instance


def chat_completion(messages):
    llm    = get_llama_instance()
    system = [{"role": "system", "content": "You are a helpful assistant. Answer all questions directly and factually."}]
    resp   = llm.create_chat_completion(messages=system + messages)
    return resp['choices'][0]['message']['content'] or ""


# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)


@app.route("/api/chat", methods=["POST"])
def chat():
    data     = request.get_json()
    question = (data.get("message") or "").strip()
    if not question:
        return jsonify({"error": "No message provided."}), 400
    model_path = os.path.join(MODELS_DIR, active_model)
    if not os.path.exists(model_path):
        threading.Thread(target=ensure_local_model, daemon=True).start()
        return jsonify({"answer": f"⏳ Downloading model {active_model} (~400MB) in the background...\nPlease wait a moment and try again. Check the terminal for download progress."})
    try:
        answer = chat_completion([{"role": "user", "content": question}])
        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"answer": f"❌ Error: {e}"})


@app.route("/api/config", methods=["GET"])
def config():
    return jsonify({"model": active_model, "provider": "none"})


@app.route("/api/set-model", methods=["POST"])
def set_model():
    global active_model, _llama_instance
    data  = request.get_json()
    model = (data.get("model") or "").strip()
    if model not in LOCAL_MODELS:
        return jsonify({"error": f"Unknown model: {model}"}), 400
    active_model    = model
    _llama_instance = None
    try:
        ensure_local_model(model)
    except Exception as e:
        return jsonify({"error": f"Download failed: {e}"}), 500
    return jsonify({"model": active_model})


# ── Skill: transcribe-cantonese ───────────────────────────────────────────────

@app.route("/api/transcribe-cantonese", methods=["POST"])
def api_transcribe_cantonese():
    data     = request.get_json()
    message  = (data.get("message") or "").strip()
    filename = re.sub(r'^(?:use\s+skill\s+transcribe-cantonese|用技能转录粤语)\s*', '', message, flags=re.IGNORECASE).strip()
    if not filename:
        return jsonify({"answer": "Please include an audio filename.\nExample: use skill transcribe-cantonese speech-Cantonese.mp3"})
    if not os.path.isabs(filename):
        filepath = os.path.join(BASE_DIR, filename)
    else:
        filepath = filename
    answer = transcribe_cantonese(filepath)
    return jsonify({"answer": answer, "skill": "transcribe-cantonese"})


# ── Static file server ────────────────────────────────────────────────────────

class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    def log_message(self, *args):
        pass


def start_static_server(port):
    http.server.HTTPServer(("localhost", port), StaticHandler).serve_forever()


if __name__ == "__main__":
    t = threading.Thread(target=start_static_server, args=(STATIC_PORT,), daemon=True)
    t.start()
    time.sleep(0.3)

    url = f"http://localhost:{STATIC_PORT}/{INDEX_FILE}"
    print(f"\n  Transcribe01")
    print(f"  UI  → {url}")
    print(f"  API → http://localhost:{API_PORT}\n")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)
    threading.Thread(target=open_browser, daemon=True).start()

    from waitress import serve
    serve(app, host="0.0.0.0", port=API_PORT, threads=4)
