#!/usr/bin/env python3
"""
Command Line Interface for Medical Diagnosis System
"""

import argparse
import os
import sys
import json
from typing import Dict, Any
from dotenv import load_dotenv

from multi_ai_medical_diagnosis import (
    MultiAIDiagnosisSystem,
    Language,
    AIProvider
)


def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def get_ai_providers_from_env(provider_name: str = None, model: str = None) -> Dict[str, Dict[str, str]]:
    """Get AI provider configuration from environment variables"""
    providers = {}
    
    if provider_name:
        # Use specific provider
        if provider_name == "gpt":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("\n❌ 오류: OPENAI_API_KEY를 찾을 수 없습니다.")
                print("Error: OPENAI_API_KEY not found in environment")
                print("\n해결 방법:")
                print("1. .env 파일에 OPENAI_API_KEY=your-key 추가")
                print("2. 또는 환경 변수로 설정: export OPENAI_API_KEY=your-key")
                print("3. API 키 발급: https://platform.openai.com/api-keys\n")
                sys.exit(1)
            providers["gpt"] = {
                "api_key": api_key,
                "model": model or "gpt-4"
            }
        elif provider_name == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                print("\n❌ 오류: ANTHROPIC_API_KEY를 찾을 수 없습니다.")
                print("Error: ANTHROPIC_API_KEY not found in environment")
                print("\n해결 방법:")
                print("1. .env 파일에 ANTHROPIC_API_KEY=your-key 추가")
                print("2. 또는 환경 변수로 설정: export ANTHROPIC_API_KEY=your-key")
                print("3. API 키 발급: https://console.anthropic.com/\n")
                sys.exit(1)
            providers["claude"] = {
                "api_key": api_key,
                "model": model or "claude-3-opus-20240229"
            }
        elif provider_name == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("\n❌ 오류: GOOGLE_API_KEY를 찾을 수 없습니다.")
                print("Error: GOOGLE_API_KEY not found in environment")
                print("\n해결 방법:")
                print("1. .env 파일에 GOOGLE_API_KEY=your-key 추가")
                print("2. 또는 환경 변수로 설정: export GOOGLE_API_KEY=your-key")
                print("3. API 키 발급: https://makersuite.google.com/app/apikey\n")
                sys.exit(1)
            providers["gemini"] = {
                "api_key": api_key,
                "model": model or "gemini-pro"
            }
        elif provider_name == "grok":
            api_key = os.getenv("XAI_API_KEY")
            if not api_key:
                print("\n❌ 오류: XAI_API_KEY를 찾을 수 없습니다.")
                print("Error: XAI_API_KEY not found in environment")
                print("\n해결 방법:")
                print("1. .env 파일에 XAI_API_KEY=your-key 추가")
                print("2. 또는 환경 변수로 설정: export XAI_API_KEY=your-key")
                print("3. API 키 발급: https://console.x.ai/\n")
                sys.exit(1)
            providers["grok"] = {
                "api_key": api_key,
                "model": model or "grok-1"
            }
    else:
        # Load all available providers
        if os.getenv("OPENAI_API_KEY"):
            providers["gpt"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "model": "gpt-4"
            }
        if os.getenv("ANTHROPIC_API_KEY"):
            providers["claude"] = {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "model": "claude-3-opus-20240229"
            }
        if os.getenv("GOOGLE_API_KEY"):
            providers["gemini"] = {
                "api_key": os.getenv("GOOGLE_API_KEY"),
                "model": "gemini-pro"
            }
        if os.getenv("XAI_API_KEY"):
            providers["grok"] = {
                "api_key": os.getenv("XAI_API_KEY"),
                "model": "grok-1"
            }
    
    if not providers:
        print("\n" + "="*60)
        print("❌ API 키를 찾을 수 없습니다")
        print("="*60)
        print("\n📋 사용 가능한 AI 제공자:")
        print("  • OpenAI (GPT-4)")
        print("  • Anthropic (Claude)")
        print("  • Google (Gemini)")
        print("  • xAI (Grok)")
        print("\n🔑 설정 방법:")
        print("1. .env 파일을 열어서 API 키를 입력하세요:")
        print("   OPENAI_API_KEY=sk-proj-...")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
        print("   GOOGLE_API_KEY=...")
        print("   XAI_API_KEY=...")
        print("\n2. 최소 1개 이상의 API 키가 필요합니다")
        print("\n🌐 API 키 발급:")
        print("  • OpenAI: https://platform.openai.com/api-keys")
        print("  • Anthropic: https://console.anthropic.com/")
        print("  • Google: https://makersuite.google.com/app/apikey")
        print("  • xAI: https://console.x.ai/")
        print("="*60 + "\n")
        sys.exit(1)
    
    return providers


