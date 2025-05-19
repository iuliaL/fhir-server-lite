from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models.patient import Patient, ContactSystem, ContactUse
from app.utils.db import (
    safe_db_operation,
    safe_add,
    safe_commit,
    safe_refresh,
)
from pydantic import BaseModel, EmailStr, constr
from datetime import date
from enum import Enum
import uuid

router = APIRouter()


class TelecomSystem(str, Enum):
    phone = "phone"
    email = "email"
    fax = "fax"
    pager = "pager"
    url = "url"
    sms = "sms"
    other = "other"


class TelecomUse(str, Enum):
    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    mobile = "mobile"


class Telecom(BaseModel):
    system: TelecomSystem
    value: str
    use: Optional[TelecomUse] = None


class PatientBase(BaseModel):
    name: Optional[List[dict]] = None
    gender: Optional[str] = None
    birth_date: Optional[date] = None
    telecom: Optional[List[Telecom]] = None
    address: Optional[List[dict]] = None

    class Config:
        extra = "allow"


class PatientCreate(PatientBase):
    pass


class PatientResponse(PatientBase):
    id: str
    created: date
    updated: date

    class Config:
        from_attributes = True


@router.post("/", status_code=201)
def create_patient(
    fhir_resource: dict, response: Response, db: Session = Depends(get_db)
):
    """Create a new patient from FHIR resource"""
    try:
        # Validate that at least some identifying information is provided
        if not any(
            [
                fhir_resource.get("name"),
                fhir_resource.get("telecom"),
                fhir_resource.get("identifier"),
            ]
        ):
            raise ValueError(
                "Patient must have at least one form of identification (name, telecom, or identifier)"
            )

        # If only email is provided, ensure it's properly structured
        if (
            not fhir_resource.get("name")
            and fhir_resource.get("telecom")
            and all(t.get("system") == "email" for t in fhir_resource["telecom"])
        ):
            # Validate email format
            for telecom in fhir_resource["telecom"]:
                if not telecom.get("value"):
                    raise ValueError("Email contact point must have a value")
                # Basic email validation
                if "@" not in telecom["value"] or "." not in telecom["value"]:
                    raise ValueError(f"Invalid email format: {telecom['value']}")

        patient = Patient()
        patient.from_fhir(fhir_resource)
        print("→ About to add patient")
        safe_add(db, patient)
        print("✓ Patient added")

        print("→ About to commit")
        safe_commit(db)
        print("✓ Commit done")

        print("→ About to refresh")
        safe_refresh(db, patient)
        print("✓ Refresh done")

        # Set Location header
        response.headers["Location"] = f"/Patient/{patient.id}"
        return patient.to_fhir()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=dict)
def search_patients(
    email: Optional[str] = Query(None),
    family: Optional[str] = Query(None),
    given: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    birth_date: Optional[str] = Query(None),
    _count: Optional[int] = Query(10, alias="count"),
    _offset: Optional[int] = Query(0),
    db: Session = Depends(get_db),
):
    """Search for patients with FHIR search parameters"""
    query = db.query(Patient)

    if email:
        # Search in telecom array for email
        query = query.filter(
            Patient.telecom.contains([{"system": "email", "value": email}])
        )
    if family:
        query = query.filter(Patient.name.contains({"family": family}))
    if given:
        query = query.filter(Patient.name.contains({"given": [given]}))
    if gender:
        query = query.filter(Patient.gender == gender)
    if birth_date:
        query = query.filter(Patient.birth_date == birth_date)

    total = query.count()
    patients = query.offset(_offset).limit(_count).all()

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": [
            {"resource": patient.to_fhir(), "fullUrl": f"/Patient/{patient.id}"}
            for patient in patients
        ],
    }


@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    """Get a specific patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient.to_fhir()


@router.put("/{patient_id}")
def update_patient(patient_id: str, fhir_resource: dict, db: Session = Depends(get_db)):
    """Update a patient from FHIR resource"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        patient.from_fhir(fhir_resource)
        safe_db_operation(db, operation="commit")
        safe_db_operation(db, patient, "refresh")
        return patient.to_fhir()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    """Delete a patient and all related resources"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        # Return 204 even if not found, as per FHIR spec
        return Response(status_code=204)

    safe_db_operation(db, patient, "delete")
    safe_db_operation(db, operation="commit")
    return Response(status_code=204)
