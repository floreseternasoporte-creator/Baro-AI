# -*- coding: utf-8 -*-
"""Entrena el modelo neuronal de Baro con el dataset expandido."""
import logging, time
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
from ml_brain import BaroNeuralEngine

t0 = time.time()
engine = BaroNeuralEngine()
print(f"ENTRENAMIENTO OK en {time.time()-t0:.1f}s")
print("Clases:", len(engine.label_encoder.classes_))
