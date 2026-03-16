import os
import json
import base64
import requests
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import io

# Configuration is read dynamically from environment to allow runtime changes
def get_ollama_base_url():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_ollama_model():
    return os.getenv("OLLAMA_MODEL", "qwen3.5:4b")


def get_ollama_timeout():
    try:
        return int(os.getenv("OLLAMA_TIMEOUT", "3600"))
    except ValueError:
        return 3600


def get_image_max_width():
    """Maximum width for images sent to the model. Smaller = faster, less VRAM."""
    try:
        return int(os.getenv("IMAGE_MAX_WIDTH", "1024"))
    except ValueError:
        return 1024


def get_skip_image_enhance():
    """Whether to skip contrast/sharpness/brightness enhancement."""
    return os.getenv("SKIP_IMAGE_ENHANCE", "false").lower() in ("true", "1", "yes")


def get_batch_delay():
    """Delay in seconds between batch file processing."""
    try:
        return float(os.getenv("BATCH_DELAY", "5"))
    except ValueError:
        return 5.0


def get_ollama_keep_alive():
    """How long Ollama keeps the model loaded after a request.
    Shorter = less VRAM wasted by idle models, but slower cold-start.
    Default: '2m'. Set to '0' to unload immediately after each request.
    """
    return os.getenv("OLLAMA_KEEP_ALIVE", "2m")


def unload_ollama_model():
    """Force Ollama to unload the current model from VRAM.
    This prevents multiple model instances from competing for VRAM
    during retries or batch processing.
    """
    try:
        base_url = get_ollama_base_url()
        model = get_ollama_model()
        print(f"[VRAM cleanup] Unloading model {model} from VRAM...")
        requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": 0},
            timeout=10
        )
        import time as _time
        _time.sleep(2)  # Give Ollama time to release VRAM
        print(f"[VRAM cleanup] Model unloaded")
    except Exception as e:
        print(f"[VRAM cleanup] Warning: could not unload model: {e}")


def is_deepseek_ocr_model(model_name):
    model_lower = (model_name or "").lower()
    return "deepseek-ocr" in model_lower


def is_glm_ocr_model(model_name):
    return "glm-ocr" in (model_name or "").lower()


def is_ocr_specialist_model(model_name):
    """True for models that use the two-phase OCR→regex pipeline
    (deepseek-ocr and glm-ocr). Both output clean OCR text with their native
    short prompts but cannot follow verbose JSON templates.
    """
    return is_deepseek_ocr_model(model_name) or is_glm_ocr_model(model_name)


def is_thinking_model(model_name):
    """Models that emit <think>...</think> before their actual answer.
    These need thinking tags stripped and a larger num_ctx.
    """
    model_lower = (model_name or "").lower()
    return any(kw in model_lower for kw in ['qwen3.5', 'qwen3:', 'qwen3-', 'qwq', 'deepseek-r1', 'deepseek-r2'])


def strip_thinking_tags(text):
    """Remove <think>...</think> blocks emitted by reasoning/thinking models.
    Must be called before any JSON parsing.
    """
    import re
    # Remove full <think>...</think> block (can span multiple lines)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()


def process_document(filepath, mime_type, page_range="all"):
    """
    Process document based on type:
    - Images: return as base64
    - PDFs: convert to images and return as base64 array
    """
    if mime_type.startswith('image/'):
        return process_image(filepath)
    elif mime_type == 'application/pdf':
        return process_pdf(filepath, page_range)
    else:
        raise ValueError(f"Unsupported file type: {mime_type}")


def process_image(image_path):
    """Process image file with optional enhancement for better OCR and return base64 encoded"""
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            max_width = get_image_max_width()
            
            # Resize if larger than max width
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)
                print(f"Resized image to {max_width}x{new_height}")
            
            # Apply image enhancement only if not skipped
            if not get_skip_image_enhance():
                img = enhance_image_for_ocr(img)
            else:
                print("[SKIP_IMAGE_ENHANCE] Skipping contrast/sharpness enhancement")
            
            # Save to buffer
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            base64_image = base64.b64encode(buffer.read()).decode('utf-8')
            return {
                "type": "image",
                "data": base64_image
            }
    except Exception as e:
        print(f"Error processing image: {e}")
        raise


def enhance_image_for_ocr(img):
    """
    Enhance image for better OCR results, especially for handwritten text.
    NOTE: No longer upscales images — the max width is handled by get_image_max_width().
    """
    # 1. Increase contrast slightly
    contrast_enhancer = ImageEnhance.Contrast(img)
    img = contrast_enhancer.enhance(1.15)
    
    # 2. Increase sharpness
    sharpness_enhancer = ImageEnhance.Sharpness(img)
    img = sharpness_enhancer.enhance(1.2)
    
    # 3. Slight brightness adjustment
    brightness_enhancer = ImageEnhance.Brightness(img)
    img = brightness_enhancer.enhance(1.02)
    
    return img


def downscale_base64_image(base64_image, max_width=1152, jpeg_quality=85):
    """Downscale a base64 image and return a lighter base64 payload."""
    try:
        image_bytes = base64.b64decode(base64_image)
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')

            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            output = io.BytesIO()
            img.save(output, format='JPEG', quality=jpeg_quality, optimize=True)
            output.seek(0)
            return base64.b64encode(output.read()).decode('utf-8')
    except Exception as e:
        print(f"Warning: could not downscale image payload: {e}")
        return base64_image


