"""
Advanced Image Utilities and Preprocessing for Product Packet Analyser.
Optimized for handling blurry, low-light, and low-resolution packet labels.
"""

import os
from PIL import Image, ImageOps, ImageEnhance
from typing import Tuple, Dict, Any

def validate_image_file(uploaded_file) -> Tuple[bool, str]:
    """Validates that the uploaded file is a supported image format and within size limits."""
    if uploaded_file is None:
        return False, "No file uploaded."
    
    max_size_mb = 10
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        return False, f"File size exceeds {max_size_mb}MB limit."

    valid_exts = (".jpg", ".jpeg", ".png")
    if not uploaded_file.name.lower().endswith(valid_exts):
        return False, "Unsupported file format. Please upload JPG, JPEG, or PNG."

    return True, ""

def load_image(uploaded_file) -> Image.Image:
    """Loads a PIL image from an uploaded file object."""
    return Image.open(uploaded_file)

def get_image_metadata(img: Image.Image, filename: str, filesize_bytes: int) -> Dict[str, Any]:
    """Extracts basic image metadata for UI display."""
    width, height = img.size
    size_kb = round(filesize_bytes / 1024, 1)
    size_str = f"{size_kb} KB" if size_kb < 1024 else f"{round(size_kb / 1024, 2)} MB"
    
    return {
        "filename": filename,
        "resolution": f"{width} × {height} px",
        "filesize": size_str,
        "format": img.format or "JPEG/PNG"
    }

def preprocess_image_for_ocr(img: Image.Image) -> Image.Image:
    """
    Advanced Preprocessing Pipeline for Tesseract OCR:
    1. Converts image to grayscale.
    2. Enhances contrast and sharpness to fix blurriness.
    3. Auto-resizes low-resolution images for better optical character recognition.
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Auto-scale if resolution is too low
    width, height = img.size
    min_dimension = 1200
    if width < min_dimension or height < min_dimension:
        scale_factor = max(min_dimension / width, min_dimension / height)
        new_size = (int(width * scale_factor), int(height * scale_factor))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    # Convert to grayscale for cleaner text extraction
    gray_img = ImageOps.grayscale(img)

    # Increase contrast to make faded or blurry text pop out
    enhancer_contrast = ImageEnhance.Contrast(gray_img)
    contrast_img = enhancer_contrast.enhance(2.0)

    # Sharpen image to fix blur artifacts
    enhancer_sharpness = ImageEnhance.Sharpen(contrast_img)
    sharp_img = enhancer_sharpness.enhance(2.5)

    return sharp_img
