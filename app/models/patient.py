from sqlalchemy import Column, String, Date, Enum, JSON
from sqlalchemy.orm import relationship
from .base import FHIRBaseModel
import enum
from typing import List, Optional
import json


class Gender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class ContactSystem(str, enum.Enum):
    phone = "phone"
    email = "email"
    fax = "fax"
    pager = "pager"
    url = "url"
    sms = "sms"
    other = "other"


class ContactUse(str, enum.Enum):
    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    mobile = "mobile"


class Patient(FHIRBaseModel):
    __tablename__ = "patients"

    # Basic attributes
    active = Column(String(5), default="true")  # FHIR boolean as string
    gender = Column(Enum(Gender))
    birth_date = Column(Date)

    # Name components stored as JSON
    name = Column(JSON)  # [{use, family, given[], prefix[], suffix[]}]

    # Contact information
    telecom = Column(JSON)  # [{system, value, use}]
    address = Column(
        JSON
    )  # [{use, type, text, line[], city, state, postalCode, country}]

    # Relationships
    observations = relationship(
        "Observation", back_populates="patient", cascade="all, delete-orphan"
    )

    def add_email(self, email: str, use: Optional[str] = None):
        """Add an email contact point to the patient's telecom array"""
        if not self.telecom:
            self.telecom = []

        contact = {"system": "email", "value": email}
        if use and use in ContactUse.__members__:
            contact["use"] = use

        # Check if this email already exists
        existing = next(
            (
                t
                for t in self.telecom
                if t.get("system") == "email" and t.get("value") == email
            ),
            None,
        )
        if not existing:
            self.telecom.append(contact)

    def get_emails(self) -> List[dict]:
        """Get all email contact points"""
        if not self.telecom:
            return []
        return [t for t in self.telecom if t.get("system") == "email"]

    def to_fhir(self):
        """Convert to FHIR resource format"""
        resource = {
            "resourceType": "Patient",
            "id": self.id,
            "active": self.active == "true",
        }

        if self.name:
            resource["name"] = self.name

        if self.gender:
            resource["gender"] = self.gender

        if self.birth_date:
            resource["birthDate"] = self.birth_date.isoformat()

        if self.telecom:
            resource["telecom"] = self.telecom

        if self.address:
            resource["address"] = self.address

        return resource

    def from_fhir(self, fhir_dict):
        """Update from FHIR resource format"""
        if fhir_dict.get("resourceType") != "Patient":
            raise ValueError("Resource type must be Patient")

        # Handle name if present
        if "name" in fhir_dict:
            self.name = fhir_dict["name"]

        # Handle telecom if present
        if "telecom" in fhir_dict:
            self.telecom = [
                {
                    "system": t.get("system"),
                    "value": t.get("value"),
                    **({"use": t["use"]} if "use" in t else {}),
                }
                for t in fhir_dict["telecom"]
                if t.get("system")
                and t.get("value")  # Only include entries with required fields
            ]

        # Handle other attributes
        self.active = str(fhir_dict.get("active", True)).lower()
        self.gender = fhir_dict.get("gender")
        self.birth_date = fhir_dict.get("birthDate")
        self.address = fhir_dict.get("address")

        return self
