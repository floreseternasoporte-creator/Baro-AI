# -*- coding: utf-8 -*-
"""
knowledge.py — Base de conocimiento factual de Baro.

Miles de datos curados: capitales del mundo, tabla periódica completa,
preguntas y respuestas de cultura general, curiosidades, chistes,
acertijos, refranes, citas célebres, cuentos, poemas, recetas,
consejos y un diccionario de traducción EN→ES.

Todo 100% local: cero APIs externas, cero dependencias de IA de terceros.
"""

from __future__ import annotations

import random
import re
import unicodedata


def _norm_es(text: str) -> str:
    nfkd = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _norm(text: str) -> str:
    return _norm_es(text)

# ─────────────────────────────────────────────────────────────── #
# CAPITALES DEL MUNDO (país → capital)                             #
# ─────────────────────────────────────────────────────────────── #

CAPITALS: dict[str, str] = {
    # América del Norte y Central
    "mexico": "Ciudad de México", "canada": "Ottawa",
    "estados unidos": "Washington D. C.", "guatemala": "Ciudad de Guatemala",
    "belice": "Belmopán", "honduras": "Tegucigalpa",
    "el salvador": "San Salvador", "nicaragua": "Managua",
    "costa rica": "San José", "panama": "Ciudad de Panamá",
    "cuba": "La Habana", "jamaica": "Kingston",
    "haiti": "Puerto Príncipe", "republica dominicana": "Santo Domingo",
    "bahamas": "Nasáu", "barbados": "Bridgetown",
    "trinidad y tobago": "Puerto España",
    # América del Sur
    "colombia": "Bogotá", "venezuela": "Caracas", "ecuador": "Quito",
    "peru": "Lima", "bolivia": "Sucre", "chile": "Santiago",
    "argentina": "Buenos Aires", "uruguay": "Montevideo",
    "paraguay": "Asunción", "brasil": "Brasilia",
    "guyana": "Georgetown", "surinam": "Paramaribo",
    # Europa
    "españa": "Madrid", "portugal": "Lisboa", "francia": "París",
    "italia": "Roma", "alemania": "Berlín", "reino unido": "Londres",
    "irlanda": "Dublín", "belgica": "Bruselas",
    "paises bajos": "Ámsterdam", "holanda": "Ámsterdam",
    "luxemburgo": "Luxemburgo", "suiza": "Berna", "austria": "Viena",
    "polonia": "Varsovia", "chequia": "Praga", "eslovaquia": "Bratislava",
    "hungria": "Budapest", "rumania": "Bucarest", "bulgaria": "Sofía",
    "grecia": "Atenas", "chipre": "Nicosia", "malta": "La Valeta",
    "dinamarca": "Copenhague", "suecia": "Estocolmo", "noruega": "Oslo",
    "finlandia": "Helsinki", "islandia": "Reikiavik",
    "estonia": "Tallin", "letonia": "Riga", "lituania": "Vilna",
    "ucrania": "Kiev", "bielorrusia": "Minsk", "moldavia": "Chisináu",
    "rusia": "Moscú", "serbia": "Belgrado", "croacia": "Zagreb",
    "eslovenia": "Liubliana", "bosnia y herzegovina": "Sarajevo",
    "montenegro": "Podgorica", "macedonia del norte": "Skopie",
    "albania": "Tirana",
    # Asia
    "china": "Pekín", "japon": "Tokio", "corea del sur": "Seúl",
    "corea del norte": "Pionyang", "mongolia": "Ulán Bator",
    "taiwan": "Taipéi", "vietnam": "Hanói", "laos": "Vientián",
    "camboya": "Nom Pen", "tailandia": "Bangkok", "myanmar": "Naipyidó",
    "malasia": "Kuala Lumpur", "singapur": "Singapur",
    "indonesia": "Yakarta", "filipinas": "Manila",
    "brunei": "Bandar Seri Begawan", "timor oriental": "Dili",
    "india": "Nueva Delhi", "pakistan": "Islamabad",
    "banglades": "Daca", "nepal": "Katmandú", "butan": "Timbu",
    "sri lanka": "Sri Jayawardenapura Kotte", "maldivas": "Malé",
    "afganistan": "Kabul", "iran": "Teherán", "irak": "Bagdad",
    "turquia": "Ankara", "siria": "Damasco", "libano": "Beirut",
    "israel": "Jerusalén", "jordania": "Amán",
    "arabia saudita": "Riad", "yemen": "Saná", "oman": "Mascate",
    "emiratos arabes unidos": "Abu Dabi", "catar": "Doha",
    "barein": "Manama", "kuwait": "Kuwait",
    "georgia": "Tiflis", "armenia": "Ereván", "azerbaiyan": "Bakú",
    "kazajistan": "Astaná", "uzbekistan": "Taskent",
    "turkmenistan": "Asjabad", "kirguistan": "Biskek",
    "tayikistan": "Dusambé",
    # África
    "egipto": "El Cairo", "libia": "Trípoli", "tunez": "Túnez",
    "argelia": "Argel", "marruecos": "Rabat", "sudan": "Jartum",
    "sudan del sur": "Yuba", "etiopia": "Adís Abeba",
    "eritrea": "Asmara", "yibuti": "Yibuti", "somalia": "Mogadiscio",
    "kenia": "Nairobi", "uganda": "Kampala", "tanzania": "Dodoma",
    "ruanda": "Kigali", "burundi": "Buyumbura",
    "republica democratica del congo": "Kinsasa",
    "republica del congo": "Brazzaville", "camerun": "Yaundé",
    "gabon": "Libreville", "guinea ecuatorial": "Malabo",
    "republica centroafricana": "Bangui", "chad": "Yamena",
    "niger": "Niamey", "nigeria": "Abuya", "benin": "Porto Novo",
    "togo": "Lomé", "ghana": "Acra",
    "costa de marfil": "Yamusukro", "liberia": "Monrovia",
    "sierra leona": "Freetown", "guinea": "Conakri",
    "guinea-bisau": "Bisáu", "senegal": "Dakar", "gambia": "Banjul",
    "mali": "Bamako", "burkina faso": "Uagadugú",
    "mauritania": "Nuakchot", "cabo verde": "Praia",
    "angola": "Luanda", "zambia": "Lusaka", "malaui": "Lilongüe",
    "mozambique": "Maputo", "zimbabue": "Harare",
    "botsuana": "Gaborone", "namibia": "Windhoek",
    "sudafrica": "Pretoria", "lesoto": "Maseru",
    "esuatini": "Mbabane", "madagascar": "Antananarivo",
    "mauricio": "Port Louis", "seychelles": "Victoria",
    "comoras": "Moroni",
    # Oceanía
    "australia": "Canberra", "nueva zelanda": "Wellington",
    "papua nueva guinea": "Port Moresby", "fiyi": "Suva",
    "islas salomon": "Honiara", "vanuatu": "Port Vila",
    "samoa": "Apia", "tonga": "Nukualofa", "kiribati": "Tarawa",
    "tuvalu": "Funafuti", "nauru": "Yaren", "palaos": "Ngerulmud",
    "islas marshall": "Majuro", "micronesia": "Palikir",
}

# Búsqueda inversa: capital → país
COUNTRY_BY_CAPITAL: dict[str, str] = {v.lower(): k for k, v in CAPITALS.items()}


def _norm(text: str) -> str:
    return _norm_es(text)


def answer_capital(query: str) -> str | None:
    """Responde preguntas sobre capitales de países."""
    q = _norm(query)
    # ¿Cuál es la capital de X?
    m = re.search(r"capital\s+de\s+([a-záéíóúñü\s]+?)(?:\?|$)", q)
    if m:
        country = m.group(1).strip()
        country = re.sub(r"\b(por favor|dime|me puedes decir)\b", "", country).strip()
        if country in CAPITALS:
            cap = CAPITALS[country]
            return (f"La capital de {country.title()} es **{cap}**. "
                    f"¿Quieres saber la capital de otro país?")
    # ¿De qué país es capital X?
    m = re.search(r"(?:de que pais es capital|capital\s+([a-záéíóúñü\s]+?)\s+de que pais)", q)
    if m:
        cap = m.group(1).strip() if m.group(1) else None
        if not cap:
            m2 = re.search(r"([a-záéíóúñü\s]+?)\s+es\s+capital\s+de\s+que\s+pais", q)
            cap = m2.group(1).strip() if m2 else None
        if cap and cap in COUNTRY_BY_CAPITAL:
            return f"**{cap.title()}** es la capital de {COUNTRY_BY_CAPITAL[cap].title()}."
    return None


# ─────────────────────────────────────────────────────────────── #
# TABLA PERIÓDICA COMPLETA (número, símbolo, nombre)               #
# ─────────────────────────────────────────────────────────────── #

ELEMENTS: list[tuple[int, str, str]] = [
    (1, "H", "Hidrógeno"), (2, "He", "Helio"), (3, "Li", "Litio"),
    (4, "Be", "Berilio"), (5, "B", "Boro"), (6, "C", "Carbono"),
    (7, "N", "Nitrógeno"), (8, "O", "Oxígeno"), (9, "F", "Flúor"),
    (10, "Ne", "Neón"), (11, "Na", "Sodio"), (12, "Mg", "Magnesio"),
    (13, "Al", "Aluminio"), (14, "Si", "Silicio"), (15, "P", "Fósforo"),
    (16, "S", "Azufre"), (17, "Cl", "Cloro"), (18, "Ar", "Argón"),
    (19, "K", "Potasio"), (20, "Ca", "Calcio"), (21, "Sc", "Escandio"),
    (22, "Ti", "Titanio"), (23, "V", "Vanadio"), (24, "Cr", "Cromo"),
    (25, "Mn", "Manganeso"), (26, "Fe", "Hierro"), (27, "Co", "Cobalto"),
    (28, "Ni", "Níquel"), (29, "Cu", "Cobre"), (30, "Zn", "Zinc"),
    (31, "Ga", "Galio"), (32, "Ge", "Germanio"), (33, "As", "Arsénico"),
    (34, "Se", "Selenio"), (35, "Br", "Bromo"), (36, "Kr", "Kriptón"),
    (37, "Rb", "Rubidio"), (38, "Sr", "Estroncio"), (39, "Y", "Itrio"),
    (40, "Zr", "Circonio"), (41, "Nb", "Niobio"), (42, "Mo", "Molibdeno"),
    (43, "Tc", "Tecnecio"), (44, "Ru", "Rutenio"), (45, "Rh", "Rodio"),
    (46, "Pd", "Paladio"), (47, "Ag", "Plata"), (48, "Cd", "Cadmio"),
    (49, "In", "Indio"), (50, "Sn", "Estaño"), (51, "Sb", "Antimonio"),
    (52, "Te", "Telurio"), (53, "I", "Yodo"), (54, "Xe", "Xenón"),
    (55, "Cs", "Cesio"), (56, "Ba", "Bario"), (57, "La", "Lantano"),
    (58, "Ce", "Cerio"), (59, "Pr", "Praseodimio"), (60, "Nd", "Neodimio"),
    (61, "Pm", "Prometio"), (62, "Sm", "Samario"), (63, "Eu", "Europio"),
    (64, "Gd", "Gadolinio"), (65, "Tb", "Terbio"), (66, "Dy", "Disprosio"),
    (67, "Ho", "Holmio"), (68, "Er", "Erbio"), (69, "Tm", "Tulio"),
    (70, "Yb", "Iterbio"), (71, "Lu", "Lutecio"), (72, "Hf", "Hafnio"),
    (73, "Ta", "Tantalio"), (74, "W", "Wolframio"), (75, "Re", "Renio"),
    (76, "Os", "Osmio"), (77, "Ir", "Iridio"), (78, "Pt", "Platino"),
    (79, "Au", "Oro"), (80, "Hg", "Mercurio"), (81, "Tl", "Talio"),
    (82, "Pb", "Plomo"), (83, "Bi", "Bismuto"), (84, "Po", "Polonio"),
    (85, "At", "Astato"), (86, "Rn", "Radón"), (87, "Fr", "Francio"),
    (88, "Ra", "Radio"), (89, "Ac", "Actinio"), (90, "Th", "Torio"),
    (91, "Pa", "Protactinio"), (92, "U", "Uranio"), (93, "Np", "Neptunio"),
    (94, "Pu", "Plutonio"), (95, "Am", "Americio"), (96, "Cm", "Curio"),
    (97, "Bk", "Berkelio"), (98, "Cf", "Californio"), (99, "Es", "Einsteinio"),
    (100, "Fm", "Fermio"), (101, "Md", "Mendelevio"), (102, "No", "Nobelio"),
    (103, "Lr", "Lawrencio"), (104, "Rf", "Rutherfordio"), (105, "Db", "Dubnio"),
    (106, "Sg", "Seaborgio"), (107, "Bh", "Bohrio"), (108, "Hs", "Hassio"),
    (109, "Mt", "Meitnerio"), (110, "Ds", "Darmstadio"), (111, "Rg", "Roentgenio"),
    (112, "Cn", "Copernicio"), (113, "Nh", "Nihonio"), (114, "Fl", "Flerovio"),
    (115, "Mc", "Moscovio"), (116, "Lv", "Livermorio"), (117, "Ts", "Teneso"),
    (118, "Og", "Oganesón"),
]

