# -*- coding: utf-8 -*-
"""
calculator.py — Calculadora ULTRA AVANZADA de Baro v4.0
========================================================
Motor matemático completo con:
- Aritmética básica y avanzada
- Trigonometría completa (sen, cos, tan, arcsen, arccos, arctan)
- Logaritmos (log natural, log base 10, log base N)
- Potencias, raíces (cuadrada, cúbica, N-ésima)
- Factorial, combinaciones, permutaciones
- Estadística (media, mediana, moda, varianza, desviación estándar)
- Conversiones de unidades (temperatura, longitud, peso, velocidad)
- Porcentajes, proporciones, regla de tres
- Interés simple e interés compuesto
- IMC (Índice de Masa Corporal)
- Área y perímetro de figuras geométricas
- Progresiones aritméticas y geométricas
- MCD y MCM
- Expresiones en lenguaje natural en español
- Evaluación segura via AST (sin eval directo)
"""

from __future__ import annotations

import ast
import math
import operator as op
import re
import statistics
from typing import Optional, Union


class CalculatorError(Exception):
    pass


# ─────────────────────────────────────────────────────────────── #
# Constantes matemáticas                                          #
# ─────────────────────────────────────────────────────────────── #

CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "phi": (1 + math.sqrt(5)) / 2,   # número áureo
    "tau": math.tau,
    "inf": math.inf,
}

# ─────────────────────────────────────────────────────────────── #
# Funciones matemáticas permitidas                                 #
# ─────────────────────────────────────────────────────────────── #

def _cot(x: float) -> float:
    if math.sin(x) == 0:
        raise CalculatorError("Cotangente indefinida en ese ángulo.")
    return math.cos(x) / math.sin(x)

def _sec(x: float) -> float:
    if math.cos(x) == 0:
        raise CalculatorError("Secante indefinida en ese ángulo.")
    return 1 / math.cos(x)

def _csc(x: float) -> float:
    if math.sin(x) == 0:
        raise CalculatorError("Cosecante indefinida en ese ángulo.")
    return 1 / math.sin(x)

def _deg_to_rad(x: float) -> float:
    return math.radians(x)

def _rad_to_deg(x: float) -> float:
    return math.degrees(x)

def _log_base(x: float, base: float) -> float:
    if x <= 0:
        raise CalculatorError("El logaritmo solo está definido para números positivos.")
    if base <= 0 or base == 1:
        raise CalculatorError("La base del logaritmo debe ser positiva y diferente de 1.")
    return math.log(x, base)

def _nroot(n: float, x: float) -> float:
    """Raíz N-ésima de x"""
    if x < 0 and n % 2 == 0:
        raise CalculatorError("No existe raíz par de número negativo.")
    return math.copysign(abs(x) ** (1.0/n), x)

def _safe_factorial(n: float) -> float:
    if n < 0 or n != int(n):
        raise CalculatorError("El factorial solo está definido para enteros no negativos.")
    if n > 170:
        raise CalculatorError("Número demasiado grande para factorial (máximo 170).")
    return float(math.factorial(int(n)))

def _combinations(n: float, r: float) -> float:
    if n < 0 or r < 0 or n != int(n) or r != int(r):
        raise CalculatorError("n y r deben ser enteros no negativos.")
    n, r = int(n), int(r)
    if r > n:
        raise CalculatorError("r no puede ser mayor que n en combinaciones.")
    return float(math.comb(n, r))

def _permutations(n: float, r: float) -> float:
    if n < 0 or r < 0 or n != int(n) or r != int(r):
        raise CalculatorError("n y r deben ser enteros no negativos.")
    n, r = int(n), int(r)
    if r > n:
        raise CalculatorError("r no puede ser mayor que n en permutaciones.")
    return float(math.perm(n, r))

def _mcd(a: float, b: float) -> float:
    return float(math.gcd(int(abs(a)), int(abs(b))))

