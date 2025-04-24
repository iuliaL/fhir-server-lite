from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db import engine
from app.models.base import Base
from app.routes import patients_router, observations_router

# Only create tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FHIR-lite Server",
    description="A lightweight FHIR server implementation focusing on Patient and Observation resources",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FHIR Content-Type middleware
@app.middleware("http")
async def add_fhir_content_type(request: Request, call_next):
    response = await call_next(request)
    if isinstance(response, JSONResponse):
        response.headers["Content-Type"] = "application/fhir+json"
    return response

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Convert HTTP exceptions to FHIR OperationOutcome format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "error",
                    "code": "processing",
                    "diagnostics": str(exc.detail)
                }
            ]
        }
    )

@app.get("/", include_in_schema=False)
def read_root():
    """Redirect to API documentation"""
    return Response(
        status_code=302,
        headers={"Location": "/docs"}
    )

@app.get("/metadata")
def capability_statement():
    """Return FHIR CapabilityStatement"""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2023-11-21",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{
            "mode": "server",
            "resource": [
                {
                    "type": "Patient",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"},
                        {"name": "gender", "type": "token"},
                        {"name": "birthdate", "type": "date"}
                    ]
                },
                {
                    "type": "Observation",
                    "interaction": [
                        {"code": "read"},
                        {"code": "create"},
                        {"code": "update"},
                        {"code": "delete"},
                        {"code": "search-type"}
                    ],
                    "searchParam": [
                        {"name": "patient", "type": "reference"},
                        {"name": "category", "type": "token"},
                        {"name": "code", "type": "token"},
                        {"name": "date", "type": "date"}
                    ]
                }
            ]
        }]
    }

# Include FHIR routers
app.include_router(patients_router, prefix="/Patient", tags=["Patient"])
app.include_router(observations_router, prefix="/Observation", tags=["Observation"])