import os
import json
import base64
import requests
from pathlib import Path
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image

# Configuration is read dynamically from environment to allow runtime changes
def get_ollama_base_url():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

def get_ollama_model():
    return os.getenv("OLLAMA_MODEL", "llama3.2-vision")


def process_document(filepath, mime_type):
    """
    Process document based on type:
    - Images: return as base64
    - PDFs: convert to images and return as base64 array
    """
    if mime_type.startswith('image/'):
        return process_image(filepath)
    elif mime_type == 'application/pdf':
        return process_pdf(filepath)
    else:
        raise ValueError(f"Unsupported file type: {mime_type}")


def process_image(image_path):
    """Process image file and return base64 encoded"""
    try:
        with open(image_path, 'rb') as img_file:
            image_data = img_file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')
            return {
                "type": "image",
                "data": base64_image
            }
    except Exception as e:
        print(f"Error processing image: {e}")
        raise


def process_pdf(pdf_path):
    """
    Process PDF by converting pages to images
    Returns array of base64 encoded images
    """
    try:
        print(f"Converting PDF to images: {pdf_path}")
        # Convert PDF pages to images with HIGHER DPI for better text recognition
        # Using 250 DPI for excellent OCR quality
        images = convert_from_path(pdf_path, dpi=250)
        print(f"PDF converted to {len(images)} page(s)")
        
        # Limit pages to avoid huge payloads
        MAX_PAGES = 10
        if len(images) > MAX_PAGES:
            print(f"WARNING: PDF has {len(images)} pages, processing only first {MAX_PAGES}")
            images = images[:MAX_PAGES]
        
        base64_images = []
        for i, image in enumerate(images):
            print(f"Processing page {i+1}/{len(images)}...")
            
                        # Resize image to fit model limits while preserving quality
            # LLaVA 1.6: supports up to 1344x1344 (4x resolution improvement!)
            # Gemma3: no strict documented limit
            # Llama Vision: tested to handle larger images than documented
            # Using 1344px to match LLaVA 1.6 max resolution for best OCR
            MAX_WIDTH = 1344
            if image.width > MAX_WIDTH:
                ratio = MAX_WIDTH / image.width
                new_height = int(image.height * ratio)
                image = image.resize((MAX_WIDTH, new_height), Image.LANCZOS)
                print(f"Resized page {i+1} to {MAX_WIDTH}x{new_height}")
            
            # Save temporarily with HIGH quality compression for OCR
            # Quality 95 for minimal JPEG artifacts on text
            temp_image_path = f"{pdf_path}_page_{i}.jpg"
            image.save(temp_image_path, 'JPEG', quality=95, optimize=True)
            
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


