from fastapi import FastAPI, Header, HTTPException
import httpx
import os

app = FastAPI(title="MCP FHIR Writeback Adapter")

FHIR_BASE = os.getenv("FHIR_BASE", "http://hapi-fhir:8080/fhir")
FHIR_AUTH_HEADER = os.getenv("FHIR_AUTH_HEADER", "")  # e.g. "Bearer xxx" if you add auth


def _get_headers():
    headers = {"Content-Type": "application/fhir+json"}
    if FHIR_AUTH_HEADER:
        headers["Authorization"] = FHIR_AUTH_HEADER
    return headers


@app.post("/tools/resolve_patient_encounter")
async def resolve_patient_encounter(payload: dict, authorization: str | None = Header(default=None)):
    """
    Resolve or create a patient based on facility/device context.
    For demo purposes, creates a patient if it doesn't exist.
    """
    facility_id = payload.get("facility_id", "facility1")
    device_id = payload.get("device_id", "deviceX")

    # Use a deterministic patient ID based on device for demo
    patient_id = f"patient-{device_id}"

    async with httpx.AsyncClient(timeout=30) as client:
        # Check if patient exists
        r = await client.get(f"{FHIR_BASE}/Patient/{patient_id}", headers=_get_headers())

        if r.status_code == 404:
            # Create the patient
            patient_resource = {
                "resourceType": "Patient",
                "id": patient_id,
                "identifier": [
                    {
                        "system": f"urn:facility:{facility_id}",
                        "value": patient_id
                    }
                ],
                "name": [{"family": "Demo", "given": ["Patient"]}],
                "active": True
            }
            create_resp = await client.put(
                f"{FHIR_BASE}/Patient/{patient_id}",
                json=patient_resource,
                headers=_get_headers()
            )
            if create_resp.status_code >= 300:
                raise HTTPException(
                    status_code=502,
                    detail={"fhir_status": create_resp.status_code, "body": create_resp.text}
                )

    return {"patient_id": patient_id, "encounter_id": None}


@app.post("/tools/ensure_patient_exists")
async def ensure_patient_exists(payload: dict, authorization: str | None = Header(default=None)):
    """
    Ensure a patient exists in FHIR. Creates if not found.
    """
    patient_id = payload.get("patient_id", "demo-patient")

    async with httpx.AsyncClient(timeout=30) as client:
        # Check if patient exists
        r = await client.get(f"{FHIR_BASE}/Patient/{patient_id}", headers=_get_headers())

        if r.status_code == 404:
            # Create the patient
            patient_resource = {
                "resourceType": "Patient",
                "id": patient_id,
                "identifier": [
                    {
                        "system": "urn:demo:patient",
                        "value": patient_id
                    }
                ],
                "name": [{"family": "Demo", "given": ["Patient"]}],
                "active": True
            }
            create_resp = await client.put(
                f"{FHIR_BASE}/Patient/{patient_id}",
                json=patient_resource,
                headers=_get_headers()
            )
            if create_resp.status_code >= 300:
                raise HTTPException(
                    status_code=502,
                    detail={"fhir_status": create_resp.status_code, "body": create_resp.text}
                )
            return {"patient_id": patient_id, "created": True}

        return {"patient_id": patient_id, "created": False}


@app.post("/tools/write_fhir_observation")
async def write_fhir_observation(payload: dict, authorization: str | None = Header(default=None)):
    obs = payload.get("observation")
    if not isinstance(obs, dict) or obs.get("resourceType") != "Observation":
        raise HTTPException(status_code=400, detail="Invalid Observation payload")

    # Extract patient_id from the observation subject reference
    subject_ref = obs.get("subject", {}).get("reference", "")
    if subject_ref.startswith("Patient/"):
        patient_id = subject_ref.replace("Patient/", "")
        # Ensure patient exists before creating observation
        await ensure_patient_exists({"patient_id": patient_id})

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{FHIR_BASE}/Observation", json=obs, headers=_get_headers())
        if r.status_code >= 300:
            raise HTTPException(status_code=502, detail={"fhir_status": r.status_code, "body": r.text})

        body = r.json()
        obs_id = body.get("id")

    return {"status": "ok", "observation_id": obs_id, "warnings": []}
