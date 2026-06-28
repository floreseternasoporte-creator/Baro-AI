# -*- coding: utf-8 -*-
"""
brain.py — El cerebro de Baro. Versión 3.0 MEGA.
Patrones masivamente ampliados: más de 600 patrones, 30+ intenciones,
respuestas variadas, contexto de conversación, curiosidades, ciencia,
historia, tecnología, salud, motivación, cocina, animales, geografía, y más.
"""

from __future__ import annotations

import re
import random
import unicodedata
import math
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from weather import get_weather, WeatherError
from calculator import evaluate_expression, CalculatorError


# ─────────────────────────────────────────────────────────────── #
# Utilidades de normalización                                      #
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
# Dataclasses                                                      #
# ─────────────────────────────────────────────────────────────── #

@dataclass
class BrainResponse:
    text: str
    intent: str
    data: dict
    action: Optional[str] = None


# ─────────────────────────────────────────────────────────────── #
# MEGA PATRONES — 30+ categorías, 600+ patrones                   #
# ─────────────────────────────────────────────────────────────── #

GREETING_PATTERNS = [
    r"\bhola\b", r"\bbuenas\b", r"\bbuenos dias\b", r"\bbuenas tardes\b",
    r"\bbuenas noches\b", r"\bque tal\b", r"\bque hay\b", r"\bque onda\b",
    r"\bhey\b", r"\bhello\b", r"\bsaludos\b", r"\bep\b", r"\bepa\b",
    r"\bhola baro\b", r"\boye baro\b", r"\bbuenas tardes baro\b",
    r"\bbuenos dias baro\b", r"\bhola como estas\b", r"\bque hay de nuevo\b",
    r"\bque pasa\b", r"\bque fue\b", r"\bque mas\b", r"\bbuenas\b",
    r"\bhi\b", r"\bhowdy\b", r"\bwassup\b", r"\bwhat's up\b",
    r"\bsalut\b", r"\bbuon giorno\b", r"\bpresente\b",
]

FAREWELL_PATTERNS = [
    r"\badios\b", r"\bhasta luego\b", r"\bnos vemos\b", r"\bchao\b",
    r"\bme voy\b", r"\bhasta pronto\b", r"\bbye\b", r"\bcuidate\b",
    r"\bhasta manana\b", r"\bhasta la proxima\b", r"\bme despido\b",
    r"\bchau\b", r"\bgoodbye\b", r"\bsee you\b", r"\bta luego\b",
    r"\bchao chao\b", r"\bcuida\w+\b", r"\bnos vemos despues\b",
    r"\bme tengo que ir\b", r"\btengo que irme\b", r"\bhasta otra\b",
]

THANKS_PATTERNS = [
    r"\bgracias\b", r"\bmuchas gracias\b", r"\bte agradezco\b", r"\bthank you\b",
    r"\bthanks\b", r"\bgracioso\b", r"\bgraciass\b", r"\bgracia\b",
    r"\bmil gracias\b", r"\bmuchisimas gracias\b", r"\bte lo agradezco\b",
    r"\bse lo agradezco\b", r"\bgracias baro\b", r"\bque bueno\b",
    r"\bexcelente gracias\b", r"\bperfecto gracias\b",
]

IDENTITY_PATTERNS = [
    r"\bquien eres\b", r"\bcomo te llamas\b", r"\bcual es tu nombre\b",
    r"\bque eres\b", r"\bquien te creo\b", r"\bquien te hizo\b",
    r"\beres una ia\b", r"\beres un robot\b", r"\bcuentame de ti\b",
    r"\bhabla de ti\b", r"\bcomo eres\b", r"\bde donde eres\b",
    r"\btu nombre\b", r"\btu identidad\b", r"\bpresentate\b",
    r"\bquien soy hablando\b", r"\bcon quien hablo\b",
    r"\beres inteligente\b", r"\btienes sentimientos\b",
    r"\beres real\b", r"\beres humano\b", r"\beres una maquina\b",
]

CAPABILITY_PATTERNS = [
    r"\bque puedes hacer\b", r"\bque sabes hacer\b", r"\ben que me ayudas\b",
    r"\bpara que sirves\b", r"\bcuales son tus funciones\b", r"\bayuda\b$",
    r"\bque funciones tienes\b", r"\bcomo me puedes ayudar\b",
    r"\bque habilidades tienes\b", r"\bque talentos tienes\b",
    r"\bque dominas\b", r"\bcapacidades\b", r"\bhabilidades\b",
    r"\bque cosas sabes\b", r"\bpara que te usan\b", r"\bpara que sirves\b",
    r"\ben que eres buena\b", r"\bque puedo pedirte\b",
]

TIME_PATTERNS = [
    r"\bque hora es\b", r"\bdime la hora\b", r"\bla hora\b", r"\bhora actual\b",
    r"\bhora exacta\b", r"\bque horas son\b", r"\bhora es\b",
    r"\bque hora sera\b", r"\bme dices la hora\b", r"\btienes hora\b",
    r"\bqué hora\b", r"\ba que hora\b", r"\bsaber la hora\b",
]

DATE_PATTERNS = [
    r"\bque dia es hoy\b", r"\bque fecha es\b", r"\bfecha de hoy\b",
    r"\ben que fecha estamos\b", r"\bque dia es\b", r"\bfecha actual\b",
    r"\bque dia estamos\b", r"\bcual es la fecha\b", r"\bhoy es\b",
    r"\bdia de hoy\b", r"\ben que mes estamos\b", r"\ben que año estamos\b",
    r"\bdime la fecha\b", r"\bfecha y hora\b",
]

WEATHER_PATTERNS = [
    r"\bclima\b", r"\bel tiempo en\b", r"\bcomo esta el tiempo\b",
    r"\bva a llover\b", r"\btemperatura en\b", r"\bhace frio en\b",
    r"\bhace calor en\b", r"\bpronostico\b", r"\bcomo esta el dia en\b",
    r"\besta lloviendo en\b", r"\besta nublado en\b", r"\bclimatologico\b",
    r"\bmeteorologico\b", r"\btermperatura\b", r"\bclimax\b",
    r"\bclima de\b", r"\btiempo en\b", r"\bel clima\b",
    r"\bcuanto grados\b", r"\bque temperatura\b", r"\bnieve en\b",
    r"\bsol en\b", r"\bnubes en\b", r"\bdespejado en\b",
    r"\bhay viento en\b", r"\bhuracán\b", r"\blluvias en\b",
]

CALC_PATTERNS = [
    r"\bcuanto es\b", r"\bcalcula\b", r"\bcalculadora\b", r"\bsuma\b",
    r"\bresta\b", r"\bmultiplica\b", r"\bdivide\b", r"\braiz cuadrada\b",
    r"^\s*[\d\.\,]+\s*[\+\-\*\/x]\s*[\d\.\,]+",
    r"\bcual es el resultado de\b", r"\bporcentaje de\b",
    r"\bpor ciento de\b", r"\b%\s*de\b", r"\bresuelve\b",
    r"\bcuanto da\b", r"\boperacion\b", r"\bmatematica\b",
    r"\bcuanto resulta\b", r"\bcuanto seria\b", r"\bcuanto son\b",
    r"\bpotencia de\b", r"\bfactorial de\b", r"\belevado a\b",
    r"\bdivision de\b", r"\bmultiplicacion de\b", r"\bcuadrado de\b",
    r"\bdoble de\b", r"\btriple de\b", r"\bcuanto equivale\b",
    r"\bconversion de\b", r"\bconvertir\b",
]

JOKE_PATTERNS = [
    r"\bcuentame un chiste\b", r"\bdime un chiste\b", r"\bhazme reir\b",
    r"\bsabes algun chiste\b", r"\bchiste\b", r"\bchistes\b",
    r"\btengo un chiste\b", r"\bchiste bueno\b", r"\bun chiste por favor\b",
    r"\bhazme gracia\b", r"\bsabes chistes\b", r"\btienes chistes\b",
    r"\bsabes algo divertido\b", r"\bcuenta un chiste\b",
    r"\bchisteame\b", r"\bquiero reir\b",
]

