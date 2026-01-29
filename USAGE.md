# Usage Guide

## 사용자 가이드

이 가이드는 실시간 심판 개입 및 순환 중첩 구조 기반 고정밀 의료 진단 시스템을 사용하는 방법을 설명합니다.

## 시작하기

### 1. 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/medical-diagnosis-system.git
cd medical-diagnosis-system

# 가상 환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. API 키 설정

Anthropic API 키가 필요합니다:

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일에 다음을 추가:
```
ANTHROPIC_API_KEY=your-api-key-here
```

API 키는 https://console.anthropic.com 에서 발급받을 수 있습니다.

### 3. 실행

```bash
python main.py
```

## 기본 사용법

### 대화형 진단

시스템을 실행하면 진단의학과 전문의가 문진을 시작합니다:

```
[진단의학과] 안녕하세요. 진단을 시작하겠습니다.
먼저 나이와 성별을 알려주시겠습니까?

> 35세 남성입니다

[진단의학과] 현재 복용 중인 약이나 진단받은 만성 질환이 있으십니까?

> 고혈압으로 암로디핀을 복용 중입니다

[진단의학과] 어떤 증상으로 방문하셨습니까?

> 두통과 어지러움이 있습니다
```

### 문진 프로세스

시스템은 다음 순서로 정보를 수집합니다:

1. **나이와 성별** (필수)
2. **만성 질환 및 복용 약물** (필수)
3. **주요 증상** (필수)
4. **가족력** (필요시)
5. **추가 정보** (필요시)

**중요:** 질문에 정직하고 상세하게 답변하세요. 정확한 진단을 위해 모든 관련 정보를 제공해야 합니다.

## 고급 사용법

### 프로그래밍 방식 사용

Python 스크립트에서 시스템을 사용할 수 있습니다:

```python
from medical_diagnosis_system import MedicalDiagnosisSystem, PatientInfo

# 시스템 초기화
system = MedicalDiagnosisSystem(api_key="your-api-key")

# 환자 정보 직접 설정 (연구용)
system.patient_info = PatientInfo(
    age=45,
    gender="여성",
    chronic_conditions=["당뇨병"],
    medications=["메트포르민"],
    symptoms=["피로", "체중 감소", "갈증"]
)
system.inquiry_complete = True

# 진단 실행
system._start_diagnosis_debate()
```

### 토론 로그 저장

진단 과정을 연구 목적으로 저장하려면:

```python
import json
from datetime import datetime

# 진단 실행
system.start_diagnosis()

# 결과 저장
result = {
    'patient': {
        'age': system.patient_info.age,
        'gender': system.patient_info.gender,
        'symptoms': system.patient_info.symptoms
    },
    'specialists': system.selected_specialists,
    'rounds': system.current_round,
    'diagnosis': [
        {
            'specialist': op.specialist,
            'diagnosis': op.diagnosis,
            'confidence': op.confidence
        }
        for op in system.active_opinions
    ]
}

with open(f'diagnosis_{datetime.now():%Y%m%d_%H%M%S}.json', 'w') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
```

### 예제 스크립트 실행

```bash
python examples.py
```

선택 옵션:
1. 기본 사용 (대화형)
2. 프로그래밍 방식 사용
3. 로깅 포함 사용

## 출력 이해하기

### 진단 결과 형식

#### 합의 도달 시

```
[합의 진단]
진단명: 긴장성 두통
확신도: 0.85
근거: 양측성 압박감, 스트레스 관련, 신경학적 이상 소견 없음
```

#### 의견 불일치 시

```
[병렬 출력 - 2개의 가능 진단]

1. [신경과+내과]
   진단명: 편두통
   확신도: 0.75
   근거: 맥박성 통증, 빛 공포증, 가족력 양성

2. [이비인후과+안과]
   진단명: 부비동염
   확신도: 0.70
   근거: 안면부 압통, 비강 분비물, 전두부 통증
```

### 시스템 메시지

- `[진단의학과]`: 문진 담당 전문의
- `[심판]`: 토론 중재자 개입
- `[Round N]`: 토론 라운드 번호
- `[합의 도달]`: 전문의들의 의견 일치
- `[병렬 출력]`: 복수의 유효한 진단

## 문제 해결

### API 키 오류

