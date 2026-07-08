import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Union

# Try to import exceptions and helper functions from image_preprocessing.
# This works whether run as a package or standalone scripts.
try:
    from .image_preprocessing import (
        load_image_safely, convert_to_grayscale, OCRError, 
        EmptyImageError, InvalidImageError
    )
except (ImportError, ValueError):
    from image_preprocessing import (
        load_image_safely, convert_to_grayscale, OCRError, 
        EmptyImageError, InvalidImageError
    )

logger = logging.getLogger(__name__)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detects if a document is photographed at a tilted angle and rotates it straight.

    Args:
        image: Input grayscale or BGR numpy array.

    Returns:
        np.ndarray: Rotation-corrected image.
    """
    logger.info("Running deskew correction.")
    gray = convert_to_grayscale(image)

    # Invert the binary image (text becomes white, background black) to detect text contours
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Grab coordinate locations of all non-zero pixels (the text)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        logger.warning("No text pixels detected for deskewing. Returning original image.")
        return image

    # Compute the minimum bounding box around all text pixels
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    # Handle angle representation differences across OpenCV versions
    # In older OpenCV versions, angle was in [-90, 0)
    # In newer versions (4.5+), it is in (0, 90]
    if angle < -45:
        angle = -(90 + angle)
    elif angle > 45:
        angle = 90 - angle

    # Safety constraint: skip rotation if skew angle is unrealistically high (avoids flipping portrait to landscape)
    if abs(angle) > 25.0:
        logger.warning(f"Detected rotation angle {angle:.2f}° is too large. Skipping deskew to avoid distortion.")
        return image

    logger.info(f"Deskewing image by {angle:.2f} degrees.")
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    # Rotate the image
    rotated = cv2.warpAffine(
        image,
        rotation_matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255  # Fill background borders with crisp white
    )
    return rotated


def enhance_text_contrast(image: np.ndarray) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE).
    Equalizes contrast locally to neutralize harsh lighting and shadow effects.

    Args:
        image: Grayscale numpy array.

    Returns:
        np.ndarray: Contrast-enhanced grayscale image.
    """
    logger.info("Applying CLAHE contrast enhancement.")
    # Ensure input is grayscale
    gray = convert_to_grayscale(image)

    # Create a CLAHE object (clipLimit handles contrast threshold, tileGridSize sets block window)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_contrast = clahe.apply(gray)

    return enhanced_contrast


def thicken_faded_text(binary_image: np.ndarray) -> np.ndarray:
    """
    Uses morphological operations (erosion) to close gaps in thin or faded print.
    Thickens dark text strokes slightly to improve recognition by the OCR engine.

    Args:
        binary_image: Binary grayscale image (black text on white background).

    Returns:
        np.ndarray: Binary image with thickened character strokes.
    """
    logger.info("Thickening faded text using morphological erosion.")
    # Create a tiny 2x2 structural pixel kernel
    kernel = np.ones((2, 2), np.uint8)

    # Since background is white (255) and text is black (0),
    # eroding the binary image will slightly expand the black regions.
    thickened = cv2.erode(binary_image, kernel, iterations=1)
    return thickened


def remove_shadows(image: np.ndarray) -> np.ndarray:
    """
    Eliminates shadows and uneven background coloring using morphological background estimation.

    Args:
        image: Grayscale or BGR image.

    Returns:
        np.ndarray: Shadow-free image (maintaining color dimension if input was BGR).
    """
    logger.info("Running shadow removal.")
    is_color = len(image.shape) == 3
    if is_color:
        # Convert to YCrCb space, process the Y channel, and convert back
        y_cr_cb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        channels = list(cv2.split(y_cr_cb))
        
        dilated = cv2.dilate(channels[0], np.ones((7, 7), np.uint8))
        bg_est = cv2.medianBlur(dilated, 21)
        diff = cv2.absdiff(channels[0], bg_est)
        channels[0] = 255 - diff
        
        y_cr_cb = cv2.merge(channels)
        return cv2.cvtColor(y_cr_cb, cv2.COLOR_YCrCb2BGR)
    else:
        dilated = cv2.dilate(image, np.ones((7, 7), np.uint8))
        bg_est = cv2.medianBlur(dilated, 21)
        diff = cv2.absdiff(image, bg_est)
        return 255 - diff