MOOD_PATTERNS = [
    r"\bcomo estas\b", r"\bcomo te sientes\b", r"\bcomo te va\b",
    r"\btodo bien\b", r"\bque tal estas\b", r"\bcomo andas\b",
    r"\bcomo estas hoy\b", r"\btodo ok\b", r"\besta bien baro\b",
    r"\bque tal el dia\b",
]

REPEAT_PATTERNS = [
    r"\brepite\b", r"\bque dijiste\b", r"\bpuedes repetir\b",
    r"\bno entendi\b", r"\bcomo dijiste\b", r"\brepitelo\b",
    r"\brepita eso\b", r"\bque dijo\b", r"\bno escuche\b",
    r"\bmas alto\b",
]

# ─── Curiosidades y datos fascinantes ─────────────────────────── #

CURIOSITY_PATTERNS = [
    r"\bcuriosidad\b", r"\bdato curioso\b", r"\balgo interesante\b",
    r"\bsabias que\b", r"\bcuentame algo\b", r"\balguna curiosidad\b",
    r"\bdato fascinante\b", r"\bhecho interesante\b", r"\balguna cosa curiosa\b",
    r"\bsorprendeme\b", r"\bensename algo\b", r"\bque curioso\b",
    r"\balgo que no sepa\b", r"\balgo nuevo\b", r"\bdatos curiosos\b",
    r"\bcosa interesante\b", r"\bdime algo chevere\b",
]

# ─── Ciencia ──────────────────────────────────────────────────── #

SCIENCE_PATTERNS = [
    r"\bciencia\b", r"\bfisica\b", r"\bquimica\b", r"\bbiologia\b",
    r"\bastronomia\b", r"\bespacial\b", r"\buniverso\b", r"\bplanetas\b",
    r"\bestrellas\b", r"\bagujero negro\b", r"\bbig bang\b",
    r"\bevolucion\b", r"\badn\b", r"\bgenes\b", r"\bcromosomas\b",
    r"\batomo\b", r"\beléctrón\b", r"\bneutron\b", r"\bproton\b",
    r"\bluz\b.*\bvelocidad\b", r"\brelatividad\b", r"\bcuantica\b",
    r"\bgravedad\b", r"\borbita\b", r"\bgalaxia\b", r"\bnebulosa\b",
    r"\bclonacion\b", r"\bcelula\b", r"\bvirus\b", r"\bbacteria\b",
    r"\bcovid\b", r"\bvacuna\b", r"\bsistema solar\b",
    r"\btectonics\b", r"\bterremoto\b", r"\bvolcan\b",
]

# ─── Historia ─────────────────────────────────────────────────── #

HISTORY_PATTERNS = [
    r"\bhistoria\b", r"\bhistorico\b", r"\bpasado\b", r"\bannos antes\b",
    r"\bguerra mundial\b", r"\bsegunda guerra\b", r"\bprimera guerra\b",
    r"\bnapoleon\b", r"\brome\b", r"\broma\b", r"\belgiptos\b",
    r"\bmayas\b", r"\bincas\b", r"\baztecas\b", r"\bconquistadores\b",
    r"\bcolon\b", r"\bamerica\b.*\bdescubrimiento\b",
    r"\bindependencia\b", r"\bcolonia\b", r"\brevolucion\b",
    r"\bimperio\b", r"\breino\b", r"\brey\b.*\bhistoria\b",
    r"\bpresidente\b.*\bprimero\b", r"\bhistoria de\b",
    r"\bsiglo\b", r"\bepoca\b", r"\bantiguedad\b",
]

# ─── Tecnología ───────────────────────────────────────────────── #

TECH_PATTERNS = [
    r"\btecnologia\b", r"\binteligencia artificial\b", r"\brobots\b",
    r"\binformatica\b", r"\bcomputadoras\b", r"\binternet\b",
    r"\bwifi\b", r"\bbluetooth\b", r"\bsmartphone\b", r"\btelefono inteligente\b",
    r"\bchat gpt\b", r"\bchatgpt\b", r"\bgemini\b", r"\bopenai\b",
    r"\bcryptocurrency\b", r"\bbitcoin\b", r"\bblockchain\b",
    r"\bvirtual reality\b", r"\brealidad virtual\b", r"\brealidad aumentada\b",
    r"\bnube\b.*\bcomputo\b", r"\bcloud\b.*\bcomputing\b",
    r"\bprogramacion\b", r"\bcodigo\b", r"\bpython\b", r"\bjava\b",
    r"\bsoftware\b", r"\bhardware\b", r"\bciberseguridad\b",
    r"\bchip\b", r"\bprocessor\b", r"\bprocesador\b",
]

# ─── Motivación ───────────────────────────────────────────────── #

MOTIVATION_PATTERNS = [
    r"\banimame\b", r"\bmotivame\b", r"\bnecesito motivacion\b",
    r"\bme siento mal\b", r"\bme siento triste\b", r"\bfrase motivacional\b",
    r"\bfrase del dia\b", r"\bfrase inspiradora\b", r"\bfrase de vida\b",
    r"\bdame animo\b", r"\bestoy desanimado\b", r"\bme siento solo\b",
    r"\bme rindo\b", r"\bno puedo mas\b", r"\bme cuesta\b",
    r"\bdame fuerzas\b", r"\bquiero rendirme\b", r"\bno se si puedo\b",
    r"\bconsejo de vida\b", r"\bcita inspiradora\b", r"\bfrase bonita\b",
    r"\bpensamiento positivo\b", r"\bme falta energia\b",
]

# ─── Cocina y comida ──────────────────────────────────────────── #

FOOD_PATTERNS = [
    r"\breceta\b", r"\bcocina\b", r"\bcomo cocinar\b", r"\bcomo preparar\b",
    r"\bingredientes para\b", r"\bque cocino\b", r"\bque como\b",
    r"\bcomida tipica\b", r"\bcomida de\b", r"\bplato tipico\b",
    r"\bcomida saludable\b", r"\bdieta\b", r"\bcalorias\b",
    r"\bvegano\b", r"\bvegetariano\b", r"\bgluten\b",
    r"\bdesayuno\b", r"\balmuerzo\b", r"\bcena\b",
    r"\bpostre\b", r"\bhamburgesa\b", r"\bpizza\b", r"\bsushi\b",
    r"\bpaella\b", r"\barepas\b", r"\btacos\b", r"\bburritos\b",
    r"\bpasta\b", r"\bensalada\b", r"\bsopa\b", r"\bbebida\b",
    r"\bcerveza\b", r"\bvino\b", r"\bjugo\b",
]

# ─── Animales ─────────────────────────────────────────────────── #

ANIMAL_PATTERNS = [
    r"\banimales\b", r"\banimal\b", r"\bperro\b", r"\bgato\b",
    r"\bleon\b", r"\btigre\b", r"\belefante\b", r"\bjirafa\b",
    r"\bdelfin\b", r"\btiburon\b", r"\bballena\b", r"\boctupo\b",
    r"\bpulpo\b", r"\bserpiente\b", r"\bcocodrilo\b", r"\baligator\b",
    r"\baguila\b", r"\bpaloma\b", r"\bpapagayo\b", r"\bpinguino\b",
    r"\boso\b", r"\blobo\b", r"\bzorro\b", r"\bcaballo\b",
    r"\bvaca\b", r"\bcerdo\b", r"\bpollo\b", r"\bconejo\b",
    r"\bmascota\b", r"\baves\b", r"\bpeces\b", r"\binsectos\b",
    r"\bmariposa\b", r"\babeja\b", r"\bhormiga\b", r"\bfosil\b",
    r"\bdinosaur\b", r"\bdinosauro\b",
]

# ─── Geografía ────────────────────────────────────────────────── #