def _mcm(a: float, b: float) -> float:
    a, b = int(abs(a)), int(abs(b))
    if a == 0 or b == 0:
        return 0.0
    return float(abs(a * b) // math.gcd(a, b))

def _safe_tan(x: float) -> float:
    cos_val = math.cos(x)
    if abs(cos_val) < 1e-10:
        raise CalculatorError("Tangente indefinida en ese ángulo (cos = 0).")
    return math.tan(x)

def _safe_log(x: float) -> float:
    if x <= 0:
        raise CalculatorError("El logaritmo natural solo está definido para números positivos.")
    return math.log(x)

def _safe_log10(x: float) -> float:
    if x <= 0:
        raise CalculatorError("El logaritmo base 10 solo está definido para números positivos.")
    return math.log10(x)

def _safe_log2(x: float) -> float:
    if x <= 0:
        raise CalculatorError("El logaritmo base 2 solo está definido para números positivos.")
    return math.log2(x)

def _safe_sqrt(x: float) -> float:
    if x < 0:
        raise CalculatorError("No existe raíz cuadrada de número negativo en los reales.")
    return math.sqrt(x)

def _safe_asin(x: float) -> float:
    if x < -1 or x > 1:
        raise CalculatorError("arcsen solo está definido para valores entre -1 y 1.")
    return math.asin(x)

def _safe_acos(x: float) -> float:
    if x < -1 or x > 1:
        raise CalculatorError("arccos solo está definido para valores entre -1 y 1.")
    return math.acos(x)

SAFE_FUNCTIONS = {
    # Trigonométricas (argumento en radianes)
    "sin": math.sin,
    "sen": math.sin,
    "cos": math.cos,
    "tan": _safe_tan,
    "tg": _safe_tan,
    "cot": _cot,
    "sec": _sec,
    "csc": _csc,
    # Trigonométricas inversas
    "asin": _safe_asin,
    "arcsin": _safe_asin,
    "arcsen": _safe_asin,
    "acos": _safe_acos,
    "arccos": _safe_acos,
    "atan": math.atan,
    "arctan": math.atan,
    "atan2": math.atan2,
    # Trigonométricas con grados
    "sind": lambda x: math.sin(math.radians(x)),
    "cosd": lambda x: math.cos(math.radians(x)),
    "tand": lambda x: _safe_tan(math.radians(x)),
    # Hiperbólicas
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    # Logaritmos
    "log": _safe_log,
    "ln": _safe_log,
    "log10": _safe_log10,
    "log2": _safe_log2,
    "logb": _log_base,        # logb(x, base)
    # Potencias y raíces
    "sqrt": _safe_sqrt,
    "raiz": _safe_sqrt,
    "cbrt": lambda x: math.copysign(abs(x)**(1/3), x),
    "nroot": _nroot,           # nroot(n, x)
    # Redondeo
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "trunc": math.trunc,
    # Exponencial
    "exp": math.exp,
    # Combinatoria
    "factorial": _safe_factorial,
    "fact": _safe_factorial,
    "C": _combinations,        # C(n, r)
    "comb": _combinations,
    "P": _permutations,        # P(n, r)
    "perm": _permutations,
    # Teoría de números
    "mcd": _mcd,
    "gcd": _mcd,
    "mcm": _mcm,
    "lcm": _mcm,
    # Conversiones angulares
    "deg": _rad_to_deg,
    "rad": _deg_to_rad,
    # Potencia
    "pow": pow,
    "min": min,
    "max": max,
}

# ─────────────────────────────────────────────────────────────── #
# Operadores binarios permitidos                                   #
# ─────────────────────────────────────────────────────────────── #

_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.FloorDiv: op.floordiv,
    ast.BitXor: op.xor,
}

_UNARY_OPS = {
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}


# ─────────────────────────────────────────────────────────────── #
# Evaluador AST seguro                                             #
# ─────────────────────────────────────────────────────────────── #