def correct_perspective(image: np.ndarray) -> np.ndarray:
    """
    Detects the document contours and corrects perspective distortion (trapezoidal distortion).
    If no 4-corner document boundary of sufficient size is found, returns original image.

    Args:
        image: Grayscale or BGR image.

    Returns:
        np.ndarray: Perspective-corrected warped image.
    """
    logger.info("Running perspective correction.")
    gray = convert_to_grayscale(image)
    
    # Calculate image area to avoid small false-positive contour matches
    h_img, w_img = gray.shape[:2]
    img_area = h_img * w_img
    
    # Edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 200)
    
    # Find contours and sort by size
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
    
    doc_contour = None
    for c in contours:
        area = cv2.contourArea(c)
        # Skip contours that do not cover at least 15% of the total image area
        if area < 0.15 * img_area:
            continue
            
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        
        # If the contour has 4 points, assume it is the document paper
        if len(approx) == 4:
            doc_contour = approx
            break
            
    if doc_contour is None:
        logger.info("No document-like 4-corner contour detected. Skipping perspective correction.")
        return image
        
    # Process contour points
    pts = doc_contour.reshape(4, 2)
    rect = np.zeros((4, 2), dtype="float32")
    
    # Order points: [top-left, top-right, bottom-right, bottom-left]
    # Top-left has the minimum sum, bottom-right has the maximum sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Top-right has the minimum difference, bottom-left has the maximum difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    (tl, tr, br, bl) = rect
    
    # Calculate width of new warped image
    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_width = max(int(width_a), int(width_b))
    
    # Calculate height of new warped image
    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_height = max(int(height_a), int(height_b))
    
    # Construct destination matrix
    dst = np.array([
        [0, 0],
        [max_width - 1, 0],
        [max_width - 1, max_height - 1],
        [0, max_height - 1]
    ], dtype="float32")
    
    # Warp perspective
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_width, max_height))
    
    logger.info(f"Warped perspective successfully. Output size: {max_width}x{max_height}")
    return warped


def full_enhancement_pipeline(image_input: Union[str, Path, np.ndarray]) -> np.ndarray:
    """
    Complete master utility tying all advanced enhancement layers together.

    Args:
        image_input: Image file path, Path object, or numpy array.

    Returns:
        np.ndarray: Enhancement-corrected grayscale document image.
    """
    logger.info("Initializing full image enhancement pipeline.")
    
    # 1. Load the image safely
    img = load_image_safely(image_input)
    
    # 2. Remove shadows first (vital for thresholding/deskewing accuracy)
    no_shadows = remove_shadows(img)
    
    # 3. Apply perspective correction (adjust trapezoidal shape)
    perspective_corrected = correct_perspective(no_shadows)
    
    # 4. Convert/ensure grayscale
    gray = convert_to_grayscale(perspective_corrected)
    
    # 5. Local contrast enhancement via CLAHE
    contrast_balanced = enhance_text_contrast(gray)
    
    # 6. Deskew correction (fix rotational misalignment)
    straight_document = deskew_image(contrast_balanced)
    
    logger.info("Image enhancement pipeline finished.")
    return straight_document


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        try:
            result = full_enhancement_pipeline(test_path)
            cv2.imwrite("enhanced_test.png", result)
            print("Success! Enhanced image saved to enhanced_test.png")
        except Exception as err:
            print(f"Error: {err}", file=sys.stderr)
    else:
        print("Usage: python image_enhancement.py <image_path>")