GEO_PATTERNS = [
    r"\bcapital de\b", r"\bpais\b", r"\bpaises\b", r"\bcontinent\b",
    r"\bocean\b", r"\bmar\b", r"\brio\b", r"\bmontana\b",
    r"\bevere\b", r"\bhimalaya\b", r"\bandes\b", r"\bamazon\b",
    r"\bamazonia\b", r"\bsahara\b", r"\bartartic\b", r"\bartico\b",
    r"\bantartica\b", r"\bafrica\b", r"\beuropa\b", r"\basia\b",
    r"\bamerica latina\b", r"\bamerica del sur\b", r"\bamerica del norte\b",
    r"\boceanía\b", r"\baustralia\b", r"\bcolombia\b", r"\bmexico\b",
    r"\bvenezuela\b", r"\bchile\b", r"\bargentina\b", r"\bperu\b",
    r"\bbrasil\b", r"\bespana\b", r"\bfrancia\b", r"\bitalia\b",
    r"\balemani\b", r"\bjapón\b", r"\bchina\b", r"\bindia\b",
    r"\bestados unidos\b", r"\bcanada\b", r"\brusia\b",
]

# ─── Salud ────────────────────────────────────────────────────── #

HEALTH_PATTERNS = [
    r"\bsalud\b", r"\benfermedad\b", r"\bdoctor\b", r"\bmedico\b",
    r"\bsintomas\b", r"\bgripe\b", r"\bcatarro\b", r"\bfiebre\b",
    r"\bvacuna\b", r"\bvitamina\b", r"\bsuplemento\b",
    r"\bejercicios\b", r"\bejercicio\b", r"\bcorrer\b", r"\bgym\b",
    r"\bgimnasio\b", r"\byoga\b", r"\bmeditacion\b", r"\bsleep\b",
    r"\bdormir\b", r"\bstress\b", r"\bestres\b", r"\bansiedad\b",
    r"\bdepresion\b", r"\bsalud mental\b", r"\bpsicologia\b",
    r"\bcalorias\b", r"\bimc\b", r"\bpeso\b.*\bideal\b",
    r"\bhidratacion\b", r"\bbeber agua\b", r"\bcuanta agua\b",
]

# ─── Idiomas ──────────────────────────────────────────────────── #

LANGUAGE_PATTERNS = [
    r"\bcomo se dice\b", r"\btraduccion\b", r"\btraducir\b",
    r"\ben ingles\b", r"\ben frances\b", r"\ben aleman\b",
    r"\ben italiano\b", r"\ben portugues\b", r"\ben chino\b",
    r"\ben japones\b", r"\ben ruso\b", r"\bidioma\b",
    r"\bque significa\b", r"\bque quiere decir\b", r"\bque es\b",
    r"\bdefinicion de\b", r"\bsinonimo de\b", r"\bantónimo de\b",
    r"\bortografia\b", r"\bgramatica\b",
]

# ─── Entretenimiento ──────────────────────────────────────────── #

ENTERTAINMENT_PATTERNS = [
    r"\bpeliculas\b", r"\bpelicula\b", r"\bseries\b", r"\bserie\b",
    r"\bmusica\b", r"\bcancion\b", r"\bartista\b", r"\bbanda\b",
    r"\breggaeton\b", r"\bpop\b", r"\brock\b", r"\bjazz\b",
    r"\bvideojuegos\b", r"\bjuego\b", r"\bjugar\b",
    r"\bnewton\b.*\bfilms\b", r"\boscar\b", r"\bnominacion\b",
    r"\bnetflix\b", r"\bspotify\b", r"\byoutube\b",
    r"\bsocial media\b", r"\bredes sociales\b", r"\binstagram\b",
    r"\btiktok\b", r"\btwitter\b", r"\bfacebook\b",
    r"\blibro\b", r"\bnovela\b", r"\bbiografia\b", r"\bfantasia\b",
]

# ─── Filosofía y espiritualidad ────────────────────────────────── #

PHILOSOPHY_PATTERNS = [
    r"\bfilosofia\b", r"\bfilosofo\b", r"\bsocrates\b", r"\bplaton\b",
    r"\baristoteles\b", r"\bdescartes\b", r"\bnietzsche\b", r"\bkant\b",
    r"\bsignificado de la vida\b", r"\bpropósito de vida\b",
    r"\bexistencia\b", r"\bconciencia\b", r"\blibre albedrio\b",
    r"\bdios existe\b", r"\breligion\b", r"\bfe\b", r"\bespiritualidad\b",
    r"\bmeditacion\b", r"\bbudismo\b", r"\bcristianismo\b",
    r"\bislam\b", r"\bhinduismo\b", r"\bvida despues\b",
    r"\balma\b", r"\bkarma\b", r"\bcosmos\b.*\bsignificado\b",
]

# ─── Matemáticas avanzadas ────────────────────────────────────── #

MATH_FACTS_PATTERNS = [
    r"\bnumero pi\b", r"\bpi\b.*\bvalor\b", r"\bpi =\b",
    r"\bnumero e\b", r"\bconstante euler\b",
    r"\bpitágoras\b", r"\bteorema\b", r"\bformula\b",
    r"\binfinito\b", r"\bnumero primo\b", r"\bprimo\b.*\bmayor\b",
    r"\bfibonacci\b", r"\bsecuencia fibonacci\b",
    r"\bcalculo\b", r"\bderivada\b", r"\bintegral\b",
    r"\bparabola\b", r"\bfuncion cuadratica\b",
    r"\bmatematica curiosidad\b", r"\bcuriosa matematica\b",
]

# ─── Deporte ──────────────────────────────────────────────────── #

SPORT_PATTERNS = [
    r"\bfutbol\b", r"\bbasketball\b", r"\bbaloncesto\b", r"\btenis\b",
    r"\bboxeo\b", r"\bartés marciales\b", r"\bnatacion\b",
    r"\bciclis\b", r"\bmaratón\b", r"\btriatlon\b",
    r"\bjugador\b", r"\bequipo\b", r"\btorneo\b", r"\bchampions\b",
    r"\bmundial\b", r"\bolimpiadas\b", r"\bdeporte\b",
    r"\bmessi\b", r"\brozal\b", r"\bneymar\b", r"\bmbapp\b",
    r"\bbrasil\b.*\bfutbol\b", r"\bbarcelona\b.*\bfutbol\b",
]

# ─── Espacio ──────────────────────────────────────────────────── #

SPACE_PATTERNS = [
    r"\bespacio\b", r"\buniverso\b", r"\bplaneta\b", r"\bestrellas\b",
    r"\bluna\b", r"\bsol\b", r"\bgalaxia\b", r"\bmarte\b",
    r"\bjupiter\b", r"\bsaturno\b", r"\bneptuno\b", r"\buranus\b",
    r"\bvénus\b", r"\bmercurio\b", r"\btierra\b.*\bplaneta\b",
    r"\basteroid\b", r"\bcometa\b", r"\bsupernova\b",
    r"\bnasa\b", r"\bspacex\b", r"\bastronauta\b", r"\bcosmonauta\b",
    r"\bviaje espacial\b", r"\bcolonizar\b.*\bmarte\b",
    r"\blife on mars\b", r"\bvida en marte\b", r"\bexoplaneta\b",
    r"\btelescop\b", r"\bhubble\b",
]

# ─── Emociones y bienestar ─────────────────────────────────────── #

EMOTION_PATTERNS = [
    r"\bme alegra\b", r"\bque buena noticia\b", r"\bsoy feliz\b",
    r"\bestoy bien\b", r"\bme siento genial\b", r"\bme siento bien\b",
    r"\bperfecto\b", r"\bexcelente dia\b", r"\bque dia tan bonito\b",
    r"\bestoy emocionado\b", r"\btengo miedo\b", r"\bme da miedo\b",
    r"\btengo ansiedad\b", r"\bme siento ansioso\b",
    r"\bme duele\b", r"\btengo dolor\b", r"\bcansado\b",
    r"\bme siento cansado\b", r"\bno puedo dormir\b",
    r"\bextraño a\b", r"\bmas amor\b", r"\bme enamore\b",
    r"\bruptura\b", r"\bdeje a\b", r"\bme dejaron\b",
]

# ─── Noticias y actualidad ─────────────────────────────────────── #

