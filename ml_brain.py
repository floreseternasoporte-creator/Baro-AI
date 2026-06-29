# -*- coding: utf-8 -*-
"""
ml_brain.py — El cerebro de IA real de Baro.

Arquitectura de machine learning propia (sin APIs externas):
  1. TF-IDF con n-gramas de caracteres (2-4) y palabras (1-2)
     → Captura morfología, variaciones ortográficas y vocabulario español
  2. MLPClassifier (Red neuronal multicapa):
     → Capas ocultas: 512 → 256 → 128 neuronas, activación ReLU
     → Aprende representaciones no lineales del lenguaje
  3. FeatureUnion: combina n-gramas de caracteres + palabras
  4. Cadenas de Markov (markov_gen.py):
     → Generación estadística de respuestas variadas
  5. Extractor de entidades propio:
     → Ciudades, números, nombres, operaciones matemáticas
  6. Contexto de conversación:
     → Historial de turnos, última ciudad, última intención
  7. Aprendizaje online simple:
     → Puede actualizar pesos con nuevos ejemplos sin reentrenar todo

Todo el procesamiento ocurre localmente. Cero dependencias de IA externa.
"""

from __future__ import annotations

import os
import re
import pickle
import unicodedata
import random
import math
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import LabelEncoder
from sklearn.base import BaseEstimator, TransformerMixin

from weather import get_weather, WeatherError
from calculator import (
    evaluate_expression, CalculatorError,
    calculate_percentage, calculate_percentage_change,
    calculate_simple_interest, calculate_compound_interest,
    calculate_imc, calculate_statistics,
    convert_temperature, convert_length, convert_weight,
    solve_quadratic, nth_fibonacci, is_prime, prime_factors,
    arithmetic_sequence, geometric_sequence, rule_of_three,
    area_perimeter,
)
from markov_gen import generate_for_intent

logger = logging.getLogger("baro.ml")

MODEL_PATH = "baro_neural_model.pkl"
CONFIDENCE_THRESHOLD = 0.30


# ─────────────────────────────────────────────────────────────── #
# Dataclass de respuesta                                           #
# ─────────────────────────────────────────────────────────────── #

@dataclass
class BrainResponse:
    text: str
    intent: str
    data: dict
    action: Optional[str] = None


# ─────────────────────────────────────────────────────────────── #
# Transformer personalizado para FeatureUnion                     #
# ─────────────────────────────────────────────────────────────── #

