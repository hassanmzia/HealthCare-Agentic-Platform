from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import httpx

from graph.graph import run_graph, analyze_vitals

app = FastAPI()

BACKEND_INTERNAL = "http://backend:8000"


class VitalsAnalysisRequest(BaseModel):
    patient_id: str
    readings: dict  # e.g., {"HR": 85, "SpO2": 97, "TempC": 37.2, "BP_SYS": 130, "BP_DIA": 85}


@app.post("/run")
async def run(data: dict):
    result = await run_graph(data["vitals_event_id"])
    return result


@app.post("/analyze-vitals")
async def analyze_vitals_endpoint(request: VitalsAnalysisRequest):
    """Analyze vitals directly and generate/persist recommendations."""
    # Analyze the vitals
    recommendation = analyze_vitals(request.readings)

    # Persist to backend
    recommendation_data = {
        "patient_id": request.patient_id,
        "severity": recommendation.get("severity", "info"),
        "title": recommendation.get("title", "Vitals Assessment"),
        "summary": recommendation.get("summary", ""),
        "actions": recommendation.get("actions", []),
        "rationale": recommendation.get("rationale", ""),
        "evidence": recommendation.get("evidence", []),
        "confidence": recommendation.get("confidence", 0.0),
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{BACKEND_INTERNAL}/api/v1/recommendations/",
                json=recommendation_data
            )
            r.raise_for_status()
            recommendation["persisted"] = r.json()
    except Exception as e:
        recommendation["persist_error"] = str(e)

    return recommendation


@app.get("/health")
async def health():
    return {"status": "healthy"}
