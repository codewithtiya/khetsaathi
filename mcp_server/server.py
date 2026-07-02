"""
KhetSaathi MCP Server
======================
A Model Context Protocol (MCP) server that exposes three tools an
agriculture agent needs:

  1. get_weather_forecast  -> live weather via Open-Meteo (free, no API key)
  2. get_mandi_price       -> local mandi (market) prices for a crop
  3. diagnose_crop_disease -> looks up likely disease from symptom text

Built with FastMCP (the reference implementation of the MCP Python SDK).
Run standalone for testing:

    uv run mcp_server/server.py
    # or
    python mcp_server/server.py

The ADK agents in `khetsaathi_agents/` connect to this server over stdio
using MCPToolset, so this process is normally spawned automatically by ADK
and you do not need to start it by hand.
"""

import json
import os
from difflib import SequenceMatcher

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

with open(os.path.join(DATA_DIR, "crop_disease_db.json"), encoding="utf-8") as f:
    DISEASE_DB = json.load(f)

with open(os.path.join(DATA_DIR, "mandi_prices.json"), encoding="utf-8") as f:
    MANDI_DB = json.load(f)

# City -> lat/lon lookup for the weather tool (extend as needed)
CITY_COORDS = {
    "agra": (27.1767, 78.0081),
    "kanpur": (26.4499, 80.3319),
    "lucknow": (26.8467, 80.9462),
    "nagpur": (21.1458, 79.0882),
    "delhi": (28.6139, 77.2090),
    "jaipur": (26.9124, 75.7873),
}

mcp = FastMCP("khetsaathi-mcp-server")


# ---------------------------------------------------------------------------
# Tool 1: Weather
# ---------------------------------------------------------------------------
@mcp.tool()
def get_weather_forecast(location: str) -> str:
    """Get a 3-day weather forecast for a farming location in India.

    Args:
        location: City/town name, e.g. "Agra", "Kanpur", "Lucknow".

    Returns:
        JSON string with daily max/min temperature, rain chance, and
        a simple irrigation recommendation based on expected rainfall.
    """
    key = location.strip().lower()
    if key not in CITY_COORDS:
        return json.dumps({
            "error": f"Location '{location}' not in coverage list.",
            "supported_locations": list(CITY_COORDS.keys()),
        })

    lat, lon = CITY_COORDS[key]
    try:
        resp = httpx.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "timezone": "Asia/Kolkata",
                "forecast_days": 3,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["daily"]
    except Exception as e:
        return json.dumps({"error": f"Weather service unavailable: {e}"})

    days = []
    for i, date in enumerate(data["time"]):
        rain_chance = data["precipitation_probability_max"][i]
        days.append({
            "date": date,
            "max_temp_c": data["temperature_2m_max"][i],
            "min_temp_c": data["temperature_2m_min"][i],
            "rain_chance_percent": rain_chance,
            "irrigation_advice": (
                "Skip irrigation, rain expected." if rain_chance >= 60
                else "Light irrigation may be needed." if rain_chance >= 30
                else "Irrigate as per normal schedule, low rain chance."
            ),
        })

    return json.dumps({"location": location, "forecast": days}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool 2: Mandi (market) prices
# ---------------------------------------------------------------------------
@mcp.tool()
def get_mandi_price(crop: str, mandi_location: str) -> str:
    """Get today's mandi (agricultural market) price for a crop.

    Args:
        crop: Crop name, e.g. "wheat", "tomato", "cotton", "rice".
        mandi_location: Market/city name, e.g. "Agra".

    Returns:
        JSON string with min/max/modal price per quintal and price trend.
    """
    crop_key = crop.strip().lower()
    if crop_key not in MANDI_DB:
        return json.dumps({
            "error": f"No price data for crop '{crop}'.",
            "supported_crops": list(MANDI_DB.keys()),
        })

    city_data = MANDI_DB[crop_key]
    # case-insensitive match on mandi_location
    match = next((v for k, v in city_data.items() if k.lower() == mandi_location.strip().lower()), None)
    if match is None:
        return json.dumps({
            "error": f"No data for '{crop}' at mandi '{mandi_location}'.",
            "supported_mandis": list(city_data.keys()),
        })

    result = {"crop": crop, "mandi": mandi_location, **match}
    return json.dumps(result, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool 3: Crop disease diagnosis
# ---------------------------------------------------------------------------
def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


@mcp.tool()
def diagnose_crop_disease(crop: str, symptoms: str) -> str:
    """Diagnose a likely crop disease from a free-text symptom description.

    Args:
        crop: Crop name, e.g. "wheat", "tomato", "cotton", "rice".
        symptoms: Free text describing what the farmer observes, e.g.
            "yellow stripes on leaves and orange powder".

    Returns:
        JSON string with the best-matching disease, severity, and
        treatment advice in both English and Hindi.
    """
    crop_key = crop.strip().lower()
    if crop_key not in DISEASE_DB:
        return json.dumps({
            "error": f"No disease data for crop '{crop}'.",
            "supported_crops": list(DISEASE_DB.keys()),
        })

    symptoms_lower = symptoms.strip().lower()
    best_match, best_score = None, 0.0

    for entry in DISEASE_DB[crop_key]:
        for kw in entry["symptom_keywords"]:
            score = _similarity(kw, symptoms_lower)
            # boost score if keyword phrase literally appears in the input
            if kw in symptoms_lower:
                score = max(score, 0.9)
            if score > best_score:
                best_score, best_match = score, entry

    if best_match is None or best_score < 0.3:
        return json.dumps({
            "result": "no_confident_match",
            "message": "Could not confidently match symptoms to a known disease. Recommend consulting local Krishi Vigyan Kendra (KVK).",
        })

    return json.dumps({
        "crop": crop,
        "confidence": round(best_score, 2),
        "disease": best_match["disease"],
        "severity": best_match["severity"],
        "advice_en": best_match["advice"],
        "advice_hi": best_match["advice_hi"],
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run(transport="stdio")
