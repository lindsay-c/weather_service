#!/usr/bin/env python3
"""Fetch today's hourly weather from the Open-Meteo Forecast API."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen


OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_today_hourly_weather(latitude: float, longitude: float, timezone: str) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
            ]
        ),
        "forecast_days": 1,
        "timezone": timezone,
    }
    url = f"{OPEN_METEO_FORECAST_URL}?{urlencode(params)}"

    try:
        with urlopen(url, timeout=10) as response:
            return json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Open-Meteo API error: HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach Open-Meteo API: {exc.reason}") from exc


def print_hourly_table(data: dict) -> None:
    hourly = data.get("hourly", {})
    units = data.get("hourly_units", {})
    today = date.today().isoformat()

    rows = zip(
        hourly.get("time", []),
        hourly.get("temperature_2m", []),
        hourly.get("relative_humidity_2m", []),
        hourly.get("precipitation_probability", []),
        hourly.get("weather_code", []),
        hourly.get("wind_speed_10m", []),
    )

    print(f"Today's hourly weather ({today})")
    print("-" * 83)
    print(f"{'Time':<17} {'Temp':>8} {'Humidity':>10} {'Rain %':>8} {'Wind':>10}  Weather")
    print("-" * 83)

    for time, temp, humidity, rain_prob, code, wind_speed in rows:
        if not str(time).startswith(today):
            continue

        weather = WEATHER_CODES.get(code, f"Code {code}")
        print(
            f"{time:<17} "
            f"{temp:>7}{units.get('temperature_2m', ''):<1} "
            f"{humidity:>9}{units.get('relative_humidity_2m', ''):<1} "
            f"{rain_prob:>7}{units.get('precipitation_probability', ''):<1} "
            f"{wind_speed:>9}{units.get('wind_speed_10m', ''):<1}  "
            f"{weather}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Get today's weather at 1-hour intervals from Open-Meteo."
    )
    parser.add_argument("--latitude", type=float, default=37.5665, help="Latitude. Default: Seoul")
    parser.add_argument("--longitude", type=float, default=126.9780, help="Longitude. Default: Seoul")
    parser.add_argument(
        "--timezone",
        default="Asia/Seoul",
        help='Timezone name, such as "Asia/Seoul" or "America/New_York".',
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = fetch_today_hourly_weather(args.latitude, args.longitude, args.timezone)
        print_hourly_table(data)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
