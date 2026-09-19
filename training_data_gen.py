# -*- coding: utf-8 -*-
"""
training_data_gen.py — Generador masivo y reproducible del dataset de Baro.

Combina:
  1) Los ejemplos curados existentes (training_data.py actual).
  2) Expansión por variantes (prefijos, sufijos, sinónimos, signos).
  3) Expansión combinatoria por plantillas para las intenciones principales.
  4) Nuevas intenciones generadas desde knowledge.py
     (capitales, química, traducción, refranes, citas, cuentos, poemas,
      recetas, consejos, ejercicio, estudio, definiciones).

Uso:
    python3 training_data_gen.py        # genera training_data.py
    python3 training_data_gen.py --count  # solo muestra el conteo

Es determinista (semilla fija): el mismo dataset siempre.
"""
from __future__ import annotations

import random
import re
import sys

random.seed(20260919)

import knowledge as K

PAIRS: list[tuple[str, str]] = []
SEEN_TEXT: dict[str, str] = {}


def add(text: str, intent: str) -> None:
    text = text.strip()
    if not text:
        return
    key = text.lower()
    # Evitar el mismo texto con dos intenciones distintas (confunde al clasificador)
    if key in SEEN_TEXT:
        return
    SEEN_TEXT[key] = intent
    PAIRS.append((text, intent))


# ── 1) Ejemplos base existentes ──────────────────────────────────
def load_base() -> None:
    # SIEMPRE partir de la semilla original (898 ejemplos curados),
    # nunca del training_data.py generado.
    import training_data_seed as td
    for text, intent in td.TRAINING_DATA:
        add(text, intent)


# ── 2) Variantes de cada ejemplo base ────────────────────────────
PREFIXES = ["oye ", "oye baro ", "baro ", "eh ", "hola baro ",
            "disculpa ", "por favor ", "me puedes decir ", "dime "]
SUFFIXES = [" por favor", " porfa", " porfis", " si puedes",
            " ahora", " hoy", " amigo", " por favorcito"]
SYNONYMS = {
    "dime": ["dime", "cuéntame", "dame", "comparte"],
    "cuéntame": ["cuéntame", "dime", "relátame"],
    "quiero": ["quiero", "quisiera", "me gustaría"],
    "dame": ["dame", "pásame", "comparte"],
    "por favor": ["por favor", "porfa", "si eres tan amable"],
    "gracias": ["gracias", "muchas gracias", "te lo agradezco"],
    "hola": ["hola", "buenas", "hey", "saludos"],
    "adiós": ["adiós", "nos vemos", "hasta luego", "chao"],
}


def expand_variants() -> None:
    base = list(PAIRS)
    for text, intent in base:
        low = text.lower()
        # prefijos
        for p in random.sample(PREFIXES, 9):
            add(p + low, intent)
        # sufijos
        for s in random.sample(SUFFIXES, 4):
            add(low + s, intent)
        # sinónimos (una sustitución por ejemplo)
        for src, dsts in SYNONYMS.items():
            if src in low:
                add(low.replace(src, random.choice(dsts), 1), intent)
                break
        # envolver pregunta
        if low.endswith("?") is False and any(
                w in low for w in ("qué", "cuál", "cómo", "dónde", "quién",
                                   "cuándo", "por qué", "cuánto", "que es")):
            add("¿" + low + "?", intent)


# ── 3) Plantillas combinatorias por intención ─────────────────────
def templates(intent: str, bodies: list[str], slots: dict[str, list[str]]) -> None:
    keys = list(slots)
    combos: set[str] = set()

    def rec(i: int, cur: str) -> None:
        if i == len(keys):
            combos.add(cur)
            return
        for v in slots[keys[i]]:
            rec(i + 1, cur.replace("{" + keys[i] + "}", v, 1))

    for b in bodies:
        rec(0, b)
    for c in combos:
        add(c, intent)


def expand_greeting() -> None:
    cores = ["hola", "buenos días", "buenas tardes", "buenas noches",
             "qué tal", "qué onda", "cómo estás", "cómo te va",
             "qué hay de nuevo", "saludos", "hey", "buenas",
             "hola qué tal", "cómo andas", "qué cuentas"]
    bodies = ["{p}{c}{s}", "{c}", "{p}{c}"]
    templates("greeting", bodies, {
        "p": ["", "oye ", "oye baro, ", "hola baro, ", "eh "],
        "c": cores,
        "s": ["", "!", "!!", " ¿cómo estás?", " ¿qué tal?"],
    })


def expand_farewell() -> None:
    cores = ["adiós", "nos vemos", "hasta luego", "chao", "me voy",
             "hasta pronto", "cuídate", "que descanses", "hablamos luego"]
    templates("farewell", ["{p}{c}{s}"], {
        "p": ["", "bueno ", "pues ", "ok, "],
        "c": cores,
        "s": ["", "!", " baro", ", gracias"],
    })