def process_pdf(pdf_path, page_range="all"):
    """
    Process PDF by converting pages to images
    Returns array of base64 encoded images
    """
    try:
        model_name = get_ollama_model()
        deepseek_mode = is_deepseek_ocr_model(model_name)
        max_width = get_image_max_width()
        skip_enhance = get_skip_image_enhance()

        print(f"Converting PDF to images: {pdf_path}")
        # Use lower DPI for smaller target widths to avoid wasting CPU
        if max_width <= 1024:
            pdf_dpi = 200
        elif deepseek_mode:
            pdf_dpi = 220
        else:
            pdf_dpi = 300
        
        last_page = None
        if page_range == "first":
            last_page = 1
        elif page_range != "all":
            try:
                last_page = int(page_range)
            except ValueError:
                pass
                
        images = convert_from_path(pdf_path, dpi=pdf_dpi, last_page=last_page)
        print(f"PDF converted to {len(images)} page(s)")
        
        # Limit pages to avoid huge payloads
        MAX_PAGES = 10
        if len(images) > MAX_PAGES:
            print(f"WARNING: PDF has {len(images)} pages, processing only first {MAX_PAGES}")
            images = images[:MAX_PAGES]
        
        base64_images = []
        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}...")
            
            # Resize image to target width directly (no upscale→downscale cycle)
            if image.width > max_width:
                ratio = max_width / image.width
                new_height = int(image.height * ratio)
                image = image.resize((max_width, new_height), Image.LANCZOS)
                print(f"Resized page {i+1} to {max_width}x{new_height}")
            
            # Apply OCR enhancement only if not skipped
            if not skip_enhance:
                image = enhance_image_for_ocr(image)
            else:
                print(f"[SKIP_IMAGE_ENHANCE] Skipping enhancement for page {i+1}")
            
            # Save temporarily with moderate quality (smaller payload)
            jpeg_quality = 80 if deepseek_mode else 85
            temp_image_path = f"{pdf_path}_page_{i}.jpg"
            image.save(temp_image_path, 'JPEG', quality=jpeg_quality, optimize=True)
            
            # Convert to base64
            with open(temp_image_path, 'rb') as img_file:
                image_data = img_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                base64_images.append(base64_image)
                
                # Show size info
                size_kb = len(image_data) / 1024
                print(f"Page {i+1} encoded: {size_kb:.1f} KB ({len(base64_image)} chars base64)")
            
            # Clean up temp image
            os.remove(temp_image_path)
        
        # Calculate total payload size
        total_size_mb = sum(len(img) for img in base64_images) / (1024 * 1024)
        print(f"PDF processing complete: {len(base64_images)} images, total ~{total_size_mb:.2f} MB")
        
        return {
            "type": "pdf",
            "pages": base64_images
        }
    except Exception as e:
        print(f"Error processing PDF: {e}")
        import traceback
        traceback.print_exc()
        raise


def merge_page_results(page_extractions, fields_to_extract):
    """
    Merge extraction results from multiple pages into a single result.
    Uses the highest confidence result for each field.
    """
    merged_data = {}
    field_confidences = {}
    all_reasonings = []
    
    # For each field, collect all values and their confidence
    for page_result in page_extractions:
        extraction_results = page_result.get("extraction_results", {})
        page_data = extraction_results.get("data", {})
        page_confidence = extraction_results.get("confidence_score", 0)
        page_reasoning = extraction_results.get("reasoning", "")
        
        if page_reasoning:
            all_reasonings.append(page_reasoning)
        
        for field_key in fields_to_extract.keys():
            field_data = page_data.get(field_key)
            
            # Handle new format with per-field confidence
            if isinstance(field_data, dict) and "value" in field_data:
                value = field_data.get("value")
                confidence = field_data.get("confidence", 0)
            else:
                # Old format
                value = field_data
                confidence = page_confidence
            
            # Skip null/empty values unless we haven't found anything yet
            if value and value != "null" and str(value).lower() not in ["not found", "none"]:
                # Use this value if it's the first one or has higher confidence
                if field_key not in merged_data or confidence > field_confidences.get(field_key, 0):
                    merged_data[field_key] = value
                    field_confidences[field_key] = confidence
    
    # Fill in missing fields with null
    for field_key in fields_to_extract.keys():
        if field_key not in merged_data:
            merged_data[field_key] = None
    
    # Calculate average confidence
    avg_confidence = sum(field_confidences.values()) / len(field_confidences) if field_confidences else 0
    
    # Combine reasonings
    combined_reasoning = " | ".join(set(all_reasonings)) if all_reasonings else "Multi-page extraction"
    
    return {
        "extraction_results": {
            "confidence_score": int(avg_confidence),
            "reasoning": f"Merged from {len(page_extractions)} pages: {combined_reasoning}",
            "data": merged_data,
            "additional_request_result": page_extractions[0].get("extraction_results", {}).get("additional_request_result")
        }
    }


