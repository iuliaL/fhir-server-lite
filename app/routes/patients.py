from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models.patient import Patient
from pydantic import BaseModel
from datetime import date
import uuid

router = APIRouter()

class PatientBase(BaseModel):
    family: str
    given: str
    gender: str
    birth_date: date
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None
    postal_code: str | None = None

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: str
    created: date
    updated: date

    class Config:
        from_attributes = True

@router.post("/", status_code=201)
def create_patient(fhir_resource: dict, response: Response, db: Session = Depends(get_db)):
    """Create a new patient from FHIR resource"""
    try:
        patient = Patient()
        patient.from_fhir(fhir_resource)
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
        # Set Location header
        response.headers["Location"] = f"/Patient/{patient.id}"
        return patient.to_fhir()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=dict)
def search_patients(
    family: Optional[str] = Query(None),
    given: Optional[str] = Query(None),
    gender: Optional[str] = Query(None),
    birth_date: Optional[str] = Query(None),
    _count: Optional[int] = Query(10, alias="count"),
    _offset: Optional[int] = Query(0),
    db: Session = Depends(get_db)
):
    """Search for patients with FHIR search parameters"""
    query = db.query(Patient)
    
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
            {
                "resource": patient.to_fhir(),
                "fullUrl": f"/Patient/{patient.id}"
            }
            for patient in patients
        ]
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
        db.commit()
        db.refresh(patient)
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
    
    db.delete(patient)  # This will cascade delete observations
    db.commit()
    return Response(status_code=204) 