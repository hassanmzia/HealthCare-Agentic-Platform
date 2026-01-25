from fastapi import FastAPI
from graph.graph import run_graph

app = FastAPI()

@app.post("/run")
async def run(data: dict):
    result = await run_graph(data["vitals_event_id"])
    return result
