const API_BASE = 'http://localhost:5075';

if (typeof marked !== 'undefined') {
  marked.use({ breaks: true, gfm: true });
}

// ── Navigation ────────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`${btn.dataset.view}-view`).classList.add('active');
    if (btn.dataset.view === 'settings') loadSettings();
  });
});

// ── Skills Catalog ────────────────────────────────────────────────────────────
const SKILLS_CATALOG = [
  {
    id: 'chat',
    icon: '🤖',
    name: 'Chat with Local Model',
    desc: 'Ask any question and get an answer.<br><span style="color:#8e8e93;font-size:12px;">提问任何问题并获得答案。</span>',
    natural: 'What is artificial intelligence?',
    examples: [
      'What is artificial intelligence?',
      '什么是人工智能？',
      '什麼是人工智能？',
    ],
  },
  {
    id: 'transcribe-cantonese',
    icon: '🎙️',
    name: 'Transcribe Cantonese',
    desc: 'Transcribe a Cantonese audio file to text using Whisper.<br><span style="color:#8e8e93;font-size:12px;">使用 Whisper 将粤语音频转录为文字。</span>',
    natural: 'use skill transcribe-cantonese speech-Cantonese.mp3',
    examples: [
      'use skill transcribe-cantonese speech-Cantonese.mp3',
      'use skill transcribe-cantonese voice.mp3',
      '用技能转录粤语 speech-Cantonese.mp3',
    ],
  },
];

function renderSkills() {
  const list = document.getElementById('skills-catalog-list');
  if (!list) return;
  list.innerHTML = '';
  SKILLS_CATALOG.forEach(skill => {
    const card = document.createElement('div');
    card.className = 'skill-card';
    const examplesHtml = skill.examples
      ? skill.examples.map(e => `<div><span class="tool-example-text" title="Click to copy to Chat">${e}</span></div>`).join('')
      : `<span class="tool-example-text" title="Click to copy to Chat">${skill.natural}</span>`;
    card.innerHTML = `
      <div class="skill-icon">${skill.icon}</div>
      <div style="flex:1;min-width:0;">
        <div class="skill-name">${skill.name}</div>
        <div class="skill-desc" style="line-height:1.6">${skill.desc}</div>
        <div class="tool-usage">Example: ${examplesHtml}</div>
      </div>`;
    card.querySelectorAll('.tool-example-text').forEach(el => {
      el.addEventListener('click', () => {
        input.value = el.textContent;
        document.querySelector('[data-view="chat"]').click();
        input.focus();
      });
    });
    list.appendChild(card);
  });
}

document.querySelector('[data-view="skills"]').addEventListener('click', renderSkills);
document.addEventListener('DOMContentLoaded', renderSkills);

// ── Settings ──────────────────────────────────────────────────────────────────
async function loadSettings() {
  try {
    const res  = await fetch(`${API_BASE}/api/config`);
    const data = await res.json();
    const sel  = document.getElementById('local-model-select');
    if (sel && data.model) {
      for (const opt of sel.options) {
        if (opt.value === data.model) { opt.selected = true; break; }
      }
    }
  } catch (_) {}
}

document.getElementById('model-save-btn').addEventListener('click', async () => {
  const status = document.getElementById('model-status');
  const model  = document.getElementById('local-model-select').value;
  status.textContent = `Applying... (downloading ${model} if not cached, please wait)`;
  status.style.color = '#8e8e93';
  try {
    const res  = await fetch(`${API_BASE}/api/set-model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model }),
    });
    const data = await res.json();
    status.textContent = data.model ? `✓ ${data.model}` : data.error || 'Failed.';
    status.style.color = data.model ? '#34c759' : '#ff3b30';
  } catch (err) {
    status.textContent = 'Error: could not reach server.';
    status.style.color = '#ff3b30';
  }
});

// ── Chat ──────────────────────────────────────────────────────────────────────
const input    = document.getElementById('user-input');
const sendBtn  = document.getElementById('send-btn');
const stopBtn  = document.getElementById('stop-btn');
const messages = document.getElementById('chat-messages');
let currentAbort = null;

function setDisabled(val) {
  input.disabled    = val;
  sendBtn.disabled  = val;
  stopBtn.style.display = val ? 'block' : 'none';
}

function addMessage(text, role) {
  const wrap = document.createElement('div');
  wrap.className = `message-wrap ${role.split(' ')[0]}`;
  const div = document.createElement('div');
  div.className = `message ${role}`;
  if (role.startsWith('assistant') && typeof marked !== 'undefined') {
    div.innerHTML = marked.parse(text || '');
  } else {
    div.textContent = text;
  }
  wrap.appendChild(div);
  messages.appendChild(wrap);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function isTranscribeCantonese(text) {
  return /use\s+skill\s+transcribe-cantonese/i.test(text)
      || /用技能转录粤语/.test(text);
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  addMessage(text, 'user');
  input.value = '';
  setDisabled(true);

  const endpoint = isTranscribeCantonese(text) ? `${API_BASE}/api/transcribe-cantonese`
                 :                                `${API_BASE}/api/chat`;
  const label    = isTranscribeCantonese(text) ? 'Transcribing...'
                 :                                'Thinking...';
  const thinking = addMessage(label, 'assistant thinking');

  currentAbort = new AbortController();
  try {
    const res  = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
      signal: currentAbort.signal,
    });
    const data   = await res.json();
    const answer = data.answer || data.error || 'No response.';
    thinking.remove();
    addMessage(answer, 'assistant');
  } catch (err) {
    thinking.remove();
    if (err.name !== 'AbortError') {
      addMessage(`Error: could not reach server at ${API_BASE}`, 'assistant');
    }
  } finally {
    setDisabled(false);
    input.focus();
  }
}

sendBtn.addEventListener('click', sendMessage);
input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } });
stopBtn.addEventListener('click', () => { if (currentAbort) currentAbort.abort(); });
