import pytesseract
import numpy as np
import logging
import re
from typing import Union, List, Dict, Any

# Import custom exceptions
try:
    from .image_preprocessing import (
        OCRError, EmptyImageError, InvalidImageError,
        EngineUnavailableError, OCRTimeoutError, OCRProcessingError
    )
except (ImportError, ValueError):
    from image_preprocessing import (
        OCRError, EmptyImageError, InvalidImageError,
        EngineUnavailableError, OCRTimeoutError, OCRProcessingError
    )

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Normalizes whitespace and strips leading/trailing space.

    Args:
        text: Raw input string.

    Returns:
        str: Cleaned string.
    """
    if not text:
        return ""
    # Normalize multiple spaces/tabs into a single space
    cleaned = re.sub(r'[ \t]+', ' ', text)
    return cleaned.strip()


def is_valid_line(text: str) -> bool:
    """
    Checks if the line of text contains valid alphanumeric content or important medical symbols.
    Filters out OCR noise/speckles.

    Args:
        text: The cleaned line string.

    Returns:
        bool: True if the line is valid, False if it is noise.
    """
    if not text:
        return False
    trimmed = text.strip()
    # Keep lines that contain at least one alphanumeric character
    if re.search(r'[a-zA-Z0-9]', trimmed):
        return True
    # Keep specific allowed medical symbols or short words
    if trimmed in ["+", "++", "+++", "-", "negative", "positive"]:
        return True
    return False


def extract_text_via_tesseract(
    binary_image: np.ndarray,
    psm: int = 6,
    oem: int = 3,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Alternative OCR extraction module using Google's Tesseract framework.
    Processes the preprocessed binary image matrix and returns structured text lines.

    Args:
        binary_image: Preprocessed numpy image matrix.
        psm: Page Segmentation Mode (configurable, default is 6).
        oem: OCR Engine Mode (configurable, default is 3).
        timeout_seconds: Maximum time allowed for OCR processing in seconds.

    Returns:
        Dict[str, Any]: Structured OCR result containing:
            - "engine": "tesseract"
            - "text": Full joined text string.
            - "confidence": Float average confidence of all lines.
            - "lines": List of dicts representing each line with:
                - "text": Line text content.
                - "confidence": Line confidence float (normalized to 0.0 - 1.0).

    Raises:
        EmptyImageError: If the input image is empty.
        InvalidImageError: If the image format is incorrect.
        EngineUnavailableError: If Tesseract cannot be loaded/is missing.
        OCRTimeoutError: If the OCR task times out.
        OCRProcessingError: If processing fails.
    """
    logger.info("Initializing Tesseract OCR extraction.")

    # 1. Validate image
    if binary_image is None:
        raise EmptyImageError("Input image is None.")
    if not isinstance(binary_image, np.ndarray):
        raise InvalidImageError("Input image must be a numpy.ndarray.")
    if binary_image.size == 0 or len(binary_image.shape) < 2 or binary_image.shape[0] == 0 or binary_image.shape[1] == 0:
        raise EmptyImageError("Input image is empty or has invalid dimensions.")

    # 2. Verify Tesseract installation
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        logger.error(f"Tesseract is not installed or not in PATH: {e}")
        raise EngineUnavailableError(
            "Tesseract OCR engine is not installed or not added to your system PATH."
        ) from e

    custom_config = f'--oem {oem} --psm {psm}'

    # 3. Perform OCR text recognition using Tesseract (image_to_data for confidence mapping)
    lines = []
    try:
        data = pytesseract.image_to_data(
            binary_image,
            config=custom_config,
            output_type=pytesseract.Output.DICT,
            timeout=timeout_seconds
        )
        
        # Group words by line hierarchy (block_num, par_num, line_num)
        lines_dict = {}
        n_boxes = len(data['text'])
        for i in range(n_boxes):
            level = data['level'][i]
            conf = float(data['conf'][i])
            text_val = data['text'][i]
            
            # Word level (5)
            if level == 5:
                text_str = text_val.strip()
                if text_str:
                    key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
                    if key not in lines_dict:
                        lines_dict[key] = {'words': [], 'confs': []}
                    lines_dict[key]['words'].append(text_str)
                    
                    # Store valid confidences (Tesseract returns -1 for spacing/non-words)
                    if conf >= 0:
                        lines_dict[key]['confs'].append(conf / 100.0)

        # Assemble and clean lines
        for key in sorted(lines_dict.keys()):
            words = lines_dict[key]['words']
            confs = lines_dict[key]['confs']
            
            line_text = " ".join(words)
            cleaned = clean_text(line_text)
            
            if is_valid_line(cleaned):
                avg_conf = sum(confs) / len(confs) if confs else 0.0
                lines.append({
                    "text": cleaned,
                    "confidence": round(avg_conf, 4)
                })

    except (RuntimeError, TimeoutError) as e:
        if "timeout" in str(e).lower():
            logger.error(f"Tesseract processing timed out: {e}")
            raise OCRTimeoutError(f"Tesseract OCR timed out after {timeout_seconds} seconds.") from e
        raise OCRProcessingError(f"Tesseract engine execution failed: {e}") from e
    except Exception as e:
        logger.error(f"Tesseract engine failed to process image: {e}")
        raise OCRProcessingError(f"Tesseract execution error: {e}") from e

    # 4. Fallback to image_to_string if image_to_data fails to extract line coordinates but text is present
    if not lines:
        try:
            logger.info("Tesseract image_to_data returned no text. Trying fallback image_to_string...")
            raw_text = pytesseract.image_to_string(binary_image, config=custom_config, timeout=timeout_seconds)
            fallback_lines = [clean_text(line) for line in raw_text.split('\n')]
            
            for f_line in fallback_lines:
                if is_valid_line(f_line):
                    # We use a neutral confidence value of 0.8 for text found via fallback
                    lines.append({
                        "text": f_line,
                        "confidence": 0.8
                    })
        except Exception as fallback_err:
            logger.warning(f"Tesseract fallback image_to_string failed: {fallback_err}")

    # 5. Compile final results
    full_text = "\n".join([line["text"] for line in lines])
    avg_confidence = round(sum(line["confidence"] for line in lines) / len(lines), 4) if lines else 0.0

    result = {
        "engine": "tesseract",
        "text": full_text,
        "confidence": avg_confidence,
        "lines": lines
    }

    logger.info(f"Tesseract extraction completed. Found {len(lines)} valid lines.")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        try:
            # Import enhance function to prepare the test image
            try:
                from .image_preprocessing import enhance_medical_image
            except (ImportError, ValueError):
                from image_preprocessing import enhance_medical_image
                
            logger.info(f"Preprocessing test image: {test_path}")
            processed = enhance_medical_image(test_path)
            
            logger.info("Extracting text via Tesseract...")
            res = extract_text_via_tesseract(processed)
            print("\n--- OCR structured output ---")
            print(f"Engine: {res['engine']}")
            print(f"Confidence: {res['confidence']}")
            print("Lines found:")
            for i, line in enumerate(res['lines']):
                print(f"  Line {i+1} ({line['confidence']:.4f}): {line['text']}")
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
    else:
        print("Usage: python tesseract_engine.py <image_path>")
