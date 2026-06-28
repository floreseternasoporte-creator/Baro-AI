# -*- coding: utf-8 -*-
"""
main.py — Servidor de Baro.

FastAPI + WebSockets para hablar con el frontend en tiempo real.

Flujo:
1. El navegador captura voz con Web Speech API (gratis, nativo del navegador)
   y la transcribe a texto.
2. El texto se envía por WebSocket a este servidor.
3. `brain.py` detecta la intención y genera una respuesta de texto.
4. `voice.py` convierte esa respuesta a audio (MP3) con Edge-TTS.
5. El servidor responde por WebSocket con: texto + audio en base64.
6. El navegador reproduce el audio y anima el orbe de partículas.

También se expone una ruta REST /api/chat para clientes que no usen
WebSocket, y /api/health para verificar que el servicio está vivo
(útil en Railway).
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from brain import BaroBrain
from voice import synthesize, VOICES, DEFAULT_VOICE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baro")

app = FastAPI(title="Baro API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- #
# Modelos
# --------------------------------------------------------------------------- #

class ChatRequest(BaseModel):
    message: str
    voice: str | None = None


class ChatResponse(BaseModel):
    text: str
    intent: str
    data: dict
    action: str | None = None
    audio_base64: str | None = None


# --------------------------------------------------------------------------- #
# Endpoints REST
# --------------------------------------------------------------------------- #

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "baro"}


@app.get("/api/voices")
async def list_voices():
    return {"voices": VOICES, "default": DEFAULT_VOICE}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    brain = BaroBrain()
    result = await brain.process(req.message)

    audio_b64 = None
    try:
        audio_bytes = await synthesize(result.text, voice=req.voice)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo sintetizar audio: %s", exc)

    return ChatResponse(
        text=result.text,
        intent=result.intent,
        data=result.data,
        action=result.action,
        audio_base64=audio_b64,
    )


# --------------------------------------------------------------------------- #
# WebSocket — conversación en tiempo real
# --------------------------------------------------------------------------- #

class ConnectionManager:
    def __init__(self) -> None:
        self.active: dict[WebSocket, BaroBrain] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active[ws] = BaroBrain()

    def disconnect(self, ws: WebSocket) -> None:
        self.active.pop(ws, None)

    def brain_for(self, ws: WebSocket) -> BaroBrain:
        return self.active[ws]


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    logger.info("Cliente conectado por WebSocket.")

    try:
        await websocket.send_json({
            "type": "ready",
            "text": "Hola, soy Baro. Estoy lista para ayudarte.",
        })

        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"message": raw}

            user_message = (payload.get("message") or "").strip()
            voice_choice = payload.get("voice")

            if not user_message:
                continue

            # Avisamos al frontend que Baro está "pensando" (para animar el orbe)
            await websocket.send_json({"type": "thinking"})

            brain = manager.brain_for(websocket)
            result = await brain.process(user_message)

            audio_b64 = None
            try:
                audio_bytes = await synthesize(result.text, voice=voice_choice)
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Fallo TTS: %s", exc)

            await websocket.send_json({
                "type": "response",
                "text": result.text,
                "intent": result.intent,
                "data": result.data,
                "action": result.action,
                "audio_base64": audio_b64,
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Cliente desconectado.")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error en WebSocket: %s", exc)
        manager.disconnect(websocket)


# --------------------------------------------------------------------------- #
# Servir el frontend estático (todos los archivos viven junto a main.py)
# --------------------------------------------------------------------------- #

@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return JSONResponse({"detail": "Frontend no encontrado."}, status_code=404)


@app.get("/styles.css")
async def serve_styles():
    return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css")


@app.get("/app.js")
async def serve_app_js():
    return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")


@app.get("/orb.js")
async def serve_orb_js():
    return FileResponse(FRONTEND_DIR / "orb.js", media_type="application/javascript")
