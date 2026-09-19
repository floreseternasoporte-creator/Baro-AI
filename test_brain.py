# -*- coding: utf-8 -*-
"""Pruebas end-to-end del cerebro de Baro (sin servidor)."""
import asyncio
from ml_brain import BaroBrain

CASES = [
    # conocimiento factual determinista
    ("¿cuál es la capital de Japón?", "capital"),
    ("capital de australia", "capital"),
    ("¿cuál es el símbolo del oro?", "chemistry"),
    ("número atómico del carbono", "chemistry"),
    ("¿cómo se dice dog en español?", "translation"),
    ("¿quién propuso la teoría de la relatividad?", "definition"),
    ("¿quién pintó la Mona Lisa?", "definition"),
    # intenciones por clasificador + knowledge lists
    ("cuéntame un chiste", "joke"),
    ("dime un dato curioso", "curiosity"),
    ("dime un refrán", "proverb"),
    ("dame una cita célebre", "quote"),
    ("cuéntame un cuento", "story"),
    ("escríbeme un poema", "poem"),
    ("dame una receta", "recipe"),
    ("dame la receta de guacamole", "recipe"),
    ("dame un consejo de dinero", "advice"),
    ("dame una rutina de ejercicio", "exercise"),
    ("cómo estudiar mejor", "study"),
    ("dime una adivinanza", "riddle"),
    # clásicas
    ("hola", "greeting"),
    ("cuánto es 25 por 4", "calculation"),
    ("qué hora es", "time"),
]

async def main():
    brain = BaroBrain()
    ok = 0
    for text, expected in CASES:
        r = await brain.process(text)
        mark = "✓" if r.intent == expected else f"✗ (esperaba {expected})"
        if r.intent == expected:
            ok += 1
        print(f"{mark} [{r.intent}] {text}\n    → {r.text[:110]}")
    print(f"\n{ok}/{len(CASES)} correctas")

asyncio.run(main())
