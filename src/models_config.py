"""Vision Models Configuration for Document Data Extraction
Primary families: GLM OCR, DeepSeek OCR, Gemma3, Llama Vision, LLaVA
Categorized by hardware requirements; also exposes a family/tier mapping for UI selection.
"""

VISION_MODELS = {
    # ========== LIGHTWEIGHT MODELS (No GPU or Low VRAM) ==========
    "lightweight": {
        "description": "Best for CPU-only or systems with very limited GPU memory (< 4GB VRAM)",
        "models": [
            {
                "name": "glm-ocr:latest",
                "display_name": "GLM-OCR",
                "size": "~2.2GB",
                "vram": "~2-3GB",
                "speed": "Very Fast",
                "accuracy": "Outstanding",
                "description": "#1 on OmniDocBench V1.5 (94.62). Purpose-built OCR model: 0.9B parameters, 128K context. Clean text output, no dotted-spelling artefacts. Works on any GPU.",
                "use_case": "Recommended OCR model for all hardware — forms, tables, handwriting",
                "recommended": True
            },
            {
                "name": "gemma3:270m",
                "display_name": "Gemma3 270M",
                "size": "~400MB",
                "vram": "~1GB",
                "speed": "Very Fast",
                "accuracy": "Basic",
                "description": "Ultra-lightweight Gemma3. Good for basic text extraction and very simple forms.",
                "use_case": "Simple invoices and receipts on low-end hardware"
            }
        ]
    },

    # ========== MEDIUM MODELS (6-8GB VRAM) ==========
    "medium": {
        "description": "Best for systems with moderate GPU memory (6-8GB VRAM)",
        "models": [
            {
                "name": "deepseek-ocr:latest",
                "display_name": "DeepSeek OCR (Latest)",
                "size": "~4-6GB",
                "vram": "6-8GB",
                "speed": "Fast-Medium",
                "accuracy": "Very Good",
                "description": "OCR-specialized vision model for printed and handwritten document extraction.",
                "use_case": "High-quality OCR-first extraction workflows",
                "recommended": True
            },
            {
                "name": "gemma3:4b",
                "display_name": "Gemma3 4B",
                "size": "~3GB",
                "vram": "5-6GB",
                "speed": "Fast",
                "accuracy": "Good",
                "description": "Balanced Gemma3 model. Good compromise of speed and quality.",
                "use_case": "General document extraction on mid-range GPUs",
                "recommended": True
            },
            {
                "name": "qwen3.5:9b",
                "display_name": "Qwen3.5 9B",
                "size": "~6.6GB",
                "vram": "8-10GB",
                "speed": "Medium",
                "accuracy": "Very Good",
                "description": "Excellent balance of size and performance for OCR and document extraction. Highly recommended.",
                "use_case": "General OCR and complex document extraction",
                "recommended": True
            },
            {
                "name": "qwen3.5:4b",
                "display_name": "Qwen3.5 4B",
                "size": "~3.4GB",
                "vram": "5-6GB",
                "speed": "Fast",
                "accuracy": "Good",
                "description": "Smaller, faster Qwen3.5 model. Good for standard OCR tasks.",
                "use_case": "Standard document extraction",
                "recommended": True
            },
            {
                "name": "qwen3-vl:8b",
                "display_name": "Qwen3 VL 8B",
                "size": "~6.1GB",
                "vram": "7-8GB",
                "speed": "Medium",
                "accuracy": "Very Good",
                "description": "Alibaba's vision-language model with strong multilingual OCR. Thinking model — supports /no_think for speed.",
                "use_case": "Multilingual document extraction",
                "recommended": False
            },
            {
                "name": "llava-phi3:3.8b",
                "display_name": "LLaVA-Phi3 3.8B",
                "size": "~2.3GB",
                "vram": "4-5GB",
                "speed": "Fast",
                "accuracy": "Good",
                "description": "LLaVA fine-tuned from Phi 3. OCR-friendly and balanced.",
                "use_case": "Entry-level OCR and document extraction"
            },
            {
                "name": "llava:7b",
                "display_name": "LLaVA 7B",
                "size": "~4.7GB",
                "vram": "6-7GB",
                "speed": "Medium",
                "accuracy": "Good",
                "description": "Classic LLaVA, well-tested for documents and OCR-like tasks.",
                "use_case": "General document extraction"
            }
        ]
    },

    # ========== LARGE MODELS (12-16GB VRAM) ==========
    "large": {
        "description": "Best for systems with high-end GPU (12-16GB VRAM)",
        "models": [
            {
                "name": "llama3.2-vision:11b",
                "display_name": "Llama 3.2 Vision 11B",
                "size": "~7.9GB",
                "vram": "10-12GB",
                "speed": "Medium-Slow",
                "accuracy": "Excellent",
                "description": "Meta's instruction-tuned image reasoning model.",
                "use_case": "High-accuracy extraction, complex reasoning",
                "recommended": True
            },
            {
                "name": "gemma3:12b",
                "display_name": "Gemma3 12B",
                "size": "~8GB",
                "vram": "11-13GB",
                "speed": "Medium-Slow",
                "accuracy": "Excellent",
                "description": "Most capable Gemma3 single-GPU model.",
                "use_case": "High-quality document extraction (user-recommended)"
            },
            {
                "name": "llava:13b",
                "display_name": "LLaVA 13B",
                "size": "~8GB",
                "vram": "11-13GB",
                "speed": "Slow",
                "accuracy": "Very Good",
                "description": "Larger LLaVA for better OCR/document accuracy.",
                "use_case": "Complex document analysis"
            }
        ]
    },

    # ========== PROFESSIONAL MODELS (24GB+ VRAM) ==========
    "professional": {
        "description": "Best for high-end workstations (24GB+ VRAM) or multi-GPU setups",
        "models": [
            {
                "name": "gemma3:27b",
                "display_name": "Gemma3 27B",
                "size": "~17GB",
                "vram": "22-26GB",
                "speed": "Slow",
                "accuracy": "Excellent",
                "description": "Largest Gemma3 model for maximum quality on a single high-memory GPU.",
                "use_case": "Maximum accuracy for critical documents"
            },
            {
                "name": "qwen3.5:27b",
                "display_name": "Qwen3.5 27B",
                "size": "~17GB",
                "vram": "22-26GB",
                "speed": "Slow",
                "accuracy": "Excellent",
                "description": "Large Qwen3.5 model with exceptional reasoning and OCR capabilities.",
                "use_case": "Maximum accuracy for critical documents and handwriting",
                "recommended": True
            },
            {
                "name": "llama3.2-vision:90b",
                "display_name": "Llama 3.2 Vision 90B",
                "size": "~55GB",
                "vram": "70-80GB",
                "speed": "Very Slow",
                "accuracy": "Outstanding",
                "description": "Meta's largest vision model with exceptional reasoning.",
                "use_case": "Enterprise: complex legal/financial documents"
            }
        ]
    }
}