def extract_structured_data_with_ollama(
    document_content,
    fields_to_extract,
    additional_request=None,
    document_type=None,
    system_prompt=None,
    filepath=None,
    mime_type=None,
    extraction_strategy='auto',
):
    """Extract structured data using a single Vision AI pipeline (image-first, no classical OCR pass).
    
    extraction_strategy:
      'auto' — pick the best strategy based on model type
      'single_pass' — direct vision-to-JSON
    """
    if not fields_to_extract or not isinstance(fields_to_extract, dict):
        return {"error": "fields_to_extract is required and must be a dictionary {field: description}"}

    # Build document type context
    doc_type_context = ""
    if document_type:
        doc_type_map = {
            "invoice": "This is an INVOICE/FATTURA document.",
            "receipt": "This is a RECEIPT/SCONTRINO document.",
            "form": "This is a FORM/MODULO with HANDWRITTEN fields.",
            "contract": "This is a CONTRACT/CONTRATTO document.",
            "id_document": "This is an ID DOCUMENT (carta d'identità, passaporto, etc.).",
            "certificate": "This is a CERTIFICATE/CERTIFICATO document.",
            "custom": "Document type specified by user."
        }
        doc_type_context = doc_type_map.get(document_type, f"Document type: {document_type}")

    return single_pass_extraction(
        document_content,
        fields_to_extract,
        additional_request,
        doc_type_context,
        system_prompt,
        filepath=filepath,
        mime_type=mime_type,
        extraction_strategy=extraction_strategy,
    )


def single_pass_extraction(
    document_content,
    fields_to_extract,
    additional_request,
    doc_type_context,
    system_prompt=None,
    filepath=None,
    mime_type=None,
    extraction_strategy='auto',
):
    """Single-pass extraction (direct vision-to-JSON)."""
    model_name = get_ollama_model()

    # Ollama-based models
    print("👁️ Using VISION-AI extraction mode")

    # Flatten pages list regardless of document type
    if document_content["type"] == "image":
        pages = [document_content["data"]]
    else:
        pages = document_content["pages"]

    num_pages = len(pages)
    print(f"Processing {'single image' if num_pages == 1 else f'PDF with {num_pages} page(s)'}")

    # Decide strategy
    if is_ocr_specialist_model(model_name):
        chosen_strategy = 'ocr_specialist'
    else:
        chosen_strategy = 'single_pass'

    print(f"Strategy: {chosen_strategy} (requested={extraction_strategy})")

    try:
        if chosen_strategy == 'ocr_specialist':
            return _ocr_specialist_extraction(
                pages, fields_to_extract, additional_request, doc_type_context
            )
        else:
            return _standard_vision_extraction(
                pages, fields_to_extract, additional_request, doc_type_context, system_prompt
            )
    except Exception as e:
        print(f"Error in single_pass_extraction: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error calling Ollama: {str(e)}",
            "extraction_results": {
                "confidence_score": 0,
                "reasoning": f"Error: {str(e)}",
                "data": {key: None for key in fields_to_extract.keys()},
                "additional_request_result": None,
            },
        }


def _ocr_specialist_extraction(pages, fields_to_extract, additional_request, doc_type_context):
    """Two-phase extraction for OCR-specialist models (deepseek-ocr, glm-ocr):
      Phase 1 – Vision call with the model's native short OCR prompt → raw text.
                 No JSON format, no verbose instructions that the model would echo back.
      Phase 2 – Pure Python regex/contextual parsing of the OCR text → structured fields.
                 Zero extra model calls: no VRAM spikes, no JSON echo problem.
    Supports:
      deepseek-ocr — prompt: '<|grounding|>Extract all text from this document.'
                      outputs grounding annotations that are stripped before parsing
      glm-ocr      — prompt: 'Text Recognition:'
                      outputs clean markdown text directly
    """
    model_name = get_ollama_model()
    if is_glm_ocr_model(model_name):
        OCR_PROMPT = "Text Recognition:"
    else:  # deepseek-ocr (default)
        OCR_PROMPT = "<|grounding|>Extract all text from this document."

    page_extractions = []
    page_errors = []
    total = len(pages)
    # Accumulate OCR text across pages for the additional_request answer
    all_ocr_text = []

    for i, page_image in enumerate(pages):
        label = f"page {i+1}/{total}" if total > 1 else "image"
        model_label = "GLM-OCR" if is_glm_ocr_model(model_name) else "DeepSeek OCR"
        print(f"{model_label} Phase 1 (vision): {label}...")
        try:
            raw_ocr = call_ollama_vision_raw(OCR_PROMPT, [page_image])
            # deepseek-ocr wraps regions in <|ref|>...<|/ref|> annotation tokens → strip them
            # glm-ocr outputs clean markdown → strip_deepseek_ocr_annotations is a safe no-op
            clean_text = strip_deepseek_ocr_annotations(raw_ocr)
            print(f"Phase 1 complete: {len(clean_text)} chars of clean text")

            if not clean_text.strip():
                raise Exception("Phase 1 returned empty text — image may be blank or unreadable")

            all_ocr_text.append(clean_text)

            # Phase 2: regex + contextual parsing (no model call, no VRAM)
            print(f"{model_label} Phase 2 (regex parse): {label}...")
            extracted_data = parse_ocr_text_to_fields(clean_text, fields_to_extract)

            found = [k for k, v in extracted_data.items() if v.get("value") is not None]
            print(f"Phase 2 complete: found {len(found)}/{len(fields_to_extract)} fields: {found}")

            page_extractions.append({
                "extraction_results": {
                    "confidence_score": 80,
                    "reasoning": f"{model_label} two-phase extraction — page {i+1}",
                    "data": extracted_data,
                    "additional_request_result": None
                }
            })

        except Exception as e:
            page_errors.append(f"Page {i+1}: {str(e)}")
            print(f"Error on {label}: {e}")
            continue

    if not page_extractions:
        raise Exception(f"Failed to process any page. {' | '.join(page_errors[:3])}")

    result = page_extractions[0] if len(page_extractions) == 1 else merge_page_results(page_extractions, fields_to_extract)

    # If there is an additional_request, do a final targeted vision call on p.1 to answer it
    if additional_request and all_ocr_text:
        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(all_ocr_text)
        result["extraction_results"]["additional_request_result"] = (
            f"[From OCR text] {combined_text[:800]}"
        )

    return result


