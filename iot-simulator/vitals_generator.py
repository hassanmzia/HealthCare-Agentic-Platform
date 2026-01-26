"""
Vitals Generator - Generates realistic synthetic vital signs data.
Supports various patient conditions and realistic variations.
"""

import random
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


@dataclass
class PatientProfile:
    """Patient profile that influences vital sign generation."""
    age: int = 50
    condition: str = "normal"  # normal, hypertensive, hypotensive, fever, tachycardic, bradycardic, hypoxic

    @classmethod
    def random(cls) -> "PatientProfile":
        conditions = ["normal", "normal", "normal", "hypertensive", "hypotensive",
                      "fever", "tachycardic", "bradycardic", "hypoxic"]
        return cls(
            age=random.randint(25, 85),
            condition=random.choice(conditions)
        )


class VitalsGenerator:
    """Generates realistic vital signs based on patient profile and device capabilities."""

    # Normal ranges for vital signs
    NORMAL_RANGES = {
        "heart_rate": (60, 100),           # bpm
        "blood_pressure_systolic": (110, 130),    # mmHg
        "blood_pressure_diastolic": (70, 85),     # mmHg
        "spo2": (95, 100),                 # %
        "temperature": (36.1, 37.2),       # Celsius
        "respiratory_rate": (12, 20),      # breaths/min
        "glucose": (70, 100),              # mg/dL (fasting)
    }

    # Abnormal ranges by condition
    CONDITION_MODIFIERS = {
        "hypertensive": {
            "blood_pressure_systolic": (140, 180),
            "blood_pressure_diastolic": (90, 110),
            "heart_rate": (70, 110),
        },
        "hypotensive": {
            "blood_pressure_systolic": (80, 100),
            "blood_pressure_diastolic": (50, 65),
            "heart_rate": (90, 120),  # compensatory tachycardia
        },
        "fever": {
            "temperature": (38.0, 40.0),
            "heart_rate": (90, 130),  # elevated due to fever
            "respiratory_rate": (18, 28),
        },
        "tachycardic": {
            "heart_rate": (100, 150),
        },
        "bradycardic": {
            "heart_rate": (40, 55),
        },
        "hypoxic": {
            "spo2": (85, 93),
            "respiratory_rate": (22, 35),
            "heart_rate": (90, 130),
        },
    }

    # LOINC codes for vital signs
    LOINC_CODES = {
        "heart_rate": {"code": "8867-4", "display": "Heart rate", "unit": "/min"},
        "blood_pressure_systolic": {"code": "8480-6", "display": "Systolic blood pressure", "unit": "mm[Hg]"},
        "blood_pressure_diastolic": {"code": "8462-4", "display": "Diastolic blood pressure", "unit": "mm[Hg]"},
        "spo2": {"code": "59408-5", "display": "Oxygen saturation in Arterial blood by Pulse oximetry", "unit": "%"},
        "temperature": {"code": "8310-5", "display": "Body temperature", "unit": "Cel"},
        "respiratory_rate": {"code": "9279-1", "display": "Respiratory rate", "unit": "/min"},
        "glucose": {"code": "2339-0", "display": "Glucose [Mass/volume] in Blood", "unit": "mg/dL"},
    }

    # Map device capabilities to vitals
    CAPABILITY_VITALS = {
        "heart_rate": ["heart_rate"],
        "blood_pressure": ["blood_pressure_systolic", "blood_pressure_diastolic"],
        "bp": ["blood_pressure_systolic", "blood_pressure_diastolic"],
        "spo2": ["spo2"],
        "oxygen": ["spo2"],
        "temperature": ["temperature"],
        "temp": ["temperature"],
        "respiratory_rate": ["respiratory_rate"],
        "respiration": ["respiratory_rate"],
        "glucose": ["glucose"],
    }

    def __init__(self, profile: Optional[PatientProfile] = None):
        self.profile = profile or PatientProfile()
        self._last_values = {}  # For realistic variations

    def _get_range(self, vital: str) -> tuple:
        """Get the range for a vital sign based on patient condition."""
        if self.profile.condition in self.CONDITION_MODIFIERS:
            modifiers = self.CONDITION_MODIFIERS[self.profile.condition]
            if vital in modifiers:
                return modifiers[vital]
        return self.NORMAL_RANGES.get(vital, (0, 100))

    def _generate_value(self, vital: str) -> float:
        """Generate a realistic value with small variations from last reading."""
        min_val, max_val = self._get_range(vital)

        # If we have a previous value, vary slightly from it
        if vital in self._last_values:
            last = self._last_values[vital]
            # Allow 5-10% variation from last value
            variation = (max_val - min_val) * 0.1
            new_val = last + random.uniform(-variation, variation)
            # Clamp to range with some tolerance
            new_val = max(min_val - (max_val - min_val) * 0.05,
                         min(max_val + (max_val - min_val) * 0.05, new_val))
        else:
            # First reading - generate within range
            new_val = random.uniform(min_val, max_val)

        self._last_values[vital] = new_val

        # Round appropriately
        if vital in ["spo2", "heart_rate", "respiratory_rate"]:
            return round(new_val)
        elif vital == "temperature":
            return round(new_val, 1)
        else:
            return round(new_val)

    def generate_vitals(self, capabilities: list[str]) -> dict:
        """Generate vitals based on device capabilities."""
        vitals = {}

        # Determine which vitals to generate
        vitals_to_generate = set()
        for cap in capabilities:
            cap_lower = cap.lower().replace("-", "_").replace(" ", "_")
            if cap_lower in self.CAPABILITY_VITALS:
                vitals_to_generate.update(self.CAPABILITY_VITALS[cap_lower])

        # If no capabilities specified, generate common vitals
        if not vitals_to_generate:
            vitals_to_generate = {"heart_rate", "spo2", "blood_pressure_systolic",
                                  "blood_pressure_diastolic", "temperature"}

        # Generate each vital
        for vital in vitals_to_generate:
            if vital in self.LOINC_CODES:
                vitals[vital] = {
                    "value": self._generate_value(vital),
                    "loinc": self.LOINC_CODES[vital]
                }

        return vitals

    def create_fhir_observations(self, vitals: dict, patient_id: str, device_id: str) -> list[dict]:
        """Convert generated vitals to FHIR Observation resources."""
        observations = []
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Handle blood pressure as combined observation with components
        if "blood_pressure_systolic" in vitals and "blood_pressure_diastolic" in vitals:
            sys_data = vitals["blood_pressure_systolic"]
            dia_data = vitals["blood_pressure_diastolic"]
            bp_obs = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "85354-9",
                        "display": "Blood pressure panel with all children optional"
                    }],
                    "text": "Blood pressure"
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "device": {
                    "reference": f"Device/{device_id}"
                },
                "effectiveDateTime": timestamp,
                "component": [
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Systolic blood pressure"
                            }]
                        },
                        "valueQuantity": {
                            "value": sys_data["value"],
                            "unit": "mm[Hg]",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    },
                    {
                        "code": {
                            "coding": [{
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastolic blood pressure"
                            }]
                        },
                        "valueQuantity": {
                            "value": dia_data["value"],
                            "unit": "mm[Hg]",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]"
                        }
                    }
                ]
            }
            observations.append(bp_obs)

        # Handle other vitals as regular observations
        for vital_name, vital_data in vitals.items():
            # Skip BP components as they're handled above
            if vital_name in ("blood_pressure_systolic", "blood_pressure_diastolic"):
                continue

            loinc = vital_data["loinc"]
            obs = {
                "resourceType": "Observation",
                "status": "final",
                "category": [{
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }]
                }],
                "code": {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": loinc["code"],
                        "display": loinc["display"]
                    }],
                    "text": loinc["display"]
                },
                "subject": {
                    "reference": f"Patient/{patient_id}"
                },
                "device": {
                    "reference": f"Device/{device_id}"
                },
                "effectiveDateTime": timestamp,
                "valueQuantity": {
                    "value": vital_data["value"],
                    "unit": loinc["unit"],
                    "system": "http://unitsofmeasure.org",
                    "code": loinc["unit"]
                }
            }
            observations.append(obs)

        return observations


# Patient profile cache to maintain consistency across readings
_patient_profiles: dict[str, PatientProfile] = {}


def get_patient_profile(patient_id: str) -> PatientProfile:
    """Get or create a patient profile for consistent vital generation."""
    if patient_id not in _patient_profiles:
        _patient_profiles[patient_id] = PatientProfile.random()
    return _patient_profiles[patient_id]


def reset_patient_profile(patient_id: str, condition: Optional[str] = None):
    """Reset or update a patient's profile."""
    if condition:
        age = _patient_profiles.get(patient_id, PatientProfile()).age
        _patient_profiles[patient_id] = PatientProfile(age=age, condition=condition)
    elif patient_id in _patient_profiles:
        del _patient_profiles[patient_id]