def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise CalculatorError("Solo se permiten números.")

    if isinstance(node, ast.Name):
        name = node.id.lower()
        if name in CONSTANTS:
            return CONSTANTS[name]
        raise CalculatorError(f"Variable '{name}' no reconocida. Constantes disponibles: pi, e, phi, tau.")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise CalculatorError("Operación no permitida.")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        try:
            result = _BIN_OPS[op_type](left, right)
            if math.isinf(result):
                raise CalculatorError("El resultado es infinito.")
            return result
        except ZeroDivisionError:
            raise CalculatorError("No se puede dividir entre cero.")
        except OverflowError:
            raise CalculatorError("El número es demasiado grande.")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise CalculatorError("Operación no permitida.")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Attribute):
            raise CalculatorError("Acceso a atributos no permitido por seguridad.")
        if not isinstance(node.func, ast.Name):
            raise CalculatorError("Llamada de función no válida.")
        func_name = node.func.id
        if func_name not in SAFE_FUNCTIONS:
            raise CalculatorError(
                f"Función '{func_name}' no reconocida. "
                f"Funciones disponibles: sin, cos, tan, sqrt, log, factorial, abs, round, ceil, floor, exp, mcd, mcm, C, P, nroot..."
            )
        args = [_eval_node(a) for a in node.args]
        try:
            return float(SAFE_FUNCTIONS[func_name](*args))
        except CalculatorError:
            raise
        except Exception as exc:
            raise CalculatorError(f"Error en {func_name}(): {exc}")

    raise CalculatorError("Expresión no válida.")


# ─────────────────────────────────────────────────────────────── #
# Formateador de resultado                                         #
# ─────────────────────────────────────────────────────────────── #

def _format_result(result: float) -> Union[int, float, str]:
    """Formatea el resultado de forma legible."""
    if math.isnan(result):
        raise CalculatorError("El resultado es indefinido (NaN).")
    if math.isinf(result):
        return "∞ (infinito)"
    if isinstance(result, float):
        if result == int(result) and abs(result) < 1e15:
            return int(result)
        # Hasta 10 decimales significativos, sin ceros innecesarios
        rounded = round(result, 10)
        formatted = f"{rounded:.10f}".rstrip("0").rstrip(".")
        return formatted
    return result


# ─────────────────────────────────────────────────────────────── #
# Evaluador principal                                             #
# ─────────────────────────────────────────────────────────────── #

def evaluate_expression(expr: str) -> Union[int, float, str]:
    """
    Evalúa una expresión matemática de forma segura.
    Soporta: operaciones básicas, trigonometría, logaritmos,
    factorial, combinatoria, constantes (pi, e, phi), etc.
    """
    expr = expr.strip()
    if not expr:
        raise CalculatorError("La expresión está vacía.")

    # Normalización de símbolos
    replacements = [
        ("×", "*"), ("÷", "/"), ("^", "**"),
        ("²", "**2"), ("³", "**3"),
        ("\u00b2", "**2"), ("\u00b3", "**3"),  # superíndices unicode
    ]
    for old, new in replacements:
        expr = expr.replace(old, new)

    # Reemplazar 'x' como multiplicación SOLO cuando está entre números
    expr = re.sub(r"(?<=\d)\s*x\s*(?=\d)", "*", expr)

    # Reemplazar comas como separador decimal SOLO cuando hay exactamente 3 dígitos
    # después (millar) o 1-2 dígitos (decimal), NO cuando preceden un número con )
    # Heurística simple: si la coma está dentro de paréntesis con más de un número,
    # es separador de argumento. Usamos marcador temporal.
    # Paso 1: proteger comas dentro de paréntesis de función (son separadores de args)
    def protect_function_commas(s: str) -> str:
        """Reemplaza comas-separadoras dentro de funciones por §."""
        result = []
        depth = 0
        in_func = False
        i = 0
        while i < len(s):
            c = s[i]
            if c == '(':
                depth += 1
                # ¿precede un nombre de función?
                j = i - 1
                while j >= 0 and (s[j].isalnum() or s[j] == '_'):
                    j -= 1
                fname = s[j+1:i]
                if fname:  # hay nombre antes del paren
                    in_func = True
                result.append(c)
            elif c == ')':
                depth -= 1
                if depth == 0:
                    in_func = False
                result.append(c)
            elif c == ',' and depth > 0:
                result.append('§')  # marcador temporal
            else:
                result.append(c)
            i += 1
        return ''.join(result)

    expr = protect_function_commas(expr)
    # Ahora las comas restantes son decimales -> convertir a punto
    expr = expr.replace(",", ".")
    # Restaurar separadores de argumentos
    expr = expr.replace("§", ",")

    # Normalizar espacios
    expr = re.sub(r"\s+", "", expr)

    # Multiplicación implícita SEGURA:
    # 2pi → 2*pi, 2(x) → 2*(x), (a)(b) → (a)*(b)
    # Pero NO romper: log10(...), log2(...), sin2(...), etc.
    # Estrategia: solo insertar * entre dígito( cuando ese dígito NO es parte de un nombre
    # de función (es decir, el dígito está precedido solo de dígitos o al inicio)
    expr = re.sub(r"(\d)(pi|tau|phi)\b", r"\1*\2", expr)
    # Insertar * en "dígito(" SOLO si precede solo dígitos (no letras): e.g. 3( pero no log10(
    expr = re.sub(r"(?<!\w)(\d+)\(", r"\1*(", expr)   # número al inicio o tras no-word
    # También para el caso 2(... pero con letra antes como log10(: el lookbehind \w lo bloquea
    # Caso simple sin letra antes:
    expr = re.sub(r"\)(\d)", r")*\1", expr)
    expr = re.sub(r"\)\(", r")*(", expr)

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise CalculatorError(f"Error de sintaxis en la expresión: {exc}")

    result = _eval_node(tree.body if hasattr(tree, "body") else tree)
    return _format_result(result)


