from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from Repository.Orchestrator_Repository import OrchestratorRepository
from Service.Orchestrator_Service import OrchestratorService
from Controller import Orchestrator_Controller as orchestrator_controller

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.orchestrator_service = OrchestratorService(
        repository=OrchestratorRepository(
            base_url=settings.document_service_url
        ),
    )
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(orchestrator_controller.router)