def extract_structured_data_with_ollama(document_content, fields_to_extract, additional_request=None):
    """
    Extract structured data from document using Ollama multimodal model
    """
    if not fields_to_extract or not isinstance(fields_to_extract, dict):
        return {"error": "fields_to_extract is required and must be a dictionary {field: description}"}

    # Build field descriptions
    fields_to_extract_str = "\n".join([f"- `{key}`: {description}" for key, description in fields_to_extract.items()])

    # Build prompt with per-field confidence based on image quality
    instruction = f"""You are a document data extraction assistant. Extract information from this document image.

EXTRACTION RULES:
1. Copy text EXACTLY as it appears (preserve formatting, spacing, case)
2. For each field, provide the extracted value and a confidence score (0-100)
3. **IMPORTANT**: Confidence must reflect the IMAGE QUALITY and text legibility:
   
   HIGH CONFIDENCE (80-100):
   - Image is sharp and clear
   - Text is crisp and perfectly readable
   - No blur, no pixelation, no fading
   - Characters are large enough and well-defined
   
   MEDIUM CONFIDENCE (50-79):
   - Image has some blur or compression artifacts
   - Text is readable but not perfectly sharp
   - Some characters may be slightly unclear
   - Slight fading or small font size
   
   LOW CONFIDENCE (20-49):
   - Image is blurry, faded, or low resolution
   - Text is difficult to read clearly
   - Characters are small and compressed
   - You had to guess some characters
   - Scanned document with poor quality
   
   VERY LOW CONFIDENCE (0-19):
   - Image is extremely poor quality
   - Text is barely legible or illegible
   - Heavy pixelation, blur, or fading
   - Cannot confidently read most characters → use null

4. **For critical data (IBAN, codes, numbers)**: 
   - If image quality makes ANY digit/character unclear → reduce confidence significantly
   - Example: If 1-2 characters in IBAN are unclear due to image quality → max confidence 60%
   - Example: If several characters unclear → confidence 30-40%
   - Better to extract with low confidence than return null

5. In "reasoning", mention image quality issues if present

Fields to extract:
{fields_to_extract_str}

Additional request: {additional_request if additional_request else 'None'}

Respond with ONLY this JSON structure:
{{
  "extraction_results": {{
    "overall_confidence": <average of all field confidences>,
    "reasoning": "<mention image quality and any difficulties reading text>",
    "data": {{
      {', '.join([f'"{key}": {{"value": "<extracted text or null>", "confidence": <0-100 reflecting image quality>}}' for key in fields_to_extract.keys()])}
    }},
    "additional_request_result": "<answer or null>"
  }}
}}"""

    try:
        # Prepare messages for Ollama
        if document_content["type"] == "image":
            # Single image
            print("Processing single image document")
            response = call_ollama_vision(instruction, [document_content["data"]])
        else:  # PDF with multiple pages
            num_pages = len(document_content["pages"])
            print(f"Processing PDF document with {num_pages} page(s)")
            
            # llama3.2-vision supports ONLY ONE image at a time
            # Process each page separately and merge results
            if num_pages == 1:
                # Single page - process directly
                response = call_ollama_vision(instruction, [document_content["pages"][0]])
            else:
                # Multiple pages - process each one and combine
                print(f"Processing {num_pages} pages individually (model supports 1 image at a time)...")
                
                page_extractions = []
                for i, page_image in enumerate(document_content["pages"]):
                    print(f"Processing page {i+1}/{num_pages}...")
                    try:
                        page_instruction = f"{instruction}\n\nNote: This is page {i+1} of {num_pages} from the document."
                        page_response = call_ollama_vision(page_instruction, [page_image])
                        
                        # Parse the page result
                        try:
                            page_result = json.loads(page_response)
                            page_extractions.append(page_result)
                        except json.JSONDecodeError:
                            print(f"Warning: Could not parse JSON from page {i+1}")
                    except Exception as page_error:
                        print(f"Error processing page {i+1}: {page_error}")
                        # Continue with other pages
                
                if not page_extractions:
                    raise Exception("Failed to process any page of the document")
                
                # Merge results from all pages
                print(f"Merging results from {len(page_extractions)} successfully processed page(s)...")
                merged_result = merge_page_results(page_extractions, fields_to_extract)
                response = json.dumps(merged_result)
        
        # Parse response - handle potential JSON issues
        try:
            result = json.loads(response)
        except json.JSONDecodeError as je:
            print(f"JSON decode error: {je}")
            print(f"Raw response (first 500 chars): {response[:500]}")
            
            # Try to extract JSON from response if wrapped in markdown or text
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    print("Successfully extracted JSON from response")
                except:
                    raise Exception(f"Could not parse JSON response. Raw: {response[:200]}")
            else:
                raise Exception(f"No JSON found in response. Raw: {response[:200]}")
        
        # Validate structure
        if "extraction_results" not in result:
            print("WARNING: Unexpected response structure, wrapping result")
            result = {
                "extraction_results": {
                    "overall_confidence": 0,
                    "reasoning": "Response format was unexpected",
                    "data": result if isinstance(result, dict) else {},
                    "additional_request_result": None
                }
            }
        
        extraction_results = result.get("extraction_results", {})
        data = extraction_results.get("data", {})
        
        # Handle new format with per-field confidence
        # Convert {"field": {"value": "...", "confidence": 90}} to {"field": "..."}
        # and calculate overall confidence from field confidences
        processed_data = {}
        field_confidences = []
        
        for field_key in fields_to_extract.keys():
            field_data = data.get(field_key)
            
            if isinstance(field_data, dict) and "value" in field_data:
                # New format with confidence per field
                processed_data[field_key] = field_data.get("value")
                confidence = field_data.get("confidence", 0)
                field_confidences.append(confidence)
                
                # Log low confidence fields
                if confidence < 50:
                    print(f"⚠️ Low confidence ({confidence}%) for field '{field_key}': {field_data.get('value')}")
            else:
                # Old format or missing field
                processed_data[field_key] = field_data
                field_confidences.append(50)  # Default medium confidence for old format
        
        # Calculate overall confidence from field confidences
        overall_confidence = int(sum(field_confidences) / len(field_confidences)) if field_confidences else 0
        
        # Override overall_confidence if present in response
        if "overall_confidence" not in extraction_results:
            extraction_results["overall_confidence"] = overall_confidence
        
        # Keep both confidence_score (old) and overall_confidence (new) for compatibility
        extraction_results["confidence_score"] = extraction_results.get("overall_confidence", overall_confidence)
        extraction_results["data"] = processed_data
        
        return result

    except Exception as e:
        print(f"Error in extract_structured_data_with_ollama: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error calling Ollama: {str(e)}",
            "extraction_results": {
                "confidence_score": 0,
                "reasoning": f"Error: {str(e)}",
                "data": {key: None for key in fields_to_extract.keys()},
                "additional_request_result": None
            }
        }


