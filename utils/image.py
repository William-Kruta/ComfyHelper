import cv2
import argparse, os
from PIL import Image
from pathlib import Path
import numpy as np


def apply_mask_to_image(image_path, mask):
    """
    Apply mask to original image - only show masked regions
    """
    # Read original image
    img = cv2.imread(image_path)

    # Ensure mask is the same size as image
    if mask.shape[:2] != img.shape[:2]:
        mask = cv2.resize(mask, (img.shape[1], img.shape[0]))

    # Convert mask to 3-channel if needed
    if len(mask.shape) == 2:
        mask_3channel = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    else:
        mask_3channel = mask

    # Apply mask - keep only masked regions
    masked_img = cv2.bitwise_and(img, img, mask=mask)

    return masked_img


def opencv_segmentation_mask(image_path):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not load image")

    # Convert to LAB color space for better segmentation
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # Split channels
    l, a, b = cv2.split(lab)

    # Apply thresholding
    _, mask = cv2.threshold(b, 128, 255, cv2.THRESH_BINARY)

    # Morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    return mask


def background_subtraction_mask(image_path):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not load image")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Use adaptive thresholding
    mask = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Invert mask (assuming clothing is lighter than background)
    mask = 255 - mask

    # Morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


def simple_clothing_mask(image_path):
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Could not load image")

    # Convert BGR to HSV for better color segmentation
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Define color ranges for common clothing colors
    # These are just examples - adjust based on your images
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])

    lower_green = np.array([35, 50, 50])
    upper_green = np.array([85, 255, 255])

    lower_brown = np.array([10, 50, 50])
    upper_brown = np.array([25, 255, 255])

    # Create masks for different colors
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

    # Combine masks
    combined_mask = mask_blue | mask_green | mask_brown

    # Apply morphological operations to clean up
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
    combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)

    return combined_mask


def calc_new_size(
    w,
    h,
    scale: float,
    width_preference=None,
    height_preference=None,
    no_aspect: bool = True,
    allow_upscale: bool = True,
):
    if scale:
        return int(w * scale), int(h * scale)

    if width_preference and height_preference and no_aspect:
        return width_preference, height_preference

    if width_preference and not height_preference:
        return width_preference, int(h * (width_preference / w))

    if height_preference and not width_preference:
        return int(w * (height_preference / h)), height_preference

    if width_preference and height_preference:
        # fit inside box, keep aspect
        r = min(width_preference / w, height_preference / h)
        if r > 1 and not allow_upscale:
            return w, h
        return int(w * r), int(h * r)

    # default: no change
    return w, h


def filter_images_by_size(paths: list, max_width: int, max_height: int):
    """
    Return paths whose image size is <= max_width and <= max_height.
    Nonexistent or unreadable images are skipped.
    """
    ok = []
    for p in map(Path, paths):
        try:
            with Image.open(p) as im:
                w, h = im.size
            if w <= max_width and h <= max_height:
                ok.append(str(p))
        except Exception:
            # skip files that can't be opened as images
            continue
    return ok


def scale_image(
    input_path: str,
    output_path: str,
    scale: float,
    width_preference=None,
    height_preference=None,
    no_aspect: bool = False,
    allow_upscale: bool = True,
):
    with Image.open(input_path) as im:
        w, h = im.size
        nw, nh = calc_new_size(
            w,
            h,
            scale,
            width_preference=width_preference,
            height_preference=height_preference,
            no_aspect=no_aspect,
            allow_upscale=allow_upscale,
        )

        if (nw, nh) == (w, h):
            print(f"No resize performed. Original: {w}x{h}")
            # im.save(output_path)
            return

        resized = im.resize((nw, nh), resample=Image.LANCZOS)
        # Preserve format by extension unless format known
        ext = os.path.splitext(output_path)[1].lower()
        save_kwargs = {}
        if ext in {".jpg", ".jpeg", ".png"}:
            save_kwargs.update({"quality": 95, "optimize": True})
        resized.save(output_path, **save_kwargs)
        print(f"{w}x{h} -> {nw}x{nh} saved to {output_path}")


def cli():
    ap = argparse.ArgumentParser(description="Upscale or downscale an image.")
    ap.add_argument("input", help="Input image path")
    ap.add_argument("output", help="Output image path")
    ap.add_argument("--scale", type=float, help="Scale factor, e.g. 0.5 or 2.0")
    ap.add_argument("--width", type=int, help="Target width (px)")
    ap.add_argument("--height", type=int, help="Target height (px)")
    ap.add_argument(
        "--no-aspect",
        action="store_true",
        help="Do not preserve aspect if both width and height given",
    )
    ap.add_argument(
        "--allow-upscale",
        action="store_true",
        help="Allow enlarging when fitting into a box",
    )
    args = ap.parse_args()

    scale_image(
        args.input,
        args.output,
        width_preference=args.width,
        height_preference=args.height,
        no_aspect=args.no_aspect,
        allow_upscale=args.allow_upscale,
    )
