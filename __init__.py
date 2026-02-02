"""
Medical Diagnosis System

Real-time Referee Intervention & Circular Overlap Structure-based 
High-Precision Medical Diagnosis System
"""

from .multi_ai_medical_diagnosis import (
    MultiAIDiagnosisSystem,
    Doctor,
    Referee,
    Patient,
    Language,
    AIProvider,
    BaseAIClient,
    ClaudeClient,
    GPTClient,
    GeminiClient,
    GrokClient,
    RepetitionDetector
)

__version__ = "1.0.0"
__author__ = "Medical Diagnosis System Contributors"
__license__ = "MIT"

__all__ = [
    "MultiAIDiagnosisSystem",
    "Doctor",
    "Referee",
    "Patient",
    "Language",
    "AIProvider",
    "BaseAIClient",
    "ClaudeClient",
    "GPTClient",
    "GeminiClient",
    "GrokClient",
    "RepetitionDetector"
]