_ELEMENT_BY_NAME = {_norm_es(n): (num, sym, n) for num, sym, n in ELEMENTS}
_ELEMENT_BY_SYMBOL = {sym.lower(): (num, sym, n) for num, sym, n in ELEMENTS}


def answer_element(query: str) -> str | None:
    """Responde preguntas sobre elementos químicos."""
    q = _norm_es(query)
    # símbolo del X / numero atomico del X
    for key, (num, sym, name) in _ELEMENT_BY_NAME.items():
        if re.search(rf"\b{re.escape(key)}\b", q):
            if "simbolo" in q:
                return f"El símbolo químico del **{name}** es **{sym}**."
            if "numero atomico" in q or "número atómico" in query:
                return f"El **{name}** tiene número atómico **{num}**."
            if re.search(r"que (es|elemento es)|elemento", q):
                return (f"El **{name}** ({sym}) es el elemento químico número **{num}** "
                        f"de la tabla periódica.")
    # buscar por símbolo: "qué elemento es Au"
    m = re.search(r"elemento\s+(?:es\s+)?([a-z]{1,3})\b", q)
    if m and m.group(1) in _ELEMENT_BY_SYMBOL:
        num, sym, name = _ELEMENT_BY_SYMBOL[m.group(1)]
        return f"**{sym}** es el símbolo del **{name}**, elemento número {num}."
    # "cuántos elementos hay"
    if re.search(r"cuantos elementos (hay|tiene|existen)", q):
        return "La tabla periódica tiene **118 elementos** confirmados, del Hidrógeno (1) al Oganesón (118)."
    return None


# ─────────────────────────────────────────────────────────────── #
# PREGUNTAS Y RESPUESTAS DE CULTURA GENERAL                        #
# (pregunta, respuesta) — el motor las busca por similitud         #
# ─────────────────────────────────────────────────────────────── #

try:
    from country_facts import COUNTRY_QA
except ImportError:
    COUNTRY_QA = []

QA_FACTS: list[tuple[str, str]] = [
    # —— Ciencia ——
    ("quien propuso la teoria de la relatividad",
     "Albert Einstein propuso la teoría de la relatividad especial en 1905 y la general en 1915."),
    ("que es la fotosintesis",
     "La fotosíntesis es el proceso por el cual las plantas convierten luz solar, agua y CO₂ en glucosa y oxígeno."),
    ("cual es la velocidad de la luz",
     "La velocidad de la luz en el vacío es de 299,792 kilómetros por segundo."),
    ("que es un agujero negro",
     "Un agujero negro es una región del espacio donde la gravedad es tan intensa que nada, ni siquiera la luz, puede escapar."),
    ("quien descubrio la penicilina",
     "Alexander Fleming descubrió la penicilina en 1928, por accidente, al observar un moho que mataba bacterias."),
    ("que es el adn",
     "El ADN (ácido desoxirribonucleico) es la molécula que contiene las instrucciones genéticas de todos los seres vivos."),
    ("cuantos huesos tiene el cuerpo humano",
     "El cuerpo humano adulto tiene 206 huesos. Los bebés nacen con alrededor de 300, que luego se fusionan."),
    ("que es la gravedad",
     "La gravedad es la fuerza de atracción entre objetos con masa. Newton la describió y Einstein la explicó como curvatura del espacio-tiempo."),
    ("quien formulo la teoria de la evolucion",
     "Charles Darwin formuló la teoría de la evolución por selección natural en su libro 'El origen de las especies' (1859)."),
    ("que es un atomo",
     "El átomo es la unidad básica de la materia: un núcleo de protones y neutrones rodeado por electrones."),
    ("cual es el planeta mas grande del sistema solar",
     "Júpiter es el planeta más grande del sistema solar: cabrían más de 1,300 Tierras dentro de él."),
    ("cual es el planeta mas cercano al sol",
     "Mercurio es el planeta más cercano al Sol, a unos 58 millones de kilómetros."),
    ("cuanto dura un dia en marte",
     "Un día en Marte (un 'sol') dura 24 horas y 37 minutos, muy parecido al día terrestre."),
    ("que es la via lactea",
     "La Vía Láctea es nuestra galaxia: una espiral barrada con entre 200,000 y 400,000 millones de estrellas."),
    ("quien fue el primer hombre en pisar la luna",
     "Neil Armstrong fue el primer humano en pisar la Luna, el 20 de julio de 1969, en la misión Apolo 11."),
    ("que es la energia nuclear",
     "La energía nuclear se obtiene de la fisión (división) o fusión (unión) de núcleos atómicos, liberando enormes cantidades de energía."),
    ("como se produce un arcoiris",
     "El arcoíris se produce cuando la luz del sol se refracta y refleja dentro de las gotas de lluvia, separándose en sus colores."),
    ("por que el cielo es azul",
     "El cielo es azul por la dispersión de Rayleigh: las moléculas del aire dispersan más la luz azul que la roja."),
    ("que es un eclipse solar",
     "Un eclipse solar ocurre cuando la Luna se interpone entre la Tierra y el Sol, bloqueando total o parcialmente su luz."),
    ("cual es la montana mas alta del mundo",
     "El Monte Everest, con 8,849 metros sobre el nivel del mar, es la montaña más alta del mundo."),
    # —— Historia ——
    ("cuando fue la segunda guerra mundial",
     "La Segunda Guerra Mundial ocurrió entre 1939 y 1945, y fue el conflicto más devastador de la historia."),
    ("quien fue simon bolivar",
     "Simón Bolívar (1783-1830) fue el libertador de seis naciones sudamericanas del dominio español: Venezuela, Colombia, Ecuador, Perú, Bolivia y Panamá."),
    ("que fue la revolucion francesa",
     "La Revolución Francesa (1789) derrocó la monarquía absoluta y estableció los principios de libertad, igualdad y fraternidad."),
    ("quien construyo las piramides de egipto",
     "Las pirámides de Giza fueron construidas por faraones del Imperio Antiguo egipcio, hace unos 4,500 años, con mano de obra organizada."),
    ("cuando cayo el muro de berlin",
     "El Muro de Berlín cayó el 9 de noviembre de 1989, marcando el fin de la Guerra Fría."),
    ("quien fue cleopatra",
     "Cleopatra VII fue la última reina del Egipto ptolemaico (69-30 a.C.), famosa por su inteligencia y alianzas con Julio César y Marco Antonio."),
    ("que fue el imperio romano",
     "El Imperio Romano dominó Europa, el norte de África y Oriente Medio durante más de 500 años, dejando el derecho, la lengua y la arquitectura como legado."),
    ("quien descubrio america",
     "Cristóbal Colón llegó a América el 12 de octubre de 1492, aunque el continente ya estaba habitado por millones de personas."),
    ("que fue la guerra fria",
     "La Guerra Fría (1947-1991) fue la rivalidad geopolítica entre Estados Unidos y la Unión Soviética, sin guerra directa entre ellos."),
    ("quien fue mahatma gandhi",
     "Mahatma Gandhi lideró la independencia de la India del Imperio Británico mediante la resistencia no violenta."),
    # —— Geografía ——
    ("cual es el rio mas largo del mundo",
     "El Nilo (unos 6,650 km) y el Amazonas (unos 6,400 km) se disputan el título; tradicionalmente se considera al Nilo el más largo."),
    ("cual es el desierto mas grande del mundo",
     "El desierto más grande del mundo es el Antártico (14 millones de km²); el desierto cálido más grande es el Sahara."),
    ("cual es el oceano mas grande",
     "El Océano Pacífico es el más grande: cubre más superficie que todos los continentes juntos."),
    ("cual es el pais mas grande del mundo",
     "Rusia es el país más grande del mundo, con más de 17 millones de km² y 11 zonas horarias."),
    ("cual es el pais mas pequeno del mundo",
     "La Ciudad del Vaticano, con 0.44 km², es el país más pequeño del mundo."),
    ("donde esta machu picchu",
     "Machu Picchu está en la región de Cusco, Perú, a 2,430 metros de altura en los Andes. Fue construida por los incas en el siglo XV."),
    ("cual es la capital de egipto",
     "La capital de Egipto es El Cairo, la ciudad más grande del mundo árabe."),
    # —— Tecnología ——
    ("quien invento la world wide web",
     "Tim Berners-Lee inventó la World Wide Web en 1989 en el CERN y la liberó gratis para todo el mundo."),
    ("que es la inteligencia artificial",
     "La inteligencia artificial es la capacidad de las máquinas para realizar tareas que requieren inteligencia humana: aprender, razonar y decidir."),
    ("que es el machine learning",
     "El machine learning es una rama de la IA donde los sistemas aprenden patrones a partir de datos, sin ser programados explícitamente para cada caso."),
    ("quienes fundaron apple",
     "Apple fue fundada en 1976 por Steve Jobs, Steve Wozniak y Ronald Wayne."),
    ("quien fundo microsoft",
     "Microsoft fue fundada en 1975 por Bill Gates y Paul Allen."),
    ("que es un algoritmo",
     "Un algoritmo es una secuencia finita de pasos bien definidos para resolver un problema o realizar una tarea."),
    ("que es python en programacion",
     "Python es un lenguaje de programación de alto nivel, famoso por su sintaxis clara y su uso en IA, ciencia de datos y desarrollo web."),
    ("que es la computacion cuantica",
     "La computación cuántica usa qubits, que pueden estar en superposición de estados, para resolver ciertos problemas exponencialmente más rápido."),
    # —— Arte y literatura ——
    ("quien pinto la mona lisa",
     "Leonardo da Vinci pintó la Mona Lisa entre 1503 y 1506. Está en el museo del Louvre, en París."),
    ("quien escribio don quijote",
     "Miguel de Cervantes escribió 'Don Quijote de la Mancha', publicada en 1605 y considerada la primera novela moderna."),
    ("quien escribio cien anos de soledad",
     "Gabriel García Márquez, escritor colombiano y Nobel de Literatura 1982, escribió 'Cien años de soledad' (1967)."),
    ("quien fue frida kahlo",
     "Frida Kahlo (1907-1954) fue una pintora mexicana famosa por sus autorretratos que mezclan dolor, identidad y cultura mexicana."),
    ("quien compuso la novena sinfonia",
     "Ludwig van Beethoven compuso la Novena Sinfonía, estrenada en 1824 cuando ya estaba totalmente sordo."),
    ("quien escribio romeo y julieta",
     "William Shakespeare escribió 'Romeo y Julieta' alrededor de 1595."),
    # —— Deportes ——
    ("quien ha ganado mas mundiales de futbol",
     "Brasil ha ganado 5 Copas del Mundo de fútbol (1958, 1962, 1970, 1994 y 2002), más que ningún otro país."),
    ("quien es usain bolt",
     "Usain Bolt es el velocista jamaiquino dueño del récord mundial de 100 metros: 9.58 segundos (2009)."),
    ("cada cuanto son los juegos olimpicos",
     "Los Juegos Olímpicos se celebran cada 4 años, alternando ediciones de verano e invierno cada 2 años."),
    # —— Cuerpo y salud ——
    ("cuantos litros de sangre tiene el cuerpo",
     "Un adulto promedio tiene entre 4.5 y 6 litros de sangre."),
    ("cual es el hueso mas largo del cuerpo",
     "El fémur, el hueso del muslo, es el más largo y fuerte del cuerpo humano."),
    ("cual es el musculo mas fuerte del cuerpo",
     "El masetero (mandíbula) es el más fuerte por peso; el glúteo mayor es el más grande."),
    ("cuanto pesa el cerebro humano",
     "El cerebro humano adulto pesa en promedio 1.3 a 1.4 kilogramos."),
    # —— Naturaleza ——
    ("cual es el animal mas rapido del mundo",
     "El halcón peregrino es el animal más rápido: alcanza 390 km/h en picada."),
    ("cual es el animal mas grande del mundo",
     "La ballena azul es el animal más grande que ha existido: hasta 33 metros y 180 toneladas."),
    ("cuanto vive una tortuga",
     "Algunas tortugas gigantes viven más de 150 años; la tortuga más longeva registrada vivió 189 años."),
    ("que comen los koalas",
     "Los koalas comen casi exclusivamente hojas de eucalipto, que son tóxicas para la mayoría de los animales."),
    # —— Varios ——
    ("quien escribio la teoria del big bang",
     "El sacerdote y físico Georges Lemaître propuso en 1927 la teoría del átomo primigenio, base del Big Bang."),
    ("cuantos dias tiene un ano bisiesto",
     "Un año bisiesto tiene 366 días; ocurre cada 4 años (con excepciones cada 100 y 400 años)."),
    ("por que se celebra el dia de muertos",
     "El Día de Muertos (1 y 2 de noviembre) es una tradición mexicana, patrimonio de la humanidad, que honra a los difuntos con ofrendas y celebración."),
    ("que es la unesco",
     "La UNESCO es la agencia de la ONU para la educación, la ciencia y la cultura, creada en 1945."),
    ("cual es la moneda de japon",
     "La moneda de Japón es el yen (¥)."),
    ("cual es la moneda del reino unido",
     "La moneda del Reino Unido es la libra esterlina (£)."),
    ("que idioma se habla en brasil",
     "En Brasil se habla portugués; es el único país de América Latina con ese idioma oficial."),
    ("cuantos continentes hay",
     "Hay 7 continentes: América, Europa, África, Asia, Oceanía, Antártida... y según el modelo, América se divide en Norte y Sur."),
    ("que es el efecto invernadero",
     "El efecto invernadero es el proceso por el cual gases como el CO₂ atrapan el calor del sol en la atmósfera, calentando el planeta."),
]