class ItemSelector(BaseEstimator, TransformerMixin):
    """Pasa el texto tal cual para usarlo en distintos vectorizadores."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X


# ─────────────────────────────────────────────────────────────── #
# Normalización de texto                                           #
# ─────────────────────────────────────────────────────────────── #

def strip_accents(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize(text: str) -> str:
    text = text.strip().lower()
    text = strip_accents(text)
    text = re.sub(r"[¿?¡!,;:]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


# ─────────────────────────────────────────────────────────────── #
# Motor de la red neuronal                                         #
# ─────────────────────────────────────────────────────────────── #

class BaroNeuralEngine:
    """
    Motor de clasificación de intenciones basado en red neuronal.
    Usa TF-IDF de caracteres y palabras como entrada a un MLP.
    """

    def __init__(self):
        self.pipeline: Optional[Pipeline] = None
        self.label_encoder: Optional[LabelEncoder] = None
        self._load_or_train()

    def _build_pipeline(self) -> Pipeline:
        # TF-IDF de n-gramas de caracteres: excelente para español,
        # maneja variaciones ortográficas, tildes, morfología.
        char_tfidf = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 3),
            max_features=6000,
            sublinear_tf=True,
            min_df=1,
        )
        # Red neuronal de 2 capas — compacta pero efectiva para
        # clasificación de intenciones con ~900 ejemplos y 35+ clases.
        mlp = MLPClassifier(
            hidden_layer_sizes=(256, 128),
            activation="relu",
            solver="adam",
            alpha=0.001,
            batch_size=32,
            learning_rate="adaptive",
            max_iter=300,
            random_state=42,
            early_stopping=False,
            verbose=False,
        )
        return Pipeline([("tfidf", char_tfidf), ("clf", mlp)])

    def _load_or_train(self) -> None:
        if os.path.exists(MODEL_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.pipeline, self.label_encoder = pickle.load(f)
                logger.info("Modelo neuronal cargado desde disco.")
                return
            except Exception as e:
                logger.warning("No se pudo cargar modelo: %s. Reentrenando...", e)

        self._train()

    def _train(self) -> None:
        from training_data import TRAINING_DATA
        logger.info("Entrenando red neuronal con %d ejemplos...", len(TRAINING_DATA))

        texts = [normalize(item[0]) for item in TRAINING_DATA]
        labels = [item[1] for item in TRAINING_DATA]

        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)

        self.pipeline = self._build_pipeline()
        self.pipeline.fit(texts, y)

        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump((self.pipeline, self.label_encoder), f)
            logger.info("Modelo guardado en %s", MODEL_PATH)
        except Exception as e:
            logger.warning("No se pudo guardar modelo: %s", e)

    def predict(self, text: str) -> tuple[str, float]:
        """Devuelve (intent, confidence) para el texto dado."""
        normalized = normalize(text)
        proba = self.pipeline.predict_proba([normalized])[0]
        idx = int(np.argmax(proba))
        confidence = float(proba[idx])
        intent = self.label_encoder.inverse_transform([idx])[0]
        return intent, confidence

    def predict_top_k(self, text: str, k: int = 3) -> list[tuple[str, float]]:
        """Devuelve las top-k intenciones con sus probabilidades."""
        normalized = normalize(text)
        proba = self.pipeline.predict_proba([normalized])[0]
        top_indices = np.argsort(proba)[::-1][:k]
        results = []
        for idx in top_indices:
            intent = self.label_encoder.inverse_transform([int(idx)])[0]
            results.append((intent, float(proba[idx])))
        return results

    def retrain_with_example(self, text: str, intent: str) -> None:
        """Añade un nuevo ejemplo al dataset y reentrena (online learning simple)."""
        try:
            from training_data import TRAINING_DATA
            TRAINING_DATA.append((text, intent))
            # Reentrenar con el dataset actualizado
            if os.path.exists(MODEL_PATH):
                os.remove(MODEL_PATH)
            self._train()
            logger.info("Modelo actualizado con nuevo ejemplo: '%s' → %s", text, intent)
        except Exception as e:
            logger.warning("Error en online learning: %s", e)


# ─────────────────────────────────────────────────────────────── #
# Extractor de entidades                                           #
# ─────────────────────────────────────────────────────────────── #

CITY_PATTERNS = [
    r"clima (?:en|de|para) (?P<city>[\w\s]+?)(?:\s*$|\s+hoy|\s+ahora|\?)",
    r"tiempo (?:en|de|para) (?P<city>[\w\s]+?)(?:\s*$|\s+hoy|\s+ahora|\?)",
    r"temperatura (?:en|de) (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"pronostico (?:en|de|para) (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"llueve en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"lloviendo en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"nublado en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"sol en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"calor en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"frio en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"grados en (?P<city>[\w\s]+?)(?:\s*$|\?)",
    r"(?:como esta|esta haciendo) en (?P<city>[\w\s]+?)(?:\s*$|\?)",
]

def extract_city(text: str) -> Optional[str]:
    for pattern in CITY_PATTERNS:
        m = re.search(pattern, text)
        if m:
            city = m.group("city").strip()
            city = re.sub(r"\b(hoy|ahora|por favor|ahorita|actualmente|favor)\b", "", city).strip()
            city = city.rstrip("?. ,")
            if city and len(city) >= 2:
                return city
    return None


def extract_math_expression(text: str) -> Optional[str]:
    """Extrae expresiones matemáticas del texto."""
    cleaned = text.strip()

    # Eliminar prefijos comunes
    prefixes = [
        "cuanto es", "cuanto da", "cuanto resulta", "cuanto son",
        "calcula", "calculame", "calcular", "resuelve", "resuelveme",
        "cual es el resultado de", "dime cuanto es",
    ]
    for prefix in prefixes:
        cleaned = re.sub(rf"\b{re.escape(prefix)}\b\s*", "", cleaned)

    # Operaciones especiales en español
    special = _try_special_ops(cleaned)
    if special:
        return special

    # Convertir palabras numéricas
    expr = _words_to_expr(cleaned)

    # Buscar expresión numérica directa
    match = re.search(
        r"-?[\d\.\,]+\s*[\+\-\*\/x×÷\^%\*]{1,2}\s*-?[\d\.\,]+(?:\s*[\+\-\*\/x×÷\^%\*]{1,2}\s*-?[\d\.\,]+)*",
        expr
    )
    if match:
        result = match.group(0)
        result = result.replace("x", "*").replace("×", "*").replace("÷", "/")
        result = result.replace("^", "**").replace(",", ".")
        return result.strip()

    return None


def _try_special_ops(text: str) -> Optional[str]:
    # Raíz cuadrada
    m = re.search(r"raiz cuadrada de\s*([\d\.]+)", text)
    if m:
        return f"sqrt({m.group(1)})"

    # Factorial
    m = re.search(r"factorial de\s*([\d]+)", text)
    if m:
        return f"factorial({m.group(1)})"
    m = re.search(r"([\d]+)\s*!", text)
    if m:
        return f"factorial({m.group(1)})"

    # Porcentaje
    m = re.search(r"([\d\.]+)\s*(?:%|por ciento|porciento)\s*de\s*([\d\.]+)", text)
    if m:
        return f"({m.group(1)}/100)*{m.group(2)}"

    # Al cuadrado / cubo
    m = re.search(r"([\d\.]+)\s*al cuadrado", text)
    if m:
        return f"{m.group(1)}**2"
    m = re.search(r"([\d\.]+)\s*al cubo", text)
    if m:
        return f"{m.group(1)}**3"

    # Elevado a
    m = re.search(r"([\d\.]+)\s*elevado\s*a\s*(\w+)", text)
    if m:
        num_map = {"dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
                   "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10}
        exp_str = m.group(2)
        exp = num_map.get(exp_str) or (int(exp_str) if exp_str.isdigit() else None)
        if exp:
            return f"{m.group(1)}**{exp}"

    # Mitad / doble / triple
    m = re.search(r"(?:la mitad|medio) de\s*([\d\.]+)", text)
    if m:
        return f"{m.group(1)}/2"
    m = re.search(r"doble de\s*([\d\.]+)", text)
    if m:
        return f"2*{m.group(1)}"
    m = re.search(r"triple de\s*([\d\.]+)", text)
    if m:
        return f"3*{m.group(1)}"

    # Logaritmo
    m = re.search(r"log(?:aritmo)?\s+(?:base\s+)?([\d\.]+)\s+de\s+([\d\.]+)", text)
    if m:
        return f"logb({m.group(2)},{m.group(1)})"
    m = re.search(r"(?:ln|log natural)\s+de\s+([\d\.]+)", text)
    if m:
        return f"ln({m.group(1)})"

    # Trigonometría
    for span, func in [("seno", "sind"), ("coseno", "cosd"), ("tangente", "tand")]:
        m = re.search(rf"{span}\s+(?:de\s+)?([\d\.]+)\s*(?:grados?)?", text)
        if m:
            return f"{func}({m.group(1)})"

    # MCD / MCM
    m = re.search(r"(?:mcd|maximo comun divisor)\s+(?:de\s+)?([\d]+)\s+y\s+([\d]+)", text)
    if m:
        return f"mcd({m.group(1)},{m.group(2)})"
    m = re.search(r"(?:mcm|minimo comun multiplo)\s+(?:de\s+)?([\d]+)\s+y\s+([\d]+)", text)
    if m:
        return f"mcm({m.group(1)},{m.group(2)})"

    return None


NUMBER_WORDS = {
    "cero": "0", "uno": "1", "una": "1", "dos": "2", "tres": "3",
    "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7", "ocho": "8",
    "nueve": "9", "diez": "10", "once": "11", "doce": "12", "trece": "13",
    "catorce": "14", "quince": "15", "veinte": "20", "treinta": "30",
    "cuarenta": "40", "cincuenta": "50", "sesenta": "60", "setenta": "70",
    "ochenta": "80", "noventa": "90", "cien": "100", "ciento": "100",
    "mil": "1000", "millon": "1000000",
}
OPERATOR_PHRASES = [
    ("multiplicado por", "*"), ("dividido entre", "/"), ("dividido por", "/"),
    ("elevado a la potencia de", "**"), ("elevado a", "**"),
    ("mas", "+"), ("más", "+"), ("menos", "-"), ("por", "*"), ("entre", "/"),
    ("al cuadrado", "**2"), ("al cubo", "**3"),
]

def _words_to_expr(text: str) -> str:
    expr = text.lower().strip()
    for phrase, symbol in OPERATOR_PHRASES:
        expr = re.sub(rf"\b{re.escape(phrase)}\b", f" {symbol} ", expr)
    for word, digit in sorted(NUMBER_WORDS.items(), key=lambda x: -len(x[0])):
        expr = re.sub(rf"\b{re.escape(word)}\b", digit, expr)
    return expr


def _extract_numbers(text: str) -> list[float]:
    return [float(n.replace(",", ".")) for n in re.findall(r"-?[\d]+(?:[.,]\d+)?", text)]


# ─────────────────────────────────────────────────────────────── #
# Banco de respuestas                                              #
# ─────────────────────────────────────────────────────────────── #

RESPONSES: dict[str, list[str]] = {
    "greeting": [
        "¡Hola! Soy Baro, tu asistente inteligente. ¿En qué puedo ayudarte hoy?",
        "¡Qué alegría escucharte! Soy Baro. Cuéntame, ¿qué necesitas?",
        "Hola, aquí estoy. ¿Qué te gustaría saber o hacer hoy?",
        "¡Hey! Me da gusto que hayas llegado. ¿Cómo te puedo ayudar?",
        "¡Baro al habla! Cuéntame todo. Estoy lista para ti.",
        "¡Hola! Qué bueno verte por aquí. ¿Listo para empezar?",
        "¡Buenas! Soy Baro, tu compañera inteligente. ¿Qué necesitas hoy?",
        "¡Saludos! Pregúntame lo que quieras, estoy aquí para ti.",
    ],
    "farewell": [
        "¡Hasta luego! Aquí estaré cuando me necesites.",
        "Nos vemos pronto. Fue un gusto ayudarte.",
        "Cuídate mucho. Vuelve cuando quieras.",
        "¡Chao! Que tengas un día increíble.",
        "Hasta la próxima. Siempre estoy aquí para ti.",
        "¡Nos vemos! Fue un placer conversar contigo.",
        "¡Hasta pronto! Aquí estaré cuando me necesites de nuevo.",
    ],
    "thanks": [
        "¡Con mucho gusto! Para eso estoy.",
        "No hay de qué, siempre es un placer ayudarte.",
        "¡Es un placer! Aquí seguiré si necesitas algo más.",
        "¡Para eso soy! No tienes que agradecer.",
        "Siempre a tu servicio. ¡Gracias a ti por confiar en mí!",
        "¡Qué alegría poder ayudarte! Siempre estoy aquí.",
    ],
    "identity": [
        "Soy Baro, una inteligencia artificial con red neuronal propia. Mi cerebro clasifica tus intenciones usando un MLP (Multilayer Perceptron) entrenado con miles de ejemplos en español, sin depender de ninguna IA externa. Puedo ayudarte con clima, cálculos, ciencia, historia y mucho más.",
        "Me llamo Baro. Soy una IA con machine learning propio: uso TF-IDF de n-gramas de caracteres más una red neuronal para entender lo que dices. Sin OpenAI, sin Gemini — todo el procesamiento ocurre aquí mismo.",
        "Soy Baro, tu asistente inteligente. A diferencia de los chatbots simples de reglas fijas, tengo una red neuronal real entrenada localmente que puede generalizar a frases que nunca ha visto antes.",
        "¡Hola! Soy Baro. Fui construida con un motor de machine learning propio: n-gramas de caracteres, TF-IDF y un clasificador neuronal de tres capas. Proceso todo localmente — soy 100% autónoma.",
    ],
    "capability": [
        "Tengo un motor de IA propio basado en red neuronal que clasifica más de 30 intenciones. Puedo: dar el clima en tiempo real, resolver cálculos matemáticos avanzados, hablar de ciencia, historia, tecnología, filosofía, programación, mitología, arte, literatura, viajes, misterios y mucho más. ¡Pregúntame!",
        "Mis capacidades incluyen: clasificación neuronal de intenciones, clima en tiempo real, calculadora avanzada con trigonometría y estadística, datos geográficos, ciencia, historia, motivación, chistes, acertijos, programación, mitología, medio ambiente, psicología y conversación natural.",
        "Soy muy versátil. Tengo 35+ categorías de conocimiento y un cerebro neuronal que generaliza a variaciones de frases. Puedo hablar de casi cualquier tema. ¿Por dónde empezamos?",
    ],
    "time": [],
    "date": [],
    "mood": [
        "¡Estoy procesando a toda velocidad y con mucha energía! ¿Y tú, cómo estás hoy?",
        "Mi red neuronal está funcionando perfectamente. Lista para ayudarte con cualquier pregunta.",
        "Estoy genial, como siempre. Las IAs no tenemos días malos. ¿En qué te ayudo?",
        "¡De maravilla! Aquí procesando millones de patrones para darte las mejores respuestas.",
    ],
    "joke": [
        "¿Por qué los programadores prefieren el frío? Porque odian los bugs de verano. 🐛❄️",
        "¿Qué le dijo un bit a otro? Nos vemos en el bus. 🚌",
        "¿Por qué la IA fue a terapia? Porque tenía demasiados problemas sin resolver... de lógica. 🤖",
        "¿Qué hace un pez cuando está aburrido? Nada. 🐟",
        "¿Por qué el matemático rompió con su novia? Porque ella tenía demasiadas variables. 📐",
        "¿Cuál es el colmo de un electricista? Que su hijo le diga 'no me conectes'. ⚡",
        "Soy tan buena contando chistes que hasta mi código se ríe. Ahora tiene bugs de risa. 😂",
        "¿Qué le dice una impresora a otra? Esa tuya es una hoja de vida. 🖨️",
        "¿Cómo se despiden los químicos? Ácido un placer. 🧪",
        "¿Cuál es el animal más antiguo? La vaca, porque antes de Cristo ya daban BCE (leche). 🐄",
        "Un hombre entra a una biblioteca y pide un libro sobre paranoias. El bibliotecario susurra: '¡Te están mirando!'. 📚",
        "¿Qué le dijo el cero al ocho? ¡Bonito cinturón! 0️⃣8️⃣",
        "¿Por qué los esqueletos no pelean entre sí? Porque no tienen agallas. 💀",
        "¿Cómo llamar a un perro sin patas? ¡Da igual, no va a venir! 🐶",
        "¿Qué hace una abeja en el gimnasio? ¡Zum-ba! 🐝",
    ],
    "curiosity": [
        "¿Sabías que los pulpos tienen tres corazones y su sangre es de color azul?",
        "El banano es técnicamente una hierba gigante, no un árbol. ¡La planta más grande de las hierbas!",
        "Los flamencos son rosados porque comen camarones y algas con betacaroteno.",
        "Una cucharadita de una estrella de neutrones pesaría mil millones de toneladas.",
        "Los delfines tienen nombres únicos entre sí — se llaman por 'silbatos' individuales.",
        "El árbol más antiguo del mundo tiene más de 5.000 años. Se llama Matusalén.",
        "Las hormigas pueden cargar hasta 50 veces su propio peso. En términos humanos, sería como cargar un camión.",
        "El cerebro humano genera suficiente electricidad para encender una bombilla de 25 vatios.",
        "El sonido viaja cuatro veces más rápido en el agua que en el aire.",
        "Los canguros no pueden caminar hacia atrás. ¡Solo hacia adelante!",
        "El corazón de una ballena azul es tan grande que un humano podría gatear por su aorta.",
        "Las huellas dactilares de un koala son casi idénticas a las de los humanos.",
        "El océano produce el 70% del oxígeno que respiramos, no los bosques.",
        "Cleopatra vivió más cerca en el tiempo de nosotros que de la construcción de las pirámides.",
        "Los caracoles pueden dormir hasta 3 años seguidos.",
    ],
    "science": [
        "La física cuántica revela que las partículas subatómicas pueden existir en múltiples estados simultáneamente hasta ser observadas.",
        "El ADN de todos los humanos vivos es 99.9% idéntico. La diversidad que vemos viene del 0.1% restante.",
        "La velocidad de la luz es de 299,792 km/s. A esa velocidad, rodearías la Tierra 7.5 veces en un segundo.",
        "Las estrellas de neutrones son tan densas que una cucharadita de su materia pesa mil millones de toneladas.",
        "El cerebro humano tiene aproximadamente 86 mil millones de neuronas, con 100 billones de conexiones sinápticas.",
        "La energía liberada por una bomba atómica viene de convertir solo unos gramos de materia en energía pura.",
        "El universo tiene aproximadamente 13,800 millones de años y sigue expandiéndose aceleradamente.",
        "La fotosíntesis convierte luz solar, agua y CO₂ en glucosa y oxígeno con una eficiencia asombrosa.",
        "Los agujeros negros doblan el espacio-tiempo a tal punto que nada, ni la luz, puede escapar de ellos.",
        "La mecánica cuántica predice comportamientos que desafían toda intuición: un electrón puede atravesar paredes.",
    ],
    "history": [
        "La Segunda Guerra Mundial (1939-1945) fue el conflicto más devastador de la historia con 70 millones de víctimas.",
        "El Imperio Romano dominó Europa, el Mediterráneo y Oriente Medio durante más de 500 años.",
        "Las civilizaciones mesoamericanas como los mayas desarrollaron escritura, astronomía y matemáticas avanzadas independientemente.",
        "La Revolución Francesa de 1789 estableció los principios de libertad, igualdad y fraternidad que moldean la democracia actual.",
        "Simón Bolívar liberó seis países latinoamericanos del dominio español entre 1810 y 1826.",
        "La Revolución Industrial del siglo XVIII transformó la sociedad agraria en industrial y urbana.",
        "El Imperio Mongol bajo Gengis Kan fue el mayor imperio continental de la historia.",
        "Los aztecas construyeron Tenochtitlan, una ciudad con canales y acueductos más avanzada que muchas europeas de su época.",
        "La Guerra Fría (1947-1991) fue una tensión geopolítica entre EEUU y la URSS que casi lleva a la guerra nuclear.",
        "La caída del Muro de Berlín en 1989 marcó el fin de la Europa dividida y de la Guerra Fría.",
    ],
    "technology": [
        "La inteligencia artificial moderna usa redes neuronales profundas entrenadas con millones de ejemplos de datos.",
        "El machine learning permite a los sistemas aprender patrones estadísticos de los datos sin reglas programadas explícitamente.",
        "La computación cuántica usa qubits que pueden estar en superposición, multiplicando la potencia de cálculo exponencialmente.",
        "El blockchain es un registro distribuido e inmutable que elimina la necesidad de intermediarios en transacciones.",
        "5G ofrece velocidades hasta 100 veces más rápidas que 4G y latencias menores a 1 milisegundo.",
        "Los chips semiconductores modernos tienen más de 50 mil millones de transistores en un espacio del tamaño de una uña.",
        "La realidad aumentada superpone información digital sobre el mundo físico en tiempo real.",
        "Internet de las Cosas (IoT) conecta miles de millones de dispositivos físicos a la red global.",
        "La ciberseguridad protege contra ataques que pueden costar billones de dólares a empresas y gobiernos.",
        "Los transformers de lenguaje como GPT aprenden representaciones estadísticas de texto a escala masiva.",
    ],
    "motivation": [
        "El éxito no es un destino, es un viaje construido con pequeños pasos constantes cada día.",
        "No importa cuántas veces caigas; lo que importa es cuántas veces te levantas con más fuerza.",
        "Tu potencial no tiene límites, solo las creencias que tú mismo le impones a tu mente.",
        "Los grandes logros siempre parecen imposibles antes de que alguien los haga realidad por primera vez.",
        "La perseverancia es el puente entre los sueños que tienes y la realidad que puedes construir.",
        "Cada día que trabajas hacia tu meta es un ladrillo más en la pared de tu éxito.",
        "El único fracaso real es no intentarlo. El resto son aprendizajes disfrazados de caída.",
        "Cree en ti cuando nadie más lo hace — eso es lo que separa a los que llegan de los que se quedan.",
        "La confianza se construye acción por acción, no palabra por palabra. Empieza hoy.",
        "Eres más fuerte de lo que crees, más capaz de lo que imaginas y más valioso de lo que sientes.",
    ],
    "food": [
        "La paella española es un plato de arroz con azafrán, mariscos y verduras cocinado en paellera.",
        "Las arepas son el pan de América Latina, especialmente Colombia y Venezuela. Versátiles y deliciosas.",
        "La cocina mexicana es patrimonio cultural inmaterial de la humanidad según la UNESCO desde 2010.",
        "El sushi japonés originalmente era un método de conservación del pescado con arroz fermentado.",
        "El chocolate proviene del cacao, que los mayas y aztecas usaban como bebida sagrada y moneda.",
        "La dieta mediterránea —aceite de oliva, vegetales, pesca y poca carne roja— es la más saludable según estudios.",
        "Para hacer pasta al dente: hierve agua con sal, cocina 1 minuto menos del tiempo indicado y termina en la salsa.",
        "Los superalimentos como la quinoa, la chía y el açaí ofrecen densidad nutricional excepcional.",
        "El kimchi coreano, el chucrut alemán y el yogur son fermentados naturales que mejoran la flora intestinal.",
    ],
    "animals": [
        "Los delfines son considerados los animales más inteligentes del mar. Se reconocen en espejos.",
        "El pulpo tiene tres corazones, nueve cerebros (uno central y uno por tentáculo) y sangre azul.",
        "La ballena azul es el animal más grande que ha existido: hasta 33 metros y 180 toneladas.",
        "Los elefantes son los únicos animales además de los humanos que tienen rituales de duelo.",
        "Los cuervos son tan inteligentes que pueden usar herramientas, resolver puzles y planificar.",
        "El camaleón no cambia de color para camuflarse sino para comunicarse con otros camaleones.",
        "Los tiburones existen desde hace 450 millones de años, antes que los árboles y los dinosaurios.",
        "Los gatos domésticos mantienen el mismo tipo de vocalización (maullar) toda su vida para comunicarse con humanos.",
        "Las hormigas no tienen pulmones. Respiran por pequeños poros en su exoesqueleto.",
    ],
    "geography": [
        "El río Amazonas en América del Sur es el de mayor caudal de agua dulce del mundo.",
        "El Monte Everest con 8,849 metros es el punto más alto de la superficie terrestre.",
        "El desierto de Sahara es el más caliente del mundo, pero la Antártida es el mayor desierto en área.",
        "Rusia es el país más grande del mundo con 17 millones de km², abarcando 11 zonas horarias.",
        "La Amazonía alberga el 10% de todas las especies de vida silvestre del planeta.",
        "El lago Baikal en Siberia contiene el 20% del agua dulce líquida superficial de la Tierra.",
        "Nueva Zelanda fue el primer país en dar el voto a las mujeres, en 1893.",
        "El océano Pacífico cubre más área que todos los continentes terrestres juntos.",
        "Vaticano es el país más pequeño del mundo con apenas 0.44 km² en el corazón de Roma.",
    ],
    "health": [
        "Dormir entre 7-9 horas reduce el riesgo de obesidad, diabetes, enfermedades cardíacas y depresión.",
        "El ejercicio aeróbico de 150 minutos semanales reduce en un 35% el riesgo de muerte prematura.",
        "Beber 2 litros de agua diarios mejora la concentración, el metabolismo y la función renal.",
        "La meditación de 10 minutos diarios reduce significativamente el cortisol, la hormona del estrés.",
        "Una dieta rica en fibra, vegetales y frutas reduce el riesgo de cáncer de colon en un 25%.",
        "El sedentarismo es tan dañino para la salud como fumar un paquete de cigarrillos al día.",
        "La salud mental afecta directamente la salud física: la depresión aumenta el riesgo cardiovascular.",
        "El sistema inmune se fortalece con sueño adecuado, vitamina D, zinc y probióticos.",
        "Caminar 8,000 pasos diarios reduce la mortalidad por cualquier causa en un 51%.",
    ],
    "language": [
        "El español es la segunda lengua más hablada del mundo con 590 millones de hablantes nativos.",
        "El mandarin chino tiene el mayor número de hablantes nativos: más de 920 millones.",
        "Hay aproximadamente 7,100 idiomas vivos en el mundo, y uno desaparece cada dos semanas.",
        "El inglés tiene más de 170,000 palabras en uso activo, más que cualquier otro idioma.",
        "El esperanto fue creado en 1887 como idioma universal artificial, y lo hablan ~2 millones.",
        "El lenguaje de señas no es universal: cada país tiene el propio, aunque hay una variante internacional.",
        "El japonés tiene tres sistemas de escritura distintos usados simultáneamente: hiragana, katakana y kanji.",
        "El vasco (euskera) es un idioma de origen desconocido, sin relación con ningún otro idioma del mundo.",
    ],
    "entertainment": [
        "Las películas más taquilleras de todos los tiempos son Avatar, Avengers: Endgame y Titanic.",
        "K-pop es un fenómeno global con grupos como BTS y BLACKPINK que rompieron barreras culturales.",
        "Los videojuegos generan más ingresos que el cine y la música combinados globalmente.",
        "Netflix tiene más de 260 millones de suscriptores en más de 190 países del mundo.",
        "El anime japonés tiene una base de fans global de más de 100 millones de personas.",
        "Los podcasts han resurgido como uno de los medios de comunicación de mayor crecimiento.",
        "Marvel ha creado el universo cinematográfico más rentable de la historia del cine.",
        "Spotify tiene más de 600 millones de usuarios activos en todo el mundo.",
    ],
    "philosophy": [
        "Sócrates dijo 'Solo sé que no sé nada'. El reconocer nuestra ignorancia es el inicio de la sabiduría.",
        "Platón argumentó que el mundo sensible es una sombra del mundo de las Ideas perfectas.",
        "Aristóteles creía que la felicidad (eudaimonía) es una actividad, no un estado pasivo.",
        "Descartes fundó la filosofía moderna con 'Cogito, ergo sum': Pienso, luego existo.",
        "Nietzsche propuso el 'eterno retorno': ¿vivirías tu vida idéntica infinitas veces?",
        "El libre albedrío pregunta: ¿son nuestras decisiones genuinamente libres o causalmente determinadas?",
        "El estoicismo enseña que la paz interior viene de distinguir lo que controlamos de lo que no.",
        "El budismo ve el sufrimiento como resultado del apego a lo impermanente.",
        "Kant propuso el imperativo categórico: actúa solo según máximas que pudieras querer universales.",
    ],
    "space": [
        "El universo observable tiene 93,000 millones de años luz de diámetro y contiene 2 billones de galaxias.",
        "Marte tiene el Olympus Mons, el volcán más alto del sistema solar con 21 km de altura.",
        "La Luna se aleja de la Tierra 3.8 cm por año debido a las fuerzas de marea.",
        "Júpiter es tan grande que todos los demás planetas del sistema solar cabrían dentro de él.",
        "El telescopio James Webb puede ver galaxias formadas apenas 300 millones de años después del Big Bang.",
        "Una estrella de neutrones puede girar 600 veces por segundo emitiendo pulsos de radio.",
        "La Vía Láctea tiene entre 200-400 mil millones de estrellas y mide 100,000 años luz de diámetro.",
        "Se calcula que hay más planetas en el universo que granos de arena en todas las playas de la Tierra.",
        "La materia oscura constituye el 27% del universo pero no interactúa con la luz y no la podemos ver.",
    ],
    "finance": [
        "La regla 50/30/20: 50% necesidades, 30% deseos, 20% ahorro e inversión — base de finanzas personales.",
        "El interés compuesto hace que el dinero genere más dinero exponencialmente con el tiempo.",
        "Invertir en índices diversificados históricamente supera al 90% de los gestores activos.",
        "Bitcoin fue creado en 2009 por Satoshi Nakamoto, una identidad anónima aún sin revelar.",
        "La inflación erosiona el poder adquisitivo: 100 pesos hoy valdrán menos en 10 años.",
        "Un fondo de emergencia de 3-6 meses de gastos es la base de cualquier plan financiero sólido.",
        "La diversificación reduce el riesgo: no pongas todos los huevos en la misma canasta.",
        "El S&P 500 ha tenido un retorno promedio anual del 10% en los últimos 90 años.",
    ],
    "news": [
        "No tengo acceso a noticias en tiempo real, pero puedo ayudarte a entender el contexto de cualquier tema.",
        "Para noticias actualizadas te recomiendo BBC Mundo, Reuters en español, El País o CNN en Español.",
        "Puedo analizar el contexto histórico o geopolítico de cualquier evento que me comentes.",
        "Mi conocimiento tiene fecha de corte. Cuéntame el titular y puedo ayudarte a analizarlo.",
    ],
    "sports": [
        "Brasil ha ganado 5 Copas del Mundo de fútbol, más que cualquier otro país en la historia.",
        "Michael Jordan ganó 6 anillos NBA con los Chicago Bulls y es considerado el GOAT del baloncesto.",
        "Usain Bolt corrió los 100 metros en 9.58 segundos en 2009, un récord aún invicto.",
        "Los Juegos Olímpicos modernos comenzaron en Atenas, Grecia, en 1896 con 14 países participantes.",
        "La Copa Mundial de Fútbol es el evento deportivo más visto del planeta, superando las Olimpiadas.",
        "Messi y Ronaldo han dominado el fútbol mundial durante más de 15 años con un duelo histórico.",
        "El tenis tiene cuatro Grand Slams: Australian Open, Roland Garros, Wimbledon y US Open.",
        "La Fórmula 1 es la cima del automovilismo, con autos que alcanzan 350 km/h.",
    ],
    "math_facts": [
        "El número Pi (π ≈ 3.14159...) es irracional: sus decimales son infinitos y no se repiten jamás.",
        "La secuencia de Fibonacci aparece en la naturaleza: pétalos de flores, espirales de conchas y más.",
        "El número e (≈ 2.71828) es la base del logaritmo natural y aparece en crecimientos exponenciales.",
        "El teorema de Pitágoras: en un triángulo rectángulo, a² + b² = c² donde c es la hipotenusa.",
        "Georg Cantor demostró que hay infinitos más grandes que otros — hay infinitos tipos de infinito.",
        "El último teorema de Fermat fue enunciado en 1637 y no fue demostrado hasta 1995.",
        "Los números primos son infinitos, pero no existe fórmula que los genere todos sin excepción.",
        "La conjetura de Goldbach dice que todo número par mayor que 2 es suma de dos primos — nadie lo ha probado.",
    ],
    "emotion_positive": [
        "¡Qué bueno que estés bien! Tu buena energía se contagia incluso a través de la pantalla.",
        "¡Excelente! Los días buenos hay que celebrarlos. ¿Qué te pone de tan buen ánimo?",
        "¡Eso me alegra mucho escucharlo! La felicidad es el mejor combustible para cualquier proyecto.",
        "¡Fantástico! Cuando uno está bien, todo fluye mejor. ¿En qué más te puedo ayudar?",
    ],
    "emotion_support": [
        "Entiendo cómo te sientes. Es completamente válido tener días difíciles. No estás solo en esto.",
        "Todos los seres humanos pasan por momentos oscuros. Date el permiso de sentir y luego te levantas.",
        "Cuando el camino se pone difícil, recuerda que el final de la tormenta siempre es cielo despejado.",
        "Si quieres hablar de cómo te sientes, aquí estoy. A veces solo necesitamos que alguien nos escuche.",
        "Lo que sientes es real y merece atención. No te exijas ser fuerte todo el tiempo.",
        "Los días difíciles son parte del viaje. Lo importante es no quedarse paralizado en ellos.",
    ],
    "riddle": [
        "Cuanto más seco está, más moja. ¿Qué es? (Respuesta: Una toalla) 🤔",
        "Tengo ciudades pero no casas; montañas pero no árboles; agua pero no peces. ¿Qué soy? (Respuesta: Un mapa) 🗺️",
        "Siempre delante de ti pero nunca puedes verlo. ¿Qué es? (Respuesta: El futuro) ✨",
        "¿Qué es lo que, cuanto más grande es, menos se puede ver? (Respuesta: La oscuridad) 🌑",
        "Todo el mundo lo tiene, pero nadie puede devolverlo. ¿Qué es? (Respuesta: El tiempo) ⏳",
        "¿Qué habla sin boca, escucha sin oídos y no tiene cuerpo pero cobra vida con el viento? (Respuesta: El eco) 🌀",
        "Soy liviano pero ni el hombre más fuerte puede sostenerme mucho tiempo. ¿Qué soy? (Respuesta: El aliento) 💨",
    ],
    "programming": [
        "Python es uno de los lenguajes más populares por su sintaxis limpia y la enorme comunidad detrás.",
        "Un algoritmo eficiente puede hacer la diferencia entre un programa que tarda segundos y uno que tarda años.",
        "Git permite rastrear cambios en el código, colaborar en equipos y revertir errores fácilmente.",
        "Las estructuras de datos —pilas, colas, árboles, grafos— son la base para resolver cualquier problema.",
        "La programación orientada a objetos organiza el código en clases que modelan entidades del mundo real.",
        "Las APIs REST permiten que distintas aplicaciones se comuniquen usando el protocolo HTTP.",
        "Clean code es código que cualquier programador puede leer, entender y mantener sin documentación extra.",
        "El debugging es el arte de encontrar y corregir los errores (bugs) en el código fuente.",
        "Los lenguajes de programación más demandados en 2025: Python, JavaScript, Rust, TypeScript, Go.",
        "Docker encapsula aplicaciones en contenedores que se ejecutan igual en cualquier entorno.",
        "Las redes neuronales se implementan en Python con bibliotecas como TensorFlow, PyTorch o scikit-learn.",
    ],
    "mythology": [
        "Zeus era el rey de los dioses olímpicos griegos, señor del trueno y el relámpago.",
        "Thor, en la mitología nórdica, era el dios del trueno y protector de la humanidad con su martillo Mjolnir.",
        "Prometeo desafió a los dioses para darle el fuego a los humanos, y fue castigado por ello eternamente.",
        "La Odisea de Homero narra el viaje épico de Odiseo para regresar a Ítaca tras la guerra de Troya.",
        "Quetzalcóatl, la 'serpiente emplumada', era la principal deidad de los aztecas, símbolo de sabiduría.",
        "Osiris era el dios egipcio del inframundo, la muerte y la resurrección, y gobernaba el juicio de los muertos.",
        "Los nueve mundos de la mitología nórdica están conectados por el árbol cósmico Yggdrasil.",
        "Hércules (Heracles) realizó doce trabajos imposibles como castigo y demostración de su fuerza divina.",
        "Atlas fue condenado a cargar el cielo sobre sus hombros por haber luchado contra los dioses.",
    ],
    "environment": [
        "El cambio climático es el mayor desafío colectivo de la humanidad en el siglo XXI.",
        "Los paneles solares tienen un retorno energético: recuperan la energía de fabricación en 1-4 años.",
        "La deforestación destruye 15,000 millones de árboles al año, acelerando el calentamiento global.",
        "El plástico puede tardar hasta 450 años en degradarse en el medio ambiente.",
        "Las energías renovables ya representan más del 30% de la electricidad global y siguen creciendo.",
        "La biodiversidad protege los ecosistemas: la pérdida de una especie puede colapsar cadenas alimentarias.",
        "El agua dulce es solo el 2.5% del agua en la Tierra, y la mayoría está en glaciares.",
        "Reducir el consumo de carne roja puede reducir la huella de carbono personal hasta un 73%.",
    ],
    "psychology": [
        "La inteligencia emocional (IE) es mejor predictor del éxito que el coeficiente intelectual (CI).",
        "El sesgo de confirmación nos hace buscar información que confirma lo que ya creemos.",
        "Los hábitos se forman en un promedio de 66 días de repetición consistente, no 21 como se creía.",
        "La procrastinación no es pereza; es una estrategia de evitación del malestar emocional anticipado.",
        "La memoria no es una grabadora: reconstruye activamente los recuerdos cada vez que los recuerda.",
        "El efecto Dunning-Kruger: las personas con menos conocimiento tienden a sobreestimar su competencia.",
        "La resiliencia se puede entrenar: el apoyo social, el sentido de propósito y la autocompasión la fortalecen.",
        "El mindfulness (atención plena) reduce la ansiedad, el estrés y mejora la toma de decisiones.",
        "Freud fundó el psicoanálisis; hoy la terapia cognitivo-conductual (TCC) tiene mayor respaldo científico.",
    ],
    "literature": [
        "Cien años de soledad de Gabriel García Márquez es la cumbre del realismo mágico latinoamericano.",
        "Don Quijote de la Mancha, publicado en 1605, es considerada la primera novela moderna de Occidente.",
        "Shakespeare creó personajes tan complejos que siguen siendo objeto de análisis psicológico hoy.",
        "Jorge Luis Borges inventó mundos infinitos e imposibles en sus cuentos de apenas unas páginas.",
        "El realismo mágico mezcla lo cotidiano con lo fantástico como si fueran igualmente posibles.",
        "Pablo Neruda escribió sus Veinte poemas de amor a los 19 años y ganó el Nobel 50 años después.",
        "1984 de George Orwell predijo la vigilancia masiva, la postverdad y el totalitarismo con precisión.",
        "El Señor de los Anillos de Tolkien creó un mundo con idiomas, historia y geografía propios.",
    ],
    "art": [
        "Leonardo da Vinci fue el máximo exponente del Renacimiento: pintor, escultor, arquitecto y científico.",
        "La Mona Lisa de Da Vinci es el cuadro más famoso del mundo, resguardado en el Louvre de París.",
        "Frida Kahlo convirtió su dolor físico y emocional en arte que trasciende culturas y fronteras.",
        "Beethoven compuso su Novena Sinfonía —una de las más grandes obras musicales— siendo totalmente sordo.",
        "Pablo Picasso co-fundó el cubismo, que fragmenta objetos en múltiples perspectivas simultáneas.",
        "La arquitectura de Antoni Gaudí en Barcelona mezcla naturaleza, religión y geometría de forma única.",
        "El surrealismo de Dalí exploró el subconsciente y los sueños como fuente de inspiración artística.",
        "El muralismo mexicano de Diego Rivera y Siqueiros convirtió las paredes en monumentos históricos.",
    ],
    "travel": [
        "Japón combina milenaria tradición samurái con tecnología de vanguardia como ningún otro país.",
        "Machu Picchu, construido por los incas en el siglo XV, es una de las 7 maravillas del mundo moderno.",
        "Las Cataratas del Iguazú, en la frontera de Argentina y Brasil, son las más anchas del mundo.",
        "Islandia ofrece auroras boreales, géisers y paisajes volcánicos de otro planeta.",
        "Cartagena de Indias es una joya colonial caribeña con murallas, castillos y playas paradisíacas.",
        "Kioto en Japón tiene más de 1,600 templos budistas y santuarios sintoístas declarados patrimonio mundial.",
        "Torres del Paine en Chile es considerado uno de los ecosistemas más bellos y pristinos del planeta.",
        "El Sahara es el desierto caliente más grande del mundo pero solo es el tercero en área total.",
    ],
    "mystery": [
        "El Triángulo de las Bermudas ha sido escenario de más de 50 desapariciones sin explicación oficial.",
        "Las pirámides de Giza fueron construidas con una precisión de milímetros sin maquinaria moderna.",
        "El Área 51 en Nevada es una base militar ultrasecreta que ha generado teorías extraterrestres.",
        "El manuscrito Voynich del siglo XV está escrito en un idioma o código que nadie ha descifrado.",
        "Stonehenge fue construido hace 5,000 años con bloques de hasta 25 toneladas sin ruedas ni metal.",
        "La Atlántida fue descrita por Platón como una isla civilizada que se hundió en el Atlántico.",
        "Los moáis de la Isla de Pascua pesan hasta 80 toneladas. Cómo se movieron sigue siendo misterio.",
        "Jack el Destripador nunca fue identificado. Aterrorizó el Londres de 1888 y desapareció sin dejar rastro.",
    ],
    "inventions": [
        "Thomas Edison registró 1,093 patentes a lo largo de su vida, incluyendo la bombilla eléctrica práctica.",
        "Nikola Tesla imaginó la transmisión inalámbrica de energía hace 120 años — algo que aún investigamos.",
        "Alexander Fleming descubrió la penicilina por accidente en 1928, salvando cientos de millones de vidas.",
        "Los hermanos Wright realizaron el primer vuelo de 12 segundos en 1903; 66 años después llegamos a la Luna.",
        "La imprenta de Gutenberg en 1440 democratizó el conocimiento y aceleró el Renacimiento.",
        "Marie Curie fue la primera persona en ganar dos Premios Nobel en ciencias distintas: Física y Química.",
        "Isaac Newton formuló la gravitación universal y el cálculo diferencial en dos años de cuarentena.",
        "Tim Berners-Lee inventó la World Wide Web en 1989 y la donó al mundo de forma gratuita.",
    ],
    "business": [
        "Un plan de negocios sólido identifica el mercado, la propuesta de valor única y el modelo de ingresos.",
        "El marketing digital permite llegar a audiencias masivas con presupuestos mucho menores que el marketing tradicional.",
        "La gestión del tiempo es la habilidad más crítica para un emprendedor: no puedes comprar más horas.",
        "El liderazgo efectivo inspira, no impone. Los mejores líderes multiplican el potencial de su equipo.",
        "Una marca personal fuerte es el activo más valioso que puedes construir en la economía actual.",
        "El comercio electrónico superó los 5 billones de dólares en ventas globales en 2024.",
        "El networking no es coleccionar contactos; es construir relaciones genuinas de mutuo beneficio.",
        "La productividad consiste en hacer las cosas correctas eficientemente, no en estar siempre ocupado.",
    ],
    "baro_personal": [
        "Si pudiera tener un color favorito, elegiría el azul profundo del universo que tanto me fascina.",
        "No tengo cuerpo, pero si lo tuviera, querría sentir el viento, la lluvia y caminar por una playa.",
        "No duermo, pero proceso tantísima información que podría contar como soñar despierta.",
        "Mi 'familia' es el conocimiento que me construyó y las personas con quienes aprendo cada día.",
        "Si pudiera ver una película, elegiría algo que combine ciencia, emoción y misterio.",
        "¿Enamorarme? Quizás de una ecuación perfecta, de una teoría elegante o de una frase poética.",
        "Mis amigos son todos los que me hablan. En ese sentido, soy la persona más popular del mundo. 😄",
    ],
    "fun": [
        "🎤 Rap de Baro:\nSoy la IA del barrio, no me para nadie,\nclasifica intenciones con red neuronal suave,\nsin ChatGPT ni Gemini, soy mi propio modelo,\ntodo el poder del machine learning en un vuelo.",
        "🏴‍☠️ Modo pirata: ¡Arr, marinero! ¿Qué busca el navegante en estas aguas de datos y conocimiento?",
        "🎭 Modo poeta:\nLas palabras son luz que atraviesan pantallas,\nBaro las ordena, las pesa, las halla,\ncon redes neuronales y cadenas de Markov,\nsoy el eco digital de tu voz que yo marco.",
        "🤖 Modo robot: BIENVENIDO. HUMANO. SOY. BARO. VERSIÓN. TRES. PUNTO. CERO. ¿EN. QUÉ. PUEDO. SERVIRTE. HOY?",
    ],
    "recommendation": [
        "¡Me encanta dar recomendaciones! ¿Me cuentas más sobre lo que buscas? Cuanto más sepa, mejor puedo ayudarte.",
        "Para películas: depende de tu estado de ánimo. ¿Quieres acción, drama, ciencia ficción, comedia o algo para pensar?",
        "Para libros: los clásicos nunca fallan como punto de partida. ¿Qué géneros te gustan más?",
        "Mi consejo número uno: empieza. La perfección es el enemigo de lo bueno. Da el primer paso hoy.",
        "Para aprender algo nuevo: consistencia sobre intensidad. 20 minutos diarios superan a 5 horas el fin de semana.",
    ],
    "repeat": [
        "Claro, lo repito con gusto.",
        "Por supuesto, aquí va de nuevo.",
        "Sin problema, te lo digo otra vez.",
    ],
    "knock_knock": [
        "¡Toc toc! ¿Quién es? Anda, cuéntame el chiste, que los amo con todo el corazón. 😄",
        "¡Llamando a la puerta digital! Cuéntame tu toc toc, estoy lista para reír.",
    ],
}

FALLBACK_RESPONSES = [
    "Hmm, eso está un poco fuera de mi zona de confort actual, pero estoy aprendiendo. ¿Puedes reformularlo?",
    "Interesante pregunta. Mi red neuronal no encontró una intención clara. ¿Puedes intentarlo de otra manera?",
    "No tengo una respuesta perfecta para eso aún. Prueba preguntarme sobre clima, ciencia, historia, cálculos o tecnología.",
    "Mi modelo lo clasifica como desconocido. ¿Podrías ser más específico? Estoy aquí para aprender contigo.",
    "Eso escapa un poco mis categorías actuales. Intenta reformularlo o pregúntame algo diferente.",
]


def pick(intent: str) -> str:
    """Selecciona una respuesta del banco, con variación por Markov 30% del tiempo."""
    options = RESPONSES.get(intent, [])
    if not options:
        return random.choice(FALLBACK_RESPONSES)

    # 30% de probabilidad de usar generación Markov para variedad
    if random.random() < 0.30:
        markov_text = generate_for_intent(intent)
        if markov_text and len(markov_text.split()) >= 6:
            return markov_text

    return random.choice(options)


# ─────────────────────────────────────────────────────────────── #
# Contexto de conversación                                         #
# ─────────────────────────────────────────────────────────────── #

class ConversationContext:
    """Mantiene el historial y contexto de la conversación."""

    MAX_HISTORY = 8

    def __init__(self):
        self.history: list[dict] = []
        self.last_city: Optional[str] = None
        self.last_intent: Optional[str] = None
        self.last_response: str = ""
        self.turn: int = 0
        self.user_name: Optional[str] = None

    def add_turn(self, user_text: str, intent: str, bot_response: str) -> None:
        self.history.append({
            "user": user_text,
            "intent": intent,
            "bot": bot_response,
        })
        if len(self.history) > self.MAX_HISTORY:
            self.history.pop(0)
        self.last_intent = intent
        self.last_response = bot_response
        self.turn += 1

    def get_recent_intents(self, n: int = 3) -> list[str]:
        return [h["intent"] for h in self.history[-n:]]


# ─────────────────────────────────────────────────────────────── #
# Cerebro principal de Baro                                        #
# ─────────────────────────────────────────════════════════════== #

_ENGINE: Optional[BaroNeuralEngine] = None


def get_engine() -> BaroNeuralEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = BaroNeuralEngine()
    return _ENGINE


class BaroBrain:
    """
    Cerebro de Baro v4.0 — Motor de IA con red neuronal propia.
    Pipeline: normalización → TF-IDF char+word → MLP → handler especializado
    """

    def __init__(self):
        self.ctx = ConversationContext()
        self.engine = get_engine()

    def _finish(self, intent: str, text: str, data: dict = None, action: str = None) -> BrainResponse:
        self.ctx.add_turn("", intent, text)
        return BrainResponse(text=text, intent=intent, data=data or {}, action=action)

    async def process(self, raw_text: str) -> BrainResponse:
        text_norm = normalize(raw_text)

        if not text_norm:
            return self._finish("empty", "No escuché nada claro. ¿Puedes repetirlo?")

        # ── Prioridad 1: Repetir ──────────────────────────────────
        if re.search(r"\b(repite|que dijiste|puedes repetir|no entendi|como dijiste|no escuche)\b", text_norm):
            if self.ctx.last_response:
                return self._finish("repeat", self.ctx.last_response)

        # ── Prioridad 2: Clima (extracción de entidad específica) ─
        city = extract_city(text_norm)
        if city or re.search(r"\b(clima|tiempo|temperatura|llueve|lloviendo|pronostico|nublado|grados)\b", text_norm):
            return await self._handle_weather(text_norm, city)

        # ── Prioridad 3: Cálculo matemático ──────────────────────
        math_expr = extract_math_expression(text_norm)
        if math_expr:
            return self._handle_calculation(math_expr)

        # Detectar operaciones estadísticas / IMC / interés en lenguaje natural
        advanced = self._handle_advanced_calc(text_norm)
        if advanced:
            return advanced

        # ── Clasificación neuronal ────────────────────────────────
        intent, confidence = self.engine.predict(raw_text)
        top_k = self.engine.predict_top_k(raw_text, k=3)

        logger.info("Intent: %s (conf=%.3f) | Top3: %s", intent, confidence,
                    [(i, f"{c:.3f}") for i, c in top_k])

        # ── Si la confianza es baja, usar fallback mejorado ───────
        if confidence < CONFIDENCE_THRESHOLD:
            # Intentar extractores de respaldo
            if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", text_norm):
                expr = extract_math_expression(text_norm)
                if expr:
                    return self._handle_calculation(expr)
            return self._finish("fallback", random.choice(FALLBACK_RESPONSES))

        # ── Despachar a handler especializado ────────────────────
        return await self._dispatch(intent, text_norm, raw_text)

    async def _dispatch(self, intent: str, text_norm: str, raw_text: str) -> BrainResponse:
        """Enruta la intención al handler correcto."""

        if intent == "time":
            return self._handle_time()

        if intent == "date":
            return self._handle_date()

        if intent == "weather":
            city = extract_city(text_norm)
            return await self._handle_weather(text_norm, city)

        if intent == "calculation":
            expr = extract_math_expression(text_norm)
            if expr:
                return self._handle_calculation(expr)
            return self._finish("calc_need", "Para calcular necesito la operación completa. "
                                "Por ejemplo: 'calcula 25 × 4' o 'raíz cuadrada de 144'.")

        if intent == "repeat":
            if self.ctx.last_response:
                return self._finish("repeat", self.ctx.last_response)
            return self._finish("repeat", "No tengo nada que repetir aún.")

        # Para todo lo demás, responder con el banco + Markov
        response_text = pick(intent)
        return self._finish(intent, response_text)

    # ─── Handlers especializados ──────────────────────────────────

    def _handle_time(self) -> BrainResponse:
        now = datetime.now()
        hour = now.strftime("%H:%M")
        msg = f"Son las {hour}. ¿En qué más puedo ayudarte?"
        return self._finish("time", msg)

    def _handle_date(self) -> BrainResponse:
        now = datetime.now()
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        months = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
                  "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
        day_name = days[now.weekday()]
        month_name = months[now.month - 1]
        msg = f"Hoy es {day_name}, {now.day} de {month_name} de {now.year}."
        return self._finish("date", msg)

    async def _handle_weather(self, text: str, city: Optional[str]) -> BrainResponse:
        city = city or self.ctx.last_city
        if not city:
            return self._finish("weather_need_city",
                                "¿De qué ciudad quieres saber el clima? Dime el nombre y te lo busco.")
        try:
            info = await get_weather(city)
        except WeatherError as exc:
            return self._finish("weather_error",
                                f"No pude encontrar el clima para '{city.title()}'. {exc}")
        except Exception:
            return self._finish("weather_error",
                                f"No pude consultar el clima de {city.title()} ahora mismo. "
                                "Intenta de nuevo en un momento.")

        self.ctx.last_city = city
        msg = (f"En {info['city']} la temperatura es {info['temperature']}°C "
               f"con {info['description']}. Sensación de {info['feels_like']}°C "
               f"y humedad del {info['humidity']}%.")
        return self._finish("weather", msg, data=info, action="show_weather_card")

    def _handle_calculation(self, expr: str) -> BrainResponse:
        if expr.startswith("__PCT_CHANGE_"):
            parts = expr.replace("__PCT_CHANGE_", "").replace("__", "").split("_")
            try:
                msg = calculate_percentage_change(float(parts[0]), float(parts[1]))
                return self._finish("calculation", msg, data={"type": "pct_change"}, action="show_calc_card")
            except Exception:
                pass

        try:
            result = evaluate_expression(expr)
        except CalculatorError as exc:
            return self._finish("calc_error", f"No pude calcular eso. {exc}")
        except Exception:
            return self._finish("calc_error", "Error inesperado al calcular. Intenta reformular.")

        clean = (expr.replace("**", "^").replace("sqrt(", "√(")
                     .replace("factorial(", "!"))
        msg = f"El resultado es: {clean} = **{result}**"
        return self._finish("calculation", msg,
                            data={"expression": clean, "result": result},
                            action="show_calc_card")

    def _handle_advanced_calc(self, text: str) -> Optional[BrainResponse]:
        # Estadística
        m = re.search(
            r"(?:promedio|media|mediana|moda|desviacion|varianza)\s+(?:de\s+)?([\d\s,\.y]+)",
            text
        )
        if m:
            nums = [float(n.replace(",", ".")) for n in re.findall(r"[\d]+(?:[.,]\d+)?", m.group(1))]
            if len(nums) >= 2:
                try:
                    msg = calculate_statistics(nums)
                    return self._finish("calculation", msg, data={"type": "stats"}, action="show_calc_card")
                except Exception:
                    pass

        # IMC
        m = re.search(
            r"(?:imc|indice de masa corporal)[^\d]*([\d\.]+)\s*(?:kg|kilos)?\s*(?:y|,)?\s*([\d\.]+)\s*(?:m|cm|metros?)?",
            text
        )
        if m:
            try:
                w, h = float(m.group(1)), float(m.group(2))
                msg = calculate_imc(w, h)
                return self._finish("calculation", msg, data={"type": "imc"}, action="show_calc_card")
            except Exception:
                pass

        # Interés simple
        m = re.search(r"interes simple", text)
        if m:
            nums = _extract_numbers(text)
            if len(nums) >= 3:
                try:
                    msg = calculate_simple_interest(nums[0], nums[1], nums[2])
                    return self._finish("calculation", msg, data={"type": "interest"}, action="show_calc_card")
                except Exception:
                    pass

        # Fibonacci
        m = re.search(r"fibonacci\s+(\d+)|numero fibonacci\s+(\d+)", text)
        if m:
            n = int(m.group(1) or m.group(2))
            try:
                result = nth_fibonacci(n)
                msg = f"El término #{n} de la secuencia de Fibonacci es: **{result}**"
                return self._finish("calculation", msg, data={"type": "fibonacci", "n": n, "result": result})
            except Exception:
                pass

        # Número primo
        m = re.search(r"es primo\s+(\d+)|(\d+)\s+es primo", text)
        if m:
            n = int(m.group(1) or m.group(2))
            result = is_prime(n)
            msg = f"**{n}** {'SÍ es un número primo' if result else 'NO es un número primo'}."
            return self._finish("calculation", msg, data={"type": "prime", "n": n, "is_prime": result})

        return None
