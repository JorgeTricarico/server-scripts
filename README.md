# server-scripts

Collection of utility scripts for server automation, TTS, and developer productivity.

## Scripts

### `bin/claude-biz`
**Launch Claude Code with business MCPs (Slack + Notion) enabled for the current project.**

Temporarily enables the Slack and Notion MCPs in `~/.claude.json` for the active project, then restores their previous state on exit. Uses a lockfile at `/tmp/claude-biz.<uid>.lock` to prevent concurrent sessions.

**Installation:**
```bash
ln -s "$(pwd)/bin/claude-biz" ~/.local/bin/claude-biz
```

**Usage:**
```bash
cd /path/to/project
claude-biz          # Launches Claude Code with MCPs enabled
claude-biz --args   # Pass arguments directly to `claude`
```

**Prerequisites:**
- Claude Code installed
- `~/.claude.json` configured (created during Claude Code setup)
- Slack and Notion MCPs registered (via Claude Code UI)

---

### `bin/speak`
**Text-to-speech wrapper using Piper TTS (Argentine Spanish) with PowerShell SoundPlayer playback.**

Pipes stdin or CLI arguments through Piper TTS (voice: `es_AR-daniela-high`), cleans markdown syntax, and plays the resulting WAV via PowerShell on WSL2 (Windows audio integration). Falls back to ffplay with PulseAudio if available.

**Installation:**
```bash
ln -s "$(pwd)/bin/speak" ~/.local/bin/speak
```

**Usage:**
```bash
echo "Hola mundo" | speak
speak "Texto directo sin pipe"
SPEAK_RATE=1.0 speak "Más rápido"  # Default is 1.25 (slower)
```

**Prerequisites:**
- Piper TTS binary at `~/.local/bin/piper`
- Argentine Spanish voice model: `~/.local/share/piper-voices/es_AR-daniela-high/`

**Voice Model Setup:**
```bash
# Download model (from Piper releases or mirror):
mkdir -p ~/.local/share/piper-voices/es_AR-daniela-high/
wget -O ~/.local/share/piper-voices/es_AR-daniela-high/es_AR-daniela-high.onnx \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/model.onnx"
wget -O ~/.local/share/piper-voices/es_AR-daniela-high/es_AR-daniela-high.onnx.json \
  "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_AR/daniela/high/model.onnx.json"
```

**Features:**
- Markdown cleanup (removes code blocks, links, bold/italic, tables, headings)
- Configurable speech rate via `SPEAK_RATE` env var
- WSL2/Windows audio playback without PulseAudio

---

## Contributing

Ensure scripts are executable and documented with a comment header explaining purpose and usage.