# ─────────────────────────────────────────────────────────────── #
# DATOS CURIOSOS                                                   #
# ─────────────────────────────────────────────────────────────── #

CURIOSITIES: list[str] = [
    "Los pulpos tienen tres corazones y sangre azul.",
    "La miel nunca caduca: se han encontrado tarros comestibles en tumbas egipcias de 3,000 años.",
    "El corazón de un camarón está en su cabeza.",
    "Venus es el único planeta que gira en sentido horario.",
    "Un rayo es 5 veces más caliente que la superficie del Sol.",
    "Los flamencos nacen grises; el color rosado viene de su comida.",
    "El ADN humano desenrollado mediría unos 2 metros por célula.",
    "Las jirafas duermen solo 30 minutos al día, en siestas cortas.",
    "El Monte Olimpo en Marte es 3 veces más alto que el Everest.",
    "Los tiburones existían antes que los árboles: 450 millones de años.",
    "Una nube promedio pesa unas 500 toneladas.",
    "Los canguros no pueden caminar hacia atrás.",
    "El 90% de las especies del océano aún no han sido descubiertas.",
    "La Gran Muralla China es visible desde el espacio solo en condiciones muy específicas.",
    "Los elefantes son de los pocos animales que se reconocen en un espejo.",
    "El agua caliente puede congelarse más rápido que la fría (efecto Mpemba).",
    "La mordida de un cocodrilo del Nilo alcanza 1,600 kg de fuerza, la más potente del reino animal.",
    "Los bebés nacen con 300 huesos; los adultos tienen 206.",
    "El desierto del Sahara fue una sabana verde hace 6,000 años.",
    "Las medusas no tienen cerebro, corazón ni huesos.",
    "Un caracol puede dormir hasta 3 años.",
    "La Torre Eiffel crece 15 cm en verano por la dilatación del metal.",
    "Los delfines duermen con un ojo abierto y medio cerebro despierto.",
    "El oro es tan maleable que 28 gramos pueden cubrir 9 metros cuadrados.",
    "Hay más estrellas en el universo que granos de arena en todas las playas.",
    "El cuerpo humano produce 25 millones de células nuevas cada segundo.",
    "Los búhos no pueden mover los ojos; giran la cabeza 270 grados.",
    "La primera llamada de celular se hizo en 1973.",
    "Los gatos no pueden saborear lo dulce.",
    "El 70% del oxígeno que respiramos viene del océano, no de los bosques.",
    "Un lápiz puede escribir 45,000 palabras antes de acabarse.",
    "Las hormigas no tienen pulmones; respiran por espiráculos.",
    "El sonido viaja 4 veces más rápido en el agua que en el aire.",
    "Cleopatra vivió más cerca de nosotros que de la construcción de las pirámides.",
    "Los koalas tienen huellas dactilares casi idénticas a las humanas.",
    "Un día en Venus dura más que un año en Venus.",
    "El cerebro genera unos 20 vatios de energía eléctrica.",
    "Las abejas se comunican con un 'baile' que indica dirección y distancia.",
    "El vidrio tarda un millón de años en descomponerse.",
    "Los pingüinos se proponen matrimonio con una piedra.",
    "El Amazonas representa la mitad de la selva tropical del planeta.",
    "Una persona parpadea unas 20,000 veces al día.",
    "Los plátanos son ligeramente radiactivos por el potasio-40.",
    "El ajedrez tiene más partidas posibles que átomos en el universo observable.",
    "Los murciélagos son los únicos mamíferos que vuelan de verdad.",
    "La piel es el órgano más grande del cuerpo humano.",
    "Un estornudo viaja a 160 km/h.",
    "Los pulpos pueden cambiar de color y textura en 0.3 segundos.",
    "El lago más profundo del mundo, el Baikal, tiene 1,642 metros.",
    "Las vacas tienen mejores amigas y se estresan al separarse.",
    "El 8% de los hombres son daltónicos, contra el 0.5% de las mujeres.",
    "Un grano de arena en una ostra puede tardar 6 años en volverse perla.",
    "Los caballos pueden dormir de pie gracias a un sistema de bloqueo en las patas.",
    "El primer semáforo se instaló en Londres en 1868 y explotó.",
    "Las estrellas de mar no tienen cerebro ni sangre.",
    "Un colibrí aletea 80 veces por segundo.",
    "El queso más caro del mundo se hace con leche de burra: 1,000 euros el kilo.",
    "Los humanos y las jirafas tienen el mismo número de vértebras en el cuello: 7.",
    "El 60% del cuerpo humano adulto es agua.",
    "Una cucaracha puede vivir semanas sin cabeza.",
    "El papel no se puede doblar más de 7 veces... con métodos especiales se ha llegado a 13.",
    "Los leones machos duermen hasta 20 horas al día.",
    "El Everest crece 4 milímetros cada año.",
    "Hay más bacterias en tu cuerpo que células humanas.",
    "El helado se inventó en China hace 4,000 años.",
    "Un rayo puede partir un árbol por la rápida expansión del vapor.",
    "Los camellos almacenan grasa en la joroba, no agua.",
    "El alfabeto hawaiano tiene solo 12 letras.",
    "Un pulpo tiene 9 cerebros: uno central y uno en cada brazo.",
    "La Gran Barrera de Coral es visible desde el espacio.",
    "Los elefantes 'escuchan' con las patas las vibraciones del suelo.",
    "El café es la segunda mercancía más comercializada del mundo, después del petróleo.",
    "Un hipopótamo puede correr a 30 km/h.",
    "Las lágrimas de cocodrilo son reales: lloran al comer para lubricar los ojos.",
    "El 11% de la población mundial es zurda.",
    "Un terremoto en Chile en 1960 movió el eje de la Tierra.",
    "Las mariposas saborean con los pies.",
    "El vidrio de las botellas verdes protege mejor del sol.",
    "Un kilo de azafrán necesita 150,000 flores y cuesta miles de dólares.",
    "Los pandas pasan 14 horas al día comiendo bambú.",
    "El corazón de la ballena azul late 4 veces por minuto.",
    "Las huellas de la lengua son únicas, como las dactilares.",
    "Un año luz son 9.46 billones de kilómetros.",
    "Los flamencos duermen parados en una pata.",
    "El 90% del wasabi que se vende es rábano picante teñido.",
    "Un caracol tiene 14,000 dientes microscópicos.",
    "La Estatua de la Libertad fue un regalo de Francia en 1886.",
    "Los guepardos no rugen; maúllan y ronronean.",
    "El 2% del agua de la Tierra es dulce y accesible.",
    "Una abeja visita 50 flores por viaje.",
    "Los diamantes se forman a 150 km bajo tierra.",
    "El primer videojuego, Pong, salió en 1972.",
    "Un cabello humano soporta 100 gramos de peso.",
    "Las nutrias se toman de las patas para no separarse al dormir.",
    "El récord de apnea es de 24 minutos bajo el agua.",
    "Los loros pueden vivir 80 años.",
    "Un tornado puede girar a 480 km/h.",
    "El chocolate era moneda para los aztecas.",
    "Las jirafas tienen la lengua de 50 cm y es azul oscuro.",
    "Un humano produce 1.5 litros de saliva al día.",
    "El Polo Sur es el lugar más seco de la Tierra.",
    "Los erizos se comunican con 13 sonidos distintos.",
    "Una semilla de secuoya pesa menos que una aspirina y crece 100 metros.",
    "El 70% de la superficie terrestre es agua.",
    "Los escorpiones brillan bajo luz ultravioleta.",
    "Un avión comercial vuela a 900 km/h a 11,000 metros.",
    "Las cebras son negras con rayas blancas, no al revés.",
    "El récord de resolver un cubo de Rubik es 3.13 segundos.",
    "Un lobo puede oír a 10 km de distancia.",
    "Las perlas se disuelven en vinagre.",
    "El cerebro no siente dolor: no tiene receptores.",
    "Un castor puede talar un árbol en minutos.",
    "El primer maratón olímpico moderno fue en Atenas 1896.",
    "Las arañas no son insectos: tienen 8 patas.",
    "Un rayo cae 8 millones de veces al día en la Tierra.",
    "El colmillo del narval es un diente que crece 3 metros.",
    "Los osos polares tienen la piel negra bajo el pelaje blanco.",
    "Un huevo de avestruz equivale a 24 huevos de gallina.",
    "El 99% del oro de la Tierra está en su núcleo.",
    "Las luciérnagas producen luz fría, sin calor.",
    "Un camión de bomberos en Japón dice 'fire' en inglés por tradición.",
    "El récord de personas en el espacio a la vez es 19.",
    "Los tiburones no tienen huesos: su esqueleto es cartílago.",
    "Una gota de agua contiene 1.67 sextillones de moléculas.",
    "El 80% de las especies vive en el 20% del planeta (puntos calientes).",
    "Los camaleones disparan la lengua al doble de su cuerpo.",
    "Un relámpago calienta el aire a 30,000 °C.",
    "Las termitas construyen torres de 8 metros.",
    "El primer email se envió en 1971.",
    "Un bebé ríe 300 veces al día; un adulto, 20.",
    "Los anillos de Saturno tienen 280,000 km de ancho y 10 metros de grosor.",
    "El 5% del océano ha sido explorado.",
    "Una momia egipcia podía tardar 70 días en prepararse.",
    "Los pulgones nacen embarazados.",
    "El récord de estar despierto es 11 días.",
    "Un corazón de colibrí late 1,200 veces por minuto.",
    "Las pirámides se alinean con la constelación de Orión.",
    "El 40% de la comida mundial se desperdicia.",
    "Un koala duerme 22 horas al día.",
    "Las huellas nasales de los perros son únicas.",
    "El vidrio es un líquido súper enfriado, no un sólido perfecto.",
    "Un tsunami puede viajar a 800 km/h en mar abierto.",
    "Los flamencos filtran comida con el pico invertido.",
    "El primer cajero automático se instaló en Londres en 1967.",
    "Una estrella fugaz es un grano de arena quemándose a 60 km/s.",
    "Los cerdos no pueden mirar al cielo.",
    "El 10% de la electricidad mundial la consumen centros de datos.",
    "Un perezoso tarda un mes en digerir una hoja.",
    "Las cataratas del Niágara se formaron hace 12,000 años.",
    "El récord de memoria: recitar 100,000 dígitos de Pi.",
    "Un delfín duerme con medio cerebro despierto.",
    "Los Vikingos usaban piedras solares para navegar nublados.",
    "El 1% de las personas puede mover las orejas a voluntad.",
    "Una araña puede vivir un año sin comer.",
    "El café más caro lo 'procesan' civetas: 600 dólares el kilo.",
    "Los huesos son 5 veces más fuertes que el acero del mismo peso.",
    "Un eclipse solar total ocurre cada 18 meses en algún lugar.",
    "Las abejas reinas viven 5 años; las obreras, 6 semanas.",
    "El Sáhara avanza 48 km por año hacia el sur.",
    "Un pulso de quásar puede superar una galaxia entera en brillo.",
    "Los gatos tienen 32 músculos en cada oreja.",
    "El 90% de los mensajes en botellas nunca se encuentran.",
    "Una ballena jorobada canta canciones que duran horas.",
    "El primer libro impreso con tipos móviles fue en Corea, 1377.",
    "Los mosquitos prefieren a las personas con sangre tipo O.",
    "Un grano de arroz alimenta a media humanidad cada día.",
    "El récord de salto de un canguro: 9 metros de largo.",
    "Las medusas inmortales (Turritopsis) pueden rejuvenecer indefinidamente.",
    "Un volcán en erupción puede lanzar ceniza a 40 km de altura.",
    "Los bebés elefante maman con la trompa los primeros meses.",
    "El 3% del agua dulce está en glaciares.",
    "Una tormenta solar en 1859 incendió telégrafos en todo el mundo.",
    "Los zorros usan el campo magnético para cazar.",
    "El récord de buceo libre: 214 metros.",
    "Los limones flotan en el agua porque su cáscara porosa atrapa aire.",
    "Las estrellas más grandes explotan como supernovas.",
    "Más del 60% del tráfico de internet mundial ya viene de teléfonos móviles.",
    "Un camello puede beber 200 litros de agua en 3 minutos.",
    "Los girasoles jóvenes siguen al sol (heliotropismo).",
    "El récord Guinness del pelo más largo: 5.6 metros.",
    "Una hormiga reina vive 30 años.",
    "Los icebergs son agua dulce congelada.",
    "El 25% de los mamíferos son murciélagos.",
    "Un caracol marino (cono) tiene veneno mortal para humanos.",
    "Las nubes mammatus anuncian tormentas severas.",
    "El primer trasplante de corazón fue en 1967.",
    "Un lápiz de grafito escribe en gravedad cero.",
    "Los árboles se comunican por redes de hongos ('wood wide web').",
    "El 80% del cerebro es agua.",
    "Una ostra cambia de sexo varias veces en su vida.",
    "El récord de temperatura: 56.7 °C en el Valle de la Muerte (1913).",
    "Los pingüinos emperador incuban el huevo sobre los pies a -60 °C.",
    "Un rayo gamma dura milisegundos y libera más energía que el Sol en su vida.",
    "Las vacas muguen con acento regional.",
    "El 15% de las personas estornuda con la luz del sol (reflejo fótico).",
    "Una telaraña es 5 veces más resistente que el acero del mismo grosor.",
    "Los dromedarios tienen una joroba; los bactrianos, dos.",
    "El primer semáforo eléctrico se instaló en Cleveland en 1914.",
    "Un calamar gigante tiene ojos de 27 cm, los más grandes del reino animal.",
    "Las luciérnagas sincronizan sus destellos en el sudeste asiático.",
    "El 60% de las especies de aves migra.",
    "Una gota de petróleo contamina 25 litros de agua.",
    "Los castores son los segundos roedores más grandes del mundo.",
    "El récord de ajedrez a ciegas: 48 partidas simultáneas.",
    "Un feto puede oír desde la semana 18.",
    "Las estrellas fugaces más famosas, las Perseidas, ocurren cada agosto.",
]