# Hardware recommendations summary
HARDWARE_RECOMMENDATIONS = {
    "cpu_only": {
        "category": "lightweight",
        "recommended_models": ["gemma3:270m"],
        "note": "CPU-only processing will be slow. Consider at least 16GB RAM."
    },
    "gpu_4gb": {
        "category": "lightweight",
        "recommended_models": ["glm-ocr:latest", "gemma3:270m"],
        "note": "GLM-OCR fits comfortably in 4GB and benchmarks #1 for OCR."
    },
    "gpu_6gb": {
        "category": "medium",
        "recommended_models": ["glm-ocr:latest", "deepseek-ocr:latest", "qwen3.5:4b", "gemma3:4b"],
        "note": "GLM-OCR is the best OCR choice; qwen3.5:4b is excellent for JSON extraction."
    },
    "gpu_8gb": {
        "category": "medium",
        "recommended_models": ["glm-ocr:latest", "qwen3.5:9b", "deepseek-ocr:latest", "gemma3:4b"],
        "note": "qwen3.5:9b is highly recommended for all-around accuracy. GLM-OCR for pure OCR."
    },
    "gpu_12gb": {
        "category": "large",
        "recommended_models": ["qwen3.5:9b", "llama3.2-vision:11b", "glm-ocr:latest", "gemma3:12b"],
        "note": "qwen3.5:9b is the best balanced choice; llama3.2-vision:11b for complex reasoning."
    },
    "gpu_16gb": {
        "category": "large",
        "recommended_models": ["llama3.2-vision:11b", "gemma3:12b"],
        "note": "Excellent performance for complex documents."
    },
    "gpu_24gb": {
        "category": "professional",
        "recommended_models": ["qwen3.5:27b", "gemma3:27b"],
        "note": "qwen3.5:27b offers exceptional accuracy for complex documents."
    },
    "gpu_48gb_plus": {
        "category": "professional",
        "recommended_models": ["llama3.2-vision:90b"],
        "note": "Enterprise-grade, maximum accuracy for critical applications."
    }
}