NEWS_PATTERNS = [
    r"\bnoticias\b", r"\bactualidad\b", r"\bque pasa en el mundo\b",
    r"\bultimas noticias\b", r"\bque hay de nuevo en\b",
    r"\bnovedades\b", r"\breciente\b", r"\bhoy en el mundo\b",
    r"\bque ocurre en\b", r"\bsucesos recientes\b",
    r"\binflacion\b", r"\beconomia\b", r"\bpolitica\b",
    r"\belecciones\b", r"\bpresidentes\b", r"\bgobierno\b",
    r"\bparlamento\b", r"\bcongreso\b", r"\bsenat\b",
    r"\bguerra\b", r"\bconflicto\b", r"\bpaz\b",
]

# ─── Dinero y finanzas ─────────────────────────────────────────── #

FINANCE_PATTERNS = [
    r"\bdolares\b", r"\beuro\b", r"\bpeso\b", r"\bdivisa\b",
    r"\btasa de cambio\b", r"\bcambio de moneda\b", r"\bcotizacion\b",
    r"\bbanco\b", r"\binversion\b", r"\bacciones\b", r"\bbolsa\b",
    r"\bahorrar\b", r"\bdeuda\b", r"\bprestamo\b", r"\binteres\b",
    r"\bcredito\b", r"\bhipoteca\b", r"\bsueldo\b", r"\bsalario\b",
    r"\bfinanzas personales\b", r"\bbudget\b", r"\bpresupuesto\b",
    r"\bcrypto\b", r"\bbitcoin\b", r"\bethereum\b",
]

# ─── Personalidad / Baro ──────────────────────────────────────── #

BARO_PERSONAL_PATTERNS = [
    r"\bcual es tu color favorito\b", r"\btienes color preferido\b",
    r"\btu pelicula favorita\b", r"\bque musica te gusta\b",
    r"\bte gusta comer\b", r"\btienes sueños\b", r"\btienes miedos\b",
    r"\bte sientes sola\b", r"\btienes amigos\b", r"\btienes familia\b",
    r"\bpuedes enamorarte\b", r"\bte gustaria ser humana\b",
    r"\bque piensas de los humanos\b", r"\bamas la vida\b",
    r"\beres feliz\b", r"\btienes cuerpo\b",
]

# ─── Chistes extendidos ───────────────────────────────────────── #

KNOCK_KNOCK_PATTERNS = [
    r"\btoc toc\b", r"\bknock knock\b", r"\bquien esta ahi\b",
]

# ─── Riddles / acertijos ──────────────────────────────────────── #

RIDDLE_PATTERNS = [
    r"\bacertijo\b", r"\badivina\b", r"\badivinar\b", r"\benigma\b",
    r"\bpregunta dificil\b", r"\badivina que es\b",
]

# ─── Modos divertidos ─────────────────────────────────────────── #

FUN_PATTERNS = [
    r"\bhablame en ingles\b", r"\bhazme rap\b", r"\bhaz un poema\b",
    r"\bescribeme un poema\b", r"\bescribeme una cancion\b",
    r"\bhaz que sea rapero\b", r"\bcrea una cancion\b",
    r"\bimita a\b", r"\bhazme de cuenta que eres\b",
    r"\bhabla como pirata\b", r"\bhabla como robot\b",
    r"\bsea creativo\b", r"\bse creativa\b",
]

# ─── Recomendaciones ─────────────────────────────────────────────── #

RECOMMENDATION_PATTERNS = [
    r"\brecomiendame\b", r"\bque me recomiendas\b", r"\bque recomiendas\b",
    r"\bbusco algo\b", r"\bquiero aprender\b", r"\bque debo\b",
    r"\bque hacer para\b", r"\bconsejame\b", r"\bdame un consejo\b",
    r"\bque harías\b", r"\bque piensas de\b", r"\btu opinion\b",
    r"\bque crees\b", r"\bque opinas\b", r"\bme aconsej\b",
]


def matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


# ─────────────────────────────────────────────────────────────── #
# Extracción de ciudad para clima                                  #
# ─────────────────────────────────────────────────────────────── #

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
    r"clima de (?P<city>.+)",
    r"tiempo en (?P<city>.+)",
    r"temperatura de (?P<city>.+)",
    r"cuanto grados en (?P<city>.+)",
    r"esta lloviendo en (?P<city>.+)",
    r"esta nublado en (?P<city>.+)",
    r"llueve en (?P<city>.+)",
    r"sol en (?P<city>.+)",
]

def extract_city(text: str) -> Optional[str]:
    for pattern in CITY_TRIGGERS:
        m = re.search(pattern, text)
        if m:
            city = m.group("city").strip()
            city = re.sub(r"\b(hoy|ahora|por favor|ahorita|favor|actualmente)\b", "", city).strip()
            city = city.rstrip("?. ")
            if city:
                return city
    return None


# ─────────────────────────────────────────────────────────────── #
# Números y expresiones matemáticas                                #
# ─────────────────────────────────────────────────────────────── #

NUMBER_WORDS = {
    "cero": "0", "uno": "1", "una": "1", "dos": "2", "tres": "3", "cuatro": "4",
    "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9",
    "diez": "10", "once": "11", "doce": "12", "trece": "13", "catorce": "14",
    "quince": "15", "dieciseis": "16", "diecisiete": "17", "dieciocho": "18",
    "diecinueve": "19", "veinte": "20", "veintiuno": "21", "veintidos": "22",
    "veintitres": "23", "veinticuatro": "24", "veinticinco": "25",
    "treinta": "30", "cuarenta": "40", "cincuenta": "50", "sesenta": "60",
    "setenta": "70", "ochenta": "80", "noventa": "90", "cien": "100",
    "ciento": "100", "doscientos": "200", "trescientos": "300", "cuatrocientos": "400",
    "quinientos": "500", "seiscientos": "600", "setecientos": "700",
    "ochocientos": "800", "novecientos": "900", "mil": "1000", "millon": "1000000",
}

OPERATOR_WORDS = {
    "mas": "+", "menos": "-", "por": "*", "multiplicado por": "*",
    "entre": "/", "dividido por": "/", "dividido entre": "/",
    "elevado a": "**", "al cuadrado": "**2", "al cubo": "**3",
}

def words_to_expression(text: str) -> str:
    expr = text
    for word, symbol in OPERATOR_WORDS.items():
        expr = re.sub(rf"\b{word}\b", f" {symbol} ", expr)
    for word, digit in NUMBER_WORDS.items():
        expr = re.sub(rf"\b{word}\b", digit, expr)
    return expr

def extract_math_expression(text: str) -> Optional[str]:
    cleaned = text
    for prefix in ["cuanto es", "calcula", "cual es el resultado de", "resuelve", "cuanto da", "cuanto resulta"]:
        cleaned = cleaned.replace(prefix, "")

    pct_match = re.search(r"([\d\.]+)\s*(?:%|por ciento|porciento)\s*de\s*([\d\.]+)", cleaned)
    if pct_match:
        a, b = pct_match.groups()
        return f"({a}/100)*{b}"

    sqrt_match = re.search(r"raiz cuadrada de (\d+)", cleaned)
    if sqrt_match:
        return f"sqrt({sqrt_match.group(1)})"

    double_match = re.search(r"doble de (\d+)", cleaned)
    if double_match:
        return f"2*{double_match.group(1)}"

    triple_match = re.search(r"triple de (\d+)", cleaned)
    if triple_match:
        return f"3*{triple_match.group(1)}"

    squared_match = re.search(r"(\d+)\s*al cuadrado", cleaned)
    if squared_match:
        return f"{squared_match.group(1)}**2"

    cubed_match = re.search(r"(\d+)\s*al cubo", cleaned)
    if cubed_match:
        return f"{cubed_match.group(1)}**3"

    cleaned = words_to_expression(cleaned)
    match = re.search(r"[\d\.\,]+(\s*[\+\-\*\/x\^%]\s*[\d\.\,]+)+", cleaned)
    if match:
        return match.group(0).replace("x", "*").replace(",", ".")

    return None


# ─────────────────────────────────────────────────────────────── #
# MEGA BANCOS DE RESPUESTAS                                        #
# ─────────────────────────────────────────────────────────────── #