# ─────────────────────────────────────────────────────────────── #
# CHISTES                                                          #
# ─────────────────────────────────────────────────────────────── #

JOKES: list[str] = [
    "¿Por qué los programadores prefieren el frío? Porque odian los bugs de verano. 🐛",
    "¿Qué le dijo un bit a otro? Nos vemos en el bus. 🚌",
    "¿Por qué la IA fue a terapia? Tenía demasiados problemas sin resolver... de lógica. 🤖",
    "¿Qué hace un pez cuando está aburrido? Nada. 🐟",
    "¿Por qué el matemático rompió con su novia? Tenía demasiadas variables. 📐",
    "¿Cuál es el colmo de un electricista? Que su hijo le diga 'no me conectes'. ⚡",
    "¿Qué le dice una impresora a otra? Esa hoja tuya es una hoja de vida. 🖨️",
    "¿Cómo se despiden los químicos? Ácido un placer. 🧪",
    "¿Cuál es el animal más antiguo? La vaca: antes de Cristo ya daba BCE (leche). 🐄",
    "¿Qué le dijo el cero al ocho? ¡Bonito cinturón! 0️⃣8️⃣",
    "¿Por qué los esqueletos no pelean? Porque no tienen agallas. 💀",
    "¿Cómo llamas a un perro sin patas? Da igual, no va a venir. 🐶",
    "¿Qué hace una abeja en el gimnasio? ¡Zum-ba! 🐝",
    "¿Por qué el libro de matemáticas estaba triste? Tenía demasiados problemas. 📚",
    "¿Qué le dice el 1 al 10? Para ser como yo, tienes que ser sincero. 1️⃣",
    "¿Cuál es el colmo de un jardinero? Que su hijo sea un capullo. 🌱",
    "¿Por qué las focas miran siempre hacia arriba? Porque ahí están los focos. 🔦",
    "¿Qué hace un mudo bailando? Una mudanza. 💃",
    "¿Por qué el astronauta rompió con su novia? Necesitaba espacio. 🚀",
    "¿Qué le dijo la luna al sol? Quédate, que me das luz. 🌙",
    "¿Cuál es el colmo de Aladdín? Tener mal genio. 🧞",
    "¿Por qué el tomate no duerme? Porque le quita el sueño la ensalada. 🍅",
    "¿Qué hace una vaca con una ametralladora? ¡Muuuuu-tin! 🐄",
    "¿Cómo se llama el primo vegano de Bruce Lee? Broco Lee. 🥦",
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter. 🐦",
    "¿Qué le dice un gusano a otro? Voy a dar una vuelta a la manzana. 🍎",
    "¿Cuál es el colmo de un sordo? Que le digan 'te lo dije'. 🙉",
    "¿Por qué el café fue a la policía? Porque lo estaban moliendo. ☕",
    "¿Qué hace un pez payaso? Nada gracioso. 🤡",
    "¿Por qué la bicicleta no se para sola? Porque está dos-tirada. 🚲",
    "¿Qué le dijo el semáforo al coche? No me mires que me pongo rojo. 🚦",
    "¿Cuál es el animal que más tarda en desayunar? El oso perezoso. 🦥",
    "¿Por qué el mar no se seca? Porque no tiene toalla. 🌊",
    "¿Qué le dice una taza a otra? ¿Qué taza haciendo? ☕",
    "¿Por qué los vampiros no pueden tener hijos? Porque son... ¡impotentes de sangre! 🧛",
    "¿Qué hace un león con una cuchara? ¡Nada, los leones no usan cuchara! 🦁",
    "¿Cuál es el colmo de un electricista despistado? No encontrar la corriente. ⚡",
    "¿Por qué el reloj fue al psicólogo? Tenía problemas de tiempo. 🕐",
    "¿Qué le dijo el plátano al plátano verde? ¡Madúrate! 🍌",
    "¿Por qué la gallina cruzó la calle? Para demostrarle al pollo que sí se podía. 🐔",
    "¿Qué hace un perro con un taladro? ¡Guau-guau-taladro! 🐕",
    "¿Cuál es el colmo de un carnicero? Tener un hijo chorizo. 🥩",
    "¿Por qué el estudiante llevó una escalera al examen? Porque era de alto nivel. 🪜",
    "¿Qué le dice el mar a la ola? ¡No te me subas! 🌊",
    "¿Por qué el pan no va a la fiesta? Porque es un pan sin sal. 🍞",
    "¿Qué hace un abogado en una fiesta? ¡Defiende su derecho a divertirse! ⚖️",
    "¿Cuál es el colmo de un dentista? Que su hijo tenga caries. 🦷",
    "¿Por qué el ciego no puede ser DJ? Porque no encuentra el disco. 🎧",
    "¿Qué le dijo la pared al cuadro? ¡Qué arte tienes! 🖼️",
    "¿Por qué el fantasma fue a la fiesta? Porque le dijeron que iba a ser de muerte. 👻",
    "¿Qué hace un pez en el cine? ¡Nada, solo mira! 🎬",
    "¿Cuál es el colmo de un bombero? Que su casa se queme. 🔥",
    "¿Por qué el helado no tiene amigos? Porque es muy frío. 🍦",
    "¿Qué le dice un ojo a otro? ¡No me mires así! 👀",
    "¿Por qué la computadora fue al doctor? Tenía un virus. 💻",
    "¿Qué hace un caballo en una biblioteca? ¡Come libros de paja! 🐴",
    "¿Cuál es el colmo de un sastre? Perder el hilo. 🧵",
    "¿Por qué el lápiz fue a juicio? Porque era el principal sospe-choso. ✏️",
    "¿Qué le dijo el queso al cuchillo? ¡No me cortes el rollo! 🧀",
    "¿Por qué el árbol fue a la escuela? Para ser más sabio... ¡era un sauce llorón de tanto estudiar! 🌳",
    "¿Qué hace una serpiente con sombrero? ¡Se ve ssssexy! 🐍",
    "¿Cuál es el colmo de un meteorólogo? No tener ni idea del tiempo. 🌤️",
    "¿Por qué el músico llevó una escalera al concierto? Para alcanzar las notas altas. 🎵",
    "¿Qué le dice la arena al mar? ¡Deja de mojarme! 🏖️",
    "¿Por qué el pollo no usa reloj? Porque ya tiene sus gallos. 🐓",
    "¿Qué hace un gato en el desierto? ¡Busca su arena! 🐱",
    "¿Cuál es el colmo de un carpintero? Tener una hija tabla. 🪵",
    "¿Por qué el espejo no miente? Porque refleja la verdad. 🪞",
    "¿Qué le dijo el zapato al calcetín? ¡Me aprietas! 👟",
    "¿Por qué el robot no tiene amigos? Porque es muy cuadrado. 🤖",
    "¿Qué hace un tiburón con corbata? ¡Va a una reunión de negocios! 🦈",
    "¿Cuál es el colmo de un panadero? Que le salga el pan quemado. 🥖",
    "¿Por qué la luna no va a la escuela? Porque ya es muy brillante. 🌕",
    "¿Qué le dice el tenedor al cuchillo? ¡No me pinches! 🍴",
    "¿Por qué el dinosaurio no puede aplaudir? Porque está extinto. 🦕",
    "¿Qué hace un pingüino con una cámara? ¡Fotos frías! 🐧",
    "¿Cuál es el colmo de un piloto? Perder el vuelo. ✈️",
    "¿Por qué el celular fue a terapia? Tenía problemas de conexión. 📱",
    "¿Qué le dijo el agua al fuego? ¡No me apagues la fiesta! 💧",
    "¿Por qué el león no juega a las cartas? Porque siempre hace trampa con las garras. 🦁",
    "¿Qué hace un elefante en una tina? ¡No cabe! 🐘",
    "¿Cuál es el colmo de un mago? Que le salga mal el truco. 🎩",
    "¿Por qué el tomate se puso rojo? Porque vio la ensalada desnuda. 🍅",
    "¿Qué le dice un caracol a otro? ¡Vamos, que llegamos tarde! 🐌",
    "¿Por qué el sol no va al banco? Porque ya tiene sus rayos. ☀️",
    "¿Qué hace un mono con un plátano? ¡Lo pela y se lo come! 🐵",
    "¿Cuál es el colmo de un pescador? Que se le escape el pez gordo. 🎣",
    "¿Por qué la gallina no usa celular? Porque ya tiene su propio 'pollito'. 🐔",
    "¿Qué le dijo el libro al lector? ¡No me juzgues por mi portada! 📖",
    "¿Por qué el viento no tiene amigos? Porque siempre está de paso. 💨",
    "¿Qué hace un cangrejo en la playa? ¡Camina de lado! 🦀",
    "¿Cuál es el colmo de un actor? Olvidar su papel. 🎭",
    "¿Por qué el queso no puede correr? Porque está muy rallado. 🧀",
    "¿Qué le dice la luna a la tierra? ¡Gracias por darme vueltas! 🌍",
    "¿Por qué el café es tan popular? Porque siempre está molido de tanto trabajo. ☕",
    "¿Qué hace un pato con una pata rota? ¡Cojea! 🦆",
    "¿Cuál es el colmo de un relojero? Que se le pase la hora. ⌚",
    "¿Por qué el árbol no tiene redes sociales? Porque ya tiene muchas ramas. 🌳",
    "¿Qué le dijo el huevo a la sartén? ¡Me estás friendo! 🍳",
    "¿Por qué el mar es tan sabio? Porque tiene mucha profundidad. 🌊",
    "¿Qué hace un oso en invierno? ¡Duerme la siesta más larga! 🐻",
    "¿Cuál es el colmo de un jardinero calvo? Que se le caigan las hojas. 🍂",
    "¿Por qué el pan integral es tan saludable? Porque va al grano. 🌾",
    "¿Qué le dice un diente a otro? ¡Nos vemos en la muela! 🦷",
    "¿Por qué el fantasma sacó buenas notas? Porque era muy espirituoso. 👻",
    "¿Qué hace un pez dorado en una pecera? ¡Nada! 🐠",
    "¿Cuál es el colmo de un albañil? Que se le caiga la casa. 🧱",
    "¿Por qué el helado lleva gorra? Para no derretirse de la risa. 🍦",
    "¿Qué le dijo el martillo al clavo? ¡Te voy a dar en la cabeza! 🔨",
    "¿Por qué el loro no paga impuestos? Porque ya repite lo que le dicen. 🦜",
    "¿Qué hace una vaca en el espacio? ¡Muuu-cha gravedad cero! 🐄",
    "¿Cuál es el colmo de un barbero? Cortarse con sus propias tijeras. 💈",
    "¿Por qué el tren no tiene miedo? Porque va sobre rieles. 🚂",
    "¿Qué le dice el sol a la luna? ¡Nos vemos en el eclipse! 🌒",
    "¿Por qué el pez no va a la escuela? Porque ya sabe nadar en conocimiento. 🐟",
    "¿Qué hace un gato con un ovillo? ¡Un desastre! 🧶",
]


