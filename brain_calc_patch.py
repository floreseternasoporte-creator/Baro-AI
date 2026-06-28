# Este archivo contiene las nuevas funciones de extracción matemática
# para ser integradas en brain.py

# ─────────────────────────────────────────────────────────────── #
# NUEVOS PATRONES DE CÁLCULO (ampliados x10)                      #
# ─────────────────────────────────────────────────────────────── #

CALC_PATTERNS_NEW = [
    # Comandos directos
    r"\bcalcula\b", r"\bcalculame\b", r"\bcalcular\b",
    r"\bresuelve\b", r"\bresuelveme\b",
    r"\bcuanto es\b", r"\bcuanto da\b", r"\bcuanto resulta\b", r"\bcuanto seria\b",
    r"\bcual es el resultado\b", r"\bcual es el valor\b",
    r"\boperacion\b", r"\bcalculadora\b",
    # Operaciones básicas
    r"\bsuma\b", r"\bsumar\b", r"\badd\b",
    r"\bresta\b", r"\brestar\b", r"\bsubtraer\b",
    r"\bmultiplica\b", r"\bmultiplicar\b", r"\bmultiplicacion\b",
    r"\bdivide\b", r"\bdividir\b", r"\bdivision\b",
    # Potencias y raíces
    r"\braiz cuadrada\b", r"\braiz cubica\b", r"\braiz de\b", r"\braiz\b",
    r"\bpotencia\b", r"\belevado a\b", r"\bal cuadrado\b", r"\bal cubo\b",
    r"\bcuadrado de\b", r"\bcubo de\b", r"\bpow\b",
    # Trigonometría
    r"\bseno\b", r"\bcoseno\b", r"\btangente\b", r"\bcotangente\b",
    r"\barcoseno\b", r"\barcocoseno\b", r"\barctangente\b",
    r"\bsin\b", r"\bcos\b", r"\btan\b",
    r"\btrigonometri\b", r"\bangulo\b", r"\bradiane\b", r"\bgrado\b",
    # Logaritmos
    r"\blogaritmo\b", r"\blog\b", r"\bln\b", r"\blog natural\b",
    r"\blog base\b", r"\blogaritmo natural\b",
    # Porcentajes
    r"\bpor ciento\b", r"\bporciento\b", r"\bporcentaje\b",
    r"[\d\.]+\s*%\s*de\b", r"\b%\s*de\b",
    r"\bcuanto es el \d+%\b", r"\bque porcentaje\b",
    # Factorial y combinatoria
    r"\bfactorial\b", r"\bcombinaciones\b", r"\bpermutaciones\b",
    r"\bcuantas combinaciones\b", r"\bcuantas permutaciones\b",
    r"\bC\(\d", r"\bP\(\d",
    # Estadística
    r"\bmedia de\b", r"\bpromedio de\b", r"\bmedia aritmetica\b",
    r"\bmediana de\b", r"\bmoda de\b", r"\bdesviacion estandar\b",
    r"\bvarianza de\b", r"\bpromedio\b",
    # Conversiones
    r"\bconvierte\b", r"\bconvertir\b", r"\bconversion\b",
    r"\bconvertir\b.*\ba\b", r"\ben\b.*\b(km|metros|cm|kg|lb|celsius|fahrenheit)\b",
    r"\bconvierte\b.*\b(grados|metros|km|kg|lb|millas)\b",
    r"\bcuantos\b.*\b(metros|km|cm|kg|lb|gramos)\b",
    # Interés
    r"\binteres simple\b", r"\binteres compuesto\b",
    r"\bcapital\b.*\btasa\b", r"\btasa de interes\b",
    # Geometría
    r"\barea del\b", r"\barea de la\b", r"\barea de un\b",
    r"\bperimetro\b", r"\bvolumen del\b", r"\bvolumen de\b",
    r"\bcirculo\b.*\bradio\b", r"\bcuadrado\b.*\blado\b",
    r"\btriangulo\b.*\blados\b", r"\bsuperficie\b",
    # Ecuaciones
    r"\becuacion cuadratica\b", r"\becuacion de segundo grado\b",
    r"\bax2\b", r"\bx\^2\b",  r"\bdiscriminante\b",
    # Fibonacci y primos
    r"\bfibonacci\b", r"\bnumero primo\b", r"\bes primo\b",
    r"\bfactores primos\b", r"\bfactorizacion\b",
    # IMC
    r"\bimc\b", r"\bindice de masa corporal\b",
    r"\bpeso ideal\b.*\bestatura\b", r"\bestatura\b.*\bpeso\b",
    # Regla de tres
    r"\bregla de tres\b", r"\bproporcional\b",
    # Progresiones
    r"\bprogresion aritmetica\b", r"\bprogresion geometrica\b",
    r"\bsuma de progresion\b",
    # MCD / MCM
    r"\bmcd\b", r"\bmcm\b", r"\bmaximo comun divisor\b", r"\bminimo comun multiplo\b",
    # Expresiones directas con números
    r"^\s*-?[\d\.\,]+\s*[\+\-\*\/x×÷\^%]\s*-?[\d\.\,]+",
    r"\b\d+\s*[\+\-\*\/]\s*\d+\b",
    # Palabras numéricas con operadores
    r"\bdos mas\b", r"\btres por\b", r"\bcinco entre\b", r"\bdiez menos\b",
    r"\bdoble de\b", r"\btriple de\b", r"\bcuadruple de\b",
    r"\bla mitad de\b", r"\bun tercio de\b", r"\bun cuarto de\b",
    r"\b\d+\s*al\s*\w+\b",
]

WORDS_TO_EXPR_MAP = {
    # Operadores
    " mas ": " + ", " más ": " + ", " and ": " + ",
    " menos ": " - ",
    " por ": " * ", " multiplicado por ": " * ", " por ": " * ",
    " entre ": " / ", " dividido entre ": " / ", " dividido por ": " / ",
    " elevado a ": " ** ", " a la potencia de ": " ** ", " a la ": " ** ",
    " al cuadrado": " ** 2", " al cubo": " ** 3",
    " al cuarto": " ** 4", " al quinto": " ** 5",
    # Números escritos
    "cero": "0", "uno": "1", "una": "1", "dos": "2", "tres": "3",
    "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7", "ocho": "8",
    "nueve": "9", "diez": "10", "once": "11", "doce": "12", "trece": "13",
    "catorce": "14", "quince": "15", "dieciseis": "16", "diecisiete": "17",
    "dieciocho": "18", "diecinueve": "19", "veinte": "20", "veintiuno": "21",
    "veintidos": "22", "veintitres": "23", "veinticuatro": "24", "veinticinco": "25",
    "treinta": "30", "cuarenta": "40", "cincuenta": "50", "sesenta": "60",
    "setenta": "70", "ochenta": "80", "noventa": "90", "cien": "100",
    "ciento": "1", "doscientos": "200", "trescientos": "300", "cuatrocientos": "400",
    "quinientos": "500", "seiscientos": "600", "setecientos": "700",
    "ochocientos": "800", "novecientos": "900", "mil": "1000",
    "millon": "1000000", "millones": "1000000",
}
