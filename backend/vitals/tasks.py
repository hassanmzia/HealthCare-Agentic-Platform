from celery import shared_task
import requests

@shared_task
def run_orchestration(vitals_event_id):
    requests.post(
        "http://orchestrator:8003/run",
        json={"vitals_event_id": vitals_event_id}
    )
