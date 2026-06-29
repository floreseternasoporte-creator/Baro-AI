# -*- coding: utf-8 -*-
"""
markov_gen.py — Generador de texto por Cadenas de Markov.
Genera variaciones de respuestas basadas en el corpus de entrenamiento.
Permite que Baro no repita siempre las mismas frases exactas.
"""

from __future__ import annotations
import random
import re
from collections import defaultdict
from typing import Optional


class MarkovGenerator:
    """
    Generador de texto por cadenas de Markov de orden N.
    Aprende de un corpus de texto y puede generar nuevas frases
    que siguen los patrones estadísticos del corpus.
    """

    def __init__(self, order: int = 2):
        self.order = order
        self.chains: dict[tuple, list[str]] = defaultdict(list)
        self.starters: list[tuple] = []
        self.trained = False

    def train(self, corpus: list[str]) -> None:
        """Entrena la cadena de Markov con una lista de frases."""
        self.chains.clear()
        self.starters.clear()

        for text in corpus:
            tokens = self._tokenize(text)
            if len(tokens) < self.order + 1:
                continue

            # Registrar inicio de frase
            starter = tuple(tokens[:self.order])
            self.starters.append(starter)

            # Construir cadena
            for i in range(len(tokens) - self.order):
                key = tuple(tokens[i:i + self.order])
                next_token = tokens[i + self.order]
                self.chains[key].append(next_token)

        self.trained = bool(self.starters)

    def generate(self, max_tokens: int = 40, seed: Optional[tuple] = None) -> str:
        """Genera una nueva frase usando la cadena de Markov."""
        if not self.trained or not self.starters:
            return ""

        # Elegir inicio
        if seed and seed in self.chains:
            current = seed
        else:
            current = random.choice(self.starters)

        result = list(current)

        for _ in range(max_tokens - self.order):
            if current not in self.chains:
                break
            next_token = random.choice(self.chains[current])
            result.append(next_token)
            current = tuple(result[-self.order:])

            # Terminar en puntuación natural
            if next_token in {'.', '!', '?', '…'} and len(result) >= 8:
                break

        return " ".join(result)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenización simple por palabras y puntuación."""
        text = text.strip()
        tokens = re.findall(r"\w+|[.!?…,;]", text, re.UNICODE)
        return tokens


# ─────────────────────────────────────────────────────────────────────────── #
# Corpus de entrenamiento para el generador Markov por intención              #
# ─────────────────────────────────────────────────────────────────────────── #

MARKOV_CORPUS: dict[str, list[str]] = {
    "greeting": [
        "Hola, estoy lista para ayudarte con lo que necesites hoy.",
        "Qué alegría escucharte, siempre es un placer conversar contigo.",
        "Bienvenido, soy Baro tu asistente personal lista para responder.",
        "Hola de nuevo, aquí estoy esperando tus preguntas.",
        "Gran día para aprender algo nuevo juntos, cuéntame qué necesitas.",
        "Hola, me alegra que hayas llegado, estoy lista para ti.",
        "Qué bueno verte por aquí, Baro al habla para servirte.",
    ],
    "science": [
        "La ciencia es la forma en que los humanos entienden el universo que los rodea.",
        "El universo tiene aproximadamente 13.800 millones de años desde el Big Bang.",
        "La física cuántica describe el comportamiento de partículas a escala subatómica.",
        "El ADN contiene toda la información genética de un organismo vivo.",
        "La velocidad de la luz es de 299.792 kilómetros por segundo en el vacío.",
        "La energía nuclear libera millones de veces más energía que los combustibles fósiles.",
        "La gravedad es la fuerza que mantiene los planetas en órbita alrededor del Sol.",
        "Las células son la unidad básica de la vida en todos los organismos conocidos.",
        "El cerebro humano tiene aproximadamente 86 mil millones de neuronas.",
    ],
    "technology": [
        "La inteligencia artificial está transformando todos los sectores de la economía mundial.",
        "El machine learning permite a las máquinas aprender patrones sin ser programadas explícitamente.",
        "Las redes neuronales artificiales se inspiran en el funcionamiento del cerebro humano.",
        "La computación cuántica promete resolver problemas imposibles para los computadores actuales.",
        "El internet conecta a más de cinco mil millones de personas en todo el mundo.",
        "La realidad virtual crea entornos inmersivos que simulan la experiencia física.",
        "Los chips semiconductores son el corazón de todos los dispositivos electrónicos modernos.",
        "El blockchain es una base de datos distribuida e inmutable que garantiza transparencia.",
        "La ciberseguridad protege sistemas, redes y datos de ataques maliciosos digitales.",
    ],
    "motivation": [
        "El éxito es la suma de pequeños esfuerzos repetidos día tras día.",
        "Los grandes logros comienzan con la decisión de intentarlo una vez más.",
        "Cada caída es una lección disfrazada de fracaso, levántate y sigue adelante.",
        "Tu potencial no tiene límites, solo tus creencias sobre él los imponen.",
        "La perseverancia es el puente entre los sueños y la realidad que deseas.",
        "No importa qué tan lento vayas, siempre y cuando no te detengas.",
        "El momento perfecto para empezar es ahora mismo, no mañana ni después.",
        "La confianza en uno mismo es el primer secreto del éxito en cualquier área.",
        "Cada día es una oportunidad nueva de ser mejor que ayer.",
    ],
    "history": [
        "La historia es la maestra de la vida según el filósofo romano Cicerón.",
        "La Segunda Guerra Mundial fue el conflicto armado más devastador de la historia humana.",
        "Las civilizaciones antiguas dejaron un legado cultural que aún moldea el mundo moderno.",
        "La Revolución Francesa de 1789 cambió para siempre el concepto de gobierno y derechos.",
        "El Imperio Romano dominó gran parte del mundo occidental durante siglos de poder.",
        "Los mayas desarrollaron uno de los sistemas astronómicos más precisos del mundo antiguo.",
        "La Revolución Industrial transformó las sociedades agrarias en economías industriales modernas.",
        "Simón Bolívar liberó varios países latinoamericanos del dominio colonial español.",
    ],
    "philosophy": [
        "La filosofía busca respuestas a las preguntas más fundamentales sobre la existencia humana.",
        "Sócrates enseñó que el autoconocimiento es el inicio de toda sabiduría verdadera.",
        "Platón argumentó que la realidad que percibimos es solo una sombra del mundo ideal.",
        "El libre albedrío pregunta si nuestras decisiones son realmente nuestras o determinadas.",
        "La ética estudia qué es el bien y cómo debemos actuar en el mundo.",
        "El existencialismo afirma que la existencia precede a la esencia del ser humano.",
        "La conciencia humana sigue siendo uno de los mayores misterios de la filosofía.",
        "La búsqueda del significado de la vida es universal en toda cultura y época.",
    ],
    "space": [
        "El universo se está expandiendo a una velocidad cada vez mayor desde el Big Bang.",
        "Marte tiene el volcán más alto del sistema solar llamado Olympus Mons.",
        "La Luna se aleja de la Tierra aproximadamente 3.8 centímetros cada año.",
        "Júpiter es tan grande que todos los planetas del sistema solar cabrían dentro de él.",
        "El telescopio James Webb puede observar galaxias a más de 13 mil millones de años luz.",
        "Hay más estrellas en el universo observable que granos de arena en todas las playas.",
        "La Vía Láctea tiene entre 200 y 400 mil millones de estrellas en su interior.",
        "Los agujeros negros supermasivos existen en el centro de la mayoría de galaxias.",
    ],
    "health": [
        "La salud es el mayor activo que tienes, cuídala como tu bien más preciado.",
        "Dormir entre 7 y 9 horas por noche es esencial para la salud física y mental.",
        "El ejercicio aeróbico regular reduce el riesgo de enfermedades cardiovasculares significativamente.",
        "Beber al menos dos litros de agua al día mantiene el metabolismo activo y saludable.",
        "La meditación y el mindfulness reducen el cortisol y mejoran el bienestar mental.",
        "Una dieta variada con frutas, verduras y proteínas es la base de la buena salud.",
        "El estrés crónico puede debilitar el sistema inmunológico y afectar la salud mental.",
        "La salud mental es tan importante como la salud física, nunca la descuides.",
    ],
    "programming": [
        "Python es uno de los lenguajes más populares del mundo por su sintaxis clara y simple.",
        "Un algoritmo es un conjunto de instrucciones definidas para resolver un problema específico.",
        "La programación orientada a objetos organiza el código en clases y objetos reutilizables.",
        "Git es el sistema de control de versiones más utilizado en el desarrollo de software.",
        "Las estructuras de datos como pilas, colas y árboles son fundamentales en programación.",
        "El frontend se encarga de lo que el usuario ve, el backend de la lógica del servidor.",
        "Las APIs permiten que diferentes aplicaciones se comuniquen entre sí de forma estándar.",
        "Clean code significa escribir código que sea fácil de leer, mantener y escalar.",
        "Los bucles, condicionales y funciones son los bloques fundamentales de cualquier programa.",
    ],
    "mythology": [
        "Zeus era el rey de los dioses griegos y gobernaba desde el monte Olimpo.",
        "Thor, el dios nórdico del trueno, empuñaba el poderoso martillo llamado Mjolnir.",
        "Prometeo robó el fuego de los dioses y se lo entregó a la humanidad como regalo.",
        "La Odisea narra las aventuras de Odiseo en su largo regreso a casa tras la guerra.",
        "Hades gobernaba el inframundo donde residían las almas de los muertos en Grecia.",
        "Quetzalcóatl era la serpiente emplumada, deidad principal de la mitología azteca.",
        "Ra era el dios sol en el panteón egipcio y se consideraba el creador del mundo.",
        "El Valhalla era el paraíso de los guerreros nórdicos caídos en batalla honorable.",
    ],
    "environment": [
        "El cambio climático es el mayor desafío ambiental que enfrenta la humanidad hoy.",
        "Las energías renovables como la solar y eólica son clave para un futuro sostenible.",
        "La deforestación destruye hábitats naturales y acelera el calentamiento global.",
        "El plástico en los océanos afecta a millones de animales marinos cada año.",
        "Reciclar correctamente reduce significativamente la cantidad de residuos en vertederos.",
        "La biodiversidad es el seguro de vida del planeta, cada especie cumple un rol.",
        "El agua dulce es un recurso escaso que debemos proteger y conservar.",
        "Reducir la huella de carbono personal contribuye a mitigar el cambio climático.",
    ],
    "psychology": [
        "La psicología estudia la mente, el comportamiento y los procesos mentales humanos.",
        "La inteligencia emocional es la capacidad de reconocer y gestionar las propias emociones.",
        "Los sesgos cognitivos son errores sistemáticos en el pensamiento que afectan nuestras decisiones.",
        "La memoria trabaja mediante codificación, almacenamiento y recuperación de información.",
        "El mindfulness consiste en prestar atención plena al momento presente sin juzgar.",
        "La procrastinación es un mecanismo de evitación del malestar asociado a ciertas tareas.",
        "Los hábitos se forman mediante la repetición consistente de comportamientos en el tiempo.",
        "La resiliencia es la capacidad de recuperarse y adaptarse ante situaciones adversas.",
    ],
    "art": [
        "El arte es la expresión más profunda de la experiencia y creatividad humana.",
        "Leonardo da Vinci fue pintor, escultor, científico e inventor del Renacimiento italiano.",
        "Frida Kahlo convirtió su dolor personal en arte universal de gran impacto emocional.",
        "La música de Beethoven sobrevivió el tiempo y su sordera para llegar a nuestros días.",
        "El cubismo de Picasso revolucionó la forma de ver y representar la realidad en pintura.",
        "La arquitectura es la síntesis de arte, funcionalidad y comprensión del espacio humano.",
        "El surrealismo exploró el subconsciente y los sueños como fuente de inspiración artística.",
    ],
    "literature": [
        "Cien años de soledad de García Márquez es la obra cumbre del realismo mágico latinoamericano.",
        "Don Quijote de la Mancha es considerada la primera novela moderna de la literatura universal.",
        "Shakespeare escribió 37 obras de teatro que siguen siendo representadas en todo el mundo.",
        "Pablo Neruda ganó el Nobel de Literatura con sus Veinte poemas de amor y una canción desesperada.",
        "Jorge Luis Borges revolucionó la literatura con sus laberintos, espejos e infinitos literarios.",
        "El realismo mágico mezcla elementos fantásticos con la realidad cotidiana de América Latina.",
        "La novela distópica 1984 de Orwell sigue siendo una advertencia vigente sobre el totalitarismo.",
    ],
    "travel": [
        "Viajar amplía la mente, rompe prejuicios y conecta con otras culturas y formas de vida.",
        "Japón combina perfectamente la tradición milenaria con la innovación tecnológica más avanzada.",
        "Machu Picchu en Perú es una de las maravillas del mundo y orgullo de América Latina.",
        "Europa tiene una densidad cultural e histórica incomparable en un territorio relativamente pequeño.",
        "El Caribe ofrece algunas de las playas más hermosas y aguas más cristalinas del planeta.",
        "Viajar con poco presupuesto es posible si planificas bien y priorizas las experiencias.",
        "África es el continente con la mayor biodiversidad y también el más diverso culturalmente.",
    ],
    "mystery": [
        "El Triángulo de las Bermudas ha sido escenario de misteriosas desapariciones de barcos y aviones.",
        "Las pirámides de Egipto siguen siendo un enigma sobre cómo fueron construidas sin maquinaria.",
        "El Área 51 es una base militar secreta que ha generado múltiples teorías sobre extraterrestres.",
        "Stonehenge fue construido hace más de 5000 años con un propósito que aún debatimos.",
        "La Atlántida es una isla legendaria mencionada por Platón cuya existencia no está probada.",
        "Los moáis de la Isla de Pascua son estatuas monumentales cuyo transporte es un misterio.",
        "El manuscrito Voynich es un libro del siglo XV escrito en un idioma aún sin descifrar.",
    ],
    "inventions": [
        "Thomas Edison inventó la bombilla eléctrica práctica y fundó el primer sistema eléctrico.",
        "Nikola Tesla revolucionó el mundo con sus avances en corriente alterna y radio.",
        "Alexander Fleming descubrió la penicilina por accidente y salvó millones de vidas.",
        "Los hermanos Wright realizaron el primer vuelo motorizado de la historia en Kitty Hawk.",
        "Johannes Gutenberg inventó la imprenta de tipos móviles y democratizó el conocimiento.",
        "Marie Curie fue pionera en investigación sobre radiactividad y ganó dos premios Nobel.",
        "Albert Einstein publicó la teoría de la relatividad y transformó la física moderna.",
        "Isaac Newton formuló las leyes del movimiento y la gravitación universal.",
    ],
    "business": [
        "Un plan de negocios sólido es el mapa que guía el camino de un emprendimiento exitoso.",
        "El marketing digital permite llegar a audiencias masivas con presupuestos relativamente pequeños.",
        "El liderazgo efectivo inspira, motiva y saca lo mejor de cada miembro del equipo.",
        "La gestión del tiempo es una habilidad crítica para cualquier empresario o profesional.",
        "El comercio electrónico ha revolucionado la forma en que compramos y vendemos productos.",
        "Una marca personal fuerte abre puertas y crea oportunidades en el mercado laboral.",
        "El networking estratégico puede multiplicar las oportunidades de negocio y colaboración.",
        "La productividad no es hacer más cosas, sino hacer las cosas correctas de manera eficiente.",
    ],
}


def build_markov_models() -> dict[str, MarkovGenerator]:
    """Construye y entrena los modelos Markov para cada intención."""
    models = {}
    for intent, corpus in MARKOV_CORPUS.items():
        gen = MarkovGenerator(order=2)
        gen.train(corpus)
        models[intent] = gen
    return models


# Instancia global entrenada
MARKOV_MODELS = build_markov_models()


def generate_for_intent(intent: str, fallback: str = "") -> str:
    """
    Genera una respuesta usando Markov para la intención dada.
    Si no hay modelo o la generación falla, devuelve el fallback.
    """
    model = MARKOV_MODELS.get(intent)
    if not model or not model.trained:
        return fallback

    generated = model.generate(max_tokens=35)
    if not generated or len(generated.split()) < 5:
        return fallback

    # Capitalizar primera letra
    return generated[0].upper() + generated[1:] if generated else fallback