# NOTE: _ocr_then_extract was removed — single_pass is more reliable for all current models


def _standard_vision_extraction(pages, fields_to_extract, additional_request, doc_type_context, system_prompt=None):
    """Standard single-pass vision extraction for llama3.2-vision, llava, bakllava, etc."""
    fields_to_extract_str = "\n".join(
        [f"- `{key}`: {description}" for key, description in fields_to_extract.items()]
    )
    default_system_prompt = """You are an expert vision document extraction system specialized in reading documents, including handwritten text.

CRITICAL INSTRUCTIONS FOR ACCURATE TEXT EXTRACTION:

1. **HANDWRITTEN TEXT**: Read each character carefully:
    - Look at the SHAPE of each letter/number
    - Consider context to disambiguate similar characters (0/O, 1/I/l, 5/S, 8/B, etc.)
    - Italian Codice Fiscale format: 16 characters (letters and digits only)
      Example: RSSMRA85M01H501Z

2. **CHARACTER-BY-CHARACTER READING**: For codes and IDs:
    - Read EACH character individually
    - Double-check ambiguous characters

3. **VISUAL CONTEXT**: Use the full page visual context (tables, labels, charts, handwritten notes)
    to infer which values map to which fields.

4. **BE PRECISE**: Extract exactly what is visible in the image."""

    base_prompt = system_prompt.strip() if system_prompt and system_prompt.strip() else default_system_prompt

    data_template = ', '.join(
        [f'"{key}": {{"value": null, "confidence": 0}}' for key in fields_to_extract.keys()]
    )
    instruction = f"""{base_prompt}
{f"DOCUMENT TYPE: {doc_type_context}" if doc_type_context else ""}

FIELD EXTRACTION:
For each field below, extract the EXACT text as written:
{fields_to_extract_str}

{f"ADDITIONAL REQUEST: {additional_request}" if additional_request else ""}

OUTPUT FORMAT: Return ONLY valid JSON matching this exact structure:
{{
  "extraction_results": {{
    "overall_confidence": 0,
    "reasoning": "describe any difficulties",
    "data": {{
      {data_template}
    }},
    "additional_request_result": null
  }}
}}

Now analyze the document image and extract the requested fields. DO NOT wrap JSON in markdown blocks like ```json."""

    total = len(pages)
    page_extractions = []
    page_errors = []

    for i, page_image in enumerate(pages):
        label = f"page {i+1}/{total}" if total > 1 else "image"
        print(f"Processing {label}...")
        try:
            page_instruction = (
                f"{instruction}\n\nNote: This is page {i+1} of {total} from the document."
                if total > 1 else instruction
            )
            page_response = call_ollama_vision(page_instruction, [page_image])
            
            # Clean possible markdown wrap
            page_response = page_response.strip()
            if page_response.startswith("```json"):
                page_response = page_response[7:]
            if page_response.startswith("```"):
                page_response = page_response[3:]
            if page_response.endswith("```"):
                page_response = page_response[:-3]

            page_result = parse_extraction_result(page_response, fields_to_extract)
            page_extractions.append(page_result)
        except Exception as page_error:
            print(f"Error processing {label}: {page_error}")
            try:
                import time as _time
                print(f"Unloading model and waiting before retry...")
                unload_ollama_model()
                print(f"Retrying {label} with aggressively smaller image (768px)...")
                smaller = downscale_base64_image(page_image, max_width=768, jpeg_quality=75)
                retry_response = call_ollama_vision(page_instruction, [smaller])
                retry_result = parse_extraction_result(retry_response, fields_to_extract)
                page_extractions.append(retry_result)
                print(f"Retry succeeded for {label}")
            except Exception as retry_error:
                page_errors.append(f"Page {i+1}: {str(retry_error)}")
                print(f"Retry failed for {label}: {retry_error}")
                continue

    if not page_extractions:
        detailed = " | ".join(page_errors[:3]) if page_errors else "No valid extraction produced"
        raise Exception(f"Failed to process any page of the document. {detailed}")

    if len(page_extractions) == 1:
        return page_extractions[0]
    print(f"Merging results from {len(page_extractions)} pages...")
    return merge_page_results(page_extractions, fields_to_extract)


