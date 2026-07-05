# Open-Meteo Weather Search

Flask web app that searches a location, fetches today's hourly weather from Open-Meteo,
and renders a Matplotlib temperature graph in the browser.

## Run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
MPLCONFIGDIR=/private/tmp/mplconfig .venv/bin/python app.py
```

Open:

```text
http://127.0.0.1:5000/
```
