"""
AURORA - Módulo QR
Genera códigos QR a partir de texto, URLs o contenido de archivos.
"""
import io
import base64
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer


def generar_qr_base64(datos: str, color_fill: str = "#00FFB2", color_back: str = "#0A0E1A") -> dict:
    """
    Genera un QR y lo devuelve como imagen base64 para renderizar en el frontend.
    
    Returns:
        dict con 'imagen_b64', 'bytes_datos', 'caracteres'
    """
    if not datos or not datos.strip():
        raise ValueError("No se proporcionaron datos para generar el QR.")

    datos = datos.strip()
    
    # Seleccionar versión según tamaño de datos
    if len(datos) <= 50:
        version = 1
        correction = qrcode.constants.ERROR_CORRECT_H
    elif len(datos) <= 200:
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
    qr.add_data(datos)
    qr.make(fit=True)

    imagen = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        fill_color=color_fill,
        back_color=color_back,
    )

    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    imagen_b64 = base64.b64encode(buffer.read()).decode("utf-8")

    return {
        "imagen_b64": imagen_b64,
        "caracteres": len(datos),
        "bytes_datos": len(datos.encode("utf-8")),
        "version_qr": qr.version,
    }


def generar_qr_desde_archivo(ruta: str) -> dict:
    """Lee un archivo de texto y genera QR de su contenido."""
    import os
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()

    if not contenido.strip():
        raise ValueError("El archivo está vacío.")

    resultado = generar_qr_base64(contenido)
    resultado["fuente"] = os.path.basename(ruta)
    return resultado
