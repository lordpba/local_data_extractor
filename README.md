# 🚀 AI-Powered Document Data Extractor

> **Extract structured data from any document - locally. Your documents, your rules, your privacy.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Vision-green.svg)](https://ollama.ai/)

---

## 💡 The Problem

Ever needed to extract specific data from hundreds of invoices, receipts, contracts, or forms? Manual data entry is:
- ⏰ **Time-consuming** - Hours spent typing what AI could read in seconds
- ❌ **Error-prone** - Human mistakes lead to incorrect data
- 💰 **Expensive** - Either pay cloud services or hire data entry staff
- 🔒 **Privacy concerns** - Sensitive documents uploaded to third-party services

## ✨ The Solution

A **flexible, intelligent document processing system** that lets you:

✅ **Define ANY fields dynamically** - No pre-training needed, just describe what you want  
✅ **Process 100% locally** - Complete privacy, your data never leaves your machine  
✅ **Batch process documents** - Drag, drop, extract multiple files at once  
✅ **Export to Excel instantly** - Ready for your workflow  
✅ **REST API included** - Integrate with your systems  
✅ **Zero template configuration** - Works with any document format  

---

## 🎯 Use Cases

Extract data from any type of document:

- 📊 **Invoices & Receipts** - Numbers, totals, tax IDs, dates, vendor info
- 📄 **Contracts & Legal Docs** - Parties, dates, terms, amounts
- 📦 **Shipping Documents** - Tracking numbers, addresses, customs info
- 🏢 **Forms & Applications** - CVs, employment forms, ID documents

---

## 🚀 Quick Start

```bash
cd Ollama
./setup.sh              # Installs everything automatically
python app.py           # Start the web interface
```

Open `http://localhost:5000` and start extracting!

**Requirements:**
- Ollama installed ([Get it here](https://ollama.ai/))
- 8GB+ RAM recommended
- GPU optional (faster with GPU)

👉 **[Full Setup Guide](Ollama/README.md)**

---

## 🎬 How It Works

**1. Upload** → Drop your PDFs or images  
**2. Define Fields** → Describe what you want to extract  
**3. Extract** → Get structured JSON with confidence scores  
**4. Export** → Download as Excel or use via API

```json
{
  "invoice_number": {"value": "INV-2024-001", "confidence": 98},
  "total_amount": {"value": "€1,250.00", "confidence": 95},
  "vendor_name": {"value": "ACME Corp", "confidence": 97}
}
```

---

## 🌟 Key Features

- 🎨 **Dynamic Fields** - No training, just describe what you need
- 🔐 **100% Private** - Data never leaves your machine
- ⚡ **Smart Processing** - Multi-page PDFs, image optimization, confidence scoring
- 🎛️ **Flexible** - Web UI + REST API + CLI support
- 🔄 **Multiple Models** - LLaVA, Llama 3.2 Vision, Gemma 3

---

## 📊 Performance

Choose the right model for your hardware:

| Model | VRAM | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| **llava:latest** | 4-6GB | ⚡ Fast | Good | Quick start, testing |
| **gemma3:4b** | 6GB | ⚡ Fast | Good | General documents |
| **llama3.2-vision:11b** | 12GB | Medium | ⭐ Excellent | Recommended |
| **gemma3:12b** | 12GB | Medium | Excellent | Professional use |
| **llama3.2-vision:90b** | 48GB+ | Slow | Outstanding | Complex legal/financial |

---

## 🛠️ Technical Stack

- **Backend**: Python + Flask
- **Vision AI**: Ollama (LLaVA, Llama Vision, Gemma)
- **PDF Processing**: pdf2image + Pillow
- **Frontend**: Vanilla JavaScript (no frameworks!)
- **Image Processing**: PIL with optimized quality (250 DPI, 95% JPEG)
- **Confidence System**: Per-field scoring based on image quality

---

## 📋 API Example

```bash
curl -X POST http://localhost:5000/extract \
  -F 'fields_to_extract={"invoice_number":"Invoice ID","total":"Total amount"}' \
  -F 'files=@invoice1.pdf' \
  -F 'files=@invoice2.pdf'
```

---

## 🎓 Documentation

- 📘 **[Complete Setup Guide](Ollama/README.md)** - Installation and usage
- 🤝 **[Contributing Guidelines](CONTRIBUTING.md)** - How to contribute
- 📜 **[License](LICENSE)** - MIT License

---

## 🤝 Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug reports
- 💡 Feature requests
- 📖 Documentation improvements
- 🔧 Code contributions

Please open an issue or submit a pull request.

---

## 📜 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - For making local AI accessible
- [LLaVA](https://llava-vl.github.io/) - Open-source vision language model
- [Meta Llama](https://llama.meta.com/) - Powerful language models
- [Google Gemma](https://ai.google.dev/gemma) - Efficient vision models

---

## 🌟 Star History

If this project helps you, please consider giving it a ⭐ on GitHub!

---

## 📧 Contact

Created by me

---

<div align="center">

**Made with ❤️ for data professionals worldwide**

[⬆ Back to Top](#-ai-powered-document-data-extractor)

</div>
