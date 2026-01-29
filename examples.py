#!/usr/bin/env python3
"""
Example usage of the Medical Diagnosis System

This script demonstrates how to use the system programmatically.
"""

import os
from medical_diagnosis_system import MedicalDiagnosisSystem, PatientInfo

def example_basic_usage():
    """Basic usage example with API"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Initialize system
    api_key = os.getenv("ANTHROPIC_API_KEY")
    system = MedicalDiagnosisSystem(api_key=api_key)
    
    # Start interactive diagnosis
    system.start_diagnosis()


def example_programmatic_usage():
    """Example of using the system programmatically (for research)"""
    print("=" * 60)
    print("Example 2: Programmatic Usage")
    print("=" * 60)
    
    # Initialize system
    api_key = os.getenv("ANTHROPIC_API_KEY")
    system = MedicalDiagnosisSystem(api_key=api_key)
    
    # Manually set patient info (for testing/research)
    system.patient_info = PatientInfo(
        age=45,
        gender="여성",
        chronic_conditions=["고혈압"],
        medications=["암로디핀"],
        symptoms=["두통", "어지러움", "시야 흐림"]
    )
    system.inquiry_complete = True
    
    # Run diagnosis
    print("환자 정보가 설정되었습니다. 진단을 시작합니다...\n")
    system._start_diagnosis_debate()


def example_with_logging():
    """Example with enhanced logging for research"""
    print("=" * 60)
    print("Example 3: With Debate Logging")
    print("=" * 60)
    
    import json
    from datetime import datetime
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    system = MedicalDiagnosisSystem(api_key=api_key)
    
    # Set up logging directory
    os.makedirs("debate_logs", exist_ok=True)
    
    # Run diagnosis
    system.patient_info = PatientInfo(
        age=30,
        gender="남성",
        symptoms=["발열", "기침", "호흡곤란"]
    )
    system.inquiry_complete = True
    
    system._start_diagnosis_debate()
    
    # Save debate history
    log_file = f"debate_logs/debate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'patient_info': {
                'age': system.patient_info.age,
                'gender': system.patient_info.gender,
                'symptoms': system.patient_info.symptoms,
                'chronic_conditions': system.patient_info.chronic_conditions
            },
            'selected_specialists': system.selected_specialists,
            'specialist_groups': system.specialist_groups,
            'total_rounds': system.current_round,
            'final_opinions': [
                {
                    'specialist': op.specialist,
                    'diagnosis': op.diagnosis,
                    'confidence': op.confidence,
                    'reasoning': op.reasoning
                }
                for op in system.active_opinions
            ]
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n토론 로그 저장: {log_file}")


if __name__ == "__main__":
    import sys
    
    print("\n의료 진단 시스템 - 사용 예제\n")
    print("사용 가능한 예제:")
    print("  1. 기본 사용 (대화형)")
    print("  2. 프로그래밍 방식 사용")
    print("  3. 로깅 포함 사용")
    print()
    
    choice = input("실행할 예제 번호를 선택하세요 (1-3): ").strip()
    
    if choice == "1":
        example_basic_usage()
    elif choice == "2":
        example_programmatic_usage()
    elif choice == "3":
        example_with_logging()
    else:
        print("잘못된 선택입니다.")
        sys.exit(1)
