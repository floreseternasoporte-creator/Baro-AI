# Baro — Asistente de inteligencia artificial con voz

Baro es tu propio asistente de IA, con voz en tiempo real, hecho 100% con
tecnología propia (sin depender de OpenAI, Gemini ni ninguna IA externa).

## Estructura del proyecto

Todos los archivos viven juntos, en una sola carpeta (sin subcarpetas):

- `main.py` — servidor FastAPI + WebSockets, también sirve el frontend.
- `brain.py` — el "cerebro": motor de detección de patrones (intents) hecho
  a mano con expresiones regulares — saludo, despedida, identidad, clima,
  cálculo, hora, fecha, chistes, estado de ánimo, etc.
- `weather.py` — consulta el clima usando **Open-Meteo**, una API pública y
  completamente gratuita (no requiere API key).
- `calculator.py` — calculadora segura (usa un parser de AST, no `eval()`
  directo sobre texto del usuario, así que es inmune a inyección de código).
- `voice.py` — convierte el texto de Baro en audio con **Edge-TTS**, las
  voces neuronales gratuitas de Microsoft.
- `index.html`, `styles.css`, `app.js`, `orb.js` — el frontend completo: el
  slide de bienvenida, el chat, el modo voz inmersivo, y el orbe de
  partículas animado.
- `requirements.txt`, `Procfile`, `railway.json` — configuración para correr
  y desplegar el servidor.

## Cómo funciona el flujo de voz

1. El navegador escucha con la **Web Speech API** (nativa de Chrome, gratis,
   sin backend) y transcribe lo que dices a texto.
2. Ese texto se envía por WebSocket a Baro.
3. `brain.py` detecta la intención y genera una respuesta.
4. `voice.py` convierte esa respuesta en audio MP3 con Edge-TTS.
5. El navegador recibe texto + audio, reproduce el audio y anima el orbe de
   partículas analizando el volumen en tiempo real (Web Audio API).

## Ejecutarlo en tu computadora

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Abre `http://localhost:8000` en **Google Chrome** (el reconocimiento de voz
del navegador funciona mejor ahí).

## Desplegarlo en Railway

1. Sube todos estos archivos a un repositorio de GitHub (todos en la raíz
   del repo, sin meterlos en una subcarpeta).
2. En Railway: **New Project → Deploy from GitHub repo**.
3. Selecciona el repositorio. Railway detecta automáticamente Python gracias
   a Nixpacks y al archivo `requirements.txt`.
4. Railway asigna automáticamente la variable `$PORT`; el `Procfile` y
   `railway.json` ya están configurados para usarla
   (`uvicorn main:app --host 0.0.0.0 --port $PORT`).
5. Despliega. Cuando termine, Railway te da una URL pública — ábrela y
   listo, Baro está viva.

No necesitas configurar ninguna variable de entorno ni API key: tanto
Open-Meteo (clima) como Edge-TTS (voz) son gratuitos y no requieren
autenticación.

## Próximos pasos (para seguir agregando funciones)

La arquitectura está pensada para crecer fácilmente:

- Agregar nuevos intents: solo se añade un patrón regex y un handler nuevo
  en `brain.py`.
- Agregar nuevas fuentes de datos (noticias, recordatorios, etc.): se crea
  un módulo nuevo como `weather.py` y se conecta desde `brain.py`.
- El frontend y el orbe (`orb.js`) ya soportan los estados `idle`,
  `listening`, `thinking` y `speaking` — cualquier función nueva puede
  reusar esos mismos estados visuales.
