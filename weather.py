# -*- coding: utf-8 -*-
"""
weather.py — Módulo de clima de Baro.

Usa Open-Meteo (https://open-meteo.com), una API pública y completamente
gratuita que NO requiere API key. Hace dos llamadas:
  1. Geocoding: convierte el nombre de la ciudad en coordenadas (lat/lon).
  2. Forecast: obtiene el clima actual para esas coordenadas.
"""

from __future__ import annotations

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Códigos WMO de clima -> descripción en español
WEATHER_CODES = {
    0: "cielo despejado",
    1: "mayormente despejado",
    2: "parcialmente nublado",
    3: "nublado",
    45: "niebla",
    48: "niebla con escarcha",
    51: "llovizna ligera",
    53: "llovizna moderada",
    55: "llovizna intensa",
    56: "llovizna helada ligera",
    57: "llovizna helada intensa",
    61: "lluvia ligera",
    63: "lluvia moderada",
    65: "lluvia intensa",
    66: "lluvia helada ligera",
    67: "lluvia helada intensa",
    71: "nevada ligera",
    73: "nevada moderada",
    75: "nevada intensa",
    77: "granizo pequeño",
    80: "lluvias ligeras aisladas",
    81: "lluvias moderadas aisladas",
    82: "lluvias intensas aisladas",
    85: "nevadas aisladas ligeras",
    86: "nevadas aisladas intensas",
    95: "tormenta eléctrica",
    96: "tormenta con granizo ligero",
    99: "tormenta con granizo intenso",
}


class WeatherError(Exception):
    pass


async def _geocode(city: str) -> dict:
    params = {"name": city, "count": 1, "language": "es", "format": "json"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(GEOCODE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = data.get("results")
    if not results:
        raise WeatherError("Intenta con el nombre de una ciudad o país válido.")

    top = results[0]
    return {
        "name": top["name"],
        "country": top.get("country", ""),
        "latitude": top["latitude"],
        "longitude": top["longitude"],
    }


async def get_weather(city: str) -> dict:
    """
    Devuelve un diccionario con el clima actual de `city`.
    Lanza WeatherError si la ciudad no existe o falla la consulta.
    """
    location = await _geocode(city)

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(FORECAST_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    current = data.get("current")
    if not current:
        raise WeatherError("No se pudo obtener el pronóstico en este momento.")

    code = current.get("weather_code", 0)
    description = WEATHER_CODES.get(code, "condiciones variables")

    display_city = location["name"]
    if location["country"]:
        display_city = f"{location['name']}, {location['country']}"

    return {
        "city": display_city,
        "temperature": round(current["temperature_2m"]),
        "feels_like": round(current["apparent_temperature"]),
        "humidity": round(current["relative_humidity_2m"]),
        "wind_speed": round(current["wind_speed_10m"]),
        "description": description,
        "code": code,
    }
