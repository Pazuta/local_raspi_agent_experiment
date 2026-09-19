import logging
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)
app = FastAPI(title="Local Chatbot API", docs_url="/api/docs")
templates = Jinja2Templates(directory="templates")

OLLAMA_URL = os.getenv("OLLAMA_URL", "").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


def configuration_error() -> str | None:
    if not OLLAMA_URL or not OLLAMA_MODEL:
        return "The Ollama configuration is incomplete."
    return None


def generate_reply(prompt: str) -> str:
    error = configuration_error()
    if error:
        raise RuntimeError(error)

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("response", "")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
def health():
    if error := configuration_error():
        return JSONResponse({"status": "misconfigured", "error": error}, status_code=503)

    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
    except requests.RequestException:
        logger.exception("Ollama health check failed")
        return JSONResponse({"status": "unavailable"}, status_code=503)

    return {"status": "ok"}


@app.post("/api/chat")
def chat(payload: ChatRequest):
    prompt = payload.message.strip()
    if not prompt:
        return JSONResponse({"error": "message is required"}, status_code=400)

    try:
        reply = generate_reply(prompt)
    except RuntimeError as error:
        return JSONResponse({"error": str(error)}, status_code=503)
    except requests.RequestException:
        logger.exception("Ollama request failed")
        return JSONResponse({"error": "The language model is unavailable."}, status_code=503)
    except (TypeError, ValueError):
        logger.exception("Invalid Ollama response")
        return JSONResponse({"error": "The language model returned an invalid response."}, status_code=502)

    return {"reply": reply}