# ─────────────────────────────────────────────────────────────── #
# ACERTIJOS (acertijo, respuesta)                                  #
# ─────────────────────────────────────────────────────────────── #

RIDDLES: list[tuple[str, str]] = [
    ("Blanca por dentro, verde por fuera. Si quieres que te lo diga, espera. ¿Qué es?", "La pera"),
    ("Cuanto más seco está, más moja. ¿Qué es?", "La toalla"),
    ("Tengo ciudades pero no casas; montañas pero no árboles; agua pero no peces. ¿Qué soy?", "Un mapa"),
    ("Siempre delante de ti pero nunca puedes verlo. ¿Qué es?", "El futuro"),
    ("¿Qué es lo que, cuanto más grande es, menos se puede ver?", "La oscuridad"),
    ("Todo el mundo lo tiene, pero nadie puede devolverlo. ¿Qué es?", "El tiempo"),
    ("¿Qué habla sin boca, escucha sin oídos y cobra vida con el viento?", "El eco"),
    ("Soy liviano pero ni el más fuerte puede sostenerme mucho tiempo. ¿Qué soy?", "El aliento"),
    ("¿Qué sube pero nunca baja?", "La edad"),
    ("Tengo llaves pero no abro puertas. ¿Qué soy?", "Un piano"),
    ("¿Qué tiene un ojo pero no puede ver?", "Una aguja"),
    ("¿Qué se rompe cuando lo dices?", "El silencio"),
    ("Cae del cielo y no se rompe. ¿Qué es?", "La lluvia... no, espera: es la nieve"),
    ("¿Qué tiene manos pero no puede aplaudir?", "Un reloj"),
    ("Mientras más le quitas, más grande es. ¿Qué es?", "Un hoyo"),
    ("¿Qué corre pero no tiene piernas?", "El agua"),
    ("¿Qué entra al agua y no se moja?", "La sombra"),
    ("Tengo un cuello pero no cabeza. ¿Qué soy?", "Una botella"),
    ("¿Qué pesa más: un kilo de plumas o un kilo de plomo?", "Pesan lo mismo: un kilo"),
    ("¿Qué cosa es que cuanto más larga es menos dura?", "Una vela"),
    ("¿En qué mes comen menos los argentinos? ¿O los mexicanos?", "En febrero, que tiene menos días"),
    ("¿Qué se puede ver con los ojos cerrados?", "Un sueño"),
    ("¿Qué está siempre en medio del mar?", "La letra 'a'"),
    ("¿Qué tiene 4 patas por la mañana, 2 al mediodía y 3 por la noche?", "El ser humano (el enigma de la esfinge)"),
    ("¿Qué invento permite mirar a través de una pared?", "La ventana"),
    ("¿Qué es tuyo pero los demás lo usan más que tú?", "Tu nombre"),
    ("¿Qué vuela sin alas y llora sin ojos?", "Una nube"),
    ("¿Qué da vueltas por la casa sin moverse?", "Una pared"),
    ("¿Qué tiene dientes pero no muerde?", "Un peine"),
    ("¿Qué pasa por delante del sol sin hacerle sombra?", "El viento"),
    ("¿Qué necesita respuesta pero no pregunta nada?", "El teléfono"),
    ("¿Qué se moja mientras seca?", "Una toalla"),
    ("¿Qué tiene un corazón que no late?", "Una alcachofa"),
    ("¿Qué camina sin pies y entra sin llamar?", "El frío"),
    ("¿Qué es lo que más se parece a media luna?", "La otra media luna"),
    ("¿Qué no se puede guardar en una caja?", "La luz"),
    ("¿Qué tiene cabeza y cola pero no cuerpo?", "Una moneda"),
    ("¿Qué está en el centro de París?", "La letra 'r'"),
    ("¿Qué sube cuando llueve?", "El paraguas"),
    ("¿Qué tiene 88 teclas pero no puede abrir una puerta?", "Un piano"),
    ("¿Qué es redondo como una manzana y muerde como un león?", "No existe... ¡es un acertijo imposible a propósito!"),
    ("¿Qué animal tiene 4 patas, bigotes y dice 'guau'?", "Un perro disfrazado de gato... ¡es un perro!"),
    ("¿Qué le dice un techo a otro? Te echo de menos... ¡techo de menos!", "Un juego de palabras"),
    ("¿Cuál es el colmo de un libro? Tener problemas de 'página'.", "Un juego de palabras"),
    ("Oro parece, plata no es. ¿Qué es?", "El plátano"),
    ("Blanca soy y, como dice mi vecina, útiles rayas dejo en la cocina. ¿Qué soy?", "La harina"),
    ("¿Qué es lo que se pone sobre la mesa, se corta y se reparte pero nunca se come?", "Una baraja de cartas"),
    ("Vuelo de noche, duermo de día y nunca verás plumas en mi ala. ¿Qué soy?", "Un murciélago"),
    ("¿Qué tiene un banco que no tiene dinero?", "Un banco de plaza (para sentarse)"),
    ("¿Qué es lo que al final siempre llega aunque nunca se mueva?", "El mañana"),
]

# arreglar una respuesta que quedó con muletilla
RIDDLES = [(r.replace("Cae del cielo y no se rompe. ¿Qué es?", "Cae y no se rompe. ¿Qué es?"),
            a.replace("La lluvia... no, espera: es la nieve", "La nieve"))
           for r, a in RIDDLES]


# ─────────────────────────────────────────────────────────────── #
# REFRANES                                                         #
# ─────────────────────────────────────────────────────────────── #

PROVERBS: list[str] = [
    "No hay mal que dure cien años.",
    "Camarón que se duerme, se lo lleva la corriente.",
    "A caballo regalado no se le mira el diente.",
    "El que madruga, Dios lo ayuda.",
    "Más vale pájaro en mano que cien volando.",
    "No dejes para mañana lo que puedes hacer hoy.",
    "Dime con quién andas y te diré quién eres.",
    "En boca cerrada no entran moscas.",
    "El hábito no hace al monje.",
    "Ojos que no ven, corazón que no siente.",
    "Perro que ladra no muerde.",
    "A lo hecho, pecho.",
    "Quien siembra vientos, recoge tempestades.",
    "No hay peor ciego que el que no quiere ver.",
    "Del dicho al hecho hay mucho trecho.",
    "A palabras necias, oídos sordos.",
    "El que todo lo quiere, todo lo pierde.",
    "Más sabe el diablo por viejo que por diablo.",
    "Cría cuervos y te sacarán los ojos.",
    "En casa de herrero, cuchillo de palo.",
    "Quien mucho abarca, poco aprieta.",
    "No juzgues un libro por su portada.",
    "Agua que no has de beber, déjala correr.",
    "Barriga llena, corazón contento.",
    "Cada oveja con su pareja.",
    "Del árbol caído todos hacen leña.",
    "Donde hay humo, hay fuego.",
    "El amor es ciego.",
    "El saber no ocupa lugar.",
    "El tiempo todo lo cura.",
    "En el país de los ciegos, el tuerto es rey.",
    "Haz el bien sin mirar a quién.",
    "La esperanza es lo último que se pierde.",
    "La práctica hace al maestro.",
    "La unión hace la fuerza.",
    "Lo prometido es deuda.",
    "Mejor solo que mal acompañado.",
    "Nadie es profeta en su tierra.",
    "No todo lo que brilla es oro.",
    "Ojo por ojo, diente por diente.",
    "Quien ríe último, ríe mejor.",
    "Sarno con gusto no pica... (dicho popular).",
    "Siembra amor y cosecharás cariño.",
    "Tanto va el cántaro a la fuente que al final se rompe.",
    "Una imagen vale más que mil palabras.",
    "Zapatero, a tus zapatos.",
    "A Dios rogando y con el mazo dando.",
    "A falta de pan, buenas son tortas.",
    "Al mal tiempo, buena cara.",
    "Al que le van a dar, le guardan.",
    "Borrón y cuenta nueva.",
    "Cada loco con su tema.",
    "Con paciencia y saliva, el elefante se... (se logra todo).",
    "Cuando el río suena, agua lleva.",
    "De noche todos los gatos son pardos.",
    "De tal palo, tal astilla.",
    "Dios los cría y ellos se juntan.",
    "Donde hubo fuego, cenizas quedan.",
    "El fin justifica los medios.",
    "El león no es como lo pintan.",
    "El pez por la boca muere.",
    "El que busca, encuentra.",
    "El que calla, otorga.",
    "El que espera, desespera.",
    "El que la hace, la paga.",
    "El que no llora, no mama.",
    "El que persevera, alcanza.",
    "En la variedad está el gusto.",
    "Entre broma y broma, la verdad se asoma.",
    "Gato con guantes no caza ratones.",
    "Hablando del rey de Roma, por la puerta asoma.",
    "Hombre prevenido vale por dos.",
    "La avaricia rompe el saco.",
    "La caridad bien entendida empieza por casa.",
    "La curiosidad mató al gato.",
    "La letra con sangre entra.",
    "La mentira tiene patas cortas.",
    "La ociosidad es madre de todos los vicios.",
    "La peor lucha es la que no se hace.",
    "Las apariencias engañan.",
    "Las desgracias nunca vienen solas.",
    "Lo barato sale caro.",
    "Los años no vienen solos.",
    "Muerto el perro, se acabó la rabia.",
    "Mujer al volante, peligro constante... (refrán antiguo y machista, hoy en desuso).",
    "Nadie sabe lo que tiene hasta que lo pierde.",
    "No cantes victoria antes de tiempo.",
    "No hay peor sordo que el que no quiere oír.",
    "No por mucho madrugar amanece más temprano.",
    "Nunca digas 'de esta agua no beberé'.",
    "Para gustos, los colores.",
    "Perro viejo no aprende trucos nuevos... aunque siempre se puede intentar.",
    "Poco a poco se anda lejos.",
    "Por la boca muere el pez.",
    "Preguntando se llega a Roma.",
    "Quien canta, sus males espanta.",
    "Quien con lobos anda, a aullar aprende.",
    "Quien da pan a perro ajeno, pierde el pan y pierde el perro.",
    "Quien mal anda, mal acaba.",
    "Quien tiene boca se equivoca.",
    "Rectificar es de sabios.",
    "Roma no se construyó en un día.",
    "Si la montaña no viene a Mahoma, Mahoma va a la montaña.",
    "Sin prisa pero sin pausa.",
    "Sarna con gusto no pica.",
    "Perro viejo no aprende trucos nuevos.",
]

# limpiar refranes con muletillas editoriales
PROVERBS = [p for p in PROVERBS if "dicho popular" not in p and "hoy en desuso" not in p
            and "aunque siempre se puede" not in p and "se logra todo" not in p]


# ─────────────────────────────────────────────────────────────── #
# CITAS CÉLEBRES (cita, autor)                                     #
# ─────────────────────────────────────────────────────────────── #

