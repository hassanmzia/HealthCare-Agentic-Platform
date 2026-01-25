from fastapi import FastAPI, Header, HTTPException
import httpx
import os

app = FastAPI(title="MCP FHIR Writeback Adapter")

FHIR_BASE = os.getenv("FHIR_BASE", "http://hapi-fhir:8080/fhir")
FHIR_AUTH_HEADER = os.getenv("FHIR_AUTH_HEADER", "")  # e.g. "Bearer xxx" if you add auth

@app.post("/tools/write_fhir_observation")
async def write_fhir_observation(payload: dict, authorization: str | None = Header(default=None)):
    # Optional simple auth gate for MCP adapter
    # if authorization != f"Bearer {os.getenv('MCP_API_KEY','dev-key')}":
    #     raise HTTPException(status_code=401, detail="Unauthorized")

    obs = payload.get("observation")
    if not isinstance(obs, dict) or obs.get("resourceType") != "Observation":
        raise HTTPException(status_code=400, detail="Invalid Observation payload")

    headers = {"Content-Type": "application/fhir+json"}
    if FHIR_AUTH_HEADER:
        headers["Authorization"] = FHIR_AUTH_HEADER

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{FHIR_BASE}/Observation", json=obs, headers=headers)
        if r.status_code >= 300:
            raise HTTPException(status_code=502, detail={"fhir_status": r.status_code, "body": r.text})

        # HAPI typically returns the created resource body
        body = r.json()
        obs_id = body.get("id")

    return {"status": "ok", "observation_id": obs_id, "warnings": []}