# ─────────────────────────────────────────────────────────────── #
# Calculadoras especializadas                                      #
# ─────────────────────────────────────────────────────────────── #

def calculate_percentage(percentage: float, total: float) -> str:
    """Calcula el porcentaje de un total."""
    result = (percentage / 100) * total
    return f"{percentage}% de {total} = {_format_result(result)}"


def calculate_percentage_change(original: float, new_val: float) -> str:
    """Calcula el cambio porcentual entre dos valores."""
    if original == 0:
        raise CalculatorError("El valor original no puede ser cero.")
    change = ((new_val - original) / original) * 100
    direction = "incremento" if change >= 0 else "disminución"
    return f"Hay un {direction} de {_format_result(abs(change))}% (de {original} a {new_val})"


def calculate_simple_interest(principal: float, rate: float, time: float) -> str:
    """Interés simple: I = P * r * t"""
    interest = principal * (rate / 100) * time
    total = principal + interest
    return (
        f"Capital: {principal} | Tasa: {rate}% | Tiempo: {time} años\n"
        f"Interés simple: {_format_result(interest)}\n"
        f"Monto total: {_format_result(total)}"
    )


def calculate_compound_interest(principal: float, rate: float, time: float, n: float = 12) -> str:
    """Interés compuesto: A = P(1 + r/n)^(nt)"""
    total = principal * (1 + (rate / 100) / n) ** (n * time)
    interest = total - principal
    return (
        f"Capital: {principal} | Tasa: {rate}% | Tiempo: {time} años | Períodos/año: {int(n)}\n"
        f"Interés compuesto ganado: {_format_result(interest)}\n"
        f"Monto total: {_format_result(total)}"
    )


def calculate_imc(weight_kg: float, height_m: float) -> str:
    """Calcula el IMC (Índice de Masa Corporal)."""
    if height_m <= 0 or weight_kg <= 0:
        raise CalculatorError("El peso y la altura deben ser valores positivos.")
    if height_m > 3:
        height_m /= 100  # convertir cm a m
    imc = weight_kg / (height_m ** 2)
    imc_f = _format_result(imc)
    if imc < 18.5:
        categoria = "Bajo peso"
    elif imc < 25:
        categoria = "Peso normal"
    elif imc < 30:
        categoria = "Sobrepeso"
    elif imc < 35:
        categoria = "Obesidad grado 1"
    elif imc < 40:
        categoria = "Obesidad grado 2"
    else:
        categoria = "Obesidad grado 3"
    return f"IMC = {imc_f} → Categoría: {categoria}"


