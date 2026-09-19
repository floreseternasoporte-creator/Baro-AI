# -*- coding: utf-8 -*-
"""
export_model.py — Empaqueta a Baro como un release de modelo open-source
(estilo Meta/Llama): reutiliza el modelo entrenado (o lo entrena si falta),
lo evalúa con un conjunto reservado generado con otra semilla y produce
la carpeta `baro-model/` con:

    baro-model/
    ├── model.pkl          # pipeline sklearn entrenado (TF-IDF + MLP) + label encoder
    ├── config.json        # arquitectura, hiperparámetros, intenciones, métricas
    ├── vocabulary.json    # vocabulario TF-IDF (el "tokenizer" del modelo)
    ├── intents.json       # lista de intenciones (clases)
    ├── example.py         # ejemplo mínimo de uso
    ├── README.md          # model card
    └── LICENSE            # MIT

Uso:
    python3 export_model.py
"""
from __future__ import annotations

import json
import logging
import os
import pickle
import random

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("export")

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "baro-model")

MODEL_ID = "baro-1"
MODEL_VERSION = "1.0.0"


def get_trained():
    """Devuelve (pipeline, label_encoder) ya entrenados."""
    import ml_brain
    for path in (ml_brain.MODEL_PATH, ml_brain._LEGACY_MODEL_PATH):
        if os.path.exists(path):
            with open(path, "rb") as f:
                log.info("Reutilizando modelo entrenado: %s", path)
                return pickle.load(f), path
    log.info("No hay modelo entrenado; entrenando ahora...")
    eng = ml_brain.BaroNeuralEngine()
    return (eng.pipeline, eng.label_encoder), ml_brain.MODEL_PATH


def build_eval_set(n_target: int = 3000):
    """Genera un conjunto de evaluación con otra semilla y sin solaparse
    con los datos de entrenamiento (comparación por texto normalizado)."""
    import training_data_gen as gen
    from training_data import TRAINING_DATA
    from ml_brain import normalize

    train_texts = {normalize(t) for t, _ in TRAINING_DATA}

    gen.PAIRS.clear()
    gen.SEEN_TEXT.clear()
    random.seed(999)
    gen.expand_all()

    eval_pairs = [(t, i) for t, i in gen.PAIRS if normalize(t) not in train_texts]
    random.seed(999)
    random.shuffle(eval_pairs)
    eval_pairs = eval_pairs[:n_target]
    log.info("Evaluación: %d ejemplos reservados (sin solape con train)",
             len(eval_pairs))

    # restaurar el generador a su estado determinista original
    gen.PAIRS.clear()
    gen.SEEN_TEXT.clear()
    random.seed(20260919)
    return eval_pairs


