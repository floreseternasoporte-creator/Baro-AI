# -*- coding: utf-8 -*-
"""Ejemplo mínimo de uso del modelo baro-1."""
import os, pickle

HERE = os.path.dirname(os.path.abspath(__file__))
pipe, le = pickle.load(open(os.path.join(HERE, "model.pkl"), "rb"))

for text in ["hola", "cuéntame un chiste",
             "¿cuál es la capital de Japón?", "¿cómo se dice love en español?"]:
    idx = pipe.predict([text])[0]
    intent = le.inverse_transform([idx])[0]
    conf = pipe.predict_proba([text])[0][idx]
    print(f"{text!r:45} -> {intent} ({conf:.2f})")
