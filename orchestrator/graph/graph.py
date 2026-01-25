from .state import GraphState
from langgraph.graph import StateGraph, END, START

from tools.mcp_client import MCPClient
from fhir.mappers import obs_hr, obs_rr, obs_spo2, obs_temp, obs_weight, obs_bp_panel
import httpx

mcp = MCPClient("http://mcp-fhir-adapter:8002", "dev-key")

BACKEND_INTERNAL = "http://backend:8000"


async def identity_node(state: GraphState):
    res = await mcp.call("resolve_patient_encounter", {
        "facility_id": "facility1",
        "device_id": "deviceX",
        "observed_at": "2026-01-01T00:00:00Z"
    })
    state.patient_id = res.get("patient_id", "demo-patient")
    return state


async def manager_node(state: GraphState):
    state.recommendation = {
        "severity": "low",
        "title": "Vitals Assessment",
        "summary": "Vitals stable",
        "actions": [{"type": "monitor"}],
        "rationale": "No abnormalities detected",
        "evidence": [],
        "confidence": 0.8
    }
    return state


async def writeback_node(state: GraphState):
    patient_id = state.patient_id
    encounter_id = None
    device_id = state.device_id or "deviceX"
    t = state.effective_time or "2026-01-01T00:00:00Z"

    readings = state.readings or {}
    payloads = [
        obs_hr(patient_id, encounter_id, t, device_id, readings.get("HR", 72)),
        obs_rr(patient_id, encounter_id, t, device_id, readings.get("RR", 14)),
        obs_spo2(patient_id, encounter_id, t, device_id, readings.get("SpO2", 98)),
        obs_temp(patient_id, encounter_id, t, device_id, readings.get("TempC", 36.7)),
        obs_weight(patient_id, encounter_id, t, device_id, readings.get("WeightKg", 82.5)),
        obs_bp_panel(patient_id, encounter_id, t, device_id, readings.get("BP_SYS", 120), readings.get("BP_DIA", 78)),
    ]

    created = []
    for o in payloads:
        res = await mcp.call("write_fhir_observation", {"observation": o})
        created.append(res)

    state.recommendation = state.recommendation or {}
    state.recommendation["fhir_writeback"] = created
    return state


async def persist_node(state: GraphState):
    """Persist the recommendation to the backend database."""
    if not state.recommendation:
        return state

    recommendation_data = {
        "patient_id": state.patient_id,
        "severity": state.recommendation.get("severity", "low"),
        "title": state.recommendation.get("title", "Vitals Assessment"),
        "summary": state.recommendation.get("summary", ""),
        "actions": state.recommendation.get("actions", []),
        "rationale": state.recommendation.get("rationale", ""),
        "evidence": state.recommendation.get("evidence", []),
        "confidence": state.recommendation.get("confidence", 0.0),
    }

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(
            f"{BACKEND_INTERNAL}/api/v1/recommendations/",
            json=recommendation_data
        )
        r.raise_for_status()
        state.recommendation["persisted"] = r.json()

    return state


# Build the graph
graph = StateGraph(GraphState)
graph.add_node("identity", identity_node)
graph.add_node("manager", manager_node)
graph.add_node("writeback", writeback_node)
graph.add_node("persist", persist_node)
graph.add_edge(START, "identity")
graph.add_edge("identity", "manager")
graph.add_edge("manager", "writeback")
graph.add_edge("writeback", "persist")
graph.add_edge("persist", END)

app_graph = graph.compile()


async def run_graph(vitals_event_id):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{BACKEND_INTERNAL}/api/v1/vitals/internal/events/{vitals_event_id}")
        r.raise_for_status()
        event = r.json()

    state = GraphState(vitals_event_id=vitals_event_id)
    state.device_id = event.get("device_id", "unknown")
    state.effective_time = event.get("effective_time")
    state.readings = event.get("readings", {})
    return await app_graph.ainvoke(state)
