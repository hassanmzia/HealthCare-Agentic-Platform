"""
IoT Simulator Service - Generates synthetic vitals for devices assigned to patients.
Provides REST API for control and status monitoring.
"""

import asyncio
import os
import logging
from datetime import datetime
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from vitals_generator import VitalsGenerator, get_patient_profile, reset_patient_profile, PatientProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IoT Simulator", description="Synthetic vitals generator for healthcare devices")

# Configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
MCP_ADAPTER_URL = os.getenv("MCP_ADAPTER_URL", "http://mcp-fhir-adapter:8002")
DEFAULT_INTERVAL = int(os.getenv("DEFAULT_INTERVAL", "30"))  # seconds

# Simulator state
class SimulatorState:
    def __init__(self):
        self.running = False
        self.interval = DEFAULT_INTERVAL
        self.last_run: Optional[datetime] = None
        self.devices_count = 0
        self.observations_sent = 0
        self.errors_count = 0
        self.task: Optional[asyncio.Task] = None
        self.generators: dict[str, VitalsGenerator] = {}

state = SimulatorState()


# Pydantic models for API
class SimulatorConfig(BaseModel):
    interval: int = 30
    enabled: bool = True


class PatientCondition(BaseModel):
    patient_id: str
    condition: str  # normal, hypertensive, hypotensive, fever, tachycardic, bradycardic, hypoxic


class SimulatorStatus(BaseModel):
    running: bool
    interval: int
    last_run: Optional[str]
    devices_count: int
    observations_sent: int
    errors_count: int
    uptime_seconds: Optional[float] = None


async def fetch_assigned_devices() -> list[dict]:
    """Fetch all devices that are assigned to patients from backend."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Fetch devices that are assigned (have active assignments)
            resp = await client.get(f"{BACKEND_URL}/api/v1/devices/", params={
                "assigned": "true",
                "status": "active",
                "limit": 500
            })
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", [])
            else:
                logger.error(f"Failed to fetch devices: {resp.status_code} - {resp.text}")
                return []
    except Exception as e:
        logger.error(f"Error fetching devices: {e}")
        return []


async def send_observation_to_fhir(observation: dict) -> bool:
    """Send a single observation to FHIR via MCP adapter."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MCP_ADAPTER_URL}/tools/write_fhir_observation",
                json={"observation": observation}
            )
            if resp.status_code == 200:
                return True
            else:
                logger.error(f"Failed to write observation: {resp.status_code} - {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending observation: {e}")
        return False


async def generate_and_send_vitals():
    """Main loop to generate and send vitals for all assigned devices."""
    logger.info("Starting vitals generation cycle")

    devices = await fetch_assigned_devices()
    state.devices_count = len(devices)

    if not devices:
        logger.info("No assigned devices found")
        return

    logger.info(f"Generating vitals for {len(devices)} devices")

    for device in devices:
        device_id = device.get("device_id", "")
        patient_id = device.get("assigned_patient_id")
        patient_fhir_id = device.get("current_assignment", {}).get("patient_fhir_id") or f"patient-{patient_id}"
        capabilities = device.get("capabilities", [])

        if not patient_id:
            continue

        # Get or create generator for this patient
        if patient_fhir_id not in state.generators:
            profile = get_patient_profile(patient_fhir_id)
            state.generators[patient_fhir_id] = VitalsGenerator(profile)

        generator = state.generators[patient_fhir_id]

        # Generate vitals
        vitals = generator.generate_vitals(capabilities)

        # Convert to FHIR observations
        observations = generator.create_fhir_observations(vitals, patient_fhir_id, device_id)

        # Send each observation
        for obs in observations:
            success = await send_observation_to_fhir(obs)
            if success:
                state.observations_sent += 1
            else:
                state.errors_count += 1

        logger.info(f"Generated {len(observations)} observations for device {device_id} -> patient {patient_fhir_id}")

    state.last_run = datetime.utcnow()


