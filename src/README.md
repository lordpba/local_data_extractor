# Ollama Local Extractor — Setup & Technical Guide

Detailed setup, configuration, and API reference for the local Ollama-based document data extractor.
For a high-level overview, see the [main README](../README.md).

---

## Quick Start

```bash
cd Ollama
./setup.sh        # creates venv, installs deps, pulls default model
python app.py     # http://localhost:5000
```

Or use the one-liner:

```bash
./start.sh
```

---

## Requirements

| Software | Required | Notes |
|---|---|---|
| **Python** | 3.8+ | 3.10+ recommended |
| **Ollama** | Latest | [ollama.ai](https://ollama.ai/) |
| **poppler-utils** | Yes | PDF → image conversion |
| **NVIDIA GPU** | Optional | 6–24 GB VRAM recommended; CPU-only works but is slow |

### Install system dependencies

```bash
# Ubuntu / Debian
sudo apt-get update && sudo apt-get install poppler-utils

# macOS
brew install poppler

# Fedora
sudo dnf install poppler-utils
```

---

## Installation (manual)

```bash
# 1. Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Pull a vision model
ollama pull llama3.2-vision:11b  # or any model from the table below

# 4. (Optional) copy env template
cp .env.example .env

# 5. Run
python app.py
```

---

## Model Selection Guide

Choose a model based on your available VRAM. The web UI also auto-detects your GPU and provides a recommendation.

### Recommended models

| Model | VRAM | Speed | Quality | Best for |
|---|---|---|---|---|
| **gemma3:27b** | ~24 GB | Slow | ⭐ Excellent | Maximum local quality (81 % on handwritten CF) |
| **llama3.2-vision:11b** | ~12 GB | Medium | Excellent | Best overall balance |
| **gemma3:12b** | ~13 GB | Medium | Excellent | Strong single-GPU option |
| **qwen3-vl:8b** | ~8 GB | Medium | Very Good | Multilingual documents |
| **deepseek-ocr:latest** | ~8 GB | Fast | Very Good | OCR-first workflows |
| **glm-ocr:latest** | ~3 GB | Very Fast | Outstanding OCR | #1 OmniDocBench — pure OCR |
| **gemma3:4b** | ~6 GB | Fast | Good | General extraction, mid-range GPU |
| **llava:7b** | ~7 GB | Medium | Good | Lightweight general vision |

### By hardware budget

```bash
# Budget / Laptop (4–8 GB VRAM)
ollama pull glm-ocr:latest
ollama pull gemma3:4b

# Mid-range (8–16 GB VRAM)
ollama pull llama3.2-vision:11b
ollama pull gemma3:12b

# High-end (24 GB+ VRAM)
ollama pull gemma3:27b
```

---

## Web Interface Features

### Two-column layout
- **Left panel (light):** Upload area, field definitions, extraction options, template management.
- **Right panel (dark):** Incremental validation queue, document preview, inline editing, export controls.

### Extraction options
- **Strategy:** Single Pass · OCR → Extract · Auto
- **Handwriting mode:** Enhanced prompts for handwritten/cursive text
- **Page range:** All pages · First page only · Custom number
- **Model override:** Per-request model selection (no restart needed)

### Template system
- 6 built-in presets: Fattura, CV, Carta d'Identità, Contratto, Ricevuta, Codice Fiscale
- Save/load custom templates to browser localStorage
- Import/export templates as JSON files

### Incremental processing
Documents are sent to Ollama one at a time. Each result appears in the validation panel immediately, so you can start reviewing and editing while the remaining files are still being processed. A "Stop" button lets you abort the queue at any time.

### Validation & Export
- Edit any extracted value inline
- Side-by-side document preview (zoom, multi-page navigation)
- Mark each document as "Validated"
- One-click Excel export — validated rows are highlighted in green
- Auto-export option when all documents are validated

---

## REST API Reference

### `POST /extract`

Extract structured data from one or more documents.

**Form fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | File(s) | Yes | PDF, JPEG, or PNG |
| `fields_to_extract` | JSON string | Yes | `{"field_name": "description", ...}` |
| `additional_request` | string | No | Extra instructions for the model |
| `document_type` | string | No | E.g. `"invoice"`, `"receipt"` |
| `system_prompt` | string | No | Override the default system prompt |
| `extraction_strategy` | string | No | `auto` (default), `single_pass` |
| `page_range` | string | No | `all` / `first` / `1-3` / etc. |
| `model` | string | No | Per-request model override |

**Example:**

```bash
curl -X POST http://localhost:5000/extract \
  -F 'files=@doc.pdf' \
  -F 'fields_to_extract={"name":"Full name","date":"Date of birth"}' \
  -F 'extraction_strategy=auto'
```

**Response:**

```json
[
  {
    "filename": "doc.pdf",
    "extraction": {
      "extraction_results": {
        "data": {
          "name": "Mario Rossi",
          "date": "15/03/1985"
        },
        "confidence_score": 87
      }
    },
    "preview_images": ["<base64>..."],
    "duration_seconds": 12.3
  }
]
```

### `GET /models/available`

Returns all installed Ollama models with a `is_vision` flag indicating vision capability.

### `POST /models/set`

```json
{ "model": "gemma3:27b" }
```

### `POST /models/pull`

```json
{ "model": "gemma3:12b", "set_current": true }
```

### `GET /gpu/detect`

Returns GPU info, total VRAM, and a recommended model.

```json
{
  "gpus": [
    { "index": 0, "name": "NVIDIA RTX 3060", "total_mb": 12288, "free_mb": 11200, "used_mb": 1088 }
  ],
  "total_vram_gb": 12.0,
  "recommended_model": "gemma3:12b"
}
```

### `POST /export-excel`

Accepts validated results as JSON, returns a downloadable `.xlsx` file.

---

## Configuration (`.env`)

```bash
OLLAMA_BASE_URL=http://localhost:11434   # Ollama server URL
OLLAMA_MODEL=llama3.2-vision:11b         # Default model
PORT=5000                                 # Flask port
```

All settings can be overridden from the web UI at runtime.

---

## Architecture

```
app.py  ─────────────────────────  Flask routes, file handling, Excel export
   │
   ├── processor.py  ────────────  Image pipeline (enhance, resize, base64),
   │                                Ollama API calls (generate / chat),
   │                                OCR-then-extract two-phase strategy,
   │                                thinking-model tag stripping
   │
   ├── models_config.py  ────────  Model catalogue, VRAM recommendations,
   │                                family/tier mapping for UI
   │
   └── templates/index.html  ────  Complete web UI (vanilla JS, no build step)
```

---

## Privacy & Security

- ✅ All processing happens on your machine via Ollama.
- ✅ Uploaded files are saved to a temp directory and deleted immediately after processing.
- ✅ No telemetry, no analytics, no external network calls (aside from Ollama at localhost).
- ✅ Open source — audit the code yourself.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `ConnectionRefusedError` to Ollama | Make sure `ollama serve` is running |
| Model not detected as vision | Update Ollama to ≥ 0.8 for `capabilities` field; older versions use heuristic detection |
| Out of VRAM | Switch to a smaller model from the UI (no restart needed) |
| Slow on CPU | Expected — use a GPU for 10–50× speedup |
| `qwen3-vl` errors | The app auto-falls back to `/api/chat`; make sure Ollama ≥ 0.6 |

---

## License

MIT — see [LICENSE](../LICENSE).

---

<div align="center">
  <a href="../README.md">← Back to main README</a>
</div>
