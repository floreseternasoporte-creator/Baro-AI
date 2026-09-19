# Baro-1 — Model Card

**baro-1 v1.0.0** es el modelo de lenguaje propio de Baro AI: un clasificador
neuronal de intenciones en español (TF-IDF de caracteres + perceptrón multicapa),
acompañado de una base de conocimiento factual determinista. Todo corre 100% local,
sin llamadas a APIs externas.

## Detalles del modelo

- **Arquitectura:** `TfidfVectorizer` (char_wb, n-gramas 2–3, 5100 features) → `MLPClassifier` ([256, 128], relu, adam)
- **Idioma:** español
- **Intenciones:** 62
- **Datos de entrenamiento:** 40,574 ejemplos etiquetados
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

- capitals: 184
- elements: 118
- qa_facts: 3,791
- country_facts: 3,720
- curiosities: 206
- jokes: 116
- riddles: 50
- proverbs: 102
- quotes: 100
- stories: 12
- poems: 10
- recipes: 20
- advice: 28
- translations: 301
- exercise_routines: 8
- study_techniques: 10

## Evaluación

Evaluado en un conjunto reservado de 3,000 ejemplos
generados con una semilla distinta y sin solape con el entrenamiento:

- **Accuracy:** 0.989
- **Macro-F1:** 0.9732

## Limitaciones

- El conocimiento factual es una foto fija: no sabe eventos posteriores a su creación.
- Las respuestas creativas (chistes, poemas) vienen de bancos curados, no son generativas.
- Puede clasificar mal entradas ambiguas o con muchos errores ortográficos.

## Intenciones soportadas

`advice`, `alarm`, `animals`, `art`, `baro_personal`, `business`, `calculation`, `calendar`, `capability`, `capital`, `chemistry`, `curiosity`, `date`, `definition`, `email`, `emotion_positive`, `emotion_support`, `entertainment`, `environment`, `exercise`, `farewell`, `finance`, `food`, `fun`, `geography`, `greeting`, `health`, `history`, `identity`, `inventions`, `joke`, `knock_knock`, `language`, `literature`, `math_facts`, `mood`, `motivation`, `mystery`, `mythology`, `news`, `philosophy`, `poem`, `programming`, `proverb`, `psychology`, `quote`, `recipe`, `recommendation`, `repeat`, `riddle`, `science`, `social`, `space`, `sports`, `story`, `study`, `technology`, `thanks`, `time`, `translation`, `travel`, `weather`

## Uso rápido

```python
import pickle
pipe, le = pickle.load(open("baro-model/model.pkl", "rb"))
intent = le.inverse_transform(pipe.predict(["¿cuál es la capital de Japón?"]))[0]
print(intent)  # capital
```

Ver `example.py` para un ejemplo completo.