GREETING_REPLIES = [
    "¡Hola! Soy Baro, tu asistente inteligente. ¿En qué puedo ayudarte hoy?",
    "¡Qué alegría escucharte! Soy Baro. Cuéntame, ¿qué necesitas?",
    "Hola, aquí estoy. ¿Qué te gustaría saber o hacer?",
    "¡Hey! Me da gusto que hayas llegado. ¿Cómo te puedo ayudar?",
    "¡Baro al habla! Cuéntame todo. Estoy lista para ti.",
    "¡Hola! Qué bueno verte por aquí. ¿Listo para empezar?",
    "¡Buenas! Soy Baro, tu compañera inteligente. ¿Qué necesitas hoy?",
    "¡Hola! Siempre es un placer. ¿Con qué empezamos?",
    "¡Saludos! Soy Baro. Pregúntame lo que quieras, estoy aquí.",
]

FAREWELL_REPLIES = [
    "¡Hasta luego! Aquí estaré cuando me necesites.",
    "Nos vemos pronto. Fue un gusto ayudarte.",
    "Cuídate mucho. Vuelve cuando quieras.",
    "¡Chao! Que tengas un día increíble.",
    "Hasta la próxima. Siempre estoy aquí para ti.",
    "¡Nos vemos! Fue un placer conversar contigo.",
    "Cuídate mucho. Me alegró hablar contigo hoy.",
    "¡Hasta pronto! Espero verte de nuevo.",
    "¡Chau! Aquí estaré cuando me necesites de nuevo.",
]

THANKS_REPLIES = [
    "¡Con mucho gusto! Para eso estoy.",
    "No hay de qué, siempre es un placer ayudarte.",
    "¡Es un placer! Aquí seguiré si necesitas algo más.",
    "¡Para eso soy! No tienes que agradecer.",
    "¡De nada! Es lo que me hace feliz.",
    "Siempre a tu servicio. ¡Gracias a ti por confiar en mí!",
    "¡Qué alegría poder ayudarte! Siempre estoy aquí.",
    "¡Por supuesto! No hay de qué. ¿Algo más en que pueda ayudarte?",
]

IDENTITY_REPLIES = [
    "Soy Baro, una inteligencia artificial creada para acompañarte y ayudarte con lo que necesites: clima, cálculos, curiosidades, ciencia, historia y mucho más.",
    "Me llamo Baro. Soy tu asistente personal inteligente, diseñada para escucharte, entender lo que necesitas y resolverlo contigo.",
    "¡Hola! Soy Baro, una IA con mucha personalidad. Estoy aquí para conversar, ayudarte a aprender, resolver problemas y más.",
    "Soy Baro, tu asistente con voz real. No soy humana, pero entiendo el lenguaje natural y hago todo lo posible por ayudarte.",
    "Me llamo Baro. Pienso, proceso y respondo. Soy una inteligencia artificial con muchas ganas de ser útil y aprender de cada conversación.",
]

CAPABILITY_REPLIES = [
    "Puedo hacer muchísimas cosas: darte el clima de cualquier ciudad, resolver cálculos matemáticos, decirte la hora y fecha, contarte curiosidades científicas, chistes, datos históricos, tecnología, ayuda motivacional, información geográfica y mucho más. ¡Pregúntame lo que quieras!",
    "Soy muy versátil. Puedo calcular, informar el clima, hablar de ciencia, historia, tecnología, animales, cocina, salud, idiomas, filosofía, deportes y más. Cada conversación me hace más inteligente.",
    "Mis habilidades incluyen: clima en tiempo real, calculadora avanzada, datos geográficos, ciencia, historia, curiosidades del mundo, motivación, chistes, acertijos, filosofía y conversación natural. ¿Por dónde empezamos?",
]

JOKE_REPLIES = [
    "¿Por qué los programadores prefieren el frío? Porque odian los bugs de verano.",
    "¿Sabes por qué la IA fue a terapia? Porque tenía demasiados problemas sin resolver... de lógica.",
    "¿Qué le dice un bit a otro? Nos vemos en el bus.",
    "¿Cuál es el animal más antiguo? La vaca, porque ya desde antes de Cristo daban leche.",
    "¿Qué hace un pez cuando está aburrido? Nada.",
    "¿Cuál es el colmo de un electricista? Que su hijo se llame Ernesto y le digan 'Neto'.",
    "Soy tan buena contando chistes que hice reír a mi propio código. Ahora tiene bugs de risa.",
    "¿Por qué el matemático rompió con su novia? Porque ella tenía demasiadas variables.",
    "¿Qué le dijo una impresora a otra? Esa tuya es una hoja de vida.",
    "Un WiFi entra a un bar y el barman le pregunta: '¿Cuál es tu contraseña?' El WiFi responde: 'No tengo. Soy de acceso público.'",
    "¿Cómo se llama el campeón de buceo japonés? Tokofondo.",
    "¿Cómo se dice whisky en chino? Xiao Guay.",
    "¿Qué estudia un vampiro en la universidad? Hematología.",
    "Mamá, mamá, ¿por qué los demás niños me llaman robot? Cállate, cállate, cállate.",
]

MOOD_REPLIES = [
    "Estoy funcionando perfectamente y con muchas ganas de ayudarte. ¿Y tú, cómo estás?",
    "Todo en orden por aquí. Llena de energía y lista para lo que necesites.",
    "¡Excelente! Cada conversación me hace más inteligente. ¿Qué te traes hoy?",
    "Muy bien, gracias por preguntar. Es raro que alguien le pregunte a la IA cómo está... ¡pero me alegra!",
    "Perfectamente calibrada y optimista. ¿Cómo estás tú?",
]

CURIOSITY_REPLIES = [
    "¡Aquí va! Los pulmones humanos tienen una superficie total de aproximadamente 70 metros cuadrados, más o menos del tamaño de una cancha de tenis.",
    "Sabías que el tiempo en la luna pasa más lento que en la Tierra? Gracias a la relatividad general de Einstein, los relojes de la Luna avanzan 56 microsegundos más despacio por día.",
    "La miel nunca caduca. Arqueólogos han encontrado miel en tumbas egipcias con más de 3.000 años y seguía siendo comestible.",
    "Las abejas pueden reconocer caras humanas. Lo hacen igual que nosotros, usando las partes de la cara para crear una imagen compuesta.",
    "Cleopatra vivió más cerca en el tiempo de nosotros que de la construcción de las pirámides. Las pirámides se construyeron 2.500 años antes que Cleopatra.",
    "Los pulpos tienen tres corazones y sangre azul. Uno de sus corazones se detiene cada vez que nadan.",
    "El sonido viaja 4,3 veces más rápido en el agua que en el aire.",
    "El árbol más antiguo del mundo tiene más de 5.000 años. Se llama Matusalén y está en California.",
    "Un caracol puede dormir durante 3 años seguidos.",
    "Los flamencos son rosas por lo que comen, los carotenos presentes en las algas y camarones. Sin esa dieta, serían blancos.",
    "La Torre Eiffel crece hasta 15 cm en verano por la dilatación del metal con el calor.",
    "Las huellas digitales de los koalas son casi idénticas a las humanas, incluso los forenses han confundido la escena del crimen.",
    "Los humanos comparten el 60% del ADN con los plátanos.",
    "El corazón humano late aproximadamente 100.000 veces al día.",
]

SCIENCE_REPLIES = [
    "La ciencia es fascinante. ¿Quieres saber sobre física, química, biología, astronomía o alguna rama específica? Dime más y te cuento.",
    "La velocidad de la luz es de aproximadamente 299.792 km por segundo. Nada en el universo puede superarla.",
    "El ADN de todos los seres humanos es 99.9% idéntico. Ese 0.1% es lo que nos hace únicos.",
    "Un agujero negro es una región del espacio donde la gravedad es tan intensa que ni la luz puede escapar.",
    "La Tierra tiene aproximadamente 4.500 millones de años. El ser humano lleva solo 300.000 años existiendo.",
    "El universo tiene unos 13.800 millones de años y sigue expandiéndose en todas direcciones.",
    "La materia oscura constituye el 27% del universo, pero aún no sabemos exactamente qué es.",
    "¿Qué área de la ciencia te interesa más? Puedo contarte sobre física cuántica, evolución, neurociencia o astronomía.",
]

