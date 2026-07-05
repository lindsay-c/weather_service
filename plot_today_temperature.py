#!/usr/bin/env python3
"""Plot today's hourly temperature from Open-Meteo and save it as an image."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from open_meteo_hourly_today import fetch_today_hourly_weather


def get_hourly_temperatures(data: dict) -> tuple[list[datetime], list[float], str]:
    hourly = data.get("hourly", {})
    units = data.get("hourly_units", {})
    times = hourly.get("time", [])
    temperatures = hourly.get("temperature_2m", [])

    if not times or not temperatures:
        raise RuntimeError("Open-Meteo response did not include hourly temperature data.")

    parsed_times = [datetime.fromisoformat(time) for time in times]
    temperature_unit = units.get("temperature_2m", "C")
    return parsed_times, temperatures, temperature_unit


def save_temperature_plot(
    times: list[datetime],
    temperatures: list[float],
    temperature_unit: str,
    output_path: str,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(times, temperatures, marker="o", linewidth=2.2, color="#2563eb")
    ax.fill_between(times, temperatures, min(temperatures), color="#bfdbfe", alpha=0.45)

    ax.set_title("Today's Hourly Temperature", fontsize=16, pad=14)
    ax.set_xlabel("Time")
    ax.set_ylabel(f"Temperature ({temperature_unit})")
    ax.grid(True, linestyle="--", alpha=0.35)

    ax.set_xticks(times[::2])
    ax.set_xticklabels([time.strftime("%H:%M") for time in times[::2]], rotation=45)

    min_temp = min(temperatures)
    max_temp = max(temperatures)
    min_time = times[temperatures.index(min_temp)].strftime("%H:%M")
    max_time = times[temperatures.index(max_temp)].strftime("%H:%M")

    ax.annotate(
        f"Min {min_temp}{temperature_unit}\n{min_time}",
        xy=(times[temperatures.index(min_temp)], min_temp),
        xytext=(0, -42),
        textcoords="offset points",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": "#475569"},
    )
    ax.annotate(
        f"Max {max_temp}{temperature_unit}\n{max_time}",
        xy=(times[temperatures.index(max_temp)], max_temp),
        xytext=(0, 34),
        textcoords="offset points",
        ha="center",
        arrowprops={"arrowstyle": "->", "color": "#475569"},
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save today's hourly temperature graph from Open-Meteo."
    )
    parser.add_argument("--latitude", type=float, default=37.5665, help="Latitude. Default: Seoul")
    parser.add_argument("--longitude", type=float, default=126.9780, help="Longitude. Default: Seoul")
    parser.add_argument("--timezone", default="Asia/Seoul", help="Timezone name. Default: Asia/Seoul")
    parser.add_argument("--output", default="today_temperature.png", help="Output image path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = fetch_today_hourly_weather(args.latitude, args.longitude, args.timezone)
        times, temperatures, temperature_unit = get_hourly_temperatures(data)
        save_temperature_plot(times, temperatures, temperature_unit, args.output)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(f"Saved graph to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
