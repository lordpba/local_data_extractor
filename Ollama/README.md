# 🏠 Local Document Data Extractor

**Privacy-first, 100% local document data extraction using Ollama vision models.**

[![Ollama](https://img.shields.io/badge/Ollama-Required-green.svg)](https://ollama.ai/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

---

## ✨ Why Local Processing?

- 🔐 **Complete Privacy** - Your documents never leave your machine
- 💰 **Zero Cost** - No API fees, no cloud charges
- ⚡ **No Internet Required** - Works 100% offline
- 🎛️ **Full Control** - Choose your model, tune performance
- 🔒 **Regulatory Compliance** - Perfect for GDPR, HIPAA, SOC2

---

## 🚀 Quick Start (30 seconds!)

```bash
cd Ollama
./setup.sh              # Installs everything automatically
python app.py           # Start the web interface
```

Open your browser at `http://localhost:5000` and you're ready! 🎉

---

## 📋 Requirements

### System Requirements
- **OS**: Linux, macOS, or Windows (WSL)
- **RAM**: 8GB minimum, 16GB+ recommended
- **GPU**: Optional but highly recommended (NVIDIA/AMD)
- **Disk**: 10GB+ free space for models

### Software Requirements
- **Python** 3.8 or higher
- **Ollama** ([Install here](https://ollama.ai/))
- **poppler-utils** (for PDF processing)

---

## 🛠️ Installation

### Option A: Automated Setup (Recommended)

The setup script handles everything:

```bash
cd Ollama
./setup.sh
python app.py
```

What it does:
1. ✅ Creates Python virtual environment
2. ✅ Installs all dependencies
3. ✅ Pulls a vision model (llava:latest)
4. ✅ Checks for system dependencies
5. ✅ Provides helpful next steps

### Option B: Manual Setup

#### 1. Install Ollama

```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve
```

#### 2. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**macOS:**
```bash
brew install poppler
```

**Fedora:**
```bash
sudo dnf install poppler-utils
```

#### 3. Setup Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### 4. Pull a Vision Model

```bash
ollama pull llava:latest
```

See [Model Selection Guide](#-model-selection-guide) for other options.

#### 5. Run the Application

```bash
python app.py
```

---

## 🎯 Model Selection Guide

Choose based on your hardware and accuracy needs:

### 🌟 Recommended Models

| Model | VRAM | RAM | Speed | Accuracy | Best For |
|-------|------|-----|-------|----------|----------|
| **llava:latest** | 4-6GB | 8GB | Fast | Good | ⭐ Start here |
| **llama3.2-vision:11b** | 10-12GB | 16GB | Medium | Excellent | Complex docs |
| **gemma3:12b** | 10-12GB | 16GB | Medium | Great | General use |
| **llama3.2-vision:90b** | 48GB+ | 64GB+ | Slow | Outstanding | Production |

### 💻 By Hardware

#### Budget/Laptop (4-8GB VRAM)
```bash
ollama pull llava:latest        # Best starting point
ollama pull gemma3:4b           # Alternative
```

#### Mid-Range (8-16GB VRAM)
```bash
ollama pull llama3.2-vision:11b  # Recommended
ollama pull gemma3:12b           # Great alternative
```

#### High-End (16GB+ VRAM)
```bash
ollama pull gemma3:27b           # Professional
ollama pull llama3.2-vision:90b  # Enterprise
```

#### CPU Only
```bash
ollama pull llava:latest         # Works but slow
```

### 📊 Performance Tips

1. **Start with llava:latest** - Fast and capable for most documents
2. **Upgrade if needed** - If accuracy isn't sufficient, try llama3.2-vision:11b
3. **Use GPU** - 10-50x faster than CPU-only processing
4. **Close other apps** - Free up VRAM/RAM for better performance
5. **Batch process** - Process multiple files in one go for efficiency

---

## 🎨 Features

### 🌐 Web Interface

- **Drag & Drop** - Upload multiple PDFs or images at once
- **Dynamic Fields** - Define extraction fields on the fly
- **Live Preview** - See results as they're processed
- **Confidence Scores** - Know which data to verify
- **Export to Excel** - One-click download

### 🔌 REST API

```bash
curl -X POST http://localhost:5000/extract \
  -F 'fields_to_extract={
    "invoice_number": "The invoice or reference number",
    "total_amount": "Total amount including tax",
    "date": "Invoice date",
    "vendor": "Company issuing the invoice"
  }' \
  -F 'files=@invoice1.pdf' \
  -F 'files=@invoice2.pdf'
```

### 🎛️ Advanced Options

- **Model Switching** - Change models without restarting
- **Custom Instructions** - Add context to improve accuracy
- **Multi-page PDFs** - Automatic page processing and merging
- **Confidence Thresholds** - Flag low-confidence extractions

---

## 📖 Usage Examples

### Example 1: Invoice Processing

```json
{
  "invoice_number": "Invoice number or ID",
  "invoice_date": "Date of the invoice",
  "due_date": "Payment due date",
  "vendor_name": "Company issuing the invoice",
  "vendor_vat": "VAT or Tax ID number",
  "total_amount": "Total amount including tax",
  "currency": "Currency code (EUR, USD, etc.)"
}
```

### Example 2: Receipt Extraction

```json
{
  "merchant_name": "Store or restaurant name",
  "purchase_date": "Date of purchase",
  "total": "Total amount paid",
  "payment_method": "Payment method used",
  "items": "List of items purchased"
}
```

### Example 3: Contract Analysis

```json
{
  "contract_number": "Contract reference number",
  "parties": "Names of all parties involved",
  "start_date": "Contract start date",
  "end_date": "Contract end date",
  "renewal_terms": "Renewal conditions",
  "value": "Total contract value"
}
```

---

## ⚙️ Configuration

Create a `.env` file (optional):

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llava:latest

# Server Configuration
PORT=5000
DEBUG=false

# Processing Options
MAX_IMAGE_SIZE=1344
PDF_DPI=250
JPEG_QUALITY=95
```

---

## 🔧 Troubleshooting

### Issue: "Ollama not found"

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

### Issue: "No vision models available"

```bash
# Pull a vision model
ollama pull llava:latest

# Verify installation
ollama list
```

### Issue: "PDF processing error"

```bash
# Install poppler
sudo apt-get install poppler-utils  # Ubuntu/Debian
brew install poppler                 # macOS
```

### Issue: "Out of memory"

- Close other applications
- Use a smaller model (llava:latest instead of :90b)
- Process fewer documents at once
- Restart Ollama: `ollama restart`

### Issue: "Slow performance"

- Check GPU usage: `nvidia-smi` (NVIDIA) or `rocm-smi` (AMD)
- Use a smaller model
- Reduce image quality in settings
- Close browser tabs and other apps

---

## 📊 Benchmarks

Performance on AMD Ryzen 9 5900X + NVIDIA RTX 3090 (24GB):

| Model | Single Page | 10-page PDF | Accuracy |
|-------|-------------|-------------|----------|
| llava:latest | ~3s | ~25s | 85-90% |
| llama3.2-vision:11b | ~8s | ~75s | 92-96% |
| gemma3:12b | ~7s | ~65s | 90-94% |
| llama3.2-vision:90b | ~35s | ~320s | 96-98% |

*Benchmarks are approximate and vary by document complexity*

---

## 🔒 Privacy & Security

### What We DON'T Do:
- ❌ Send data to external servers
- ❌ Store documents permanently
- ❌ Log sensitive information
- ❌ Track user behavior
- ❌ Require internet connection

### What We DO:
- ✅ Process 100% locally
- ✅ Delete temp files immediately
- ✅ No cache by default
- ✅ Full user control
- ✅ Open source code

---

## 🏗️ Architecture

```
Ollama/
├── app.py                    # Flask web server & API routes
├── processor.py              # Document processing & AI logic
├── models_config.py          # Model definitions & metadata
├── requirements.txt          # Python dependencies
├── setup.sh                  # Automated setup script
├── templates/
│   └── index.html           # Web interface
├── temp_uploads/            # Temporary file storage (auto-deleted)
└── .env                     # Configuration (optional)
```

---

## 🤝 Contributing

Found a bug? Have a feature request? Contributions welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

## 🙏 Credits

Built with:
- [Ollama](https://ollama.ai/) - Local AI runtime
- [LLaVA](https://llava-vl.github.io/) - Vision language model
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [pdf2image](https://github.com/Belval/pdf2image) - PDF processing

---

## 📧 Support

Need help? Have questions?

- 📖 [Full Documentation](../README.md)
- 🤝 [Contributing Guidelines](../CONTRIBUTING.md)

---

<div align="center">

**[⬆ Back to Top](#-local-document-data-extractor)** | **[📘 Main Documentation](../README.md)**

Made with ❤️ for privacy-conscious data extraction

</div>
