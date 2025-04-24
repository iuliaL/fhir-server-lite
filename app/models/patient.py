from sqlalchemy import Column, String, Date, Enum, JSON
from sqlalchemy.orm import relationship
from .base import FHIRBaseModel
import enum

class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"

class Patient(FHIRBaseModel):
    __tablename__ = "patients"

    # Basic attributes
    active = Column(String(5), default="true")  # FHIR boolean as string
    gender = Column(Enum(Gender))
    birth_date = Column(Date)
    
    # Name components stored as JSON
    name = Column(JSON, nullable=False)  # [{use, family, given[], prefix[], suffix[]}]
    
    # Contact information
    telecom = Column(JSON)  # [{system, value, use}]
    address = Column(JSON)  # [{use, type, text, line[], city, state, postalCode, country}]
    
    # Relationships
    observations = relationship("Observation", back_populates="patient", cascade="all, delete-orphan")

    def to_fhir(self):
        """Convert to FHIR resource format"""
        return {
            "resourceType": "Patient",
            "id": self.id,
            "active": self.active == "true",
            "name": self.name,
            "gender": self.gender,
            "birthDate": self.birth_date.isoformat() if self.birth_date else None,
            "telecom": self.telecom or [],
            "address": self.address or []
        }

    def from_fhir(self, fhir_dict):
        """Update from FHIR resource format"""
        if fhir_dict.get("resourceType") != "Patient":
            raise ValueError("Resource type must be Patient")
        
        # Handle name
        if "name" in fhir_dict:
            self.name = fhir_dict["name"]
        
        # Handle other attributes
        self.active = str(fhir_dict.get("active", True)).lower()
        self.gender = fhir_dict.get("gender")
        self.birth_date = fhir_dict.get("birthDate")
        self.telecom = fhir_dict.get("telecom")
        self.address = fhir_dict.get("address")
        
        return self 