```
Error: ANTHROPIC_API_KEY environment variable not set.
```

**해결:**
1. `.env` 파일이 존재하는지 확인
2. API 키가 올바르게 설정되었는지 확인
3. 환경 변수가 로드되었는지 확인

### 응답 지연

진단 과정은 다음과 같은 이유로 시간이 걸릴 수 있습니다:
- 복잡한 증상 분석
- 다수의 전문의 참여
- 심도 있는 토론 진행

**정상 소요 시간:**
- 간단한 진단: 5-10분
- 중간 복잡도: 10-20분
- 복잡한 경우: 20-30분

### 토론 교착

시스템이 10라운드 동안 진전이 없으면 자동으로 개입합니다:

```
[심판 개입] 10회 반복 감지. 개입을 시작합니다.
```

**자동 처리:**
- 2개 의견: 병렬 출력 후 종료
- 3개 이상: 제3의 관점 투입

## 모범 사례

### 문진 시

1. **정확한 정보 제공**
   - 나이, 성별을 정확히 입력
   - 모든 복용 약물 명시
   - 증상을 구체적으로 설명

2. **시간 순서 명확히**
   - 증상 시작 시점
   - 악화/호전 경과
   - 관련 사건

3. **빠짐없이 답변**
   - 질문을 건너뛰지 않기
   - "잘 모르겠습니다"보다는 추정치라도 제공
   - 관련 없다고 생각되는 정보도 언급

### 연구 목적 사용 시

1. **데이터 수집**
   ```python
   # 여러 케이스 실행
   for patient_case in test_cases:
       system = MedicalDiagnosisSystem(api_key=api_key)
       system.patient_info = patient_case
       system.inquiry_complete = True
       system._start_diagnosis_debate()
       save_results(system)
   ```

2. **로그 분석**
   - 토론 라운드 수 분석
   - 합의 도달률 계산
   - 전문의 선별 패턴 연구

3. **성능 평가**
   - 정확도 측정 (실제 진단과 비교)
   - 응답 시간 기록
   - API 비용 추적

## 제한사항

### 의료적 제한사항

⚠️ **중요:**
- 이 시스템은 **연구 목적**으로만 사용됩니다
- **실제 의료 진단을 대체할 수 없습니다**
- 모든 의료 결정은 **자격을 갖춘 의료 전문가**와 상담해야 합니다

### 기술적 제한사항

1. **언어 지원**
   - 현재 한국어로 최적화
   - 다른 언어는 추가 조정 필요

2. **진단 범위**
   - 일반적인 증상 기반 진단
   - 전문 검사 결과 해석 불가
   - 응급 상황 판단 불가

3. **API 의존성**
   - 인터넷 연결 필요
   - API 사용량 제한 적용
   - 비용 발생

## 자주 묻는 질문 (FAQ)

**Q: 개인 의료 정보는 어떻게 처리되나요?**

A: 모든 대화는 Anthropic의 API를 통해 처리됩니다. Anthropic의 개인정보 처리방침을 확인하세요. 민감한 개인정보는 입력하지 않는 것을 권장합니다.

**Q: 진단 결과를 의사에게 보여줘도 되나요?**

A: 연구 참고 자료로는 가능하나, 이를 의료 진단으로 간주해서는 안 됩니다.

**Q: 응급 상황에 사용할 수 있나요?**

A: **절대 아닙니다.** 응급 상황에는 즉시 119에 연락하거나 응급실을 방문하세요.

**Q: API 비용은 얼마나 드나요?**

A: 진단당 약 $0.50-$3.00 (복잡도에 따라). 자세한 내용은 Anthropic 가격 정책을 확인하세요.

**Q: 시스템을 수정/확장할 수 있나요?**

A: 네, MIT 라이선스 하에 자유롭게 수정 가능합니다. CONTRIBUTING.md를 참고하세요.

## 도움받기

- **이슈 보고:** GitHub Issues
- **기능 제안:** GitHub Discussions
- **기여:** CONTRIBUTING.md 참고
- **문의:** 저장소 이슈로 문의

## 추가 리소스

- [시스템 아키텍처](docs/ARCHITECTURE.md)
- [API 문서](https://docs.anthropic.com)
- [연구 논문](docs/PAPER.md) (해당시)
- [예제 코드](examples.py)
