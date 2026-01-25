from .state import GraphState
from langgraph.graph import StateGraph, END
from tools.mcp_client import MCPClient

mcp = MCPClient("http://mcp-server:8002", "dev-key")

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

async def run_graph(vitals_event_id):
    return await app_graph.ainvoke(GraphState(vitals_event_id=vitals_event_id))