def get_models_by_category(category):
    """Get all models in a specific category"""
    return VISION_MODELS.get(category, {}).get("models", [])

def get_recommended_models_by_vram(vram_gb):
    """Get recommended models based on available VRAM"""
    if vram_gb == 0:  # CPU only
        return HARDWARE_RECOMMENDATIONS["cpu_only"]
    elif vram_gb <= 4:
        return HARDWARE_RECOMMENDATIONS["gpu_4gb"]
    elif vram_gb <= 6:
        return HARDWARE_RECOMMENDATIONS["gpu_6gb"]
    elif vram_gb <= 8:
        return HARDWARE_RECOMMENDATIONS["gpu_8gb"]
    elif vram_gb <= 12:
        return HARDWARE_RECOMMENDATIONS["gpu_12gb"]
    elif vram_gb <= 16:
        return HARDWARE_RECOMMENDATIONS["gpu_16gb"]
    elif vram_gb <= 24:
        return HARDWARE_RECOMMENDATIONS["gpu_24gb"]
    else:
        return HARDWARE_RECOMMENDATIONS["gpu_48gb_plus"]

def get_all_model_names():
    """Get list of all model names for validation"""
    all_models = []
    for category in VISION_MODELS.values():
        for model in category.get("models", []):
            all_models.append(model["name"])
    return all_models

def get_family_tiers():
    """Return the family->tiers mapping used by the UI"""
    return {
        "gemma3": {
            "label": "Gemma3",
            "tiers": {
                "small": "gemma3:4b",
                "medium": "gemma3:12b",
                "large": "gemma3:27b"
            }
        },
        "llama": {
            "label": "Llama 3.2 Vision",
            "tiers": {
                "small": None,  # No small variant available
                "medium": "llama3.2-vision:11b",
                "large": "llama3.2-vision:90b"
            }
        },
        "llava": {
            "label": "LLaVA (OCR-oriented)",
            "tiers": {
                "small": "llava-phi3:3.8b",
                "medium": "llava:7b",
                "large": "llava:13b"
            }
        },
        "glm_ocr": {
            "label": "GLM-OCR (#1 OmniDocBench)",
            "tiers": {
                "small": "glm-ocr:latest",
                "medium": None,
                "large": None
            }
        },
        "deepseek_ocr": {
            "label": "DeepSeek OCR",
            "tiers": {
                "small": None,
                "medium": "deepseek-ocr:latest",
                "large": None
            }
        },
        "qwen3vl": {
            "label": "Qwen3 VL / 3.5",
            "tiers": {
                "small": "qwen3.5:4b",
                "medium": "qwen3.5:9b",
                "large": "qwen3.5:27b"
            }
        }
    }
