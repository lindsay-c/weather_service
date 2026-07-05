#!/usr/bin/env python3
"""Weather search web page powered by Open-Meteo."""

from __future__ import annotations

import base64
import json
from datetime import datetime
from io import BytesIO
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template, request

from open_meteo_hourly_today import WEATHER_CODES, fetch_today_hourly_weather
from plot_today_temperature import get_hourly_temperatures


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
DEFAULT_LOCATION = "Seoul"

app = Flask(__name__)


def find_location(query: str) -> dict:
    params = {
        "name": query,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    url = f"{GEOCODING_URL}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=10) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Open-Meteo geocoding error: HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Open-Meteo geocoding API: {exc.reason}") from exc

    results = payload.get("results", [])
    if not results:
        raise RuntimeError(f'No location found for "{query}".')

    location = results[0]
    return {
        "name": location.get("name", query),
        "country": location.get("country", ""),
        "admin1": location.get("admin1", ""),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location.get("timezone", "auto"),
    }


def build_temperature_chart(times: list[datetime], temperatures: list[float], unit: str) -> str:
    fig, ax = plt.subplots(figsize=(11, 5.4))
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    ax.plot(times, temperatures, marker="o", linewidth=2.4, color="#2563eb")
    ax.fill_between(times, temperatures, min(temperatures), color="#bfdbfe", alpha=0.5)

    ax.set_title("Today's Hourly Temperature", fontsize=15, pad=12)
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Temperature ({unit})")
    ax.grid(True, linestyle="--", linewidth=0.8, alpha=0.35)
    ax.set_xticks(times[::2])
    ax.set_xticklabels([time.strftime("%H:%M") for time in times[::2]], rotation=45)

    min_temp = min(temperatures)
    max_temp = max(temperatures)
    ax.text(
        0.02,
        0.95,
        f"Low {min_temp}{unit}   High {max_temp}{unit}",
        transform=ax.transAxes,
        va="top",
        fontsize=11,
        color="#334155",
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "#f8fafc", "edgecolor": "#cbd5e1"},
    )

    fig.tight_layout()
    buffer = BytesIO()
    fig.savefig(buffer, format="png", dpi=150)
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("ascii")


def summarize_weather(data: dict, timezone: str) -> dict:
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    rain_probability = hourly.get("precipitation_probability", [])
    weather_codes = hourly.get("weather_code", [])
    wind_speed = hourly.get("wind_speed_10m", [])
    units = data.get("hourly_units", {})

    try:
        now = datetime.now(ZoneInfo(timezone)).replace(tzinfo=None)
    except ZoneInfoNotFoundError:
        now = datetime.now()
    parsed_times = [datetime.fromisoformat(value) for value in times]
    current_index = min(
        range(len(parsed_times)),
        key=lambda index: abs((parsed_times[index] - now).total_seconds()),
    )

    return {
        "temperature": temperatures[current_index],
        "temperature_unit": units.get("temperature_2m", "C"),
        "humidity": humidity[current_index],
        "humidity_unit": units.get("relative_humidity_2m", "%"),
        "rain_probability": rain_probability[current_index],
        "rain_unit": units.get("precipitation_probability", "%"),
        "wind_speed": wind_speed[current_index],
        "wind_unit": units.get("wind_speed_10m", "km/h"),
        "weather": WEATHER_CODES.get(weather_codes[current_index], f"Code {weather_codes[current_index]}"),
        "time": parsed_times[current_index].strftime("%H:%M"),
        "high": max(temperatures),
        "low": min(temperatures),
    }


def get_weather_view(location_query: str) -> dict:
    location = find_location(location_query)
    weather_data = fetch_today_hourly_weather(
        location["latitude"],
        location["longitude"],
        location["timezone"],
    )
    times, temperatures, unit = get_hourly_temperatures(weather_data)
    return {
        "location": location,
        "summary": summarize_weather(weather_data, location["timezone"]),
        "chart": build_temperature_chart(times, temperatures, unit),
    }


@app.route("/", methods=["GET", "POST"])
def index():
    query = request.form.get("location", DEFAULT_LOCATION).strip() or DEFAULT_LOCATION
    weather = None
    error = None

    if request.method == "POST" or request.args.get("demo") == "1":
        try:
            weather = get_weather_view(query)
        except RuntimeError as exc:
            error = str(exc)

    return render_template("index.html", query=query, weather=weather, error=error)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
