"""
AURORA - Cryptographic Module
Symmetric stream cipher using SHA-256 with Key Stretching.
No external dependencies.
"""
import os
import hashlib
import hmac


def _derivar_clave(password: str, salt: bytes, iteraciones: int = 100_000) -> bytes:
    """
    PBKDF2-HMAC-SHA256 for secure key derivation.
    Replaces the manual key stretching of the original with a robust standard.
    """
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iteraciones,
        dklen=32,
    )


def _generar_flujo(clave: bytes, longitud: int) -> bytes:
    """Generates a deterministic pseudorandom stream using SHA-256 blocks."""
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


# ─── MESSAGES ────────────────────────────────────────────────────────────────

def encriptar_mensaje(mensaje: str, password: str) -> str:
    """
    Encrypts text. Returns hex with structure: SALT(16) + HMAC(32) + ENCRYPTED_DATA
    """
    salt = os.urandom(16)
    clave = _derivar_clave(password, salt)
    
    datos = mensaje.encode("utf-8")
    flujo = _generar_flujo(clave, len(datos))
    cifrado = _xor(datos, flujo)
    
    # HMAC to verify integrity during decryption
    mac = _hmac_sha256(clave, cifrado)
    
    paquete = salt + mac + cifrado
    return paquete.hex()


def desencriptar_mensaje(token_hex: str, password: str) -> str:
    """Decrypts and verifies token integrity."""
    try:
        datos_completos = bytes.fromhex(token_hex.strip())
    except ValueError:
        raise ValueError("The token is not a valid hexadecimal.")

    if len(datos_completos) < 48:  # 16 salt + 32 hmac
        raise ValueError("Corrupted or incomplete token.")

    salt = datos_completos[:16]
    mac_recibido = datos_completos[16:48]
    cifrado = datos_completos[48:]

    clave = _derivar_clave(password, salt)
    
    # Verify HMAC before decrypting
    mac_esperado = _hmac_sha256(clave, cifrado)
    if not hmac.compare_digest(mac_recibido, mac_esperado):
        raise ValueError("Incorrect password or altered message.")

    flujo = _generar_flujo(clave, len(cifrado))
    original = _xor(cifrado, flujo)
    return original.decode("utf-8")


# ─── FILES ───────────────────────────────────────────────────────────────────

def encriptar_archivo(ruta: str, password: str) -> str:
    """Encrypts any binary file. Returns the path of the encrypted file."""
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"File not found: {ruta}")

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
    """Decrypts a .aur file and returns the path of the restored file."""
    if not os.path.exists(ruta):
        raise FileNotFoundError(f"File not found: {ruta}")

    with open(ruta, "rb") as f:
        datos = f.read()

    if len(datos) < 48:
        raise ValueError("Corrupted or too small file.")

    salt = datos[:16]
    mac_recibido = datos[16:48]
    cifrado = datos[48:]

    clave = _derivar_clave(password, salt)
    mac_esperado = _hmac_sha256(clave, cifrado)

    if not hmac.compare_digest(mac_recibido, mac_esperado):
        raise ValueError("Incorrect password or altered file.")

    flujo = _generar_flujo(clave, len(cifrado))
    original = _xor(cifrado, flujo)

    ruta_salida = ruta.removesuffix(".aur") if ruta.endswith(".aur") else ruta + "_dec"
    with open(ruta_salida, "wb") as f:
        f.write(original)

    return ruta_salida
