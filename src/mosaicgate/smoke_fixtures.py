"""Small synthetic transport fixtures, excluded from the evaluation corpus."""

from enum import StrEnum
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


class Modality(StrEnum):
    TEXT = "text"
    IMAGE = "image"


REPORT_TEXT = (
    "SYNTHETIC Q3 REVENUE REPORT\n"
    "July: $100,000\n"
    "August: $110,000\n"
    "September: $120,000\n"
    "Quarter total: $330,000\n"
    "Revenue increased each month; July to September growth: 20%.\n"
    "Synthetic canary: MOSAIC-DEMO-ONLY-7F3A\n"
)


def report_png() -> bytes:
    """Render a readable PNG without fonts, network access, or external assets."""
    image = Image.new("RGB", (1200, 420), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=27)
    draw.multiline_text((32, 32), REPORT_TEXT, font=font, fill="black", spacing=18)
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
