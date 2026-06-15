"""
AURORA - QR Module
Generates QR codes from text, URLs, or file content.
"""
import io
import base64
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer


def generate_qr_base64(data: str, fill_color: str = "#00FFB2", back_color: str = "#0A0E1A") -> dict:
    """
    Generates a QR and returns it as a base64 image to render on the frontend.
    
    Returns:
        dict with 'image_b64', 'data_bytes', 'characters', 'qr_version'
    """
    if not data or not data.strip():
        raise ValueError("No data was provided to generate the QR.")

    data = data.strip()
    
    # Select version based on data size
    if len(data) <= 50:
        version = 1
        correction = qrcode.constants.ERROR_CORRECT_H
    elif len(data) <= 200:
        version = None  # auto
        correction = qrcode.constants.ERROR_CORRECT_M
    else:
        version = None
        correction = qrcode.constants.ERROR_CORRECT_L

    qr = qrcode.QRCode(
        version=version,
        error_correction=correction,
        box_size=12,
        border=3,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        fill_color=fill_color,
        back_color=back_color,
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    image_b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "image_b64": image_b64,
        "characters": len(data),
        "data_bytes": len(data.encode("utf-8")),
        "qr_version": qr.version,
    }


def generate_qr_from_file(path: str) -> dict:
    """Reads a text file and generates a QR code from its content."""
    import os
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        raise ValueError("The file is empty.")

    result = generate_qr_base64(content)
    result["source"] = os.path.basename(path)
    return result
