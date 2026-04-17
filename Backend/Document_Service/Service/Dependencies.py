from Service.IDocument_Service import IDocumentService
from fastapi import Request

def get_document_service(request: Request) -> IDocumentService:
    return request.app.state.document_service