import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from vcc_totem.core.query import (
    query_with_fallback,
    query_fnb,
    query_gaso,
    validate_dni,
)
from vcc_totem.core.messages import format_response
from vcc_totem.clients.gaso import check_connection
from vcc_totem.clients.session import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Cálidda",
    version="3.0",
    description="API de consulta de líneas de crédito Cálidda",
)


class DNIRequest(BaseModel):
    dni: str = Field(pattern=r"^\d{8}$", examples=["12345678"])


class QueryResponse(BaseModel):
    success: bool
    dni: str
    channel: str
    client_message: str
    has_offer: bool
    data: dict | None = None
    error: str | None = None


@app.get("/health")
def health():
    fnb_ok = False
    gaso_ok = False

    try:
        get_session()
        fnb_ok = True
    except Exception as e:
        logger.error(f"FNB health check failed: {e}")

    try:
        gaso_ok = check_connection()
    except Exception as e:
        logger.error(f"GASO health check failed: {e}")

    all_ok = fnb_ok and gaso_ok
    status_code = 200 if all_ok else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if all_ok else "degraded",
            "fnb": "ok" if fnb_ok else "error",
            "gaso": "ok" if gaso_ok else "error",
        },
    )


@app.post("/query", response_model=QueryResponse)
def query_endpoint(body: DNIRequest):
    try:
        dni = validate_dni(body.dni)
        result = query_with_fallback(dni)
        message, has_offer = format_response(result)

        return QueryResponse(
            success=result.success,
            dni=result.dni,
            channel=result.channel,
            client_message=message,
            has_offer=has_offer,
            data=result.data,
            error=result.error_message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception(f"Query failed for DNI {body.dni}")
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/query/fnb", response_model=QueryResponse)
def query_fnb_endpoint(body: DNIRequest):
    try:
        dni = validate_dni(body.dni)
        result = query_fnb(dni)
        message, has_offer = format_response(result)

        return QueryResponse(
            success=result.success,
            dni=result.dni,
            channel="fnb",
            client_message=message,
            has_offer=has_offer,
            data=result.data,
            error=result.error_message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception(f"FNB query failed for DNI {body.dni}")
        raise HTTPException(status_code=500, detail="Internal error")


@app.post("/query/gaso", response_model=QueryResponse)
def query_gaso_endpoint(body: DNIRequest):
    try:
        dni = validate_dni(body.dni)
        result = query_gaso(dni)
        message, has_offer = format_response(result)

        return QueryResponse(
            success=result.success,
            dni=result.dni,
            channel="gaso",
            client_message=message,
            has_offer=has_offer,
            data=result.data,
            error=result.error_message,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception(f"GASO query failed for DNI {body.dni}")
        raise HTTPException(status_code=500, detail="Internal error")


if __name__ == "__main__":
    uvicorn.run("api_wrapper:app", host="0.0.0.0", port=5000, log_level="info")
