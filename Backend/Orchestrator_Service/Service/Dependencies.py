from fastapi import Request
from Service.IOrchestrator_Service import IOrchestratorService

def get_orchestrator_service(request: Request) -> IOrchestratorService:
    return request.app.state.orchestrator_service