def parse_ocr_text_to_fields(ocr_text, fields_to_extract):
    """Parse cleaned deepseek-ocr text output into field values.

    DeepSeek OCR reads handwritten block letters as dotted spelling artifacts:
      'STILO' → 'S.T.I.L.O.'   'FABIO' → 'F.A.B.I.O.'
    This function:
      1. De-dots the full OCR text (S.T.I.L.O. → STILO) before any search
      2. Finds each label and captures the value up to the NEXT Italian field label
      3. Applies a dedicated CF regex, with fallback to raw segment extraction
    """
    import re

    # ── Step 1: de-dot ────────────────────────────────────────────────────────
    # Collapse X.Y.Z. patterns where each char is a single letter/digit followed by a dot.
    # Only triggered when starting with a letter to avoid breaking dates (04.09.1987)
    # and phone numbers.
    # NOTE: do NOT allow spaces inside the collapsed group — keep inter-word spaces intact
    # so that "V.I.B.O. V.A.L.E.N.T.I.A." → "VIBO VALENTIA" (not "VIBOVALENTIA").
    def dedot(t):
        def collapse(m):
            return re.sub(r'\.', '', m.group(0))   # remove ONLY dots, keep spaces
        # Match: letter followed by 2+ occurrences of (dot + letter/digit) — NO space allowed
        return re.sub(r'[A-Za-z](?:\.[A-Za-z0-9]){2,}\.?', collapse, t)

    text = dedot(ocr_text)

    # ── Step 2: boundary label pattern ────────────────────────────────────────
    # Used to terminate value capture at the next recognised Italian field label
    _BOUNDARY = re.compile(
        r'(?i)\b(?:'
        r'codice\s+fiscale|cod\.?\s*fiscale|cognome|nome|sesso|'
        r'data\s+(?:di\s+)?nascita|nato\s+a|nata\s+a|in\s+data|'
        r'residente\s+nel|residente|comune\s+(?:di\s+)?nascita|luogo\s+di\s+nascita|'
        r'il\s+sottoscritto|in\s+qualit|id_arera|con\s+sede|'
        r'denominazione|ragione\s+sociale|'
        r'indirizzo\s+e-?mail|indirizzo|telefono|tel\.|partita\s+iva|'
        r'(?:e-?mail|email)\s|pec(?:\s|$)|provincia|comune\b|cap\b|tipologia|'
        r'chiede|per\s+la\s+figura|l\'abilitazione|modulo\s+\d|pag\.\s*\d'
        r')\b'
    )

    def extract_value(aliases):
        """Return the text between a matched label and the next boundary label or newline."""
        escaped = '|'.join(re.escape(a) for a in sorted(aliases, key=len, reverse=True))
        label_pat = re.compile(rf'(?i)(?:^|\n|(?<=\s))(?:{escaped})\s*[.:\-]*\s*')
        m = label_pat.search(text)
        if not m:
            return None
        start = m.end()
        # Priority 1: stop at end of current line (values don't span lines in these forms)
        newline_pos = text.find('\n', start)
        line_end = newline_pos if newline_pos != -1 else start + 120
        # Priority 2: stop at next boundary label within the same line
        next_b = _BOUNDARY.search(text, start)
        end = min(
            line_end,
            next_b.start() if next_b else start + 120
        )
        raw = text[start:end]
        # Strip trailing dots/spaces, collapse internal whitespace
        val = re.sub(r'\s+', ' ', raw).strip().strip('.,;: -')
        if val and len(val) >= 1 and not re.match(r'^[.\s]+$', val):
            return val
        return None

    # ── Step 3: ALIASES table ─────────────────────────────────────────────────
    ALIASES = {
        "codice_fiscale":    ["codice fiscale", "cod. fiscale", "codice\nfiscale", "cf"],
        "cognome":           ["cognome"],
        "nome":              ["nome"],
        "sesso":             ["sesso"],
        "data_nascita":      ["in data", "data di nascita", "data nascita", "nato il", "nata il"],
        "comune_nascita":    ["nato a", "nata a", "comune di nascita", "luogo di nascita"],
        "provincia_nascita": ["provincia di nascita", "prov. nascita"],
        "denominazione_ente":["denominazione ente", "ragione sociale", "denominazione"],
        "indirizzo":         ["indirizzo"],
        "telefono":          ["telefono", "tel."],
        "email":             ["indirizzo e-mail", "indirizzo email", "e-mail", "email"],
        "pec":               ["pec"],
        "tipologia":         ["tipologia"],
        "comune":            ["comune"],
        "provincia":         ["provincia"],
        "cap":               ["cap"],
    }

    # ── Step 4: Italian CF regex (strict) ─────────────────────────────────────
    CF_STRICT = re.compile(
        r'\b([A-Z]{6}[0-9]{2}[A-EHLMPRST][0-9]{2}[A-Z][0-9]{3}[A-Z])\b',
        re.IGNORECASE
    )

    # ── Step 5: extract each field ────────────────────────────────────────────
    result = {}
    for field_key in fields_to_extract.keys():
        value = None
        confidence = 0
        key_lower = field_key.lower()

        # ─ Codice Fiscale: strict regex first, then segment fallback ──────────
        if any(x in key_lower for x in ("codice", "fiscal", "tax_code")):
            m = CF_STRICT.search(text)
            if m:
                value = m.group(1).upper()
                confidence = 95
            else:
                # OCR misread some chars → fall back to segment extraction
                seg = extract_value(ALIASES["codice_fiscale"])
                if seg:
                    # Strip "Sesso" and everything after (often on same line)
                    seg = re.sub(r'(?i)\s*sesso.*', '', seg).strip()
                    # Remove internal spaces (two dotted groups may have been joined with space)
                    candidate = re.sub(r'\s+', '', seg)
                    if 14 <= len(candidate) <= 20:
                        value = candidate[:16] if len(candidate) >= 16 else candidate
                        confidence = 55  # lower: OCR errors possible

        # ─ Sesso: M/F or MASCHILE/FEMMINILE ──────────────────────────────────
        elif key_lower == "sesso":
            seg = extract_value(ALIASES["sesso"])
            if seg:
                s = seg.strip().upper()
                if s.startswith("M"):
                    value, confidence = "M", 90
                elif s.startswith("F"):
                    value, confidence = "F", 90
                else:
                    value, confidence = s, 70

        # ─ Data di nascita: grab date with dots intact (04.09.1987 style) ─────
        elif any(x in key_lower for x in ("data", "nascita_d", "birth_date", "dob")):
            seg = extract_value(ALIASES.get(key_lower, ["data di nascita", "in data"]))
            if seg:
                # Prefer 8-10 char date-like segment
                date_m = re.search(r'\d{2}[.\-/]\d{2}[.\-/]\d{2,4}', seg)
                if date_m:
                    value, confidence = date_m.group(0), 90
                else:
                    value, confidence = seg, 70

        # ─ Generic fields ─────────────────────────────────────────────────────
        else:
            aliases = ALIASES.get(key_lower, [key_lower.replace("_", " ")])
            seg = extract_value(aliases)
            if seg:
                value, confidence = seg, 80

        result[field_key] = {"value": value, "confidence": confidence}

    return result