async def simulator_loop():
    """Background task that runs the simulator at configured intervals."""
    logger.info(f"Simulator loop started with interval {state.interval}s")

    while state.running:
        try:
            await generate_and_send_vitals()
        except Exception as e:
            logger.error(f"Error in simulator loop: {e}")
            state.errors_count += 1

        await asyncio.sleep(state.interval)

    logger.info("Simulator loop stopped")


# API Endpoints
@app.get("/")
async def root():
    return {"service": "IoT Simulator", "status": "running" if state.running else "stopped"}


@app.get("/status", response_model=SimulatorStatus)
async def get_status():
    """Get current simulator status."""
    return SimulatorStatus(
        running=state.running,
        interval=state.interval,
        last_run=state.last_run.isoformat() if state.last_run else None,
        devices_count=state.devices_count,
        observations_sent=state.observations_sent,
        errors_count=state.errors_count
    )


@app.post("/start")
async def start_simulator(config: Optional[SimulatorConfig] = None):
    """Start the simulator."""
    if state.running:
        return {"status": "already_running", "interval": state.interval}

    if config:
        state.interval = config.interval

    state.running = True
    state.task = asyncio.create_task(simulator_loop())

    return {"status": "started", "interval": state.interval}


@app.post("/stop")
async def stop_simulator():
    """Stop the simulator."""
    if not state.running:
        return {"status": "already_stopped"}

    state.running = False
    if state.task:
        state.task.cancel()
        try:
            await state.task
        except asyncio.CancelledError:
            pass
        state.task = None

    return {"status": "stopped"}


@app.post("/configure")
async def configure_simulator(config: SimulatorConfig):
    """Update simulator configuration."""
    state.interval = config.interval

    if config.enabled and not state.running:
        state.running = True
        state.task = asyncio.create_task(simulator_loop())
    elif not config.enabled and state.running:
        state.running = False
        if state.task:
            state.task.cancel()

    return {"status": "configured", "interval": state.interval, "running": state.running}


@app.post("/trigger")
async def trigger_once():
    """Manually trigger one vitals generation cycle."""
    await generate_and_send_vitals()
    return {
        "status": "triggered",
        "devices_count": state.devices_count,
        "observations_sent": state.observations_sent
    }


@app.post("/patient-condition")
async def set_patient_condition(data: PatientCondition):
    """Set a patient's condition for realistic vital generation."""
    valid_conditions = ["normal", "hypertensive", "hypotensive", "fever",
                        "tachycardic", "bradycardic", "hypoxic"]

    if data.condition not in valid_conditions:
        raise HTTPException(status_code=400, detail=f"Invalid condition. Must be one of: {valid_conditions}")

    reset_patient_profile(data.patient_id, data.condition)

    # Reset the generator for this patient
    if data.patient_id in state.generators:
        del state.generators[data.patient_id]

    return {"status": "updated", "patient_id": data.patient_id, "condition": data.condition}


@app.get("/patient-profiles")
async def get_patient_profiles():
    """Get all current patient profiles."""
    from vitals_generator import _patient_profiles
    return {
        pid: {"age": p.age, "condition": p.condition}
        for pid, p in _patient_profiles.items()
    }


@app.post("/reset-stats")
async def reset_stats():
    """Reset observation and error counters."""
    state.observations_sent = 0
    state.errors_count = 0
    return {"status": "reset"}


@app.get("/devices")
async def get_assigned_devices():
    """Get list of currently assigned devices."""
    devices = await fetch_assigned_devices()
    return {
        "count": len(devices),
        "devices": [
            {
                "device_id": d.get("device_id"),
                "name": d.get("name"),
                "patient_id": d.get("assigned_patient_id"),
                "patient_name": d.get("assigned_patient_name"),
                "capabilities": d.get("capabilities", [])
            }
            for d in devices
        ]
    }


# Auto-start on startup if configured
@app.on_event("startup")
async def startup_event():
    auto_start = os.getenv("AUTO_START", "false").lower() == "true"
    if auto_start:
        state.running = True
        state.task = asyncio.create_task(simulator_loop())
        logger.info("Simulator auto-started on startup")