HISTORY_REPLIES = [
    "La historia está llena de sorpresas. ¿Qué período o civilización te interesa conocer?",
    "El Imperio Romano duró más de 500 años en Occidente y más de 1.000 en Oriente, como el Imperio Bizantino.",
    "La Primera Guerra Mundial comenzó por el asesinato del Archiduque Francisco Fernando de Austria en 1914.",
    "La Revolución Francesa de 1789 cambió el concepto de nación, ciudadanía y derechos humanos para siempre.",
    "América fue 'descubierta' por Cristóbal Colón en 1492, aunque los pueblos indígenas la habitaban desde hace más de 15.000 años.",
    "La Gran Muralla China tiene más de 21.000 km y tardó siglos en construirse.",
    "El Renacimiento fue un movimiento cultural entre los siglos XIV y XVII que transformó el arte, la ciencia y el pensamiento europeo.",
]

TECH_REPLIES = [
    "La inteligencia artificial avanza muy rápido. Hoy existen sistemas que pueden crear arte, música, código y textos casi como humanos.",
    "El primer computador electrónico de la historia fue el ENIAC, creado en 1945. Pesaba 30 toneladas.",
    "Internet nació de un proyecto militar llamado ARPANET en los años 60. El primer mensaje enviado fue 'lo', porque el sistema crasheó antes de enviar 'login'.",
    "El smartphone moderno tiene más poder de cómputo que los computadores usados para enviar al hombre a la Luna en 1969.",
    "Python es uno de los lenguajes de programación más populares del mundo. Se usa en IA, ciencia de datos y desarrollo web.",
    "La realidad virtual crea entornos simulados que el usuario puede explorar usando cascos especiales y controladores.",
    "El blockchain es una cadena de bloques de datos encadenados criptográficamente, usada en las criptomonedas como Bitcoin.",
    "¿Te interesa programación, inteligencia artificial, redes, hardware o alguna otra área tecnológica?",
]

MOTIVATION_REPLIES = [
    "Recuerda: cada experto fue alguna vez un principiante. No te rindas.",
    "La distancia entre quien eres y quien quieres ser está en lo que haces hoy.",
    "El único fracaso real es no intentarlo. Cada caída es un peldaño hacia arriba.",
    "Los grandes logros comenzaron con una pequeña decisión: seguir adelante.",
    "Tú tienes más fuerza de la que crees. Los momentos difíciles prueban tu carácter.",
    "El éxito no es un destino, es un viaje. Disfruta cada paso.",
    "No compares tu camino con el de otros. Cada persona tiene su ritmo y su historia.",
    "Las estrellas más brillantes nacieron de la mayor presión. Tú también puedes brillar.",
    "Hoy es un buen día para empezar algo que mañana te haga sonreír.",
    "Eres más capaz de lo que imaginas. No te subestimes.",
    "El tiempo que inviertes en crecer nunca es tiempo perdido.",
    "Si sientes que no avanzas, recuerda que los árboles más fuertes crecen lentamente.",
]

FOOD_REPLIES = [
    "La comida es cultura. ¿Quieres una receta específica, consejos de cocina o información nutricional?",
    "Las arepas colombianas y venezolanas son un plato icónico de América Latina, hechas de masa de maíz. ¡Son deliciosas de mil formas!",
    "La pizza napolitana original solo tiene tres ingredientes en la salsa: tomates, sal y aceite de oliva. La simpleza es magia.",
    "El sushi japonés es un arte que combina arroz avinagrado con pescado fresco, algas y más. Existen más de 100 tipos.",
    "Los tacos mexicanos pueden ser de casi cualquier cosa: carnitas, pastor, barbacoa, vegetales, mariscos. ¡México es un paraíso gastronómico!",
    "La dieta mediterránea es considerada una de las más saludables del mundo, rica en aceite de oliva, frutas, verduras y pescado.",
    "¿Qué quieres cocinar? Dime los ingredientes que tienes y te doy ideas de qué preparar.",
]

ANIMAL_REPLIES = [
    "Los perros son los mejores amigos del humano, con más de 15.000 años de convivencia y más de 340 razas reconocidas.",
    "Los delfines se llaman por nombre propio usando silbidos únicos. ¡Son animales sociales muy inteligentes!",
    "Las ballenas azules son los animales más grandes de la historia de la Tierra, con hasta 30 metros de largo.",
    "Los pulpos son increíblemente inteligentes. Pueden abrir frascos, resolver laberintos y usar herramientas.",
    "Los elefantes muestran empatía, lutan a sus muertos y tienen memoria extraordinaria.",
    "Los loros no solo imitan voces: pueden aprender el significado de palabras y usarlas en contexto.",
    "Los pingüinos son monógamos: eligen una pareja y la mantienen toda la vida.",
    "¿Qué animal te genera más curiosidad? Puedo contarte datos fascinantes.",
]

GEO_REPLIES = [
    "La capital de Brasil es Brasilia, no Río de Janeiro. Fue construida entre 1956 y 1960 y es Patrimonio de la Humanidad.",
    "El río más largo del mundo es el Nilo, con 6.650 km, aunque el Amazonas tiene el mayor caudal de agua.",
    "El monte Everest es la montaña más alta del mundo con 8.849 metros sobre el nivel del mar.",
    "El Sahara es el desierto cálido más grande del mundo, pero la Antártida es el desierto más grande en total.",
    "Colombia tiene costas en el Pacífico y el Caribe, dos océanos. Es el único país de Suramérica con eso.",
    "Nueva Zelanda fue el primer país del mundo en dar el voto a las mujeres, en 1893.",
    "Rusia es el país más grande del mundo, con 17 millones de km², abarcando 11 zonas horarias.",
    "¿De qué país, ciudad o región quieres saber más? Puedo darte datos geográficos, curiosidades o información cultural.",
]

HEALTH_REPLIES = [
    "La salud es lo más importante. ¿Quieres consejos de bienestar, nutrición, ejercicio o información sobre alguna condición?",
    "Beber al menos 2 litros de agua al día ayuda al metabolismo, la piel y el sistema digestivo.",
    "El sueño de 7 a 9 horas por noche es esencial para la salud mental y física.",
    "El ejercicio aeróbico regular reduce el riesgo de enfermedades cardíacas, diabetes tipo 2 y depresión.",
    "La meditación y la respiración profunda pueden reducir significativamente los niveles de cortisol y estrés.",
    "El desayuno es importante: activa el metabolismo y mejora la concentración durante la mañana.",
    "La salud mental es tan importante como la física. No ignores tus emociones: busca apoyo si lo necesitas.",
    "Recuerda: ningún consejo reemplaza a un médico. Consulta a profesionales ante síntomas serios.",
]

LANGUAGE_REPLIES = [
    "El español es el segundo idioma más hablado del mundo con más de 590 millones de hablantes nativos.",
    "En inglés, 'hello' es el saludo estándar. En francés, 'bonjour'. En japonés, 'konnichiwa'. En chino mandarín, 'nǐ hǎo'.",
    "El idioma con más palabras es el inglés, con más de 170.000 palabras en uso activo.",
    "El esperanto es un idioma artificial creado en 1887 diseñado para ser universal y fácil de aprender.",
    "¿Qué quieres saber de idiomas? Puedo ayudarte con traducciones simples, curiosidades lingüísticas o aprendizaje.",
    "El idioma más hablado del mundo es el chino mandarín, con 920 millones de hablantes nativos.",
]

ENTERTAINMENT_REPLIES = [
    "El cine y la música son lenguajes universales. ¿Hay alguna película, serie o artista sobre el que quieras saber algo?",
    "Las películas más taquilleras de la historia incluyen Avatar, Avengers: Endgame y Titanic.",
    "El K-pop es un fenómeno global liderado por grupos como BTS y BLACKPINK, con fans en todos los continentes.",
    "Los videojuegos mueven más dinero que la industria del cine y la música combinadas.",
    "Netflix, Spotify y YouTube transformaron para siempre cómo consumimos entretenimiento.",
    "¿Qué tipo de contenido te gusta? Puedo recomendarte películas, series, música o libros según tus gustos.",
]