def calculate_statistics(numbers: list) -> str:
    """Calcula estadísticas descriptivas de una lista de números."""
    if not numbers:
        raise CalculatorError("La lista de números está vacía.")
    if len(numbers) < 2:
        raise CalculatorError("Se necesitan al menos 2 números para calcular estadísticas.")
    n = len(numbers)
    mean = statistics.mean(numbers)
    median = statistics.median(numbers)
    try:
        mode = statistics.mode(numbers)
        mode_str = str(_format_result(mode))
    except statistics.StatisticsError:
        mode_str = "No hay moda única"
    stdev = statistics.stdev(numbers)
    variance = statistics.variance(numbers)
    total = sum(numbers)
    return (
        f"N = {n} datos: {numbers}\n"
        f"Suma: {_format_result(total)}\n"
        f"Media: {_format_result(mean)}\n"
        f"Mediana: {_format_result(median)}\n"
        f"Moda: {mode_str}\n"
        f"Desv. estándar: {_format_result(stdev)}\n"
        f"Varianza: {_format_result(variance)}\n"
        f"Mínimo: {_format_result(min(numbers))} | Máximo: {_format_result(max(numbers))}"
    )


def convert_temperature(value: float, from_unit: str, to_unit: str) -> str:
    """Convierte entre Celsius, Fahrenheit y Kelvin."""
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    celsius_map = {"c": lambda v: v, "f": lambda v: (v - 32) * 5/9, "k": lambda v: v - 273.15}
    to_celsius_map = {"c": lambda v: v, "f": lambda v: v * 9/5 + 32, "k": lambda v: v + 273.15}
    abbrevs = {"celsius": "c", "fahrenheit": "f", "kelvin": "k", "°c": "c", "°f": "f", "°k": "k"}
    from_unit = abbrevs.get(from_unit, from_unit)
    to_unit = abbrevs.get(to_unit, to_unit)
    if from_unit not in celsius_map or to_unit not in to_celsius_map:
        raise CalculatorError("Unidades de temperatura no reconocidas. Usa: C, F, K")
    celsius_val = celsius_map[from_unit](value)
    result = to_celsius_map[to_unit](celsius_val)
    unit_names = {"c": "°C", "f": "°F", "k": "K"}
    return f"{value}{unit_names[from_unit]} = {_format_result(result)}{unit_names[to_unit]}"


UNIT_CONVERSIONS = {
    # Longitud a metros
    "km": 1000, "m": 1, "cm": 0.01, "mm": 0.001,
    "mi": 1609.344, "yd": 0.9144, "ft": 0.3048, "in": 0.0254,
    "nm": 1852,  # milla náutica
    # Peso a gramos
    "kg_g": 1000, "g": 1, "mg": 0.001, "lb_g": 453.592, "oz_g": 28.3495, "ton_g": 1_000_000,
    # Velocidad a km/h
    "kmh": 1, "mph": 1.60934, "ms": 3.6, "knot": 1.852,
}

LENGTH_UNITS = {"km", "m", "cm", "mm", "mi", "yd", "ft", "in", "nm"}
WEIGHT_UNITS_G = {"kg": 1000, "g": 1, "mg": 0.001, "lb": 453.592, "oz": 28.3495, "ton": 1_000_000}
SPEED_UNITS = {"km/h": 1, "kmh": 1, "mph": 1.60934, "m/s": 3.6, "ms": 3.6, "knot": 1.852, "nudos": 1.852}

LENGTH_TO_METERS = {"km": 1000, "m": 1, "cm": 0.01, "mm": 0.001,
                    "mi": 1609.344, "milla": 1609.344, "millas": 1609.344,
                    "yd": 0.9144, "yarda": 0.9144, "yardas": 0.9144,
                    "ft": 0.3048, "pie": 0.3048, "pies": 0.3048,
                    "in": 0.0254, "pulgada": 0.0254, "pulgadas": 0.0254,
                    "nm": 1852}

