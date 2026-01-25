from pydantic import BaseModel
from typing import Dict

class GraphState(BaseModel):
    vitals_event_id: int
    patient_id: str | None = None
    recommendation: Dict | None = None