def expand_joke() -> None:
    bodies = ["{a} un chiste", "{a} otro chiste", "{a} un chiste {b}",
              "{a} algo gracioso", "{a} un chiste {b}"]
    templates("joke", bodies, {
        "a": ["cuéntame", "dime", "quiero escuchar", "pásame", "suéltame"],
        "b": ["bueno", "cortito", "de animales", "malo", "para reírme"],
    })


def expand_curiosity() -> None:
    bodies = ["{a} un dato curioso", "{a} una curiosidad",
              "{a} algo interesante", "{a} un dato curioso {b}"]
    templates("curiosity", bodies, {
        "a": ["dime", "cuéntame", "quiero saber", "pásame", "comparte"],
        "b": ["de ciencia", "de animales", "del espacio", "de historia", ""],
    })


def expand_motivation() -> None:
    bodies = ["{a} {b}", "{a} {b} {c}"]
    templates("motivation", bodies, {
        "a": ["necesito", "dame", "quiero", "estoy buscando"],
        "b": ["motivación", "ánimo", "inspiración", "una frase motivadora",
              "palabras de aliento"],
        "c": ["", "por favor", "hoy", "para seguir adelante"],
    })


def expand_riddle() -> None:
    bodies = ["{a} una adivinanza", "{a} un acertijo", "{a} {b}"]
    templates("riddle", bodies, {
        "a": ["dime", "cuéntame", "quiero", "pásame"],
        "b": ["una adivinanza", "un acertijo", "algo para adivinar"],
    })


# ── 4) Nuevas intenciones desde knowledge.py ──────────────────────
def expand_capital() -> None:
    bodies = [
        "cuál es la capital de {p}", "capital de {p}", "dime la capital de {p}",
        "¿cuál es la capital de {p}?", "la capital de {p} cuál es",
        "me dices la capital de {p}", "quiero saber la capital de {p}",
        "capital de {p} por favor", "¿sabes cuál es la capital de {p}?",
        "dime cuál es la capital de {p}", "oye, ¿capital de {p}?",
        "la capital de {p}", "¿me dices la capital de {p}?",
        "capital del país {p}",
    ]
    countries = list(K.CAPITALS.keys())
    for b in bodies:
        for c in countries:
            add(b.format(p=c), "capital")


def expand_chemistry() -> None:
    sym_bodies = ["cuál es el símbolo de {e}", "símbolo químico de {e}",
                  "dime el símbolo de {e}", "¿qué símbolo tiene {e}?",
                  "símbolo de {e} por favor", "el símbolo químico del {e}",
                  "¿me dices el símbolo de {e}?", "símbolo del elemento {e}"]
    num_bodies = ["cuál es el número atómico de {e}", "número atómico de {e}",
                  "dime el número atómico de {e}", "¿qué número atómico tiene {e}?",
                  "el número atómico del {e}", "¿me dices el número atómico de {e}?"]
    elems = [n for _, _, n in K.ELEMENTS]
    for b in sym_bodies:
        for e in elems:
            add(b.format(e=e.lower()), "chemistry")
    for b in num_bodies:
        for e in elems:
            add(b.format(e=e.lower()), "chemistry")
    add("cuántos elementos tiene la tabla periódica", "chemistry")
    add("dime la tabla periódica", "chemistry")
    add("qué es un elemento químico", "chemistry")


def expand_translation() -> None:
    bodies = ["cómo se dice {w} en español", "qué significa {w} en español",
              "traduce {w} al español", "{w} en español",
              "cómo se dice {w} en espanol", "dime qué significa {w}",
              "¿qué significa {w}?", "traducción de {w} al español"]
    words = list(K.TRANSLATIONS_EN_ES.keys())
    for b in bodies:
        for w in words:
            add(b.format(w=w), "translation")


def expand_definition() -> None:
    topics = [q.split("que es ")[-1].split("quien ")[-1]
              for q, _ in K.QA_FACTS if q.startswith("que es ")]
    bodies = ["qué es {t}", "qué es {t}?", "define {t}", "dime qué es {t}",
              "explícame qué es {t}", "qué significa {t}"]
    for b in bodies:
        for t in random.sample(topics, min(len(topics), 25)):
            add(b.format(t=t), "definition")
    # preguntas "quién" también van a definición/búsqueda
    who = [q for q, _ in K.QA_FACTS if q.startswith("quien")]
    for q in who:
        add(q, "definition")
        add("¿" + q + "?", "definition")