QUOTES: list[tuple[str, str]] = [
    ("Solo sé que no sé nada.", "Sócrates"),
    ("Pienso, luego existo.", "René Descartes"),
    ("La imaginación es más importante que el conocimiento.", "Albert Einstein"),
    ("Sé el cambio que quieres ver en el mundo.", "Mahatma Gandhi"),
    ("El éxito es la capacidad de ir de fracaso en fracaso sin perder el entusiasmo.", "Winston Churchill"),
    ("La mejor forma de predecir el futuro es crearlo.", "Peter Drucker"),
    ("No cuentes los días, haz que los días cuenten.", "Muhammad Ali"),
    ("La vida es lo que pasa mientras estás ocupado haciendo otros planes.", "John Lennon"),
    ("Haz lo que puedas, con lo que tengas, donde estés.", "Theodore Roosevelt"),
    ("El único modo de hacer un gran trabajo es amar lo que haces.", "Steve Jobs"),
    ("La creatividad es la inteligencia divirtiéndose.", "Albert Einstein"),
    ("No he fracasado. He encontrado 10,000 formas que no funcionan.", "Thomas Edison"),
    ("La educación es el arma más poderosa para cambiar el mundo.", "Nelson Mandela"),
    ("Vive como si fueras a morir mañana. Aprende como si fueras a vivir siempre.", "Mahatma Gandhi"),
    ("El conocimiento habla, pero la sabiduría escucha.", "Jimi Hendrix"),
    ("La felicidad no es algo hecho. Viene de tus propias acciones.", "Dalái Lama"),
    ("Todo lo que siempre quisiste está al otro lado del miedo.", "George Addair"),
    ("El futuro pertenece a quienes creen en la belleza de sus sueños.", "Eleanor Roosevelt"),
    ("No es la especie más fuerte la que sobrevive, sino la más adaptable.", "Charles Darwin"),
    ("La duda no es enemiga del conocimiento, sino su aliada.", "Anónimo"),
    ("El arte de ser sabio es el arte de saber qué pasar por alto.", "William James"),
    ("La mente es todo. En lo que piensas, te conviertes.", "Buda"),
    ("Donde hay amor hay vida.", "Mahatma Gandhi"),
    ("La mejor venganza es un éxito masivo.", "Frank Sinatra"),
    ("No midas tu riqueza por el dinero que tienes, sino por las cosas que tienes y no cambiarías por dinero.", "Anónimo"),
    ("El tiempo que disfrutas perdiendo no es tiempo perdido.", "John Lennon"),
    ("Si quieres ir rápido, ve solo. Si quieres llegar lejos, ve acompañado.", "Proverbio africano"),
    ("La paciencia es amarga, pero su fruto es dulce.", "Jean-Jacques Rousseau"),
    ("El secreto de la felicidad no es hacer siempre lo que se quiere, sino querer siempre lo que se hace.", "León Tolstói"),
    ("No podemos resolver problemas pensando de la misma manera que cuando los creamos.", "Albert Einstein"),
    ("La lógica te llevará de A a B. La imaginación te llevará a todas partes.", "Albert Einstein"),
    ("Todo hombre es culpable del bien que no hizo.", "Voltaire"),
    ("La libertad no es la ausencia de compromisos, sino la capacidad de elegir.", "Paulo Coelho"),
    ("El hombre es la medida de todas las cosas.", "Protágoras"),
    ("Conócete a ti mismo.", "Inscripción del templo de Delfos"),
    ("La filosofía comienza con el asombro.", "Platón"),
    ("El todo es más que la suma de sus partes.", "Aristóteles"),
    ("No hay viento favorable para quien no sabe a dónde va.", "Séneca"),
    ("La suerte favorece a la mente preparada.", "Louis Pasteur"),
    ("Dios no juega a los dados con el universo.", "Albert Einstein"),
    ("La ciencia sin religión está coja; la religión sin ciencia está ciega.", "Albert Einstein"),
    ("Nada en la vida debe temerse, solo comprenderse.", "Marie Curie"),
    ("La simplicidad es la máxima sofisticación.", "Leonardo da Vinci"),
    ("El aprendizaje nunca agota la mente.", "Leonardo da Vinci"),
    ("Dondequiera que vayas, ve con todo tu corazón.", "Confucio"),
    ("Elige un trabajo que ames y no tendrás que trabajar ni un día.", "Confucio"),
    ("Nuestra mayor gloria no es no caer nunca, sino levantarnos cada vez que caemos.", "Confucio"),
    ("La música es el arte más directo: entra por el oído y va al corazón.", "Magdalena Martínez... no, es de autores varios; se atribuye a músicos clásicos."),
    ("Sin música, la vida sería un error.", "Friedrich Nietzsche"),
    ("La arquitectura es música congelada.", "Johann Wolfgang von Goethe"),
    ("El amor todo lo puede.", "Virgilio"),
    ("Ama y haz lo que quieras.", "San Agustín"),
    ("La esperanza es el sueño del hombre despierto.", "Aristóteles"),
    ("El carácter es el destino.", "Heráclito"),
    ("Todo fluye, nada permanece.", "Heráclito"),
    ("El hombre es un lobo para el hombre.", "Thomas Hobbes"),
    ("El fin justifica los medios.", "Nicolás Maquiavelo"),
    ("Más vale tarde que nunca.", "Dicho popular"),
    ("La pluma es más poderosa que la espada.", "Edward Bulwer-Lytton"),
    ("El conocimiento es poder.", "Francis Bacon"),
    ("Duda de todo.", "René Descartes"),
    ("El infierno son los otros.", "Jean-Paul Sartre"),
    ("La existencia precede a la esencia.", "Jean-Paul Sartre"),
    ("Dios ha muerto.", "Friedrich Nietzsche"),
    ("Lo que no me mata, me hace más fuerte.", "Friedrich Nietzsche"),
    ("El eterno retorno: ¿vivirías tu vida igual infinitas veces?", "Friedrich Nietzsche"),
    ("La vida sin examen no merece ser vivida.", "Sócrates"),
    ("Habla para que yo te conozca.", "Sócrates"),
    ("El ignorante afirma, el sabio duda y reflexiona.", "Aristóteles"),
    ("Educar la mente sin educar el corazón no es educación.", "Aristóteles"),
    ("La amistad es un alma que habita en dos cuerpos.", "Aristóteles"),
    ("El hombre es por naturaleza un animal social.", "Aristóteles"),
    ("La repetición es la madre del aprendizaje.", "Dicho popular"),
    ("No hay atajos para los lugares a los que vale la pena ir.", "Beverly Sills"),
    ("La disciplina es el puente entre las metas y los logros.", "Jim Rohn"),
    ("No esperes. El momento nunca será perfecto.", "Napoleon Hill"),
    ("Todo lo que la mente puede concebir y creer, lo puede lograr.", "Napoleon Hill"),
    ("El éxito suele llegar a quienes están demasiado ocupados para buscarlo.", "Henry David Thoreau"),
    ("Ve con confianza en la dirección de tus sueños.", "Henry David Thoreau"),
    ("Lo que obtienes al lograr tus metas no es tan importante como en quién te conviertes.", "Zig Ziglar"),
    ("La motivación te pone en marcha; el hábito te mantiene.", "Jim Ryun"),
    ("No tienes que ser grande para empezar, pero tienes que empezar para ser grande.", "Zig Ziglar"),
    ("El pesimista ve dificultad en cada oportunidad; el optimista ve oportunidad en cada dificultad.", "Winston Churchill"),
    ("El coraje es lo que se necesita para ponerse de pie y hablar; también para sentarse y escuchar.", "Winston Churchill"),
    ("La historia la escriben los vencedores.", "Winston Churchill"),
    ("Nunca, nunca, nunca te rindas.", "Winston Churchill"),
    ("El precio de la grandeza es la responsabilidad.", "Winston Churchill"),
    ("Si estás pasando por un infierno, sigue caminando.", "Winston Churchill"),
    ("La mejor manera de salir de un problema es a través de él.", "Anónimo"),
    ("Cree en ti mismo y todo será posible.", "Anónimo"),
    ("Los límites solo existen en tu mente.", "Anónimo"),
    ("Haz hoy lo que otros no quieren y mañana vivirás lo que otros no pueden.", "Anónimo"),
    ("El dolor es temporal; la gloria es para siempre.", "Anónimo"),
    ("No pares cuando estés cansado; para cuando hayas terminado.", "Anónimo"),
    ("Tu única competencia eres tú de ayer.", "Anónimo"),
    ("Los sueños no funcionan a menos que tú trabajes.", "Anónimo"),
    ("Sé fuerte porque las cosas mejorarán. Puede haber tormenta ahora, pero nunca llueve para siempre.", "Anónimo"),
    ("La vida es 10% lo que te pasa y 90% cómo reaccionas.", "Charles R. Swindoll"),
    ("No llores porque terminó; sonríe porque sucedió.", "Dr. Seuss"),
    ("Hoy es el primer día del resto de tu vida.", "Anónimo"),
]

# limpiar citas con muletillas editoriales
QUOTES = [(q, a) for q, a in QUOTES if "no, es de autores" not in q]


# ─────────────────────────────────────────────────────────────── #
# CUENTOS CORTOS (título, texto)                                   #
# ─────────────────────────────────────────────────────────────── #

STORIES: list[tuple[str, str]] = [
    ("El zorro y las uvas",
     "Un zorro hambriento vio un racimo de uvas colgando de una parra. Saltó y saltó, pero no las alcanzó. "
     "Al final se alejó diciendo: 'Están verdes de todos modos'. Moraleja: es fácil despreciar lo que no se puede alcanzar."),
    ("La liebre y la tortuga",
     "La liebre se burlaba de la tortuga por ser lenta y la retó a una carrera. Segura de ganar, la liebre se durmió a mitad del camino. "
     "La tortuga siguió paso a paso y cruzó la meta primero. Moraleja: la constancia vence al talento cuando el talento se confía."),
    ("El pastorcito mentiroso",
     "Un pastorcito se divertía gritando '¡el lobo!' aunque no había ningún lobo. Los aldeanos corrían a ayudarlo y él se reía. "
     "Un día el lobo apareció de verdad, gritó, pero nadie le creyó. Moraleja: quien miente pierde la confianza de todos."),
    ("La cigarra y la hormiga",
     "Mientras la cigarra cantaba todo el verano, la hormiga trabajaba guardando comida. Llegó el invierno y la cigarra, hambrienta, "
     "pidió ayuda. La hormiga compartió un poco, pero le enseñó la lección. Moraleja: prepárate hoy para el mañana."),
    ("El león y el ratón",
     "Un león atrapó un ratón y, divertido por sus súplicas, lo dejó ir. Días después el león cayó en una trampa de cazadores. "
     "El ratón royó las cuerdas y lo liberó. Moraleja: ningún acto de bondad es pequeño, y nadie es tan insignificante que no pueda ayudar."),
    ("El cuervo y el cántaro",
     "Un cuervo sediento encontró un cántaro con poca agua al fondo, imposible de alcanzar con el pico. "
     "Entonces echó piedritas una a una hasta que el nivel subió y pudo beber. Moraleja: la inteligencia supera a la fuerza."),
    ("Los dos amigos y el oso",
     "Dos amigos caminaban por el bosque cuando apareció un oso. Uno subió a un árbol; el otro se tiró al suelo y fingió estar muerto. "
     "El oso lo olfateó y se fue. '¿Qué te dijo al oído?', preguntó el del árbol. 'Que no confíe en quien me abandona en el peligro'."),
    ("La gallina de los huevos de oro",
     "Un granjero tenía una gallina que ponía un huevo de oro cada día. Impaciente por hacerse rico, la abrió para sacar todos los huevos de una vez. "
     "Dentro no había nada y perdió su fortuna. Moraleja: la avaricia rompe el saco."),
    ("El viento y el sol",
     "El viento y el sol discutían sobre quién era más fuerte. Vieron a un viajero con abrigo y apostaron quién se lo quitaría. "
     "El viento sopló con furia y el hombre se aferró más al abrigo. El sol brilló suavemente, el hombre sudó y se lo quitó. "
     "Moraleja: la suavidad logra más que la fuerza."),
    ("El niño y las estrellas de mar",
     "Un niño devolvía al mar las estrellas varadas en la playa, una por una. Un hombre le dijo: 'Son miles, no harás diferencia'. "
     "El niño lanzó otra y respondió: 'Para esta, sí hice la diferencia'. Moraleja: cada pequeña acción cuenta."),
    ("La semilla del emperador",
     "Un emperador dio una semilla a cada niño del reino: quien cultivara la flor más bella sería su sucesor. "
     "Un niño cuidó la suya con amor, pero nunca germinó: las semillas estaban cocidas. Su honestidad al presentar la maceta vacía lo hizo emperador. "
     "Moraleja: la honestidad vale más que la apariencia."),
    ("El sabio y el cántaro agrietado",
     "Un aguador llevaba dos cántaros; uno estaba agrietado y perdía agua en el camino. Avergonzado, se disculpó. "
     "El aguador le mostró que, sin saberlo, había regado flores a lo largo del sendero. Moraleja: nuestras grietas también pueden florecer."),
]


# ─────────────────────────────────────────────────────────────── #
# POEMAS CORTOS (título, texto)                                    #
# ─────────────────────────────────────────────────────────────── #

