# -*- coding: utf-8 -*-
"""
brain.py — El "cerebro" de Baro.

Este módulo se encarga de TODA la inteligencia de detección de patrones:
- Analiza el texto que llega (de voz o texto) y decide qué intención tiene
  el usuario (clima, cálculo, hora, saludo, despedida, identidad, etc).
- Cada intención tiene un conjunto de expresiones regulares y palabras clave
  "entrenadas a mano" (sin depender de ninguna IA externa).
- Devuelve una respuesta de texto que luego el servidor convierte a voz
  con Edge-TTS.

No se usa ninguna API de IA externa (OpenAI, Gemini, etc). Toda la lógica
de comprensión es de Baro, hecha con reglas, patrones y heurísticas propias.
"""

from __future__ import annotations

import re
import random
import unicodedata
from dataclasses import dataclass
from typing import Callable, Optional

from weather import get_weather, WeatherError
from calculator import evaluate_expression, CalculatorError


# --------------------------------------------------------------------------- #
# Utilidades de normalización de texto
# --------------------------------------------------------------------------- #

def strip_accents(text: str) -> str:
    """Quita tildes para que el matching de patrones sea más robusto."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = strip_accents(text)
    text = re.sub(r"[¿?¡!]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


# --------------------------------------------------------------------------- #
# Estructura de una intención detectada
# --------------------------------------------------------------------------- #

@dataclass
class Intent:
    name: str
    confidence: float
    data: dict


@dataclass
class BrainResponse:
    text: str
    intent: str
    data: dict
    # "action" le dice al frontend si debe disparar algo especial,
    # por ejemplo mostrar una tarjeta de clima o de resultado matemático.
    action: Optional[str] = None


# --------------------------------------------------------------------------- #
# Patrones de intención (regex entrenadas a mano)
# --------------------------------------------------------------------------- #

GREETING_PATTERNS = [
    r"\bhola\b", r"\bbuenas\b", r"\bbuenos dias\b", r"\bbuenas tardes\b",
    r"\bbuenas noches\b", r"\bque tal\b", r"\bque hay\b", r"\bque onda\b",
    r"\bhey\b", r"\bhello\b", r"\bsaludos\b",
]

FAREWELL_PATTERNS = [
    r"\badios\b", r"\bhasta luego\b", r"\bnos vemos\b", r"\bchao\b",
    r"\bme voy\b", r"\bhasta pronto\b", r"\bbye\b", r"\bcuidate\b",
]

THANKS_PATTERNS = [
    r"\bgracias\b", r"\bmuchas gracias\b", r"\bte agradezco\b", r"\bthank you\b",
]

IDENTITY_PATTERNS = [
    r"\bquien eres\b", r"\bcomo te llamas\b", r"\bcual es tu nombre\b",
    r"\bque eres\b", r"\bquien te creo\b", r"\bquien te hizo\b",
    r"\beres una ia\b", r"\beres un robot\b", r"\bcuentame de ti\b",
]

CAPABILITY_PATTERNS = [
    r"\bque puedes hacer\b", r"\bque sabes hacer\b", r"\ben que me ayudas\b",
    r"\bpara que sirves\b", r"\bcuales son tus funciones\b", r"\bayuda\b$",
    r"\bque funciones tienes\b",
]

TIME_PATTERNS = [
    r"\bque hora es\b", r"\bdime la hora\b", r"\bla hora\b", r"\bhora actual\b",
]

DATE_PATTERNS = [
    r"\bque dia es hoy\b", r"\bque fecha es\b", r"\bfecha de hoy\b",
    r"\ben que fecha estamos\b", r"\bque dia es\b",
]

WEATHER_PATTERNS = [
    r"\bclima\b", r"\bel tiempo en\b", r"\bcomo esta el tiempo\b",
    r"\bva a llover\b", r"\btemperatura en\b", r"\bhace frio en\b",
    r"\bhace calor en\b", r"\bpronostico\b", r"\bcomo esta el dia en\b",
]

CALC_PATTERNS = [
    r"\bcuanto es\b", r"\bcalcula\b", r"\bcalculadora\b", r"\bsuma\b",
    r"\bresta\b", r"\bmultiplica\b", r"\bdivide\b", r"\braiz cuadrada\b",
    r"^\s*[\d\.\,]+\s*[\+\-\*\/x]\s*[\d\.\,]+",
    r"\bcual es el resultado de\b", r"\bporcentaje de\b",
    r"\bpor ciento de\b", r"\b%\s*de\b", r"\bresuelve\b",
]

JOKE_PATTERNS = [
    r"\bcuentame un chiste\b", r"\bdime un chiste\b", r"\bhazme reir\b",
    r"\bsabes algun chiste\b",
]

MOOD_PATTERNS = [
    r"\bcomo estas\b", r"\bcomo te sientes\b", r"\bcomo te va\b",
    r"\btodo bien\b",
]

REPEAT_PATTERNS = [
    r"\brepite\b", r"\bque dijiste\b", r"\bpuedes repetir\b",
]


def matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


# --------------------------------------------------------------------------- #
# Extracción de la ciudad para preguntas de clima
# --------------------------------------------------------------------------- #

CITY_TRIGGERS = [
    r"clima en (?P<city>.+)",
    r"el tiempo en (?P<city>.+)",
    r"temperatura en (?P<city>.+)",
    r"como esta el tiempo en (?P<city>.+)",
    r"como esta el clima en (?P<city>.+)",
    r"va a llover en (?P<city>.+)",
    r"pronostico (?:del tiempo )?(?:para|en) (?P<city>.+)",
    r"hace frio en (?P<city>.+)",
    r"hace calor en (?P<city>.+)",
]


def extract_city(text: str) -> Optional[str]:
    for pattern in CITY_TRIGGERS:
        m = re.search(pattern, text)
        if m:
            city = m.group("city").strip()
            # Limpiar conectores finales tipo "hoy", "ahora", "por favor"
            city = re.sub(r"\b(hoy|ahora|por favor|ahorita)\b", "", city).strip()
            city = city.rstrip("?. ")
            if city:
                return city
    return None


# --------------------------------------------------------------------------- #
# Extracción de expresión matemática
# --------------------------------------------------------------------------- #

NUMBER_WORDS = {
    "cero": "0", "uno": "1", "una": "1", "dos": "2", "tres": "3", "cuatro": "4",
    "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9",
    "diez": "10", "once": "11", "doce": "12", "veinte": "20", "treinta": "30",
    "cuarenta": "40", "cincuenta": "50", "cien": "100", "mil": "1000",
}

OPERATOR_WORDS = {
    "mas": "+", "menos": "-", "por": "*", "multiplicado por": "*",
    "entre": "/", "dividido por": "/", "dividido entre": "/",
}


def words_to_expression(text: str) -> str:
    """Convierte una frase como 'cuanto es 5 mas 3' en '5 + 3'."""
    expr = text
    for word, symbol in OPERATOR_WORDS.items():
        expr = re.sub(rf"\b{word}\b", f" {symbol} ", expr)
    for word, digit in NUMBER_WORDS.items():
        expr = re.sub(rf"\b{word}\b", digit, expr)
    return expr


def extract_math_expression(text: str) -> Optional[str]:
    cleaned = text
    for prefix in ["cuanto es", "calcula", "cual es el resultado de", "resuelve"]:
        cleaned = cleaned.replace(prefix, "")

    # Caso porcentaje: se revisa ANTES de convertir palabras a operadores,
    # porque "por ciento" se rompería si "por" ya se volvió "*".
    pct_match = re.search(
        r"([\d\.]+)\s*(?:%|por ciento|porciento)\s*de\s*([\d\.]+)", cleaned
    )
    if pct_match:
        a, b = pct_match.groups()
        return f"({a}/100)*{b}"

    # Caso: raíz cuadrada de N (también antes de la conversión genérica)
    sqrt_match = re.search(r"raiz cuadrada de (\d+)", cleaned)
    if sqrt_match:
        return f"sqrt({sqrt_match.group(1)})"

    cleaned = words_to_expression(cleaned)

    # Buscar algo que luzca a una expresión matemática válida
    match = re.search(
        r"[\d\.\,]+(\s*[\+\-\*\/x\^%]\s*[\d\.\,]+)+", cleaned
    )
    if match:
        return match.group(0).replace("x", "*").replace(",", ".")

    return None


# --------------------------------------------------------------------------- #
# Bancos de respuesta (variedad para que no suene repetitivo)
# --------------------------------------------------------------------------- #

GREETING_REPLIES = [
    "¡Hola! Soy Baro, tu asistente. ¿En qué puedo ayudarte hoy?",
    "¡Qué alegría escucharte! Soy Baro. Cuéntame, ¿qué necesitas?",
    "Hola, aquí estoy. ¿Qué te gustaría saber o hacer?",
]

FAREWELL_REPLIES = [
    "¡Hasta luego! Aquí estaré cuando me necesites.",
    "Nos vemos pronto. Fue un gusto ayudarte.",
    "Cuídate mucho. Vuelve cuando quieras.",
]

THANKS_REPLIES = [
    "¡Con mucho gusto! Para eso estoy.",
    "No hay de qué, siempre es un placer ayudarte.",
    "¡Es un placer! Aquí seguiré si necesitas algo más.",
]

IDENTITY_REPLIES = [
    "Soy Baro, una inteligencia artificial creada para acompañarte y ayudarte con lo que necesites: clima, cálculos, preguntas generales y más.",
    "Me llamo Baro. Soy tu asistente personal, diseñada para escucharte, entender lo que necesitas y resolverlo contigo.",
]

CAPABILITY_REPLIES = [
    "Puedo darte el clima de cualquier ciudad, hacer cálculos matemáticos, decirte la hora y la fecha, y conversar contigo. Cada día aprenderé a hacer más cosas.",
    "Por ahora puedo ayudarte con el clima en cualquier región, resolver operaciones matemáticas, decirte la hora exacta y mantener una conversación contigo.",
]

JOKE_REPLIES = [
    "¿Por qué los programadores prefieren el frío? Porque odian los bugs de verano.",
    "¿Sabes por qué la IA fue a terapia? Porque tenía demasiados problemas sin resolver... de lógica.",
    "¿Qué le dice un bit a otro? Nos vemos en el bus.",
]

MOOD_REPLIES = [
    "Estoy funcionando perfectamente y con muchas ganas de ayudarte.",
    "Todo en orden por aquí. ¿Y tú, cómo estás?",
]

FALLBACK_REPLIES = [
    "No estoy segura de haber entendido eso del todo, pero estoy aprendiendo. ¿Puedes reformularlo?",
    "Todavía no sé responder eso, pero pronto aprenderé más cosas. ¿Quieres preguntarme sobre el clima o algún cálculo?",
    "Hmm, eso aún no lo manejo bien. Intenta preguntarme por el clima en una ciudad, o pídeme que calcule algo.",
]


def pick(replies: list[str]) -> str:
    return random.choice(replies)


# --------------------------------------------------------------------------- #
# Motor principal
# --------------------------------------------------------------------------- #

class BaroBrain:
    """
    Orquesta la detección de intención + generación de respuesta.
    Mantiene un pequeño historial de contexto por sesión (para "repite",
    seguimiento conversacional simple, etc.)
    """

    def __init__(self) -> None:
        self.last_response: str = ""
        self.last_city: Optional[str] = None

    async def process(self, raw_text: str) -> BrainResponse:
        text = normalize(raw_text)

        if not text:
            return BaroResponseEmpty()

        # 1) Repetir última respuesta
        if matches_any(REPEAT_PATTERNS, text) and self.last_response:
            return BrainResponse(
                text=self.last_response, intent="repeat", data={}
            )

        # 2) Clima — alta prioridad porque suele incluir ciudad con "en"
        if matches_any(WEATHER_PATTERNS, text):
            return await self._handle_weather(text)

        # 3) Calculadora
        if matches_any(CALC_PATTERNS, text):
            maybe_expr = extract_math_expression(text)
            if maybe_expr:
                return self._handle_calculation(maybe_expr)

        # 4) Identidad
        if matches_any(IDENTITY_PATTERNS, text):
            return self._finish("identity", pick(IDENTITY_REPLIES))

        # 5) Capacidades
        if matches_any(CAPABILITY_PATTERNS, text):
            return self._finish("capability", pick(CAPABILITY_REPLIES))

        # 6) Hora
        if matches_any(TIME_PATTERNS, text):
            return self._handle_time()

        # 7) Fecha
        if matches_any(DATE_PATTERNS, text):
            return self._handle_date()

        # 8) Chiste
        if matches_any(JOKE_PATTERNS, text):
            return self._finish("joke", pick(JOKE_REPLIES))

        # 9) Estado de ánimo
        if matches_any(MOOD_PATTERNS, text):
            return self._finish("mood", pick(MOOD_REPLIES))

        # 10) Saludo
        if matches_any(GREETING_PATTERNS, text):
            return self._finish("greeting", pick(GREETING_REPLIES))

        # 11) Despedida
        if matches_any(FAREWELL_PATTERNS, text):
            return self._finish("farewell", pick(FAREWELL_REPLIES))

        # 12) Agradecimiento
        if matches_any(THANKS_PATTERNS, text):
            return self._finish("thanks", pick(THANKS_REPLIES))

        # 13) Fallback inteligente: si hay números sueltos, intenta calculadora igual
        loose_expr = extract_math_expression(text)
        if loose_expr:
            return self._handle_calculation(loose_expr)

        # 14) No se entendió nada
        return self._finish("fallback", pick(FALLBACK_REPLIES))

    # ----------------------------------------------------------------- #

    def _finish(self, intent: str, text: str, data: dict | None = None, action: str | None = None) -> BrainResponse:
        self.last_response = text
        return BrainResponse(text=text, intent=intent, data=data or {}, action=action)

    async def _handle_weather(self, text: str) -> BrainResponse:
        city = extract_city(text) or self.last_city
        if not city:
            msg = "¿De qué ciudad o región quieres saber el clima?"
            return self._finish("weather_need_city", msg)

        try:
            info = await get_weather(city)
        except WeatherError as exc:
            msg = f"No pude encontrar el clima para '{city.title()}'. {exc}"
            return self._finish("weather_error", msg)
        except Exception:  # noqa: BLE001 — cualquier fallo de red/API no debe tumbar el servidor
            msg = (
                f"No pude consultar el clima de {city.title()} en este momento. "
                "El servicio de clima podría estar temporalmente fuera de línea, intenta de nuevo más tarde."
            )
            return self._finish("weather_error", msg)

        self.last_city = city
        msg = (
            f"En {info['city']} la temperatura actual es de {info['temperature']}°C, "
            f"con {info['description']}. La sensación es de {info['feels_like']}°C "
            f"y la humedad relativa es de {info['humidity']}%."
        )
        return self._finish("weather", msg, data=info, action="show_weather_card")

    def _handle_calculation(self, expr: str) -> BrainResponse:
        try:
            result = evaluate_expression(expr)
        except CalculatorError as exc:
            msg = f"No pude calcular eso. {exc}"
            return self._finish("calc_error", msg)

        clean_expr = re.sub(r"\s+", " ", expr.strip())
        msg = f"El resultado de {clean_expr} es {result}."
        return self._finish(
            "calculation", msg,
            data={"expression": clean_expr, "result": result},
            action="show_calc_card",
        )

    def _handle_time(self) -> BrainResponse:
        from datetime import datetime
        now = datetime.now()
        msg = f"Son las {now.strftime('%I:%M %p')}."
        return self._finish("time", msg, data={"time": now.isoformat()})

    def _handle_date(self) -> BrainResponse:
        from datetime import datetime
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        meses = [
            "enero", "febrero", "marzo", "abril", "mayo", "junio",
            "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
        ]
        now = datetime.now()
        dia_semana = dias[now.weekday()]
        mes = meses[now.month - 1]
        msg = f"Hoy es {dia_semana} {now.day} de {mes} de {now.year}."
        return self._finish("date", msg, data={"date": now.isoformat()})


def BaroResponseEmpty() -> BrainResponse:
    return BrainResponse(
        text="No escuché nada claro. ¿Puedes repetirlo?",
        intent="empty",
        data={},
    )