def main() -> None:
    from sklearn.metrics import accuracy_score, f1_score
    from ml_brain import normalize
    import knowledge as K

    (pipe, le), src_path = get_trained()

    eval_pairs = build_eval_set()
    X_eval = [normalize(t) for t, _ in eval_pairs]
    y_eval = le.transform([i for _, i in eval_pairs])
    pred = pipe.predict(X_eval)
    acc = float(accuracy_score(y_eval, pred))
    f1 = float(f1_score(y_eval, pred, average="macro", zero_division=0))
    log.info("Held-out accuracy: %.4f | macro-F1: %.4f", acc, f1)

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "model.pkl"), "wb") as f:
        pickle.dump((pipe, le), f)

    vocab = pipe.named_steps["tfidf"].vocabulary_
    with open(os.path.join(OUT, "vocabulary.json"), "w", encoding="utf-8") as f:
        json.dump({k: int(v) for k, v in vocab.items()}, f, ensure_ascii=False)

    intents = list(le.classes_)
    with open(os.path.join(OUT, "intents.json"), "w", encoding="utf-8") as f:
        json.dump(intents, f, ensure_ascii=False, indent=2)

    from training_data import TRAINING_DATA
    kb = K.knowledge_stats()
    mlp = pipe.named_steps["clf"]
    config = {
        "model_id": MODEL_ID,
        "version": MODEL_VERSION,
        "architecture": {
            "vectorizer": {"type": "TfidfVectorizer", "analyzer": "char_wb",
                           "ngram_range": [2, 3], "max_features": 6000,
                           "sublinear_tf": True,
                           "vocabulary_size": len(vocab)},
            "classifier": {"type": "MLPClassifier",
                           "hidden_layer_sizes": list(mlp.hidden_layer_sizes),
                           "activation": mlp.activation, "solver": mlp.solver,
                           "max_iter": mlp.max_iter, "random_state": 42},
        },
        "intents": intents,
        "num_intents": len(intents),
        "training": {"examples": len(TRAINING_DATA), "seed": 20260919,
                     "source": "training_data_gen.py"},
        "evaluation": {"method": "held-out generado con semilla 999, sin solape",
                       "eval_examples": len(eval_pairs),
                       "accuracy": round(acc, 4), "macro_f1": round(f1, 4)},
        "knowledge_base": kb,
        "language": "es",
        "license": "MIT",
    }
    with open(os.path.join(OUT, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    write_model_card(config)
    write_license()
    write_example()
    log.info("Release escrita en %s", OUT)
    log.info("Modelo fuente: %s", src_path)


def write_model_card(cfg: dict) -> None:
    kb = cfg["knowledge_base"]
    kb_lines = "\n".join(f"- {k}: {v:,}" for k, v in kb.items())
    intents = ", ".join(f"`{i}`" for i in cfg["intents"])
    arch = cfg["architecture"]
    card = f"""# Baro-1 — Model Card

**baro-1 v{cfg["version"]}** es el modelo de lenguaje propio de Baro AI: un clasificador
neuronal de intenciones en español (TF-IDF de caracteres + perceptrón multicapa),
acompañado de una base de conocimiento factual determinista. Todo corre 100% local,
sin llamadas a APIs externas.

## Detalles del modelo

- **Arquitectura:** `TfidfVectorizer` (char_wb, n-gramas 2–3, {arch["vectorizer"]["vocabulary_size"]} features) → `MLPClassifier` ({arch["classifier"]["hidden_layer_sizes"]}, {arch["classifier"]["activation"]}, {arch["classifier"]["solver"]})
- **Idioma:** español
- **Intenciones:** {cfg["num_intents"]}
- **Datos de entrenamiento:** {cfg["training"]["examples"]:,} ejemplos etiquetados
- **Licencia:** MIT

## Uso previsto

Asistente conversacional en español: chat, preguntas de cultura general, capitales,
química, traducción EN→ES, chistes, refranes, citas, cuentos, poemas, recetas,
consejos, rutinas de ejercicio y técnicas de estudio.

## Datos de entrenamiento

Dataset sintético generado de forma reproducible con `training_data_gen.py`
(semilla 20260919): expansión combinatoria de ejemplos curados + plantillas
generadas desde la base de conocimiento. Sin datos de usuarios reales.

## Base de conocimiento incluida

{kb_lines}

## Evaluación

Evaluado en un conjunto reservado de {cfg["evaluation"]["eval_examples"]:,} ejemplos
generados con una semilla distinta y sin solape con el entrenamiento:

- **Accuracy:** {cfg["evaluation"]["accuracy"]}
- **Macro-F1:** {cfg["evaluation"]["macro_f1"]}

## Limitaciones

- El conocimiento factual es una foto fija: no sabe eventos posteriores a su creación.
- Las respuestas creativas (chistes, poemas) vienen de bancos curados, no son generativas.
- Puede clasificar mal entradas ambiguas o con muchos errores ortográficos.

## Intenciones soportadas

{intents}

## Uso rápido

```python
import pickle
pipe, le = pickle.load(open("baro-model/model.pkl", "rb"))
intent = le.inverse_transform(pipe.predict(["¿cuál es la capital de Japón?"]))[0]
print(intent)  # capital
```

Ver `example.py` para un ejemplo completo.
"""
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as f:
        f.write(card)


def write_license() -> None:
    with open(os.path.join(OUT, "LICENSE"), "w", encoding="utf-8") as f:
        f.write("""MIT License

Copyright (c) 2026 Baro AI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""")


def write_example() -> None:
    with open(os.path.join(OUT, "example.py"), "w", encoding="utf-8") as f:
        f.write('''# -*- coding: utf-8 -*-
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
''')


if __name__ == "__main__":
    main()
