from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mautrix_iot.db import models
from mautrix_iot.db.database import _initial_db_population, engine
from mautrix_iot.exceptions import MatrixError
from mautrix_iot.routers import api

models.Base.metadata.create_all(bind=engine)
_initial_db_population()

app = FastAPI()


@app.exception_handler(MatrixError)
async def matrix_exception_handler(request: Request, exc: MatrixError):
    return JSONResponse(
        status_code=exc.m_code.value,
        content={"errcode": exc.m_code.name, "error": exc.msg},
    )


app.include_router(api.router)