def strip_deepseek_ocr_annotations(text):
    """Remove deepseek-ocr grounding annotations from OCR output.
    The model wraps each text region with:
      <|ref|>label<|/ref|><|det|>[[x1,y1,x2,y2]]<|/det|>
    followed by the actual text. We strip the annotation tags and keep only the text.
    """
    import re
    # Remove full annotation blocks: <|ref|>...<|/ref|><|det|>...<|/det|>
    text = re.sub(r'<\|ref\|>.*?<\|/ref\|>\s*<\|det\|>.*?<\|/det\|>', '', text, flags=re.DOTALL)
    # Remove any remaining special tokens like <|token|>
    text = re.sub(r'<\|[^|]+\|>', '', text)
    # Collapse multiple blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _call_ollama_chat(model, prompt, images_base64, base_url, options, format_json=False):
    """Call Ollama /api/chat endpoint using streaming to work around the Qwen3.5
    non-streaming empty-content bug.

    Qwen3.5 (thinking model) sends thinking tokens in a separate 'thinking' field
    and the actual answer in 'content'. With stream=False the Ollama server collapses
    these into a single message where 'content' is often empty. With stream=True each
    chunk arrives individually so we can collect only the 'content' pieces.

    If content is still empty after streaming, we fall back to:
      1. Trying to use any 'thinking' tokens collected (the model may have put the
         actual answer there by mistake)
      2. If still empty, retry once after a short delay
    """
    import time as _time
    url = f"{base_url}/api/chat"

    # Images go inside the message object for /api/chat
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": images_base64
            }
        ],
        "stream": True,   # ← must be True for Qwen3.5 to return non-empty content
        "keep_alive": get_ollama_keep_alive(),
        "options": options
    }

    # format:json causes empty responses on Qwen — skip it, we parse JSON ourselves
    if format_json and not any(kw in model.lower() for kw in ['qwen', 'qwq']):
        payload["format"] = "json"

    def _do_streaming_call():
        """Perform one streaming call, return (content_text, thinking_text)."""
        content_chunks = []
        thinking_chunks = []
        print(f"[Chat API streaming] Calling {model} via /api/chat (stream=True)...")
        with requests.post(url, json=payload, stream=True, timeout=get_ollama_timeout()) as response:
            response.raise_for_status()
            for raw_line in response.iter_lines(decode_unicode=True):
                if not raw_line:
                    continue
                try:
                    chunk = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                msg = chunk.get("message", {})
                # Collect 'content' (the actual answer)
                piece = msg.get("content", "")
                if piece:
                    content_chunks.append(piece)
                # Also collect 'thinking' as fallback diagnostic
                think_piece = msg.get("thinking", "")
                if think_piece:
                    thinking_chunks.append(think_piece)
                if chunk.get("done", False):
                    break

        content_text = "".join(content_chunks)
        thinking_text = "".join(thinking_chunks)
        return content_text, thinking_text

    # First attempt
    response_text, thinking_text = _do_streaming_call()
    print(f"[Chat API streaming] Collected {len(response_text)} chars of content, {len(thinking_text)} chars of thinking")

    # If content is empty, try to salvage from thinking tokens
    if not response_text and thinking_text:
        print(f"[Chat API streaming] Content is empty but got {len(thinking_text)} thinking chars — checking for JSON in thinking...")
        # Strip thinking tags and try to use the text
        cleaned_thinking = strip_thinking_tags(thinking_text)
        if cleaned_thinking:
            # Check if thinking contains JSON (model might have put the answer there)
            if '{' in cleaned_thinking and '}' in cleaned_thinking:
                print(f"[Chat API streaming] Found potential JSON in thinking block, using as response")
                response_text = cleaned_thinking
            else:
                print(f"[Chat API streaming] Thinking block has text but no JSON")

    # If still empty, unload model and retry once
    if not response_text:
        print(f"[Chat API streaming] Empty response — unloading model and retrying...")
        unload_ollama_model()
        response_text, thinking_text = _do_streaming_call()
        print(f"[Chat API streaming RETRY] Collected {len(response_text)} chars of content, {len(thinking_text)} chars of thinking")

        # Try thinking fallback again on retry
        if not response_text and thinking_text:
            cleaned_thinking = strip_thinking_tags(thinking_text)
            if cleaned_thinking and '{' in cleaned_thinking and '}' in cleaned_thinking:
                print(f"[Chat API streaming RETRY] Using JSON from thinking block")
                response_text = cleaned_thinking

    return response_text