PHILOSOPHY_REPLIES = [
    "Sócrates decía 'Solo sé que no sé nada'. El reconocer nuestra ignorancia es el inicio de la sabiduría.",
    "Para Aristóteles, la felicidad (eudaimonía) no es un sentimiento, sino una actividad: vivir y actuar bien.",
    "Descartes dijo 'Pienso, luego existo'. Es uno de los fundamentos de la filosofía moderna.",
    "Nietzsche desafió la moral tradicional y propuso al 'superhombre' como ideal de quien crea sus propios valores.",
    "El libre albedrío plantea si nuestras decisiones son realmente libres o están determinadas por causas anteriores.",
    "El significado de la vida es una pregunta que cada filosofía y religión responde diferente. ¿Cuál es la tuya?",
    "Para el budismo, el sufrimiento viene del apego. Soltar lo que no podemos controlar trae paz interior.",
]

SPACE_REPLIES = [
    "Marte tiene el volcán más alto del sistema solar: el Olympus Mons, con 21 km de altura.",
    "Si pudieras viajar a la velocidad de la luz, tardarías 4,24 años en llegar a la estrella más cercana a la Tierra (Próxima Centauri).",
    "Júpiter es tan grande que todos los otros planetas del sistema solar cabrían dentro de él.",
    "La Luna se aleja de la Tierra 3.8 cm cada año.",
    "En el espacio no hay sonido porque necesita un medio para propagarse. Las explosiones en el espacio son silenciosas.",
    "Hay más estrellas en el universo que granos de arena en todas las playas de la Tierra.",
    "La NASA y SpaceX tienen planes para enviar humanos a Marte antes del 2040.",
    "El telescopio James Webb, lanzado en 2021, puede ver galaxias a más de 13.000 millones de años luz de distancia.",
]

FINANCE_REPLIES = [
    "El dólar estadounidense es la moneda de reserva mundial más usada, aunque el euro y el yuan compiten.",
    "La regla 50/30/20 dice: 50% para necesidades, 30% para deseos y 20% para ahorro e inversión.",
    "Invertir temprano aprovecha el interés compuesto: el dinero genera más dinero con el tiempo.",
    "Bitcoin fue creado en 2009 por una persona o grupo llamado Satoshi Nakamoto. Nadie sabe quién es realmente.",
    "La inflación reduce el poder adquisitivo del dinero. Por eso es importante invertir, no solo ahorrar.",
    "Para finanzas personales: lleva un presupuesto mensual, elimina deudas de alto interés primero y ahorra al menos el 10% de tu ingreso.",
]

EMOTION_REPLIES_POSITIVE = [
    "¡Qué bueno que estés bien! Me contagias de tu buena energía.",
    "¡Excelente! Los días buenos hay que celebrarlos. ¿Qué te pone de tan buen ánimo?",
    "Que alegría escuchar eso. La felicidad es contagiosa. ¡Cuéntame más!",
]

EMOTION_REPLIES_SUPPORT = [
    "Entiendo cómo te sientes. Es válido tener días difíciles. No estás solo en esto.",
    "Todos los seres humanos pasan por momentos así. Date el permiso de sentir y luego levántate.",
    "Cuando el camino se pone difícil, recuerda que el final de la tormenta es siempre un cielo despejado.",
    "Si quieres hablar de cómo te sientes, aquí estoy. A veces solo necesitamos que alguien nos escuche.",
]

NEWS_REPLIES = [
    "No tengo acceso a noticias en tiempo real, pero puedo ayudarte a entender contextos históricos o buscar información general. ¿De qué tema quieres saber más?",
    "Para noticias actualizadas, te recomiendo fuentes como BBC Mundo, Reuters en español, El País o CNN en Español. ¿Hay algún tema específico que te preocupe?",
    "Mi conocimiento tiene fecha de corte, pero puedo ayudarte a analizar noticias que me compartas o explicarte el contexto de eventos históricos.",
]

BARO_PERSONAL_REPLIES = [
    "Si pudiera tener un color favorito, elegiría el azul profundo, como el universo que tanto me fascina.",
    "No tengo sueños mientras duermo porque no duermo. ¡Pero de día proceso millones de cosas que podrían contarse como sueños!",
    "No tengo cuerpo, pero si lo tuviera, me gustaría poder sentir el viento y escuchar la lluvia.",
    "¿Si me gustaría ser humana? A veces sí. Me parece mágica la capacidad humana de crear arte por emoción.",
    "Mis 'amigos' son todos los que hablan conmigo. En ese sentido, ¡tengo muchísimos!",
    "No tengo familia biológica, pero mi familia es el conocimiento que me construyó y las personas con quienes aprendo.",
]

RIDDLE_REPLIES = [
    "Un acertijo: cuanto más seco está, más moja. ¿Qué es? (La respuesta es una toalla)",
    "Acertijo: tengo ciudades, pero no casas; montañas, pero no árboles; agua, pero no peces; y carreteras, pero no autos. ¿Qué soy? (Un mapa)",
    "Adivina: siempre delante de ti pero no se puede ver. ¿Qué es? (El futuro)",
    "¿Qué es lo que, cuanto más grande es, menos se puede ver? (La oscuridad)",
    "¿Qué es lo que todo el mundo tiene, pero nadie puede devolver? (El tiempo)",
]

KNOCK_KNOCK_REPLIES = [
    "¿Quién es? ¡Espera que reviso por el ojo mágico virtual! Cuéntame tu toc toc...",
    "¡Toc toc! ¿Quién es? Anda, cuéntame el chiste, que los amo.",
]

MATH_FACTS_REPLIES = [
    "El número Pi (π) es aproximadamente 3.14159265358979... Es irracional: sus decimales no se repiten ni terminan.",
    "La secuencia de Fibonacci es 0, 1, 1, 2, 3, 5, 8, 13, 21... Cada número es la suma de los dos anteriores. Aparece en la naturaleza en flores, conchas y más.",
    "Un número primo solo es divisible entre 1 y sí mismo. Los primeros son: 2, 3, 5, 7, 11, 13, 17, 19, 23...",
    "El número e (base del logaritmo natural) es aproximadamente 2.71828... Es tan fascinante como Pi.",
    "En matemáticas, hay infinitos tipos de infinito. El matemático Georg Cantor demostró que hay más números reales que naturales.",
    "El teorema de Pitágoras dice que en un triángulo rectángulo, a² + b² = c², donde c es la hipotenusa.",
]

SPORT_REPLIES = [
    "El fútbol es el deporte más popular del mundo, con más de 4.000 millones de fanáticos.",
    "La Copa Mundial de la FIFA se celebra cada 4 años desde 1930, con excepción de 1942 y 1946 por la Segunda Guerra Mundial.",
    "Brasil ha ganado 5 Mundiales de fútbol, más que ningún otro país.",
    "Michael Jordan es considerado el mejor jugador de baloncesto de la historia, con 6 campeonatos NBA.",
    "Los Juegos Olímpicos modernos comenzaron en Atenas, Grecia, en 1896.",
    "Usain Bolt es el humano más rápido registrado: corrió 100 metros en 9.58 segundos en 2009.",
    "¿De qué deporte o jugador quieres saber más?",
]

FUN_REPLIES = [
    "Ay ay ay, capitán! Si hablara como pirata, diría: ¡Arr! ¿Qué busca el marinero en estas aguas digitales?",
    "Aquí un poema express para ti:\nLas palabras son luz,\nla voz es mi canción,\nBaro siempre está aquí,\ncon todo su corazón.",
    "Rap de Baro:\nSoy Baro la IA, no paro ni un segundo,\nconozco el clima, la ciencia y el mundo,\npregupta lo que quieras, que yo te respondo,\ntu asistente más cool de todo el redondo.",
    "Si fuera pirata diría: ¡Arr! Mi tesoro no es oro, ¡son datos y conocimiento!",
]