def convert_length(value: float, from_unit: str, to_unit: str) -> str:
    """Convierte entre unidades de longitud."""
    from_u = from_unit.lower()
    to_u = to_unit.lower()
    if from_u not in LENGTH_TO_METERS or to_u not in LENGTH_TO_METERS:
        raise CalculatorError(f"Unidad no reconocida. Disponibles: {', '.join(LENGTH_TO_METERS.keys())}")
    meters = value * LENGTH_TO_METERS[from_u]
    result = meters / LENGTH_TO_METERS[to_u]
    return f"{value} {from_unit} = {_format_result(result)} {to_unit}"


def convert_weight(value: float, from_unit: str, to_unit: str) -> str:
    """Convierte entre unidades de peso."""
    from_u = from_unit.lower()
    to_u = to_unit.lower()
    if from_u not in WEIGHT_UNITS_G or to_u not in WEIGHT_UNITS_G:
        raise CalculatorError(f"Unidad no reconocida. Disponibles: {', '.join(WEIGHT_UNITS_G.keys())}")
    grams = value * WEIGHT_UNITS_G[from_u]
    result = grams / WEIGHT_UNITS_G[to_u]
    return f"{value} {from_unit} = {_format_result(result)} {to_unit}"


def solve_quadratic(a: float, b: float, c: float) -> str:
    """Resuelve ecuación cuadrática: ax² + bx + c = 0"""
    if a == 0:
        if b == 0:
            if c == 0:
                return "La ecuación tiene infinitas soluciones (0 = 0)."
            return "No hay solución (la ecuación es una contradicción)."
        x = -c / b
        return f"Ecuación lineal: x = {_format_result(x)}"
    discriminante = b**2 - 4*a*c
    if discriminante > 0:
        x1 = (-b + math.sqrt(discriminante)) / (2*a)
        x2 = (-b - math.sqrt(discriminante)) / (2*a)
        return (
            f"Ecuación: {a}x² + {b}x + {c} = 0\n"
            f"Discriminante: {_format_result(discriminante)} > 0 → Dos raíces reales\n"
            f"x₁ = {_format_result(x1)}\n"
            f"x₂ = {_format_result(x2)}"
        )
    elif discriminante == 0:
        x = -b / (2*a)
        return (
            f"Ecuación: {a}x² + {b}x + {c} = 0\n"
            f"Discriminante = 0 → Raíz doble\n"
            f"x = {_format_result(x)}"
        )
    else:
        real_part = -b / (2*a)
        imag_part = math.sqrt(-discriminante) / (2*a)
        return (
            f"Ecuación: {a}x² + {b}x + {c} = 0\n"
            f"Discriminante: {_format_result(discriminante)} < 0 → Raíces complejas\n"
            f"x₁ = {_format_result(real_part)} + {_format_result(imag_part)}i\n"
            f"x₂ = {_format_result(real_part)} - {_format_result(imag_part)}i"
        )


def nth_fibonacci(n: int) -> str:
    """Calcula el n-ésimo número de Fibonacci."""
    if n < 0:
        raise CalculatorError("El índice debe ser no negativo.")
    if n > 1000:
        raise CalculatorError("Índice muy grande (máximo 1000).")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return f"Fibonacci({n}) = {a}"


def is_prime(n: int) -> str:
    """Determina si un número es primo."""
    if n < 2:
        return f"{n} NO es primo."
    if n == 2:
        return f"{n} ES primo."
    if n % 2 == 0:
        return f"{n} NO es primo (es par)."
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return f"{n} NO es primo (divisible entre {i})."
    return f"{n} ES primo."


def prime_factors(n: int) -> str:
    """Factorización prima de un número."""
    if n < 2:
        raise CalculatorError("El número debe ser mayor o igual a 2.")
    factors = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
    if n > 1:
        factors.append(n)
    factor_str = " × ".join(str(f) for f in factors)
    return f"Factores primos: {factor_str}"


def arithmetic_sequence(first: float, diff: float, n: int) -> str:
    """Progresión aritmética: suma de n términos."""
    if n <= 0:
        raise CalculatorError("El número de términos debe ser positivo.")
    last = first + (n - 1) * diff
    total = n * (first + last) / 2
    return (
        f"Progresión aritmética\n"
        f"a₁={first}, d={diff}, n={n}\n"
        f"Último término: {_format_result(last)}\n"
        f"Suma de {n} términos: {_format_result(total)}"
    )