def call_ollama_vision(prompt, images_base64):
    """
    Call Ollama API with vision model
    images_base64: list of base64 encoded images
    """
    base_url = get_ollama_base_url()
    model = get_ollama_model()
    url = f"{base_url}/api/generate"
    
    # Check if model supports vision before calling
    if not is_vision_model(model, base_url):
        raise Exception(f"❌ Model '{model}' does not support vision/image input. Please select a vision-capable model like: llama3.2-vision, llava, or bakllava.")
    
    payload = {
        "model": model,
        "prompt": prompt,
        "images": images_base64,
        "stream": False,
        "format": "json",  # Force JSON output
        "options": {
            "temperature": 0.0,  # Zero temperature for maximum determinism and no creativity
            "top_p": 0.1,  # Very low top_p to reduce randomness
            "top_k": 10,  # Limit vocabulary choices
            "num_predict": 2000,  # Max tokens for detailed responses
            "repeat_penalty": 1.0  # No penalty, we want exact text extraction
        }
    }
    
    try:
        print(f"Calling Ollama with model: {model}")
        print(f"Processing {len(images_base64)} image(s)...")

        response = requests.post(url, json=payload, timeout=300)  # Increased timeout
        response.raise_for_status()

        result = response.json()
        response_text = result.get("response", "")
        
        if not response_text:
            print("WARNING: Empty response from Ollama")
            return "{}"
        
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
                    raise Exception(f"❌ Model '{model}' does not support vision/image input. Please select a vision-capable model like: llama3.2-vision, llava, or bakllava.")
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
    Check if a model supports vision/image input by checking:
    1. If model has 'clip' in families (vision encoder present)
    2. If model has projector_info (multimodal projector)
    3. Known vision family names
    4. 'vision' keyword in model name
    """
    try:
        # First try to get detailed model info from /api/show
        show_response = requests.post(
            f"{base_url}/api/show",
            json={"name": model_name},
            timeout=5
        )
        
        if show_response.status_code == 200:
            show_data = show_response.json()
            details = show_data.get('details', {})
            
            # Check 1: Does it have 'clip' in families? (vision encoder)
            families = details.get('families', [])
            if 'clip' in families:
                print(f"Model {model_name} is vision-capable (has CLIP vision encoder)")
                return True
            
            # Check 2: Does it have projector_info? (multimodal projector)
            if 'projector_info' in show_data:
                print(f"Model {model_name} is vision-capable (has multimodal projector)")
                return True
        
        # Fallback: Check via /api/tags (less reliable but works)
        tags_response = requests.get(f"{base_url}/api/tags", timeout=5)
        if tags_response.status_code != 200:
            print(f"Warning: Could not verify if {model_name} is a vision model")
            return True  # Assume yes if can't check
        
        data = tags_response.json()
        models = data.get('models', [])
        
        for m in models:
            if m.get('name') == model_name:
                details = m.get('details', {})
                family = details.get('family', '').lower()
                families = details.get('families', [])
                
                # Check for 'clip' in families
                if 'clip' in families:
                    print(f"Model {model_name} is vision-capable (has CLIP in families)")
                    return True
                
                # Check for known vision families
                vision_families = ['mllama', 'llava', 'bakllava', 'gemma3', 'gemma2']
                if family in vision_families or any(f in vision_families for f in families):
                    return True
                
                # Check for vision keywords in model name
                model_lower = model_name.lower()
                if any(keyword in model_lower for keyword in ['vision', 'llava', 'bakllava']):
                    return True
                
                # If we got here, it's likely text-only
                print(f"Model {model_name} appears to be text-only (family: {family}, families: {families})")
                return False
        
        # Model not found in list, assume it might support vision
        print(f"Warning: Model {model_name} not found in Ollama list")
        return True
        
    except Exception as e:
        print(f"Error checking if model is vision-capable: {e}")
        return True  # Assume yes on error to avoid blocking
