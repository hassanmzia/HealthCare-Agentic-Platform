from .state import GraphState
from langgraph.graph import StateGraph, END
from tools.mcp_client import MCPClient

#mcp = MCPClient("http://mcp-server:8002", "dev-key")
mcp = MCPClient("http://mcp-fhir-adapter:8002", "dev-key")


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
        "summary": "Vitals stable",
        "actions": [{"type": "monitor"}],
        "rationale": ["No abnormalities"],
        "confidence": 0.8
    }
    return state

graph = StateGraph(GraphState)
graph.add_node("identity", identity_node)
graph.add_node("manager", manager_node)
graph.add_edge("identity", "manager")
graph.add_edge("manager", END)

app_graph = graph.compile()

#async def run_graph(vitals_event_id):
#    return await app_graph.ainvoke(GraphState(vitals_event_id=vitals_event_id))


import httpx

BACKEND_INTERNAL = "http://backend:8000"

async def run_graph(vitals_event_id):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(f"{BACKEND_INTERNAL}/api/v1/vitals/internal/events/{vitals_event_id}")
        r.raise_for_status()
        event = r.json()

    # You’ll adapt this to your device payload shape.
    # Expected minimal format example:
    # {"device_id":"abc", "effective_time":"...Z", "readings":{"HR":72,"RR":14,"SpO2":98,"TempC":36.7,"WeightKg":82.5,"BP_SYS":120,"BP_DIA":78}}
    state = GraphState(vitals_event_id=vitals_event_id)
    state.device_id = event.get("device_id", "unknown")
    state.effective_time = event.get("effective_time")
    state.readings = event.get("readings", {})
    return await app_graph.ainvoke(state)



from fhir.mappers import obs_hr, obs_rr, obs_spo2, obs_temp, obs_weight, obs_bp_panel

async def writeback_node(state: GraphState):
    # Demo: build a minimal set (replace with actual vitals from backend DB next)
    patient_id = state.patient_id
    encounter_id = None
    device_id = "deviceX"
    t = "2026-01-01T00:00:00Z"

    payloads = [
        obs_hr(patient_id, encounter_id, t, device_id, 72),
        obs_rr(patient_id, encounter_id, t, device_id, 14),
        obs_spo2(patient_id, encounter_id, t, device_id, 98),
        obs_temp(patient_id, encounter_id, t, device_id, 36.7),
        obs_weight(patient_id, encounter_id, t, device_id, 82.5),
        obs_bp_panel(patient_id, encounter_id, t, device_id, 120, 78),
    ]

    created = []
    for o in payloads:
        res = await mcp.call("write_fhir_observation", {"observation": o})
        created.append(res)

    # attach created IDs into recommendation object if you want
    state.recommendation = state.recommendation or {}
    state.recommendation["fhir_writeback"] = created
    return state

graph.add_node("writeback", writeback_node)
graph.add_edge("policy", "writeback")   # temporary: always writeback after policy
graph.add_edge("writeback", END)

