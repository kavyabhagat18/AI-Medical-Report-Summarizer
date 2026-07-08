import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Custom OCR Module Exceptions ---
class OCRError(Exception):
    """Base exception class for all OCR-related errors."""
    pass

class EmptyImageError(OCRError):
    """Raised when the input image is empty or has zero dimensions."""
    pass

class InvalidImageError(OCRError):
    """Raised when the image format is invalid or corrupted."""
    pass

class EngineUnavailableError(OCRError):
    """Raised when the OCR engine is not installed or unavailable."""
    pass

class OCRTimeoutError(OCRError):
    """Raised when the OCR engine times out during processing."""
    pass

class OCRProcessingError(OCRError):
    """Raised when the OCR processing fails internally."""
    pass


def load_image_safely(image_input: Union[str, Path, np.ndarray]) -> np.ndarray:
    """
    Safely loads an image from a file path, Path object, or validates a numpy array.

    Args:
        image_input: A file path (str/Path) or a numpy array representing the image.

    Returns:
        np.ndarray: The loaded BGR or grayscale image matrix.

    Raises:
        FileNotFoundError: If the specified file path does not exist.
        InvalidImageError: If the image file is corrupted or of an unsupported format.
        TypeError: If the input type is invalid.
    """
    if isinstance(image_input, (str, Path)):
        file_path = Path(image_input)
        if not file_path.exists():
            logger.error(f"Image file not found: {file_path}")
            raise FileNotFoundError(f"Could not load image. File does not exist: {file_path}")
        
        try:
            # Read image using OpenCV
            img = cv2.imread(str(file_path))
            if img is None:
                logger.error(f"Failed to decode image: {file_path}. Unsupported or corrupted format.")
                raise InvalidImageError(f"Failed to decode image at path: {file_path}")
            return img
        except InvalidImageError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading image from {file_path}: {e}")
            raise InvalidImageError(f"Error loading image from path: {file_path}") from e
            
    elif isinstance(image_input, np.ndarray):
        if image_input.size == 0:
            logger.error("Input numpy array is empty.")
            raise EmptyImageError("The provided image numpy array is empty.")
        return image_input.copy()
        
    else:
        logger.error(f"Invalid type for image_input: {type(image_input)}")
        raise TypeError("Image input must be a file path string, Path object, or a numpy ndarray.")


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """
    Converts a BGR or BGRA image to grayscale.

    Args:
        image: Input numpy array (BGR, BGRA, or Grayscale).

    Returns:
        np.ndarray: Grayscale image.
    """
    if len(image.shape) == 3:
        channels = image.shape[2]
        if channels == 4:
            logger.debug("Converting BGRA image to Grayscale.")
            return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        elif channels == 3:
            logger.debug("Converting BGR image to Grayscale.")
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def resize_low_resolution(image: np.ndarray, target_width: int = 1600) -> np.ndarray:
    """
    Resizes low-resolution images to a target width while maintaining aspect ratio.
    Also logs a warning if the image is extremely low resolution.

    Args:
        image: Grayscale numpy array.
        target_width: The minimum desired width of the image.

    Returns:
        np.ndarray: Resized image if width was below target, else original.
    """
    h, w = image.shape[:2]
    
    # Check for extremely low resolution
    if w < 300 or h < 300:
        logger.warning(f"Image resolution is extremely low ({w}x{h}). OCR accuracy may be significantly affected.")
        
    if w < target_width:
        scale_factor = target_width / w
        new_h = int(h * scale_factor)
        # Avoid zero dimensions
        new_h = max(1, new_h)
        logger.info(f"Upscaling low-resolution image from {w}x{h} to {target_width}x{new_h}")
        return cv2.resize(image, (target_width, new_h), interpolation=cv2.INTER_CUBIC)
        
    return image


def remove_noise(image: np.ndarray) -> np.ndarray:
    """
    Applies Bilateral Filtering to remove noise and paper grain while preserving sharp edges.

    Args:
        image: Grayscale numpy array.

    Returns:
        np.ndarray: Denoised grayscale image.
    """
    logger.debug("Applying bilateral filtering for noise reduction.")
    return cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)


def normalize_brightness(image: np.ndarray) -> np.ndarray:
    """
    Normalizes uneven lighting/brightness using morphological background estimation.

    Args:
        image: Grayscale numpy array.

    Returns:
        np.ndarray: Grayscale image with flat field lighting.
    """
    logger.debug("Normalizing brightness and removing uneven illumination.")
    # Estimate background illumination using dilation followed by median blur
    dilated = cv2.dilate(image, np.ones((7, 7), np.uint8))
    bg_est = cv2.medianBlur(dilated, 21)
    
    # Subtract estimated background illumination and normalize contrast
    diff = cv2.absdiff(image, bg_est)
    normalized = 255 - diff
    return normalized


def apply_adaptive_threshold(image: np.ndarray) -> np.ndarray:
    """
    Applies adaptive thresholding to convert a grayscale image to a binary image.

    Args:
        image: Grayscale numpy array.

    Returns:
        np.ndarray: High-contrast binary image.
    """
    logger.debug("Applying adaptive Gaussian thresholding.")
    return cv2.adaptiveThreshold(
        image,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=11,
        C=2
    )


def apply_morphological_cleanup(binary_image: np.ndarray) -> np.ndarray:
    """
    Uses morphological operations to clean up background noise/dots
    and improve character stroke continuity.

    Args:
        binary_image: Binary numpy array (black text on white background).

    Returns:
        np.ndarray: Cleaned binary image.
    """
    logger.debug("Applying morphological cleanup.")
    # Create a small 2x2 structural element
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    
    # Since background is white (255) and text is black (0),
    # MORPH_CLOSE closes small holes inside letters, and MORPH_OPEN removes small noise dots.
    # We apply closing then opening to preserve text legibility.
    cleaned = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
    return cleaned


def enhance_medical_image(image_path: Union[str, Path, np.ndarray]) -> np.ndarray:
    """
    Cleans up raw smartphone camera snaps or scanned copies of medical reports.
    Handles loading, upscaling, noise removal, brightness normalization,
    adaptive thresholding, and morphological cleanup.

    Args:
        image_path: A path to the image file, a Path object, or a numpy array.

    Returns:
        np.ndarray: Preprocessed high-contrast binary image ready for OCR.

    Raises:
        FileNotFoundError: If path input is missing.
        InvalidImageError: If the image cannot be decoded.
        EmptyImageError: If the image has zero dimensions.
    """
    logger.info("Starting medical image preprocessing pipeline.")
    
    # 1. Safely load the image
    img = load_image_safely(image_path)
    
    # 2. Convert to grayscale
    gray = convert_to_grayscale(img)
    
    # 3. Upscale if low resolution
    resized = resize_low_resolution(gray, target_width=1600)
    
    # 4. Remove image noise while keeping text edges sharp
    denoised = remove_noise(resized)
    
    # 5. Normalize brightness and remove uneven shadow/illumination
    normalized = normalize_brightness(denoised)
    
    # 6. Perform Adaptive Thresholding
    binary = apply_adaptive_threshold(normalized)
    
    # 7. Morphological operations to clean speckle noise and connect text
    cleaned_binary = apply_morphological_cleanup(binary)
    
    logger.info("Medical image preprocessing pipeline completed successfully.")
    return cleaned_binary


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        try:
            result = enhance_medical_image(test_path)
            cv2.imwrite("preprocessed_test.png", result)
            print(f"Success! Preprocessed image saved to preprocessed_test.png")
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
    else:
        print("Usage: python image_preprocessing.py <image_path>")
