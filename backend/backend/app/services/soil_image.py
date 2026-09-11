from io import BytesIO
from PIL import Image


def analyze(image_bytes):
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image.thumbnail((300, 300))
    pixels = list(image.getdata())
    n = max(1, len(pixels))
    rgb = [sum(p[i] for p in pixels) / n for i in range(3)]
    brightness = sum(rgb) / 3

    if brightness < 80:
        visual_class = "dark_visual_soil"
    elif brightness < 150:
        visual_class = "medium_visual_soil"
    else:
        visual_class = "light_visual_soil"

    return {
        "visual_class": visual_class,
        "average_rgb": {"r": round(rgb[0], 2), "g": round(rgb[1], 2), "b": round(rgb[2], 2)},
        "brightness": round(brightness, 2),
        "warning": "Colour analysis is only a visual indicator, not a laboratory soil-quality test.",
    }
