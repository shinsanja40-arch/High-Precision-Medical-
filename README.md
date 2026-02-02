

🩺 Multi-AI Medical Diagnosis System

High-Precision Medical Diagnosis System based on Real-time Referee Intervention & Circular Overlap Structure

(실시간 심판 개입 및 순환 중첩 구조 기반 고정밀 의료 진단 시스템)

🚀 Overview (개요)

This system is a research-oriented diagnostic framework that minimizes errors through multi-agent collaboration and a dual-referee checking system.

(본 시스템은 다중 에이전트 협업과 이중 심판 체계를 통해 오진을 최소화하는 연구용 진단 프레임워크입니다.)

✨ Key Features (주요 특징)

1. Dual Referee System (이중 심판 체계)

Referee 1 ($5n$): Intervenes every 5 rounds to reset context and eliminate bias.

(매 5라운드마다 개입하여 컨텍스트를 정돈하고 편향성을 제거합니다.)

Referee 2 ($5n-3$): Intervenes at rounds 2, 7, 12... to monitor logical gaps.

(2, 7, 12... 라운드에 개입하여 논리적 허점을 감시합니다.)

Compatibility: These two schedules never overlap, ensuring continuous but independent oversight.

(두 일정은 절대 겹치지 않으며, 독립적인 상호 감시를 보장합니다.)

2. Circular Overlap Group Structure (순환 중첩 그룹 구조)

Doctors are organized into groups where each group shares at least one member with another.

(의사들을 그룹으로 구성하되, 각 그룹이 최소 한 명 이상의 멤버를 공유하여 의견의 연속성을 유지합니다.)

Example: Group 1(A+B), Group 2(B+C), Group 3(C+D), Group 4(D+A).

3. Multi-AI Provider Support (다중 AI 지원)

Fully compatible with GPT-4, Claude 3.5, Gemini 1.5, and Grok.

(GPT-4, Claude 3.5, Gemini 1.5, Grok과 완벽히 호환됩니다.)

Can operate in Single-AI mode or Multi-AI mode for cross-verification.

(교차 검증을 위해 단일 AI 또는 다중 AI 모드로 작동 가능합니다.)

🛠 Installation & Setup (설치 및 설정)

1. Requirements (필수 라이브러리)

Bash



pip install -r requirements.txt

2. Environment Variables (환경 변수 설정)

Create a .env file and add your API keys:

(.env 파일을 생성하고 API 키를 입력하세요.)

코드 스니펫



OPENAI_API_KEY=your_key

ANTHROPIC_API_KEY=your_key

GOOGLE_API_KEY=your_key

🔍 How to Run (실행 방법)

Bash



# Standard run in Korean (한국어 기본 실행)

python cli.py --language ko# Multi-AI mode with detailed logs (다중 AI 모드 및 상세 로그)

python cli.py --multi-ai --verbose

⚠️ Disclaimer (주의 사항)

This system is for research and educational purposes only. It is NOT a substitute for professional medical advice, diagnosis, or treatment.

(본 시스템은 연구 및 교육용입니다. 실제 전문의의 의학적 권고, 진단 또는 치료를 대신할 수 없습니다.)

💡 Compatibility Note (호환성 참고)

This documentation matches the logic in multi_ai_medical_diagnosis.py and cli.py. The sequential inquiry protocol and stagnation detection (10 rounds) are fully implemented and described.

(이 문서는 업로드된 코드의 순차 문진 프로토콜 및 정체 감지 로직과 완벽히 일치합니다.)
