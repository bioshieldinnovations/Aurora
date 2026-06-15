# AURORA SUITE · v2.0

Suite de herramientas con interfaz web de aurora boreal.  
Generador de QR · Cifrado Criptográfico · Descargador Universal.

---

## Instalación

```bash
# 1. Clonar / descomprimir el proyecto
cd aurora/

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
python app.py
```

El navegador se abre automáticamente en `http://localhost:5000`.

---

## Herramientas

### ⬡ Generador QR
- QR de URLs, texto plano o cualquier cadena
- Colores personalizables (fill + fondo)
- Módulos redondeados con corrección de errores adaptativa
- Descarga directa en PNG

### ◈ Cifrador de Mensajes
- Cifrado simétrico por flujo con PBKDF2-HMAC-SHA256
- Verificación de integridad con HMAC antes de desencriptar
- 100.000 iteraciones de key-stretching
- Salt aleatorio de 16 bytes por cada operación
- Salida en hexadecimal limpio

### ↓ Descargador Universal
- Compatible con YouTube, Twitter/X, Reddit, Vimeo, TikTok y 1000+ sitios
- Vista previa con miniatura, título, canal y duración antes de descargar
- Modo Video (MP4 máxima calidad) o Audio (MP3 192kbps)
- Barra de progreso en tiempo real

---

## Estructura

```
aurora/
├── app.py                   # Servidor Flask principal
├── requirements.txt
├── modules/
│   ├── qr_module.py         # Generación de QR
│   ├── crypto_module.py     # Cifrado/descifrado
│   └── downloader_module.py # Descarga de video/audio
└── templates/
    └── index.html           # Interfaz web
```

---

## Seguridad criptográfica

El módulo de cifrado usa un esquema **Encrypt-then-MAC**:

1. Se deriva una clave con **PBKDF2-HMAC-SHA256** (100k iteraciones + salt aleatorio)
2. Se cifra con **XOR de flujo** generado por SHA-256 en modo contador
3. Se añade un **HMAC-SHA256** del texto cifrado para verificar integridad
4. El paquete final: `SALT(16B) + HMAC(32B) + DATOS_CIFRADOS`

Esto garantiza que una contraseña incorrecta sea detectada **antes** de intentar descifrar.

---

## Notas

- Las descargas se guardan en `~/Aurora_Downloads/`
- Los archivos cifrados usan la extensión `.aur`
- El servidor escucha en `0.0.0.0:5000` (accesible en red local)

---

*AURORA SUITE — Construido con Python + Flask*
