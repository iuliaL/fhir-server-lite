from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models.observation import Observation
from app.utils.db import safe_db_operation, safe_add, safe_commit, safe_refresh
from datetime import datetime

router = APIRouter()


@router.post("/", status_code=201)
def create_observation(
    fhir_resource: dict, response: Response, db: Session = Depends(get_db)
):
    """Create a new observation from FHIR resource"""
    try:
        observation = Observation()
        observation.from_fhir(fhir_resource)
        print("→ About to add observation")
        safe_add(db, observation)
        print("✓ Observation added")

        print("→ About to commit")
        safe_commit(db)
        print("✓ Commit done")

        print("→ About to refresh")
        safe_refresh(db, observation)
        print("✓ Refresh done")

        # Set Location header
        response.headers["Location"] = f"/Observation/{observation.id}"
        return observation.to_fhir()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=dict)
def search_observations(
    patient: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    _count: Optional[int] = Query(10, alias="count"),
    _offset: Optional[int] = Query(0),
    db: Session = Depends(get_db),
):
    """Search for observations with FHIR search parameters"""
    query = db.query(Observation)

    if patient:
        if patient.startswith("Patient/"):
            patient = patient.split("Patient/")[1]
        query = query.filter(Observation.subject_reference == patient)

    if category:
        query = query.filter(
            Observation.category.contains([{"coding": [{"code": category}]}])
        )

    if code:
        query = query.filter(Observation.code.contains({"coding": [{"code": code}]}))

    if date:
        # Handle date equality for now (could be expanded to support ranges)
        query = query.filter(
            Observation.effective_datetime == datetime.fromisoformat(date)
        )

    total = query.count()
    observations = query.offset(_offset).limit(_count).all()

    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": [
            {"resource": obs.to_fhir(), "fullUrl": f"/Observation/{obs.id}"}
            for obs in observations
        ],
    }


@router.get("/{observation_id}")
def get_observation(observation_id: str, db: Session = Depends(get_db)):
    """Get a specific observation by ID"""
    observation = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")
    return observation.to_fhir()


@router.put("/{observation_id}")
def update_observation(
    observation_id: str, fhir_resource: dict, db: Session = Depends(get_db)
):
    """Update an observation from FHIR resource"""
    observation = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Observation not found")

    try:
        observation.from_fhir(fhir_resource)
        safe_db_operation(db, operation="commit")
        safe_db_operation(db, observation, "refresh")
        return observation.to_fhir()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{observation_id}", status_code=204)
def delete_observation(observation_id: str, db: Session = Depends(get_db)):
    """Delete an observation"""
    observation = db.query(Observation).filter(Observation.id == observation_id).first()
    if observation is None:
        # Return 204 even if not found, as per FHIR spec
        return Response(status_code=204)

    safe_db_operation(db, observation, "delete")
    safe_db_operation(db, operation="commit")
    return Response(status_code=204)
