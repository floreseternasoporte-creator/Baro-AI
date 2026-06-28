# -*- coding: utf-8 -*-
"""
voice.py — Síntesis de voz de Baro usando Edge-TTS (Microsoft, gratuito).

Edge-TTS usa el mismo servicio de voces neuronales que el lector en voz alta
de Microsoft Edge. Son voces de altísima calidad y no requieren API key ni
suscripción: son de uso gratuito mientras se respete el servicio.

Voz por defecto: es-US-PalomaNeural (voz femenina neutral en español,
sonido muy natural). También dejamos otras voces femeninas en español
disponibles por si se quiere cambiar la personalidad de Baro.
"""

from __future__ import annotations

import io
import edge_tts

# Voces femeninas neuronales en español disponibles gratis en Edge-TTS.
# Todas suenan muy naturales; "es-US-PalomaNeural" es neutral / latam-friendly.
VOICES = {
    "neutral": "es-US-PalomaNeural",      # Español neutro (EE.UU. latino)
    "mexico": "es-MX-DaliaNeural",        # Español de México
    "colombia": "es-CO-SalomeNeural",     # Español de Colombia
    "espana": "es-ES-ElviraNeural",       # Español de España
    "argentina": "es-AR-ElenaNeural",     # Español de Argentina
    "chile": "es-CL-CatalinaNeural",      # Español de Chile
}

DEFAULT_VOICE = VOICES["neutral"]


async def synthesize(text: str, voice: str | None = None, rate: str = "+4%", pitch: str = "+0Hz") -> bytes:
    """
    Convierte `text` en audio MP3 (bytes) usando la voz neuronal indicada.
    `rate` y `pitch` permiten afinar la naturalidad (ej: "+4%" un poco más
    ágil que el default, para que suene más a asistente vivo).
    """
    if not text or not text.strip():
        raise ValueError("No hay texto para sintetizar.")

    selected_voice = voice or DEFAULT_VOICE

    communicate = edge_tts.Communicate(
        text=text,
        voice=selected_voice,
        rate=rate,
        pitch=pitch,
    )

    buffer = io.BytesIO()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buffer.write(chunk["data"])

    return buffer.getvalue()
