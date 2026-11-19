import logging

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import config
from .routers import modulos, relatos, rpa, saude

logging.getLogger("citizentech").setLevel(logging.INFO)

app = FastAPI(title="CitizenTech API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,   # lista explícita, sem "*"
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)
for r in (saude.router, relatos.router, rpa.router, modulos.router):
    app.include_router(r)


@app.exception_handler(RequestValidationError)
async def validar_requisicao(request: Request, exc: RequestValidationError):
    if request.url.path == "/modulos/assistente/perguntar":
        return JSONResponse(status_code=422, content={"detail": "A pergunta deve ter de 3 a 500 caracteres e o histórico até 8 turnos."})
    return await request_validation_exception_handler(request, exc)
