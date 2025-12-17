import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn

from vcc_totem.core.query import query_with_fallback, query_fnb, query_gaso, validate_dni
from vcc_totem.core.messages import format_response
from vcc_totem.clients.gaso import check_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Calidda Credit API",
    version="3.0",
    description="API to query credit lines in Calidda systems"
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
    return {
        "status": "ok",
    }


@app.get("/health/gaso")
def health_gaso():
    connected = check_connection()
    return {
        "status": "ok" if connected else "error",
        "channel": "gaso",
        "connected": connected
    }


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
            error=result.error_message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
            error=result.error_message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
            error=result.error_message
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"GASO query failed for DNI {body.dni}")
        raise HTTPException(status_code=500, detail="Internal error")


if __name__ == "__main__":
    uvicorn.run("api_wrapper:app", host="0.0.0.0", port=5000, log_level="info")