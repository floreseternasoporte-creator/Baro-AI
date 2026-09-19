# -*- coding: utf-8 -*-
"""
gen_country_facts.py — Genera country_facts.py con miles de preguntas y
respuestas factuales sobre países (moneda, idioma, región, capital,
superficie), a partir de external_data/countries.json (dataset abierto).

Uso:
    python3 gen_country_facts.py
"""
from __future__ import annotations

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "external_data", "countries.json")
OUT = os.path.join(BASE, "country_facts.py")

CURRENCY_ES = {
    "USD": "dólar estadounidense", "EUR": "euro", "MXN": "peso mexicano",
    "JPY": "yen japonés", "GBP": "libra esterlina", "CAD": "dólar canadiense",
    "BRL": "real brasileño", "ARS": "peso argentino", "CLP": "peso chileno",
    "COP": "peso colombiano", "PEN": "sol peruano", "CHF": "franco suizo",
    "CNY": "yuan chino", "INR": "rupia india", "KRW": "won surcoreano",
    "RUB": "rublo ruso", "AUD": "dólar australiano", "NZD": "dólar neozelandés",
    "SEK": "corona sueca", "NOK": "corona noruega", "DKK": "corona danesa",
    "PLN": "zloti polaco", "CZK": "corona checa", "HUF": "forinto húngaro",
    "RON": "leu rumano", "BGN": "lev búlgaro", "HRK": "kuna croata",
    "TRY": "lira turca", "ZAR": "rand sudafricano", "EGP": "libra egipcia",
    "NGN": "naira nigeriana", "KES": "chelín keniano", "MAD": "dírham marroquí",
    "DZD": "dinar argelino", "TND": "dinar tunecino",
    "SAR": "riyal saudí", "AED": "dírham emiratí", "QAR": "riyal catarí",
    "KWD": "dinar kuwaití", "ILS": "séquel israelí", "JOD": "dinar jordano",
    "LBP": "libra libanesa", "THB": "baht tailandés", "VND": "dong vietnamita",
    "IDR": "rupia indonesia", "MYR": "ringgit malasio", "PHP": "peso filipino",
    "SGD": "dólar singapurense", "HKD": "dólar hongkonés", "TWD": "dólar taiwanés",
    "PKR": "rupia pakistaní", "BDT": "taka bangladesí", "LKR": "rupia esrilanquesa",
    "NPR": "rupia nepalí", "UAH": "grivna ucraniana", "BYN": "rublo bielorruso",
    "GEL": "lari georgiano", "AMD": "dram armenio", "AZN": "manat azerbaiyano",
    "KZT": "tenge kazajo", "UZS": "som uzbeko",
    "UYU": "peso uruguayo", "PYG": "guaraní paraguayo", "BOB": "boliviano",
    "GTQ": "quetzal guatemalteco", "HNL": "lempira hondureña",
    "NIO": "córdoba nicaragüense", "CRC": "colón costarricense",
    "PAB": "balboa panameño", "DOP": "peso dominicano", "CUP": "peso cubano",
    "JMD": "dólar jamaiquino", "TTD": "dólar trinitense",
    "XCD": "dólar del Caribe Oriental", "AWG": "florín arubeño",
    "ANG": "florín antillano", "BBD": "dólar barbadense", "BZD": "dólar beliceño",
    "GYD": "dólar guyanés", "SRD": "dólar surinamés", "FKP": "libra malvinense",
    "GIP": "libra gibraltareña", "SHP": "libra de Santa Elena",
    "ISK": "corona islandesa", "ALL": "lek albanés", "MKD": "denar macedonio",
    "RSD": "dinar serbio", "BAM": "marco bosnio", "MDL": "leu moldavo",
}

LANGUAGE_ES = {
    "Spanish": "español", "English": "inglés", "French": "francés",
    "Portuguese": "portugués", "German": "alemán", "Italian": "italiano",
    "Dutch": "neerlandés", "Chinese": "chino", "Mandarin": "mandarín",
    "Japanese": "japonés", "Korean": "coreano", "Arabic": "árabe",
    "Russian": "ruso", "Hindi": "hindi", "Bengali": "bengalí",
    "Turkish": "turco", "Polish": "polaco", "Swedish": "sueco",
    "Norwegian": "noruego", "Danish": "danés", "Finnish": "finés",
    "Greek": "griego", "Hungarian": "húngaro", "Czech": "checo",
    "Slovak": "eslovaco", "Romanian": "rumano", "Bulgarian": "búlgaro",
    "Croatian": "croata", "Serbian": "serbio", "Ukrainian": "ucraniano",
    "Hebrew": "hebreo", "Persian": "persa", "Urdu": "urdu",
    "Thai": "tailandés", "Vietnamese": "vietnamita", "Indonesian": "indonesio",
    "Malay": "malayo", "Tagalog": "tagalo", "Swahili": "suajili",
    "Hausa": "hausa", "Yoruba": "yoruba", "Amharic": "amárico",
    "Catalan": "catalán", "Galician": "gallego", "Basque": "euskera",
    "Welsh": "galés", "Irish": "irlandés", "Maltese": "maltés",
    "Estonian": "estonio", "Latvian": "letón", "Lithuanian": "lituano",
    "Icelandic": "islandés", "Albanian": "albanés", "Macedonian": "macedonio",
    "Georgian": "georgiano", "Armenian": "armenio", "Azerbaijani": "azerbaiyano",
    "Kazakh": "kazajo", "Uzbek": "uzbeko", "Mongolian": "mongol",
    "Nepali": "nepalí", "Sinhala": "cingalés", "Tamil": "tamil",
    "Telugu": "télugu", "Marathi": "maratí", "Gujarati": "guyaratí",
    "Punjabi": "panyabí", "Malayalam": "malayalam", "Kannada": "canarés",
}

