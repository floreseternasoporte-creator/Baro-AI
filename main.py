# -*- coding: utf-8 -*-
"""
main.py — Servidor de Baro v3.0.
FastAPI + WebSockets. Ahora incluye el saludo automático de bienvenida.
"""

from __future__ import annotations

import base64
import json
import logging
import random
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from brain import BaroBrain
from voice import synthesize, VOICES, DEFAULT_VOICE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("baro")

app = FastAPI(title="Baro API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent

WELCOME_GREETINGS = [
    "¡Hola! Soy Baro, tu asistente inteligente. Ya estoy escuchando. Solo di oye Baro y luego tu pregunta.",
    "¡Hola! Baro lista y activada. Di oye Baro seguido de tu pregunta y te respondo al instante.",
    "¡Hola! Aquí estoy. Soy Baro. Para hablar conmigo, di oye Baro y luego lo que necesitas.",
    "¡Hola de nuevo! Soy Baro. Di oye Baro cuando quieras hablar y te escucho de inmediato.",
]


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
    return {"status": "ok", "service": "baro", "version": "3.0.0"}


@app.get("/api/voices")
async def list_voices():
    return {"voices": VOICES, "default": DEFAULT_VOICE}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # Saludo de bienvenida automático (petición especial del frontend)
    if req.message == "saludo_inicial_baro_v3":
        greeting_text = random.choice(WELCOME_GREETINGS)
        audio_b64 = None
        try:
            audio_bytes = await synthesize(greeting_text, voice=req.voice)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        except Exception as exc:
            logger.warning("No se pudo sintetizar saludo: %s", exc)
        return ChatResponse(
            text=greeting_text,
            intent="welcome_greeting",
            data={},
            action=None,
            audio_base64=audio_b64,
        )

    brain = BaroBrain()
    result = await brain.process(req.message)

    audio_b64 = None
    try:
        audio_bytes = await synthesize(result.text, voice=req.voice)
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    except Exception as exc:
        logger.warning("No se pudo sintetizar audio: %s", exc)

    return ChatResponse(
        text=result.text,
        intent=result.intent,
        data=result.data,
        action=result.action,
        audio_base64=audio_b64,
    )


# --------------------------------------------------------------------------- #
# WebSocket
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
            "text": "Baro conectada y lista.",
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

            await websocket.send_json({"type": "thinking"})

            brain = manager.brain_for(websocket)
            result = await brain.process(user_message)

            audio_b64 = None
            try:
                audio_bytes = await synthesize(result.text, voice=voice_choice)
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as exc:
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
    except Exception as exc:
        logger.exception("Error en WebSocket: %s", exc)
        manager.disconnect(websocket)


# --------------------------------------------------------------------------- #
# Servir frontend estático
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