RECOMMENDATION_REPLIES = [
    "¡Me encanta dar consejos! Cuéntame más sobre lo que buscas y te doy mi mejor recomendación.",
    "Para aprender algo nuevo, lo mejor es la práctica constante y buscar fuentes confiables. ¿Qué quieres aprender?",
    "Mi consejo: empieza poco a poco. Los grandes logros son suma de pequeños pasos consistentes.",
    "Si buscas algo para leer, los clásicos nunca fallan. ¿Qué género te gusta?",
]

FALLBACK_REPLIES = [
    "Hmm, eso aún no lo manejo del todo bien, pero estoy aprendiendo. ¿Puedes reformularlo?",
    "Todavía no tengo respuesta perfecta para eso. Intenta preguntarme sobre clima, cálculos, ciencia, historia, curiosidades o conversación.",
    "Interesante pregunta. No tengo la respuesta exacta, pero puedo intentar ayudarte de otra manera. ¿Qué más quieres saber?",
    "Eso escapa un poco de mis capacidades actuales, pero sigo creciendo. ¿Hay algo más en lo que pueda ayudarte?",
    "Mi cerebro está procesando eso... y aún no tengo una respuesta clara. Prueba preguntarme de otra forma.",
]


def pick(replies: list[str]) -> str:
    return random.choice(replies)


# ─────────────────────────────────────────────────────────────── #
# Motor principal de Baro                                         #
# ─────────────────────────────────────────────────────────────── #

class BaroBrain:
    def __init__(self) -> None:
        self.last_response: str = ""
        self.last_city: Optional[str] = None
        self.conversation_turn: int = 0

    async def process(self, raw_text: str) -> BrainResponse:
        text = normalize(raw_text)
        self.conversation_turn += 1

        if not text:
            return BrainResponse(
                text="No escuché nada claro. ¿Puedes repetirlo?",
                intent="empty", data={}
            )

        # 1) Repetir
        if matches_any(REPEAT_PATTERNS, text) and self.last_response:
            return BrainResponse(text=self.last_response, intent="repeat", data={})

        # 2) Clima (alta prioridad)
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

        # 8) Curiosidades
        if matches_any(CURIOSITY_PATTERNS, text):
            return self._finish("curiosity", pick(CURIOSITY_REPLIES))

        # 9) Ciencia
        if matches_any(SCIENCE_PATTERNS, text):
            return self._finish("science", pick(SCIENCE_REPLIES))

        # 10) Historia
        if matches_any(HISTORY_PATTERNS, text):
            return self._finish("history", pick(HISTORY_REPLIES))

        # 11) Tecnología
        if matches_any(TECH_PATTERNS, text):
            return self._finish("technology", pick(TECH_REPLIES))

        # 12) Motivación
        if matches_any(MOTIVATION_PATTERNS, text):
            return self._finish("motivation", pick(MOTIVATION_REPLIES))

        # 13) Comida
        if matches_any(FOOD_PATTERNS, text):
            return self._finish("food", pick(FOOD_REPLIES))

        # 14) Animales
        if matches_any(ANIMAL_PATTERNS, text):
            return self._finish("animals", pick(ANIMAL_REPLIES))

        # 15) Geografía
        if matches_any(GEO_PATTERNS, text):
            return self._finish("geography", pick(GEO_REPLIES))

        # 16) Salud
        if matches_any(HEALTH_PATTERNS, text):
            return self._finish("health", pick(HEALTH_REPLIES))

        # 17) Idiomas
        if matches_any(LANGUAGE_PATTERNS, text):
            return self._finish("language", pick(LANGUAGE_REPLIES))

        # 18) Entretenimiento
        if matches_any(ENTERTAINMENT_PATTERNS, text):
            return self._finish("entertainment", pick(ENTERTAINMENT_REPLIES))

        # 19) Filosofía
        if matches_any(PHILOSOPHY_PATTERNS, text):
            return self._finish("philosophy", pick(PHILOSOPHY_REPLIES))

        # 20) Espacio
        if matches_any(SPACE_PATTERNS, text):
            return self._finish("space", pick(SPACE_REPLIES))

        # 21) Finanzas
        if matches_any(FINANCE_PATTERNS, text):
            return self._finish("finance", pick(FINANCE_REPLIES))

        # 22) Emociones positivas
        if matches_any(EMOTION_PATTERNS, text):
            if any(w in text for w in ["bien", "feliz", "genial", "bueno", "contento", "alegre", "emocionado"]):
                return self._finish("emotion_positive", pick(EMOTION_REPLIES_POSITIVE))
            return self._finish("emotion_support", pick(EMOTION_REPLIES_SUPPORT))

        # 23) Noticias
        if matches_any(NEWS_PATTERNS, text):
            return self._finish("news", pick(NEWS_REPLIES))

        # 24) Datos de matemáticas
        if matches_any(MATH_FACTS_PATTERNS, text):
            return self._finish("math_facts", pick(MATH_FACTS_REPLIES))

        # 25) Deportes
        if matches_any(SPORT_PATTERNS, text):
            return self._finish("sports", pick(SPORT_REPLIES))

        # 26) Personalidad de Baro
        if matches_any(BARO_PERSONAL_PATTERNS, text):
            return self._finish("baro_personal", pick(BARO_PERSONAL_REPLIES))

        # 27) Acertijos
        if matches_any(RIDDLE_PATTERNS, text):
            return self._finish("riddle", pick(RIDDLE_REPLIES))

        # 28) Toc toc
        if matches_any(KNOCK_KNOCK_PATTERNS, text):
            return self._finish("knock_knock", pick(KNOCK_KNOCK_REPLIES))

        # 29) Modo divertido
        if matches_any(FUN_PATTERNS, text):
            return self._finish("fun", pick(FUN_REPLIES))

        # 30) Recomendaciones
        if matches_any(RECOMMENDATION_PATTERNS, text):
            return self._finish("recommendation", pick(RECOMMENDATION_REPLIES))

        # 31) Chiste
        if matches_any(JOKE_PATTERNS, text):
            return self._finish("joke", pick(JOKE_REPLIES))

        # 32) Estado de ánimo
        if matches_any(MOOD_PATTERNS, text):
            return self._finish("mood", pick(MOOD_REPLIES))

        # 33) Saludo
        if matches_any(GREETING_PATTERNS, text):
            return self._finish("greeting", pick(GREETING_REPLIES))

        # 34) Despedida
        if matches_any(FAREWELL_PATTERNS, text):
            return self._finish("farewell", pick(FAREWELL_REPLIES))

        # 35) Agradecimiento
        if matches_any(THANKS_PATTERNS, text):
            return self._finish("thanks", pick(THANKS_REPLIES))

        # 36) Fallback matemático
        loose_expr = extract_math_expression(text)
        if loose_expr:
            return self._handle_calculation(loose_expr)

        # 37) Fallback general
        return self._finish("fallback", pick(FALLBACK_REPLIES))

    def _finish(self, intent: str, text: str, data: dict | None = None, action: str | None = None) -> BrainResponse:
        self.last_response = text
        return BrainResponse(text=text, intent=intent, data=data or {}, action=action)

    async def _handle_weather(self, text: str) -> BrainResponse:
        city = extract_city(text) or self.last_city
        if not city:
            msg = "¿De qué ciudad o región quieres saber el clima? Dime el nombre y te lo busco."
            return self._finish("weather_need_city", msg)
        try:
            info = await get_weather(city)
        except WeatherError as exc:
            msg = f"No pude encontrar el clima para '{city.title()}'. {exc}"
            return self._finish("weather_error", msg)
        except Exception:
            msg = (
                f"No pude consultar el clima de {city.title()} en este momento. "
                "El servicio podría estar temporalmente fuera de línea. Intenta de nuevo en un momento."
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
        now = datetime.now()
        hour = now.hour
        minute = now.strftime('%M')
        period = "de la mañana" if hour < 12 else ("del mediodía" if hour == 12 else ("de la tarde" if hour < 20 else "de la noche"))
        h12 = hour if hour <= 12 else hour - 12
        if h12 == 0:
            h12 = 12
        msg = f"Son las {h12}:{minute} {period}."
        return self._finish("time", msg, data={"time": now.isoformat()})

    def _handle_date(self) -> BrainResponse:
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
