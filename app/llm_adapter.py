import os
from typing import Any

import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")


def ollama_health() -> dict[str, str | bool]:
    base_url = OLLAMA_URL.replace("/api/generate", "")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=4)
        response.raise_for_status()
        models = [item.get("name", "") for item in response.json().get("models", [])]
        if OLLAMA_MODEL in models:
            message = f"Ollama ist erreichbar. Modell {OLLAMA_MODEL} ist verfügbar."
            ok = True
        else:
            message = (
                f"Ollama ist erreichbar, aber das Modell {OLLAMA_MODEL} wurde nicht gefunden. "
                f"Installierte Modelle: {', '.join(models) if models else 'keine Modelle gefunden'}."
            )
            ok = False
        return {"ok": ok, "model": OLLAMA_MODEL, "url": OLLAMA_URL, "message": message}
    except requests.RequestException as error:
        return {
            "ok": False,
            "model": OLLAMA_MODEL,
            "url": OLLAMA_URL,
            "message": f"Ollama ist nicht erreichbar. Starte Ollama und prüfe {OLLAMA_URL}. Details: {error}",
        }


def generate_text(prompt: str, *, fallback: str = "") -> str:
    payload: dict[str, Any] = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.25},
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=240)
        response.raise_for_status()
        data = response.json()
        text = data.get("response", "").strip()
        return text or fallback or "Das Modell hat eine leere Antwort zurückgegeben."
    except requests.exceptions.ConnectionError:
        return fallback or (
            "Fehler: Keine Verbindung zu Ollama. Starte Ollama und prüfe, ob qwen3-coder:30b installiert ist."
        )
    except requests.exceptions.Timeout:
        return fallback or "Fehler: Das lokale Modell antwortet zu langsam. Für die Demo kann das Demo-Projekt verwendet werden."
    except requests.exceptions.HTTPError as error:
        return fallback or f"Fehler: Ollama konnte die Anfrage nicht verarbeiten. Ist {OLLAMA_MODEL} installiert? Details: {error}"
    except requests.exceptions.RequestException as error:
        return fallback or f"Fehler bei der Anfrage an das lokale Modell: {error}"