def call_ollama_vision_raw(prompt, images_base64):
    """Call Ollama vision model WITHOUT format:json — returns plain text.
    Used for Phase 1 of OCR two-phase extraction.
    Falls back to /api/chat if /api/generate returns empty (qwen3-vl compat).
    """
    base_url = get_ollama_base_url()
    model = get_ollama_model()
    url = f"{base_url}/api/generate"

    thinking = is_thinking_model(model)
    num_ctx = 8192 if thinking else 4096

    options = {
        "temperature": 0.1,
        "num_predict": 3000,
        "num_ctx": num_ctx,
        "num_keep": 0
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "images": images_base64,
        "stream": False,
        "keep_alive": get_ollama_keep_alive(),
        "options": options
    }

    try:
        if any(kw in model.lower() for kw in ['qwen', 'qwq']):
            print(f"[OCR Phase 1] By-passing /api/generate for {model}, using /api/chat directly...")
            response_text = _call_ollama_chat(model, prompt, images_base64, base_url, options)
        else:
            print(f"[OCR Phase 1] Calling {model} for raw text extraction...")
            response = requests.post(url, json=payload, timeout=get_ollama_timeout())
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")

        if not response_text:
            print("WARNING: Empty OCR response from Ollama")
            return ""
        # Strip thinking tags if present
        response_text = strip_thinking_tags(response_text)
        print(f"[OCR Phase 1] Got {len(response_text)} chars of OCR text")
        return response_text
    except requests.exceptions.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            raise Exception(f"OCR Phase 1 failed: HTTP {e.response.status_code} — {e.response.text[:200]}")
        raise