def geometric_sequence(first: float, ratio: float, n: int) -> str:
    """Progresión geométrica: suma de n términos."""
    if n <= 0:
        raise CalculatorError("El número de términos debe ser positivo.")
    if ratio == 1:
        total = first * n
    else:
        total = first * (1 - ratio**n) / (1 - ratio)
    last = first * ratio**(n - 1)
    return (
        f"Progresión geométrica\n"
        f"a₁={first}, r={ratio}, n={n}\n"
        f"Último término: {_format_result(last)}\n"
        f"Suma de {n} términos: {_format_result(total)}"
    )


def rule_of_three(a: float, b: float, c: float, inverse: bool = False) -> str:
    """Regla de tres simple: si a → b, entonces c → ?"""
    if a == 0:
        raise CalculatorError("El primer valor no puede ser cero.")
    if inverse:
        x = (a * b) / c
        return f"Regla de tres inversa: si {a}→{b}, entonces {c}→ {_format_result(x)}"
    x = (b * c) / a
    return f"Regla de tres directa: si {a}→{b}, entonces {c}→ {_format_result(x)}"


def area_perimeter(shape: str, *args) -> str:
    """Calcula área y perímetro de figuras geométricas."""
    shape = shape.lower()
    if shape in ("circulo", "círculo", "circle"):
        r = args[0]
        area = math.pi * r**2
        perimeter = 2 * math.pi * r
        return f"Círculo (r={r})\nÁrea = {_format_result(area)}\nCircunferencia = {_format_result(perimeter)}"
    elif shape in ("cuadrado", "square"):
        l = args[0]
        area = l**2
        perimeter = 4 * l
        return f"Cuadrado (lado={l})\nÁrea = {_format_result(area)}\nPerímetro = {_format_result(perimeter)}"
    elif shape in ("rectangulo", "rectángulo", "rectangle"):
        w, h = args[0], args[1]
        area = w * h
        perimeter = 2 * (w + h)
        return f"Rectángulo ({w}×{h})\nÁrea = {_format_result(area)}\nPerímetro = {_format_result(perimeter)}"
    elif shape in ("triangulo", "triángulo", "triangle"):
        a, b, c = args[0], args[1], args[2]
        s = (a + b + c) / 2
        area = math.sqrt(s * (s-a) * (s-b) * (s-c))
        perimeter = a + b + c
        return f"Triángulo (lados: {a}, {b}, {c})\nÁrea = {_format_result(area)}\nPerímetro = {_format_result(perimeter)}"
    elif shape in ("trapecio", "trapezoid"):
        b1, b2, h = args[0], args[1], args[2]
        area = (b1 + b2) * h / 2
        return f"Trapecio (b1={b1}, b2={b2}, h={h})\nÁrea = {_format_result(area)}"
    elif shape in ("esfera", "sphere"):
        r = args[0]
        volume = (4/3) * math.pi * r**3
        surface = 4 * math.pi * r**2
        return f"Esfera (r={r})\nVolumen = {_format_result(volume)}\nÁrea superficial = {_format_result(surface)}"
    elif shape in ("cilindro", "cylinder"):
        r, h = args[0], args[1]
        volume = math.pi * r**2 * h
        surface = 2 * math.pi * r * (r + h)
        return f"Cilindro (r={r}, h={h})\nVolumen = {_format_result(volume)}\nÁrea superficial = {_format_result(surface)}"
    elif shape in ("cono", "cone"):
        r, h = args[0], args[1]
        slant = math.sqrt(r**2 + h**2)
        volume = (1/3) * math.pi * r**2 * h
        surface = math.pi * r * (r + slant)
        return f"Cono (r={r}, h={h})\nVolumen = {_format_result(volume)}\nÁrea superficial = {_format_result(surface)}"
    else:
        raise CalculatorError(f"Figura '{shape}' no reconocida. Disponibles: circulo, cuadrado, rectangulo, triangulo, trapecio, esfera, cilindro, cono")
