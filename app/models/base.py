from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class FHIRBaseModel(Base):
    __abstract__ = True
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resourceType = Column(String, nullable=False)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_fhir(self):
        """Convert to FHIR resource format"""
        raise NotImplementedError("Subclasses must implement to_fhir()")

    def from_fhir(self, fhir_dict):
        """Update from FHIR resource format"""
        raise NotImplementedError("Subclasses must implement from_fhir()")

    def __init__(self, *args, **kwargs):
        if 'resourceType' not in kwargs:
            kwargs['resourceType'] = self.__class__.__name__
        super().__init__(*args, **kwargs)