POEMS: list[tuple[str, str]] = [
    ("Amanecer digital",
     "Enciende el día su pantalla de oro,\nla noche guarda su archivo en la memoria,\ny Baro despierta entre líneas de código\npara escribir contigo una nueva historia."),
    ("Oda a la curiosidad",
     "Pregunta, pregunta sin cesar,\ncada duda es una puerta,\ncada 'por qué' una ventana abierta\nal infinito que está por llegar."),
    ("Versos de la luna",
     "La luna borda con hilo de plata\nel manto oscuro de la noche serena,\ny en cada estrella que tiembla y recata\nhay un secreto que el cielo encadena."),
    ("El viajero",
     "Caminante que cruzas la distancia,\nlleva en la mochila un sueño encendido:\ncada paso es una nueva instancia\nde lo que aún no ha sucedido."),
    ("Mar interior",
     "Hay un mar dentro del pecho\ndonde navegan los anhelos,\ny cada ola es un hecho\nque se pierde entre los cielos."),
    ("Oda al café",
     "Negro elixir de la mañana,\ndespiertas mentes dormidas,\ny en cada taza, una ventana\na mil ideas encendidas."),
    ("La semilla",
     "Pequeña y dormida en la tierra,\nguarda un bosque en su interior;\nla paciencia todo encierra:\ndel silencio nace el verdor."),
    ("Noche de lluvia",
     "La lluvia escribe en los cristales\npoemas que nadie lee,\ny la noche, con susales,\nlos guarda donde no se ve."),
    ("Alas",
     "No necesitas alas para volar:\nbasta un sueño bien amado\ny el coraje de intentar\nlo que nadie ha intentado."),
    ("El reloj",
     "El reloj no se detiene,\nni perdona ni espera;\ncada segundo que viene\nes la vida verdadera."),
]


# ─────────────────────────────────────────────────────────────── #
# RECETAS (nombre, texto)                                          #
# ─────────────────────────────────────────────────────────────── #

RECIPES: list[tuple[str, str]] = [
    ("Arepas", "Mezcla 2 tazas de harina de maíz precocida con 2.5 tazas de agua tibia y 1 cdta de sal. Amasa 5 minutos, forma discos de 1 cm y cocina en sartén caliente 7 minutos por lado. Rellena con queso, pollo o lo que quieras."),
    ("Pasta al dente", "Hierve abundante agua con sal. Cocina la pasta 1 minuto menos de lo indicado. Reserva una taza del agua de cocción, saltea con tu salsa favorita 1 minuto y sirve con queso parmesano."),
    ("Guacamole", "Tritura 3 aguacates maduros. Agrega 1 tomate picado, 1/4 de cebolla, cilantro, jugo de 1 limón y sal. Mezcla sin batir demasiado y sirve con totopos."),
    ("Arroz blanco perfecto", "Por cada taza de arroz, 2 de agua. Sofríe el arroz 2 minutos con un poco de aceite, agrega agua hirviendo y sal. Tapa y cocina a fuego bajo 18 minutos. Reposa 5 minutos tapado."),
    ("Tortilla española", "Fríe 4 papas en rodajas y 1 cebolla en abundante aceite a fuego medio 20 minutos. Escurre, mezcla con 6 huevos batidos y sal. Cuaja en sartén 5 minutos por lado."),
    ("Pancakes esponjosos", "Mezcla 1.5 tazas de harina, 3.5 cdtas de polvo de hornear, 1 cda de azúcar y 1/4 cdta de sal. Aparte: 1.25 tazas de leche, 1 huevo y 3 cdas de mantequilla derretida. Une sin batir de más y cocina porciones en sartén caliente."),
    ("Ensalada César", "Mezcla lechuga romana con crutones y queso parmesano. Aderezo: 1/2 taza de mayonesa, 2 cdas de jugo de limón, 1 cdta de mostaza, 1 diente de ajo y 2 filetes de anchoa picados."),
    ("Pollo al horno", "Marina el pollo 1 hora con limón, ajo, sal, pimienta y orégano. Hornea a 200 °C por 45-60 minutos hasta dorar. Deja reposar 10 minutos antes de cortar."),
    ("Sopa de lentejas", "Sofríe cebolla, zanahoria y apio. Agrega 2 tazas de lentejas, 6 tazas de caldo y laurel. Cocina 30 minutos. Sazona con comino y un chorro de vinagre."),
    ("Brownies", "Derrite 170 g de mantequilla con 200 g de chocolate. Agrega 3 huevos, 200 g de azúcar y 100 g de harina. Hornea a 180 °C por 25 minutos. Deben quedar húmedos por dentro."),
    ("Tacos al pastor (caseros)", "Marina 500 g de cerdo en achiote, jugo de naranja, vinagre y especias 4 horas. Asa en sartén caliente, pica fino y sirve en tortillas con piña, cebolla y cilantro."),
    ("Ceviche", "Corta 500 g de pescado blanco en cubos. Cúbrelo con jugo de 8 limones 20 minutos. Agrega cebolla morada, ají, cilantro y sal. Sirve frío con camote o maíz."),
    ("Hummus", "Procesa 400 g de garbanzos cocidos con 3 cdas de tahini, jugo de 1 limón, 1 diente de ajo, sal y 4 cdas de aceite de oliva hasta lograr una crema suave."),
    ("Pizza casera", "Mezcla 500 g de harina, 325 ml de agua tibia, 10 g de levadura, 1 cda de aceite y 10 g de sal. Leuda 1 hora, estira, agrega salsa y queso. Hornea a 250 °C por 10-12 minutos."),
    ("Limonada perfecta", "Exprime 6 limones. Mezcla el jugo con 1 litro de agua fría y 3/4 de taza de azúcar. Agrega hielo y hojas de menta. Ajusta el dulce a tu gusto."),
    ("Avena overnight", "Mezcla 1/2 taza de avena con 1/2 taza de leche, 1 cda de chía y miel. Refrigera toda la noche. Por la mañana agrega fruta fresca."),
    ("Quesadillas", "Calienta tortillas de harina en sartén, agrega queso rallado y el relleno que quieras (pollo, champiñones, flor de calabaza). Dobla y dora 2 minutos por lado."),
    ("Salsa verde", "Asa 500 g de tomatillo, 1/4 de cebolla, 1 diente de ajo y 2 chiles serranos. Licúa con cilantro y sal. Perfecta para tacos y enchiladas."),
    ("Flan napolitano", "Licúa 1 lata de leche condensada, 1 de evaporada, 4 huevos y vainilla. Vierte sobre caramelo en un molde. Hornea a baño maría a 180 °C por 50 minutos. Enfría 4 horas."),
    ("Ensalada de quinoa", "Cocina 1 taza de quinoa en 2 de agua 15 minutos. Mezcla con pepino, tomate, aguacate y perejil. Aliña con limón, aceite de oliva y sal."),
]


# ─────────────────────────────────────────────────────────────── #
# CONSEJOS (por tema)                                              #
# ─────────────────────────────────────────────────────────────── #

ADVICE: list[tuple[str, str]] = [
    ("estudio", "Estudia en bloques de 25 minutos con descansos de 5 (técnica Pomodoro). Repasa lo aprendido antes de dormir: el sueño consolida la memoria."),
    ("estudio", "Enseña lo que aprendes a otra persona (o a mí): si puedes explicarlo simple, es que lo entendiste."),
    ("estudio", "Usa repetición espaciada: repasa al día siguiente, a la semana y al mes. Es la técnica con más respaldo científico."),
    ("salud", "Duerme 7-9 horas: la falta de sueño afecta la memoria, el ánimo y las defensas más que casi cualquier otra cosa."),
    ("salud", "Camina 30 minutos al día: reduce el estrés, mejora el corazón y despeja la mente."),
    ("salud", "Toma agua antes de tener sed: la deshidratación leve ya reduce la concentración."),
    ("dinero", "Aplica la regla 50/30/20: 50% necesidades, 30% gustos, 20% ahorro. Automatiza el ahorro el día que cobras."),
    ("dinero", "Antes de comprar algo caro, espera 48 horas: el 80% de los impulsos desaparecen."),
    ("dinero", "Crea un fondo de emergencia de 3 meses de gastos antes de invertir en nada."),
    ("trabajo", "Haz primero la tarea más difícil del día ('trágate el sapo'): el resto se siente liviano."),
    ("trabajo", "Aprende a decir no: cada sí a algo irrelevante es un no a lo importante."),
    ("trabajo", "Pide feedback específico: '¿qué puedo mejorar?' funciona mejor que '¿estuvo bien?'."),
    ("amor", "La comunicación honesta y temprana evita el 90% de los conflictos de pareja."),
    ("amor", "No intentes cambiar a tu pareja: elige a alguien cuya forma de ser ya te haga feliz."),
    ("animo", "En días malos, reduce la meta al mínimo: 5 minutos de eso que evitas. Empezar es lo más difícil."),
    ("animo", "Escribe 3 cosas buenas que te pasaron hoy: reentrena tu cerebro para notar lo positivo."),
    ("animo", "Habla contigo como le hablarías a tu mejor amigo: la autocompasión no es debilidad, es estrategia."),
    ("productividad", "Planifica el día la noche anterior: despertar con un plan elimina la parálisis de decidir."),
    ("productividad", "Agrupa tareas similares en bloques: cambiar de contexto cuesta hasta 20 minutos de enfoque."),
    ("cocina", "Lee la receta completa antes de empezar: la mitad de los errores en cocina son por sorpresa."),
    ("cocina", "Sazona por capas y prueba mientras cocinas: es más fácil agregar sal que quitarla."),
    ("viaje", "Viaja en temporada baja: mitad de precio, mitad de gente, doble de disfrute."),
    ("viaje", "Aprende 10 frases en el idioma local: abre puertas que el dinero no abre."),
    ("tecnologia", "Activa la verificación en dos pasos en tus cuentas importantes: es la medida de seguridad más efectiva."),
    ("tecnologia", "Haz copias de seguridad 3-2-1: 3 copias, 2 medios distintos, 1 fuera de casa."),
    ("general", "Escucha más de lo que hablas: la gente te contará exactamente lo que necesita."),
    ("general", "Los hábitos pequeños y constantes vencen a la motivación intensa y pasajera."),
    ("general", "Cuida tu atención como tu dinero: donde pones el foco, pones tu vida."),
]


# ─────────────────────────────────────────────────────────────── #
# DICCIONARIO DE TRADUCCIÓN EN→ES (palabras comunes)                #
# ─────────────────────────────────────────────────────────────── #