REGION_ES = {
    "Americas": "América", "Europe": "Europa", "Asia": "Asia",
    "Africa": "África", "Oceania": "Oceanía", "Antarctic": "la Antártida",
}
SUBREGION_ES = {
    "North America": "Norteamérica", "South America": "Sudamérica",
    "Central America": "Centroamérica", "Caribbean": "el Caribe",
    "Western Europe": "Europa occidental", "Eastern Europe": "Europa oriental",
    "Northern Europe": "Europa del norte", "Southern Europe": "Europa del sur",
    "South-Eastern Asia": "el sudeste asiático", "Southern Asia": "el sur de Asia",
    "Eastern Asia": "el este de Asia", "Western Asia": "el oeste de Asia",
    "Central Asia": "Asia central", "Middle Africa": "África central",
    "Western Africa": "África occidental", "Eastern Africa": "África oriental",
    "Southern Africa": "África austral", "Northern Africa": "África del norte",
    "Australia and New Zealand": "Australia y Nueva Zelanda",
    "Melanesia": "Melanesia", "Polynesia": "Polinesia", "Micronesia": "Micronesia",
}


def fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def main() -> None:
    data = json.load(open(SRC, encoding="utf-8"))
    qa: list[tuple[str, str]] = []

    for c in data:
        spa = (c.get("translations") or {}).get("spa") or {}
        pais = spa.get("common") or c["name"]["common"]
        if not pais:
            continue

        # ── Capital ──
        cap = (c.get("capital") or [None])[0]
        if cap:
            ans = f"La capital de {pais} es {cap}."
            for q in (f"cuál es la capital de {pais}",
                      f"dime la capital de {pais}",
                      f"capital de {pais}"):
                qa.append((q, ans))

        # ── Moneda ──
        cur = c.get("currencies") or {}
        if cur:
            code = next(iter(cur))
            info = cur[code] or {}
            nombre = CURRENCY_ES.get(code, info.get("name", code))
            ans = f"La moneda de {pais} es el {nombre} ({code})."
            for q in (f"cuál es la moneda de {pais}",
                      f"qué moneda se usa en {pais}",
                      f"con qué moneda se paga en {pais}"):
                qa.append((q, ans))

        # ── Idioma ──
        langs = c.get("languages") or {}
        if langs:
            nombres = [LANGUAGE_ES.get(v, v) for v in langs.values()]
            if len(nombres) == 1:
                ans = f"En {pais} se habla {nombres[0]}."
            else:
                ans = f"En {pais} se hablan: {', '.join(nombres)}."
            for q in (f"qué idioma se habla en {pais}",
                      f"cuál es el idioma de {pais}",
                      f"qué lengua hablan en {pais}"):
                qa.append((q, ans))

        # ── Región ──
        region = REGION_ES.get(c.get("region", ""), c.get("region", ""))
        sub = SUBREGION_ES.get(c.get("subregion", ""), c.get("subregion", ""))
        if region:
            ans = f"{pais} está en {region}" + (f" ({sub})." if sub else ".")
            for q in (f"en qué continente está {pais}",
                      f"dónde queda {pais}",
                      f"en qué región está {pais}"):
                qa.append((q, ans))

        # ── Superficie ──
        area = c.get("area")
        if area:
            ans = f"La superficie de {pais} es de {fmt_num(int(area))} km²."
            for q in (f"cuál es la superficie de {pais}",
                      f"qué tamaño tiene {pais}",
                      f"cuántos kilómetros cuadrados tiene {pais}"):
                qa.append((q, ans))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""Datos factuales de países generados con gen_country_facts.py."""\n')
        f.write(f"COUNTRY_QA: list[tuple[str, str]] = [\n")
        for q, a in qa:
            f.write(f"    ({q!r}, {a!r}),\n")
        f.write("]\n")

    print(f"{len(qa)} pares Q&A de países generados en {OUT}")


if __name__ == "__main__":
    main()