def call_ollama_vision(prompt, images_base64):
    """
    Call Ollama API with vision model.
    Falls back to /api/chat if /api/generate returns empty (qwen3-vl compat).
    images_base64: list of base64 encoded images
    """
    base_url = get_ollama_base_url()
    model = get_ollama_model()
    url = f"{base_url}/api/generate"
    
    # Check if model supports vision before calling
    if not is_vision_model(model, base_url):
        raise Exception(f"❌ Model '{model}' does not support vision/image input. Please select a vision-capable model like: deepseek-ocr, llama3.2-vision, llava, or bakllava.")

    # Thinking models need more context and benefit from /no_think to avoid
    # wasting tokens on chain-of-thought during structured extraction.
    # Vision calls require a large num_ctx: a 1600x2261 image produces ~13,000 visual
    # patch tokens (14x14px each). If num_ctx < total tokens the model silently returns
    # an empty string. We use 16384 for vision to stay safe.
    thinking = is_thinking_model(model)
    num_ctx = 16384 if thinking else 8192
    if thinking:
        prompt = prompt + " /no_think"
        print(f"[Thinking model] Added /no_think, num_ctx={num_ctx}")

    # Qwen VL models tile images into 14x14px patches. Large images (>1024px wide)
    # can produce thousands of tokens and overflow the context window silently.
    # Pre-downscale to 1024px for Qwen to keep the patch count manageable.
    max_w = get_image_max_width()
    is_qwen_model = any(kw in model.lower() for kw in ['qwen', 'qwq'])
    if is_qwen_model:
        images_base64 = [
            downscale_base64_image(img, max_width=max_w, jpeg_quality=85)
            for img in images_base64
        ]
        print(f"[Qwen vision] Pre-downscaled images to max {max_w}px to avoid context overflow")
    
    options = {
        "temperature": 0.1,
        "top_p": 0.9,
        "top_k": 40,
        "num_predict": 4000,
        "repeat_penalty": 1.0,
        "num_ctx": num_ctx,
        "num_keep": 0
    }

    # Disable the thinking/CoT chain for Qwen3 models.
    # /no_think in the prompt is unreliable; the Ollama 'think' option is the proper switch.
    # Without this, Qwen3.5 burns ALL context tokens on its thinking chain and
    # produces 0 chars of actual 'content', causing the empty response bug.
    if thinking:
        options["think"] = False
        print(f"[Thinking model] Disabled CoT (think=False), num_ctx={num_ctx}")
    
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images_base64,
        "stream": False,
        "keep_alive": get_ollama_keep_alive(),
        "options": options
    }
    
    # Qwen models often bug out with empty responses if "format": "json" is used.
    # We already prompt them to return raw JSON and strip markdown.
    is_qwen = any(kw in model.lower() for kw in ['qwen', 'qwq'])
    if not is_qwen:
        payload["format"] = "json"
    
    try:
        print(f"Calling Ollama with model: {model}")
        print(f"Processing {len(images_base64)} image(s)...")

        if is_qwen:
            print(f"[{model}] Routing directly to /api/chat to bypass empty /generate bug...")
            response_text = _call_ollama_chat(model, prompt, images_base64, base_url, options, format_json=True)
        else:
            response = requests.post(url, json=payload, timeout=get_ollama_timeout())
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "")

            # Fallback to /api/chat if generate returned empty (qwen3-vl, etc.)
            if not response_text:
                print("[Vision] Empty from /api/generate, trying /api/chat fallback...")
                response_text = _call_ollama_chat(model, prompt, images_base64, base_url, options, format_json=True)

        if not response_text:
            print("WARNING: Empty response from Ollama")
            raise Exception("Empty response from Ollama")

        # Strip <think>...</think> from thinking models before JSON parsing
        if thinking:
            response_text = strip_thinking_tags(response_text)
        
        print(f"Ollama response length: {len(response_text)} characters")
        return response_text
    
    except requests.exceptions.Timeout:
        print("ERROR: Ollama request timed out")
        raise Exception("Ollama request timed out. Try with a smaller document or faster model.")
    except requests.exceptions.RequestException as e:
        print(f"Error calling Ollama API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            print(f"Response status: {status_code}")
            print(f"Response body: {e.response.text[:500]}")
            
            # Provide helpful error messages
            if status_code == 400:
                error_body = e.response.text.lower()
                if 'does not support images' in error_body or 'vision' in error_body:
                    raise Exception(f"❌ Model '{model}' does not support vision/image input. Please select a vision-capable model like: deepseek-ocr, llama3.2-vision, llava, or bakllava.")
                raise Exception("Bad Request to Ollama. Possible causes: image too large, too many images, or invalid format. Try with a smaller/simpler document.")
            elif status_code == 413:
                raise Exception("Payload too large for Ollama. The document images are too big. Try with a smaller document.")
            elif status_code == 500:
                raise Exception("Ollama internal error. The model might have crashed. Try restarting Ollama: ollama serve")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

def is_vision_model(model_name, base_url):
    """
    Check if a model supports vision/image input.
    
    Primary method: check 'capabilities' list from /api/show (Ollama ≥ 0.8).
    Fallback: check for CLIP in families, projector_info, vision model_info keys,
    or known vision family names.
    """
    try:
        show_response = requests.post(
            f"{base_url}/api/show",
            json={"name": model_name},
            timeout=5
        )
        
        if show_response.status_code == 200:
            show_data = show_response.json()
            
            # ── Primary: 'capabilities' field (most reliable) ──
            capabilities = show_data.get('capabilities', [])
            if 'vision' in capabilities:
                print(f"Model {model_name} is vision-capable (capabilities={capabilities})")
                return True
            if capabilities and 'vision' not in capabilities:
                print(f"Model {model_name} is text-only (capabilities={capabilities})")
                return False
            
            # ── Fallback 1: CLIP in families or projector_info ──
            details = show_data.get('details', {})
            families = details.get('families', [])
            if 'clip' in families:
                print(f"Model {model_name} is vision-capable (has CLIP)")
                return True
            if 'projector_info' in show_data:
                print(f"Model {model_name} is vision-capable (has projector)")
                return True
            
            # ── Fallback 2: vision keys in model_info ──
            model_info = show_data.get('model_info', {})
            if any('.vision.' in k for k in model_info.keys()):
                print(f"Model {model_name} is vision-capable (has vision keys in model_info)")
                return True
            
            # ── Fallback 3: known vision families ──
            family = details.get('family', '').lower()
            known_vision_families = {
                'mllama', 'llava', 'bakllava', 'qwen3vl', 'qwen2vl',
                'deepseekocr', 'deepseek-ocr', 'deepseek-vl', 'glm-ocr',
                'gemma3', 'llama4',
            }
            if family in known_vision_families or any(f.lower() in known_vision_families for f in families):
                print(f"Model {model_name} is vision-capable (known vision family: {family})")
                return True
            
            # ── Fallback 4: keywords in model name ──
            model_lower = model_name.lower()
            if any(kw in model_lower for kw in ['vision', 'llava', 'bakllava', '-vl', 'deepseek-ocr', 'glm-ocr']):
                print(f"Model {model_name} is vision-capable (name contains vision keyword)")
                return True
            
            print(f"Model {model_name} appears to be text-only (family: {family}, families: {families})")
            return False
        
        # If /api/show failed, assume vision to avoid blocking
        print(f"Warning: Could not verify if {model_name} is a vision model")
        return True
        
    except Exception as e:
        print(f"Error checking if model is vision-capable: {e}")
        return True  # Assume yes on error to avoid blocking

def parse_extraction_result(response_text, fields_to_extract, ocr_text=None):
    """
    Parse the extraction result from Ollama, handling various response formats.
    """
    import re
    
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError as je:
        print(f"JSON decode error: {je}")
        print(f"Raw response (first 500 chars): {response_text[:500]}")
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except:
                raise Exception(f"Could not parse JSON response")
        else:
            raise Exception(f"No JSON found in response")
    
    # Validate structure
    if "extraction_results" not in result:
        result = {
            "extraction_results": {
                "overall_confidence": 50,
                "reasoning": "Response format was unexpected",
                "data": result if isinstance(result, dict) else {},
                "additional_request_result": None
            }
        }
    
    extraction_results = result.get("extraction_results", {})
    data = extraction_results.get("data", {})
    if not isinstance(data, dict):
        data = {}
    
    # Map model's returned keys (might have different casing) to our lowercased keys
    data_lower_keys = {str(k).lower().strip(): k for k in data.keys()}
    
    # Process per-field confidence format
    processed_data = {}
    field_confidences = []
    
    for field_key in fields_to_extract.keys():
        # Match case-insensitively
        actual_key = data_lower_keys.get(field_key.lower().strip())
        field_data = data.get(actual_key) if actual_key else None
        
        if isinstance(field_data, dict) and "value" in field_data:
            processed_data[field_key] = field_data.get("value")
            raw_conf = field_data.get("confidence", 50)
            
            # Fix if model returns confidence as 0.99 instead of 99
            if isinstance(raw_conf, float) and raw_conf <= 1.0:
                raw_conf = raw_conf * 100
            
            try:
                confidence = int(raw_conf)
            except:
                confidence = 50
                
            field_confidences.append(confidence)
            
            if confidence < 50:
                print(f"⚠️ Low confidence ({confidence}%) for field '{field_key}': {processed_data[field_key]}")
        else:
            processed_data[field_key] = field_data
            field_confidences.append(50)
            
    overall_confidence = int(sum(field_confidences) / len(field_confidences)) if field_confidences else 0
    
    if "overall_confidence" not in extraction_results:
        extraction_results["overall_confidence"] = overall_confidence
    
    extraction_results["confidence_score"] = extraction_results.get("overall_confidence", overall_confidence)
    extraction_results["data"] = processed_data
    
    # Add OCR text reference if available
    if ocr_text:
        extraction_results["ocr_preview"] = ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text
    
    return result