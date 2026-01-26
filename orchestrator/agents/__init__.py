"""
Multi-Agent Healthcare System

This package contains specialized AI agents for clinical decision support:

Agents:
- SupervisorAgent: Orchestrates all specialist agents
- DiagnosticianAgent: Generates differential diagnoses with ICD-10 codes
- TreatmentAgent: Creates treatment plans with CPT codes
- (Future) TriageAgent: Urgency assessment
- (Future) SafetyAgent: Drug interaction and allergy checking
- (Future) Specialist Agents: Cardiology, Oncology, etc.

A2A Protocol:
Agents communicate using a standardized message format (AgentMessage)
enabling coordination and information sharing.
"""

from .base_agent import (
    BaseAgent,
    AgentMessage,
    AgentCapability,
    AgentCard,
    PatientContext,
    ClinicalFinding,
    DiagnosisRecommendation,
    TreatmentRecommendation,
    AgentOutput,
    MCPClient
)

from .diagnostician_agent import DiagnosticianAgent
from .treatment_agent import TreatmentAgent
from .supervisor_agent import SupervisorAgent, ComprehensiveRecommendation

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentMessage",
    "AgentCapability",
    "AgentCard",
    "PatientContext",
    "ClinicalFinding",
    "DiagnosisRecommendation",
    "TreatmentRecommendation",
    "AgentOutput",
    "MCPClient",

    # Agents
    "DiagnosticianAgent",
    "TreatmentAgent",
    "SupervisorAgent",

    # Outputs
    "ComprehensiveRecommendation"
]
