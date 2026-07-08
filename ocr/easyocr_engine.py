import easyocr
import numpy as np
import logging
import concurrent.futures
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

# Global cache for the EasyOCR Reader instance to avoid reloading weights on every call
_READER_CACHE = {}


def get_reader(languages: tuple = ('en',), gpu: bool = True) -> easyocr.Reader:
    """
    Retrieves a cached EasyOCR Reader or creates a new one if not cached.

    Args:
        languages: Tuple of language codes to load (e.g., ('en',)).
        gpu: Boolean indicating whether to use GPU acceleration.

    Returns:
        easyocr.Reader: Instantiated EasyOCR Reader.
    """
    key = (languages, gpu)
    if key not in _READER_CACHE:
        try:
            logger.info(f"Initializing EasyOCR Reader for {languages} (GPU={gpu}).")
            _READER_CACHE[key] = easyocr.Reader(list(languages), gpu=gpu)
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR Reader: {e}")
            raise EngineUnavailableError(f"EasyOCR Reader initialization failed: {e}") from e
    return _READER_CACHE[key]


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


def extract_text_from_processed_image(
    binary_image: np.ndarray,
    gpu: Union[bool, None] = None,
    languages: Union[List[str], None] = None,
    timeout_seconds: int = 30
) -> Dict[str, Any]:
    """
    Initializes EasyOCR and reads structural text from the preprocessed binary image matrix.
    Returns structured output.

    Args:
        binary_image: Preprocessed numpy image matrix.
        gpu: Explicitly enable/disable GPU. If None, GPU is automatically detected.
        languages: List of language codes. Default is ['en'].
        timeout_seconds: Maximum time allowed for OCR processing in seconds.

    Returns:
        Dict[str, Any]: Structured OCR result containing:
            - "engine": "easyocr"
            - "text": Full joined text string.
            - "confidence": Float average confidence of all lines.
            - "lines": List of dicts representing each line with:
                - "text": Line text content.
                - "confidence": Line confidence float.

    Raises:
        EmptyImageError: If the input image is empty.
        InvalidImageError: If the image format is incorrect.
        EngineUnavailableError: If EasyOCR cannot be loaded.
        OCRTimeoutError: If the OCR task takes longer than timeout_seconds.
        OCRProcessingError: If processing fails.
    """
    logger.info("Initializing EasyOCR extraction.")

    # 1. Validate image
    if binary_image is None:
        raise EmptyImageError("Input image is None.")
    if not isinstance(binary_image, np.ndarray):
        raise InvalidImageError("Input image must be a numpy.ndarray.")
    if binary_image.size == 0 or len(binary_image.shape) < 2 or binary_image.shape[0] == 0 or binary_image.shape[1] == 0:
        raise EmptyImageError("Input image is empty or has invalid dimensions.")

    # 2. Configure GPU automatically if not specified
    if gpu is None:
        try:
            import torch
            gpu = torch.cuda.is_available()
            logger.info(f"Auto-detected GPU availability: {gpu}")
        except ImportError:
            gpu = False
            logger.info("PyTorch not installed. Falling back to CPU for EasyOCR.")

    # 3. Retrieve reader instance
    lang_list = languages or ['en']
    reader = get_reader(tuple(lang_list), gpu=gpu)

    # 4. Perform OCR text recognition with timeout
    try:
        # Run reader.readtext inside a thread pool to enforce timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(reader.readtext, binary_image)
            raw_results = future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as e:
        logger.error(f"EasyOCR processing timed out after {timeout_seconds} seconds.")
        raise OCRTimeoutError(f"EasyOCR processing timed out after {timeout_seconds} seconds.") from e
    except Exception as e:
        logger.error(f"EasyOCR failed to process image: {e}")
        raise OCRProcessingError(f"EasyOCR engine encountered an error: {e}") from e

    # 5. Process raw outputs into structured format
    lines = []
    for res in raw_results:
        # EasyOCR returns: (bbox, text, confidence)
        if len(res) >= 3:
            text_val, conf_val = res[1], res[2]
        elif len(res) == 2:
            text_val, conf_val = res[0], res[1]
        else:
            continue

        cleaned = clean_text(text_val)
        if is_valid_line(cleaned):
            lines.append({
                "text": cleaned,
                "confidence": round(float(conf_val), 4)
            })

    # Join text and calculate average confidence
    full_text = "\n".join([line["text"] for line in lines])
    avg_confidence = round(sum(line["confidence"] for line in lines) / len(lines), 4) if lines else 0.0

    result = {
        "engine": "easyocr",
        "text": full_text,
        "confidence": avg_confidence,
        "lines": lines
    }

    logger.info(f"EasyOCR extraction completed. Found {len(lines)} valid lines.")
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
            
            logger.info("Extracting text via EasyOCR...")
            res = extract_text_from_processed_image(processed)
            print("\n--- OCR structured output ---")
            print(f"Engine: {res['engine']}")
            print(f"Confidence: {res['confidence']}")
            print("Lines found:")
            for i, line in enumerate(res['lines']):
                print(f"  Line {i+1} ({line['confidence']:.4f}): {line['text']}")
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
    else:
        print("Usage: python easyocr_engine.py <image_path>")
