# -*- coding: utf-8 -*-
"""
calculator.py — Calculadora segura de Baro.

Evalúa expresiones matemáticas SIN usar eval() directamente sobre texto
arbitrario (eso sería un riesgo de seguridad). En su lugar, parseamos la
expresión a un árbol de sintaxis (AST) y solo permitimos operaciones
matemáticas básicas: +, -, *, /, **, %, paréntesis y sqrt().
"""

from __future__ import annotations

import ast
import math
import operator as op


class CalculatorError(Exception):
    pass


# Operadores binarios permitidos
_BIN_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.FloorDiv: op.floordiv,
}

# Operadores unarios permitidos (ej. -5)
_UNARY_OPS = {
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

# Funciones permitidas
_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise CalculatorError("Solo se permiten números.")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise CalculatorError("Operación no permitida.")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        try:
            return _BIN_OPS[op_type](left, right)
        except ZeroDivisionError:
            raise CalculatorError("No se puede dividir entre cero.")

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise CalculatorError("Operación no permitida.")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
            raise CalculatorError("Función no permitida.")
        args = [_eval_node(a) for a in node.args]
        return _FUNCTIONS[node.func.id](*args)

    raise CalculatorError("Expresión no válida.")


def evaluate_expression(expr: str) -> float:
    """
    Evalúa una expresión matemática de forma segura.
    Ej: '5 + 3', '(2+3)*4', 'sqrt(16)'
    """
    expr = expr.strip()
    if not expr:
        raise CalculatorError("La expresión está vacía.")

    # Normalizar símbolos comunes que pueden venir de voz/teclado
    expr = expr.replace("x", "*").replace("X", "*").replace(",", ".")
    expr = expr.replace("÷", "/").replace("^", "**")

    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval_node(tree.body if hasattr(tree, "body") else tree)
    except CalculatorError:
        raise
    except Exception:
        raise CalculatorError("No entendí la operación matemática.")

    if isinstance(result, float):
        # Redondear a un máximo de 4 decimales, sin colas raras de float
        result = round(result, 4)
        if result == int(result):
            result = int(result)

    return result
