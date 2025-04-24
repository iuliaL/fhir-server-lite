from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from .base import FHIRBaseModel
import enum

class ObservationStatus(str, enum.Enum):
    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"

class Observation(FHIRBaseModel):
    __tablename__ = "observations"

    # Status
    status = Column(Enum(ObservationStatus), nullable=False)
    
    # Category and Code (stored as FHIR CodeableConcept)
    category = Column(JSON)  # [{coding: [{system, code, display}], text}]
    code = Column(JSON, nullable=False)  # {coding: [{system, code, display}], text}
    
    # Subject reference (Patient)
    subject_reference = Column(String, ForeignKey("patients.id"), nullable=False)
    
    # Timing
    effective_datetime = Column(DateTime)
    
    # Value[x] - focusing on Quantity for now
    value_quantity = Column(JSON)  # {value: float, unit: string, system: uri, code: string}
    
    # Reference Ranges
    reference_range = Column(JSON)  # [{low: {value, unit}, high: {value, unit}}]
    
    # Relationships
    patient = relationship("Patient", back_populates="observations")

    def to_fhir(self):
        """Convert to FHIR resource format"""
        resource = {
            "resourceType": "Observation",
            "id": self.id,
            "status": self.status,
            "category": self.category,
            "code": self.code,
            "subject": {
                "reference": f"Patient/{self.subject_reference}"
            }
        }
        
        if self.effective_datetime:
            resource["effectiveDateTime"] = self.effective_datetime.isoformat()
            
        if self.value_quantity:
            resource["valueQuantity"] = self.value_quantity
            
        if self.reference_range:
            resource["referenceRange"] = self.reference_range
            
        return resource

    def from_fhir(self, fhir_dict):
        """Update from FHIR resource format"""
        if fhir_dict.get("resourceType") != "Observation":
            raise ValueError("Resource type must be Observation")
            
        self.status = fhir_dict.get("status")
        self.category = fhir_dict.get("category")
        self.code = fhir_dict.get("code")
        
        # Extract patient ID from reference
        subject_ref = fhir_dict.get("subject", {}).get("reference", "")
        if subject_ref.startswith("Patient/"):
            self.subject_reference = subject_ref.split("Patient/")[1]
        
        # Handle effective[x]
        if "effectiveDateTime" in fhir_dict:
            self.effective_datetime = fhir_dict["effectiveDateTime"]
            
        # Handle value[x]
        if "valueQuantity" in fhir_dict:
            self.value_quantity = fhir_dict["valueQuantity"]
            
        # Handle reference range
        if "referenceRange" in fhir_dict:
            self.reference_range = fhir_dict["referenceRange"]
            
        return self 