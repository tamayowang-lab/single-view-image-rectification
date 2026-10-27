"""Run from room-simulator: uvicorn analysis.server:app --host 127.0.0.1 --port 8000."""
import asyncio
from contextlib import asynccontextmanager
import io
import time

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from .models import VisionModels

models = None
inference_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(app):
    global models
    models = await run_in_threadpool(VisionModels)
    yield
    models = None


app = FastAPI(title="Headspace local photo analysis", lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"ready": models is not None, "device": "cpu", "metric_depth": False}


@app.post("/api/analyze")
async def analyze(image: UploadFile = File(...)):
    payload = await image.read(8 * 1024 * 1024 + 1)
    if len(payload) > 8 * 1024 * 1024:
        raise HTTPException(413, "Screenshot must be smaller than 8 MB")
    try:
        with Image.open(io.BytesIO(payload)) as source:
            if source.width * source.height > 4_000_000 or min(source.size) < 64:
                raise HTTPException(422, "Screenshot must be at least 64 pixels per side and at most 4 megapixels")
            picture = source.convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(422, "A valid screenshot image is required")
    if models is None:
        raise HTTPException(503, "Local models are not ready")
    # Keep one CPU inference active; reject extra callers instead of queuing stale frames.
    if inference_lock.locked():
        raise HTTPException(429, "Analysis is busy; try the latest view again shortly")
    async with inference_lock:
        start = time.monotonic()
        result = await run_in_threadpool(models.infer, picture)
        result["elapsed_seconds"] = round(time.monotonic() - start, 2)
        return result