def interactive_mode(system: MedicalDiagnosisSystem):
    """Run interactive diagnosis session"""
    print("\n" + "="*60)
    print("Medical Diagnosis System - Interactive Mode")
    print("="*60 + "\n")
    
    # Start inquiry
    question = system.start_diagnosis()
    print(f"System: {question}")
    
    # Collect patient information
    while not system.is_inquiry_complete():
        response = input("You: ").strip()
        
        if response.lower() in ['quit', 'exit', 'q']:
            print("Exiting diagnosis session.")
            sys.exit(0)
        
        result = system.process_patient_response(response)
        print(f"\nSystem: {result}\n")
    
    # Ask if user wants to upload images
    print("\nDo you have any medical images (X-ray, MRI, CT) to upload? (yes/no)")
    has_images = input("You: ").strip().lower()
    
    if has_images in ['yes', 'y']:
        print("Please provide the file path to your medical image:")
        image_path = input("You: ").strip()
        if os.path.exists(image_path):
            system.diagnostic_medicine.patient_info.images.append(image_path)
            print("Image added successfully.")
        else:
            print("Image file not found. Continuing without image.")
    
    # Run debate
    print("\n" + "="*60)
    print("Starting Multi-Specialist Debate")
    print("="*60 + "\n")
    print("Please wait while specialists analyze your case...\n")
    
    final_result = system.run_debate()
    
    # Display results
    print("\n" + "="*60)
    print("FINAL DIAGNOSIS RESULT")
    print("="*60 + "\n")
    print(json.dumps(final_result, indent=2, ensure_ascii=False))
    
    # Save results
    print("\n" + "="*60)
    output_file = "diagnosis_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {output_file}")
    print("="*60)


def batch_mode(system: MedicalDiagnosisSystem, config_path: str):
    """Run diagnosis from configuration file"""
    config = load_config(config_path)
    
    # Process patient info from config
    patient_data = config.get("patient", {})
    
    responses = [
        str(patient_data.get("age", "")),
        patient_data.get("gender", ""),
        patient_data.get("symptoms", ""),
        patient_data.get("chronic_diseases", "none"),
        patient_data.get("medications", "none"),
        patient_data.get("family_history", "none")
    ]
    
    # Start diagnosis
    system.start_diagnosis()
    
    for response in responses:
        system.process_patient_response(response)
        if system.is_inquiry_complete():
            break
    
    # Add images if provided
    if "images" in patient_data:
        for img_path in patient_data["images"]:
            if os.path.exists(img_path):
                system.diagnostic_medicine.patient_info.images.append(img_path)
    
    # Run debate
    print("Running diagnosis...")
    final_result = system.run_debate()
    
    # Save results
    output_file = config.get("output_file", "diagnosis_result.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False)
    
    print(f"Diagnosis complete. Results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Medical Diagnosis System - Multi-AI Specialist Debate"
    )
    
    # Mode selection
    parser.add_argument(
        "--config",
        type=str,
        help="Path to patient configuration JSON file (batch mode)"
    )
    
    # Language selection
    parser.add_argument(
        "--language",
        type=str,
        choices=["en", "ko", "ja", "zh", "es"],
        default="en",
        help="System language (default: en)"
    )
    
    # AI provider selection
    parser.add_argument(
        "--provider",
        type=str,
        choices=["gpt", "claude", "gemini", "grok"],
        help="Specific AI provider to use (if not set, uses all available)"
    )
    
    parser.add_argument(
        "--model",
        type=str,
        help="Specific model name for the provider"
    )
    
    parser.add_argument(
        "--multi-ai",
        action="store_true",
        help="Use multiple AI providers if available"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed debate process"
    )
    
    parser.add_argument(
        "--env-file",
        type=str,
        default=".env",
        help="Path to .env file (default: .env)"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    if os.path.exists(args.env_file):
        load_dotenv(args.env_file)
    else:
        load_dotenv()
    
    # Get AI providers
    ai_providers = get_ai_providers_from_env(args.provider, args.model)
    
    # Map language code to Language enum
    language_map = {
        "en": Language.ENGLISH,
        "ko": Language.KOREAN,
        "ja": Language.JAPANESE,
        "zh": Language.CHINESE,
        "es": Language.SPANISH
    }
    
    # Initialize system
    system = MultiAIDiagnosisSystem(
        api_keys=ai_providers,
        language=args.language
    )
    
    # Run in appropriate mode
    if args.config:
        batch_mode(system, args.config)
    else:
        interactive_mode(system)


if __name__ == "__main__":
    main()
