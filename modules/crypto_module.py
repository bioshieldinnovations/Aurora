"""
AURORA - Módulo Criptográfico
Cifrado simétrico por flujo usando SHA-256 con Key Stretching.
Sin dependencias externas.
"""
import os
import hashlib
import hmac


def _derivar_clave(password: str, salt: bytes, iteraciones: int = 100_000) -> bytes:
    """
    PBKDF2-HMAC-SHA256 para derivación de clave segura.
    Reemplaza el key stretching manual del original por un estándar robusto.
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iteraciones,
        dklen=32,
    )


def _generar_flujo(clave: bytes, longitud: int) -> bytes:
    """Genera un flujo pseudoaleatorio determinista mediante bloques SHA-256."""
    flujo = bytearray()
    contador = 0
    while len(flujo) < longitud:
        bloque = hashlib.sha256(clave + contador.to_bytes(4, "big")).digest()
        flujo.extend(bloque)
        contador += 1
    return bytes(flujo[:longitud])


def _xor(datos: bytes, flujo: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(datos, flujo))


def _hmac_sha256(clave: bytes, datos: bytes) -> bytes:
    return hmac.new(clave, datos, hashlib.sha256).digest()


# ─── MENSAJES ────────────────────────────────────────────────────────────────

def encriptar_mensaje(mensaje: str, password: str) -> str:
    """
    Encripta texto. Devuelve hex con estructura: SALT(16) + HMAC(32) + DATOS_CIFRADOS
    """
    salt = os.urandom(16)
    clave = _derivar_clave(password, salt)
    
    datos = mensaje.encode("utf-8")
    flujo = _generar_flujo(clave, len(datos))
    cifrado = _xor(datos, flujo)
    
    # HMAC para verificar integridad en desencriptado
    mac = _hmac_sha256(clave, cifrado)
    
    paquete = salt + mac + cifrado
    return paquete.hex()


def desencriptar_mensaje(token_hex: str, password: str) -> str:
    """Desencripta y verifica integridad del token."""
    try:
        datos_completos = bytes.fromhex(token_hex.strip())
    except ValueError:
        raise ValueError("El token no es hexadecimal válido.")

    if len(datos_completos) < 48:  # 16 salt + 32 hmac
        raise ValueError("Token corrupto o incompleto.")

    salt = datos_completos[:16]
    mac_recibido = datos_completos[16:48]
    cifrado = datos_completos[48:]

    clave = _derivar_clave(password, salt)
    
    # Verificar HMAC antes de desencriptar
    mac_esperado = _hmac_sha256(clave, cifrado)
    if not hmac.compare_digest(mac_recibido, mac_esperado):
        raise ValueError("Contraseña incorrecta o mensaje alterado.")

    flujo = _generar_flujo(clave, len(cifrado))
    original = _xor(cifrado, flujo)
    return original.decode("utf-8")


# ─── ARCHIVOS ────────────────────────────────────────────────────────────────

def encriptar_archivo(ruta: str, password: str) -> str:
    """Encripta cualquier archivo binario. Retorna la ruta del archivo cifrado."""
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    with open(ruta, "rb") as f:
        datos = f.read()

    salt = os.urandom(16)
    clave = _derivar_clave(password, salt)
    flujo = _generar_flujo(clave, len(datos))
    cifrado = _xor(datos, flujo)
    mac = _hmac_sha256(clave, cifrado)

    ruta_salida = ruta + ".aur"
    with open(ruta_salida, "wb") as f:
        f.write(salt + mac + cifrado)

    return ruta_salida


def desencriptar_archivo(ruta: str, password: str) -> str:
    """Desencripta un archivo .aur y retorna la ruta del archivo restaurado."""
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

    with open(ruta, "rb") as f:
        datos = f.read()

    if len(datos) < 48:
        raise ValueError("Archivo corrupto o demasiado pequeño.")

    salt = datos[:16]
    mac_recibido = datos[16:48]
    cifrado = datos[48:]

    clave = _derivar_clave(password, salt)
    mac_esperado = _hmac_sha256(clave, cifrado)

    if not hmac.compare_digest(mac_recibido, mac_esperado):
        raise ValueError("Contraseña incorrecta o archivo alterado.")

    flujo = _generar_flujo(clave, len(cifrado))
    original = _xor(cifrado, flujo)

    ruta_salida = ruta.removesuffix(".aur") if ruta.endswith(".aur") else ruta + "_dec"
    with open(ruta_salida, "wb") as f:
        f.write(original)

    return ruta_salida