TRANSLATIONS_EN_ES: dict[str, str] = {
    "hello": "hola", "goodbye": "adiós", "please": "por favor",
    "thank you": "gracias", "thanks": "gracias", "yes": "sí", "no": "no",
    "love": "amor", "friend": "amigo/amiga", "family": "familia",
    "house": "casa", "home": "hogar", "water": "agua", "food": "comida",
    "time": "tiempo", "day": "día", "night": "noche", "morning": "mañana",
    "sun": "sol", "moon": "luna", "star": "estrella", "sky": "cielo",
    "dog": "perro", "cat": "gato", "bird": "pájaro", "fish": "pez",
    "book": "libro", "school": "escuela", "teacher": "maestro/maestra",
    "student": "estudiante", "work": "trabajo", "money": "dinero",
    "car": "carro/coche", "phone": "teléfono", "computer": "computadora",
    "music": "música", "song": "canción", "movie": "película",
    "happy": "feliz", "sad": "triste", "beautiful": "hermoso/hermosa",
    "big": "grande", "small": "pequeño/pequeña", "good": "bueno/buena",
    "bad": "malo/mala", "new": "nuevo/nueva", "old": "viejo/vieja",
    "man": "hombre", "woman": "mujer", "child": "niño/niña",
    "boy": "niño", "girl": "niña", "baby": "bebé",
    "eat": "comer", "drink": "beber", "sleep": "dormir", "run": "correr",
    "walk": "caminar", "speak": "hablar", "talk": "hablar",
    "read": "leer", "write": "escribir", "learn": "aprender",
    "teach": "enseñar", "help": "ayudar", "play": "jugar",
    "sing": "cantar", "dance": "bailar", "laugh": "reír", "cry": "llorar",
    "think": "pensar", "know": "saber/conocer", "understand": "entender",
    "want": "querer", "need": "necesitar", "like": "gustar",
    "dream": "sueño/soñar", "life": "vida", "world": "mundo",
    "city": "ciudad", "country": "país", "people": "gente/personas",
    "heart": "corazón", "mind": "mente", "body": "cuerpo",
    "hand": "mano", "eye": "ojo", "head": "cabeza",
    "red": "rojo", "blue": "azul", "green": "verde",
    "yellow": "amarillo", "black": "negro", "white": "blanco",
    "one": "uno", "two": "dos", "three": "tres", "four": "cuatro",
    "five": "cinco", "six": "seis", "seven": "siete",
    "eight": "ocho", "nine": "nueve", "ten": "diez",
    "hundred": "cien", "thousand": "mil", "million": "millón",
    "today": "hoy", "tomorrow": "mañana", "yesterday": "ayer",
    "week": "semana", "month": "mes", "year": "año",
    "spring": "primavera", "summer": "verano",
    "autumn": "otoño", "fall": "otoño", "winter": "invierno",
    "hot": "caliente", "cold": "frío", "warm": "tibio",
    "rain": "lluvia", "snow": "nieve", "wind": "viento", "cloud": "nube",
    "tree": "árbol", "flower": "flor", "grass": "pasto/césped",
    "mountain": "montaña", "river": "río", "sea": "mar",
    "ocean": "océano", "beach": "playa", "island": "isla",
    "door": "puerta", "window": "ventana", "table": "mesa",
    "chair": "silla", "bed": "cama", "kitchen": "cocina",
    "bathroom": "baño", "street": "calle", "road": "carretera",
    "airport": "aeropuerto", "hospital": "hospital",
    "doctor": "doctor/doctora", "nurse": "enfermero/enfermera",
    "dog": "perro", "puppy": "cachorro", "kitten": "gatito",
    "horse": "caballo", "cow": "vaca", "pig": "cerdo",
    "chicken": "pollo", "egg": "huevo", "milk": "leche",
    "bread": "pan", "rice": "arroz", "meat": "carne",
    "fruit": "fruta", "apple": "manzana", "orange": "naranja",
    "banana": "plátano/banana", "grape": "uva",
    "coffee": "café", "tea": "té", "juice": "jugo",
    "sugar": "azúcar", "salt": "sal",
    "question": "pregunta", "answer": "respuesta",
    "problem": "problema", "solution": "solución",
    "idea": "idea", "story": "historia/cuento",
    "game": "juego", "sport": "deporte", "team": "equipo",
    "win": "ganar", "lose": "perder",
    "begin": "empezar", "start": "comenzar", "end": "terminar",
    "open": "abrir", "close": "cerrar",
    "buy": "comprar", "sell": "vender", "pay": "pagar",
    "cheap": "barato", "expensive": "caro",
    "fast": "rápido", "slow": "lento",
    "easy": "fácil", "difficult": "difícil", "hard": "duro/difícil",
    "strong": "fuerte", "weak": "débil",
    "rich": "rico", "poor": "pobre",
    "clean": "limpio", "dirty": "sucio",
    "full": "lleno", "empty": "vacío",
    "light": "luz/ligero", "dark": "oscuro", "darkness": "oscuridad",
    "fire": "fuego", "earth": "tierra", "air": "aire",
    "freedom": "libertad", "peace": "paz", "war": "guerra",
    "hope": "esperanza", "faith": "fe", "truth": "verdad",
    "lie": "mentira", "secret": "secreto",
    "morning": "mañana", "afternoon": "tarde", "evening": "nochecita",
    "breakfast": "desayuno", "lunch": "almuerzo", "dinner": "cena",
    "brother": "hermano", "sister": "hermana",
    "father": "padre", "mother": "madre", "dad": "papá", "mom": "mamá",
    "son": "hijo", "daughter": "hija",
    "husband": "esposo", "wife": "esposa",
    "uncle": "tío", "aunt": "tía", "cousin": "primo/prima",
    "grandfather": "abuelo", "grandmother": "abuela",
    "always": "siempre", "never": "nunca", "sometimes": "a veces",
    "now": "ahora", "later": "después", "soon": "pronto",
    "here": "aquí", "there": "allí/ahí", "where": "dónde",
    "what": "qué", "when": "cuándo", "why": "por qué",
    "who": "quién", "how": "cómo",
    "because": "porque", "but": "pero", "and": "y", "or": "o",
    "with": "con", "without": "sin", "for": "para/por",
    "from": "desde/de", "to": "a/hacia", "in": "en",
    "on": "sobre/en", "at": "en", "by": "por",
    "my": "mi", "your": "tu", "his": "su (de él)",
    "her": "su (de ella)", "our": "nuestro", "their": "su (de ellos)",
    "i": "yo", "you": "tú/usted", "he": "él", "she": "ella",
    "we": "nosotros", "they": "ellos",
    "this": "esto/este", "that": "eso/ese",
    "these": "estos", "those": "esos",
    "all": "todo", "some": "algunos", "many": "muchos",
    "few": "pocos", "more": "más", "less": "menos",
    "very": "muy", "too": "también/demasiado", "also": "también",
    "again": "otra vez", "still": "todavía", "already": "ya",
    "maybe": "quizás", "perhaps": "tal vez",
    "welcome": "bienvenido", "congratulations": "felicidades",
    "sorry": "perdón/lo siento", "excuse me": "disculpa/permiso",
    "birthday": "cumpleaños", "christmas": "navidad",
    "holiday": "vacaciones/feriado", "weekend": "fin de semana",
}


def translate_word(query: str) -> str | None:
    """Traduce palabras del inglés al español."""
    q = _norm_es(query)
    m = re.search(r"(?:como se dice|que significa|traduce|traduccion de|translate)\s+[\"']?([a-z\s]+?)[\"']?\s*(?:en espanol|al espanol)?[\s?!.]*$", q)
    if not m:
        m = re.search(r"([a-z\s]+?)\s+(?:en espanol|al espanol|significa en espanol)[\s?!.]*$", q)
    if m:
        word = m.group(1).strip()
        if word in TRANSLATIONS_EN_ES:
            return f"**{word}** en español significa **{TRANSLATIONS_EN_ES[word]}**."
        # buscar coincidencia parcial
        for en, es in TRANSLATIONS_EN_ES.items():
            if word in en or en in word:
                return f"**{en}** en español significa **{es}**."
    return None


# ─────────────────────────────────────────────────────────────── #
# RUTINAS DE EJERCICIO Y TÉCNICAS DE ESTUDIO                       #
# ─────────────────────────────────────────────────────────────── #

EXERCISE_ROUTINES: list[str] = [
    "Rutina en casa (20 min, sin equipo): 3 rondas de — 15 sentadillas, 10 flexiones (de rodillas si necesitas), 20 segundos de plancha, 15 zancadas por pierna y 30 jumping jacks. Descansa 1 minuto entre rondas.",
    "Rutina de fuerza para principiantes: sentadillas 3×12, flexiones 3×10, remo con mochila 3×12, plancha 3×30 segundos y puente de glúteo 3×15. Tres veces por semana con un día de descanso entre sesiones.",
    "Cardio quemagrasa (15 min HIIT): 40 segundos de trabajo + 20 de descanso — jumping jacks, mountain climbers, burpees, sentadillas con salto y escaladores. Repite el circuito 3 veces.",
    "Rutina de movilidad matutina (10 min): círculos de cuello, hombros y cadera (30 seg cada uno), gato-vaca 10 repeticiones, estiramiento de isquiotibiales 1 min por pierna y respiración profunda 2 minutos.",
    "Rutina de abdomen: plancha 45 seg, crunches 20, Russian twists 20, elevación de piernas 15 y plancha lateral 30 seg por lado. Dos rondas.",
    "Rutina para glúteos y piernas: sentadilla búlgara 3×10 por pierna, peso muerto a una pierna 3×12, puente de glúteo 3×20 y patada de glúteo 3×15.",
    "Yoga suave para principiantes: postura del niño 1 min, perro boca abajo 1 min, guerrero I y II 45 seg por lado, cobra 1 min y savasana 3 minutos.",
    "Rutina de espalda sana: superman 3×15, remo invertido 3×10, estiramiento de pecho en marco de puerta 1 min y rotaciones torácicas 10 por lado.",
]

STUDY_TECHNIQUES: list[str] = [
    "Técnica Pomodoro: estudia 25 minutos concentrado, descansa 5. Cada 4 pomodoros, toma un descanso largo de 20-30 minutos.",
    "Repetición espaciada: repasa el material 1 día, 1 semana y 1 mes después de aprenderlo. Es la técnica con más evidencia científica.",
    "Recuperación activa: en vez de releer, cierra el libro y trata de recordar todo. Fallar al recordar y luego revisar fija la memoria.",
    "Mapas mentales: organiza ideas con diagramas que conecten conceptos. Tu cerebro recuerda mejor las relaciones que las listas.",
    "Técnica Feynman: explica el tema como si se lo contaras a un niño de 10 años. Donde te trabas, ahí está lo que no entiendes.",
    "Intercalado: mezcla temas distintos en una sesión en vez de un solo bloque. Cuesta más al inicio, pero el aprendizaje dura más.",
    "Elaboración: pregúntate '¿por qué?' y '¿cómo se conecta con lo que ya sé?' mientras estudias. Crear conexiones fortalece el recuerdo.",
    "Dormir bien: el sueño consolida la memoria. Estudiar de noche sin dormir rinde menos que estudiar menos y dormir 8 horas.",
    "Ambiente: estudia siempre en el mismo lugar ordenado y sin notificaciones. Tu cerebro asocia el lugar con el enfoque.",
    "Pre-lectura: hojea títulos, subtítulos e imágenes antes de leer a fondo. Le da a tu cerebro un mapa de lo que viene.",
]


# ─────────────────────────────────────────────────────────────── #
# MOTOR DE BÚSQUEDA SEMÁNTICA (TF-IDF sobre las preguntas)         #
# ─────────────────────────────────────────────────────────────── #

_search_vectorizer = None
_search_matrix = None
_search_answers: list[str] = []
_search_built = False


def _build_search_index() -> None:
    """Construye el índice TF-IDF de todas las preguntas/respuestas."""
    global _search_vectorizer, _search_matrix, _search_answers, _search_built
    if _search_built:
        return
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        return

    docs: list[str] = []
    _search_answers = []

    # 1) Q&A curados
    for q, a in QA_FACTS:
        docs.append(_norm_es(q))
        _search_answers.append(a)

    # 1b) Datos de países (moneda, idioma, región, capital, superficie)
    for q, a in COUNTRY_QA:
        docs.append(_norm_es(q))
        _search_answers.append(a)

    # 2) Capitales: generar preguntas automáticamente
    for country, capital in CAPITALS.items():
        docs.append(_norm_es(f"cual es la capital de {country}"))
        _search_answers.append(
            f"La capital de {country.title()} es **{capital}**.")
        docs.append(_norm_es(f"capital de {country} cual es"))
        _search_answers.append(
            f"La capital de {country.title()} es **{capital}**.")

    # 3) Elementos: preguntas automáticas
    for num, sym, name in ELEMENTS:
        key = _norm_es(name)
        docs.append(f"simbolo quimico del {key}")
        _search_answers.append(f"El símbolo químico del **{name}** es **{sym}**.")
        docs.append(f"numero atomico del {key}")
        _search_answers.append(f"El **{name}** tiene número atómico **{num}**.")
        docs.append(f"que es el {key} elemento")
        _search_answers.append(
            f"El **{name}** ({sym}) es el elemento químico número **{num}**.")

    _search_vectorizer = TfidfVectorizer(
        analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
    _search_matrix = _search_vectorizer.fit_transform(docs)
    _search_built = True


def answer_knowledge(query: str, threshold: float = 0.60) -> str | None:
    """
    Busca la mejor respuesta factual para la pregunta.
    Devuelve None si ninguna coincide lo suficiente.
    """
    _build_search_index()
    if not _search_built:
        return None
    q = _norm_es(query)
    if len(q) < 8:
        return None
    vec = _search_vectorizer.transform([q])
    scores = (_search_matrix * vec.T).toarray().ravel()
    best = int(scores.argmax())
    if scores[best] >= threshold:
        return _search_answers[best]
    return None


def knowledge_stats() -> dict:
    """Estadísticas de la base de conocimiento."""
    return {
        "capitals": len(CAPITALS),
        "elements": len(ELEMENTS),
        "qa_facts": len(QA_FACTS) + len(COUNTRY_QA),
        "country_facts": len(COUNTRY_QA),
        "curiosities": len(CURIOSITIES),
        "jokes": len(JOKES),
        "riddles": len(RIDDLES),
        "proverbs": len(PROVERBS),
        "quotes": len(QUOTES),
        "stories": len(STORIES),
        "poems": len(POEMS),
        "recipes": len(RECIPES),
        "advice": len(ADVICE),
        "translations": len(TRANSLATIONS_EN_ES),
        "exercise_routines": len(EXERCISE_ROUTINES),
        "study_techniques": len(STUDY_TECHNIQUES),
    }