def expand_country_facts() -> None:
    """Preguntas sobre países (moneda, idioma, región, superficie)
    como intención 'definition' (las responde el knowledge)."""
    try:
        from country_facts import COUNTRY_QA
    except ImportError:
        return
    for q, _ in random.sample(COUNTRY_QA, min(len(COUNTRY_QA), 1500)):
        add(q, "definition")
        add("¿" + q + "?", "definition")


def expand_request_intent(intent: str, nouns: list[str]) -> None:
    bodies = ["{a} {n}", "{a} {n} {b}", "{a} {n}, por favor"]
    templates(intent, bodies, {
        "a": ["dime", "cuéntame", "quiero", "pásame", "regálame",
              "comparte", "necesito", "¿me das"],
        "n": nouns,
        "b": ["", "por favor", "bueno", "cortito", "ahora"],
    })


# ── 5) Datos externos: Amazon MASSIVE en español ─────────────────
# Escenarios del dataset MASSIVE (Amazon Science) mapeados a intenciones
# de Baro. Archivos: external_data/massive_es_{train,valid,test}.jsonl
MASSIVE_SCENARIO_MAP = {
    "alarm": "alarm",
    "audio": "capability",
    "calendar": "calendar",
    "cooking": "food",
    "datetime": "time",
    "email": "email",
    "general": "capability",
    "iot": "capability",
    "lists": "capability",
    "music": "entertainment",
    "news": "news",
    "play": "entertainment",
    "qa": "definition",
    "recommendation": "recommendation",
    "social": "social",
    "takeaway": "food",
    "transport": "travel",
    "weather": "weather",
}


def load_massive_scenarios() -> None:
    import json
    import os as _os
    base = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "external_data")
    loaded = 0
    for fn in ("massive_es_train.jsonl", "massive_es_valid.jsonl",
               "massive_es_test.jsonl"):
        path = _os.path.join(base, fn)
        if not _os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                intent = MASSIVE_SCENARIO_MAP.get(d.get("label_text", ""))
                if intent and d.get("text"):
                    add(d["text"], intent)
                    loaded += 1
    if loaded:
        print(f"  massive escenarios (es): {loaded} ejemplos")


def expand_all() -> None:
    load_base()
    expand_variants()
    expand_greeting()
    expand_farewell()
    expand_joke()
    expand_curiosity()
    expand_motivation()
    expand_riddle()
    expand_capital()
    expand_chemistry()
    expand_translation()
    expand_definition()
    expand_country_facts()
    load_massive_scenarios()
    expand_request_intent("proverb", ["un refrán", "un dicho popular",
                                     "un refrán mexicano", "sabiduría popular"])
    expand_request_intent("quote", ["una cita célebre", "una frase famosa",
                                    "una frase de un filósofo", "una cita inspiradora",
                                    "una frase para reflexionar"])
    expand_request_intent("story", ["un cuento", "un cuento corto",
                                    "una historia", "un cuento para niños",
                                    "una fábula"])
    expand_request_intent("poem", ["un poema", "unos versos",
                                   "un poema corto", "una poesía"])
    expand_request_intent("recipe", ["una receta", "una receta de cocina",
                                     "qué cocinar", "una receta fácil",
                                     "una receta rápida", "algo rico para cocinar"])
    expand_request_intent("advice", ["un consejo", "un consejo de vida",
                                     "un consejo útil", "qué me recomiendas",
                                     "un tip"])
    expand_request_intent("exercise", ["una rutina de ejercicio",
                                       "ejercicios para hacer en casa",
                                       "una rutina de gym",
                                       "cómo ejercitarme", "ejercicios"])
    expand_request_intent("study", ["cómo estudiar mejor",
                                    "técnicas de estudio",
                                    "consejos para estudiar",
                                    "cómo memorizar", "cómo concentrarme",
                                    "tips para el examen"])


def write_dataset(path: str = "training_data.py") -> None:
    expand_all()
    with open(path, "w", encoding="utf-8") as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('"""\ntraining_data.py — Dataset de entrenamiento para la red neuronal de Baro.\n')
        f.write('Generado automáticamente por training_data_gen.py (determinista, semilla 20260919).\n')
        f.write(f'{len(PAIRS)} ejemplos etiquetados en español.\n"""\n\n')
        f.write('TRAINING_DATA = [\n')
        for text, intent in PAIRS:
            safe = text.replace('\\', '\\\\').replace('"', '\\"')
            f.write(f'    ("{safe}", "{intent}"),\n')
        f.write(']\n')
    print(f"Generados {len(PAIRS)} ejemplos → {path}")


if __name__ == "__main__":
    if "--count" in sys.argv:
        expand_all()
        print(f"{len(PAIRS)} ejemplos generados")
        from collections import Counter
        for intent, n in Counter(i for _, i in PAIRS).most_common():
            print(f"  {intent}: {n}")
    else:
        write_dataset()