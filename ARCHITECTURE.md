# System Architecture

## Overview

이 문서는 실시간 심판 개입 및 순환 중첩 구조 기반 고정밀 의료 진단 시스템의 내부 아키텍처를 설명합니다.

## Core Components

### 1. Diagnostic Medicine Specialist (진단의학과)

**역할:**
- 초기 문진 수행
- 환자 정보 수집 및 구조화
- 적절한 전문의 과 선별
- 순환 중첩 그룹 구성

**문진 프로토콜:**
```
질문 → 답변 수집 → 다음 질문 → ... → 문진 완료
```

**필수 확인 항목:**
- 나이 (age)
- 성별 (gender)
- 만성 질환 (chronic_conditions)
- 복용 약물 (medications)
- 가족력 (family_history) - 필요시
- 증상 (symptoms)

### 2. Circular Overlap Structure (순환 중첩 구조)

전문의들을 중첩되는 그룹으로 편성하여 다각적 분석을 수행합니다.

**예시:**
```
전문의: [A, B, C, D]
그룹 구성:
  - 그룹 1: A + B
  - 그룹 2: B + C
  - 그룹 3: C + D
  - 그룹 4: D + A
```

**장점:**
- 모든 전문의가 2개 그룹에 참여
- 다양한 관점의 교차 검증
- 편향 감소

### 3. Referee Agent (심판)

**핵심 기능:**

1. **환각 탐지 (Hallucination Detection)**
   - 의학적 근거 없는 주장 식별
   - 상식에 반하는 진단 차단
   - 근거 요구 및 검증

2. **토론 제어 (Debate Control)**
   - 5단계 프로토콜 강제
   - 발언 순서 관리
   - 시간 제한 적용

3. **교착 상태 해결 (Stagnation Resolution)**
   - 10회 반복 감지
   - 2개 이견: 강제 종료 → 병렬 출력
   - 3개 이상: 제3의 관점 투입

4. **Persona Reset**
   - 반항하는 에이전트 초기화
   - 오류 반복 에이전트 교체

### 4. 5-Stage Debate Protocol

```
┌─────────────────┐
│  1. Opinion     │ ← 초기 진단 의견 제시
└────────┬────────┘
         │
┌────────▼────────┐
│ 2. Referee Check│ ← 근거 검증, 환각 체크
└────────┬────────┘
         │
┌────────▼────────┐
│ 3. Cross-Counter│ ← 상호 반박
└────────┬────────┘
         │
┌────────▼────────┐
│  4. Rebuttal    │ ← 재반박
└────────┬────────┘
         │
┌────────▼────────┐
│ 5. Final Judgment│ ← 최종 판단
└────────┬────────┘
         │
    합의 여부 확인
         │
    ┌────▼────┐
    │합의 도달?│
    └─┬────┬──┘
      │    │
     예   아니오
      │    │
   종료  다음 라운드
```

## Control Flow

### Main Execution Loop

```python
while current_round < max_rounds:
    # 1. Check stagnation
    if stagnation_detected():
        handle_stagnation()
    
    # 2. Run debate cycle
    consensus = run_5_stage_debate()
    
    # 3. Check termination
    if consensus or max_rounds_reached():
        break
    
    current_round += 1
```

### Stagnation Handling Logic

```python
if same_opinions_for_10_rounds:
    unique_opinions_count = count_unique_opinions()
    
    if unique_opinions_count == 2:
        # 강제 종료
        terminate_and_output_parallel()
    
    elif unique_opinions_count >= 3:
        # 제3의 관점 투입
        inject_third_perspective()
        reset_stagnation_counter()
```

## Data Structures

### PatientInfo
```python
@dataclass
class PatientInfo:
    age: Optional[int]
    gender: Optional[str]
    chronic_conditions: List[str]
    medications: List[str]
    family_history: List[str]
    symptoms: List[str]
    additional_info: Dict
```

### DiagnosisOpinion
```python
@dataclass
class DiagnosisOpinion:
    specialist: str          # "내과+신경과"
    diagnosis: str           # "편두통"
    confidence: float        # 0.0 - 1.0
    reasoning: str           # 의학적 근거
    evidence: List[str]      # 지지 증거들
```

### DebateRound
```python
@dataclass
class DebateRound:
    round_number: int
    stage: DebateStage
    speaker: str
    content: str
    referee_feedback: Optional[str]
    hallucination_detected: bool
    timestamp: str
```

## API Integration

### Claude API Usage

모든 에이전트는 Anthropic Claude API를 통해 구현됩니다:

```python
def _call_claude(self, system_prompt: str, user_message: str) -> str:
    message = self.client.messages.create(
        model=self.model,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )
    return message.content[0].text
```

**System Prompts:**
- 각 에이전트별 특화된 시스템 프롬프트
- 역할, 제약사항, 출력 형식 명시
- 중립성 및 의학적 정확성 강조

## Safety Mechanisms

### 1. Hallucination Prevention
- 모든 주장에 대한 근거 요구
- 심판의 실시간 검증
- 근거 없는 주장 즉시 정정

### 2. Bias Mitigation
- 중립적 전문가 페르소나 강제
- 순환 중첩 구조로 다각적 검토
- 심판의 공정한 중재

### 3. Infinite Loop Prevention
- 최대 라운드 제한 (100)
- 교착 상태 자동 감지 (10회)
- 강제 종료 및 결과 출력

### 4. Quality Assurance
- 5단계 프로토콜 강제
- 단계별 검증
- 최종 심판 판단

## Performance Considerations

### API Call Optimization
- 배치 처리 가능 부분 그룹화
- 불필요한 중복 호출 방지
- 토큰 사용량 모니터링

### Response Time
- 평균 1라운드: 약 30-60초
- 전체 진단 시간: 5-30분 (복잡도에 따라)
- 최대 100라운드: ~3시간

## Extensibility

### Adding New Specialists
```python
# 전문과 목록 확장
AVAILABLE_SPECIALISTS = [
    "내과", "신경과", "정형외과",
    "이비인후과", "안과", "피부과",
    # 새로운 전문과 추가
    "정신건강의학과", "재활의학과"
]
```

### Custom Debate Protocols
```python
class CustomDebateProtocol:
    def run_cycle(self):
        # 커스텀 토론 프로토콜 구현
        pass
```

### Integration with Medical Databases
```python
def _validate_against_database(self, diagnosis: str) -> bool:
    # 의학 데이터베이스와 연동
    # ICD-10 코드 검증 등
    pass
```

## Testing Strategy

### Unit Tests
- 각 컴포넌트별 독립 테스트
- Mock API 응답 사용

### Integration Tests
- 전체 워크플로우 테스트
- 실제 API 호출 포함

### Edge Cases
- 교착 상태 시나리오
- 환각 감지 테스트
- 경계 조건 검증

## Future Enhancements

1. **Multi-modal Input**
   - 의료 이미지 분석
   - 검사 결과 통합

2. **Knowledge Base Integration**
   - 의학 문헌 검색
   - 최신 연구 반영

3. **Real-time Learning**
   - 피드백 학습
   - 진단 정확도 향상

4. **Collaboration Tools**
   - 실제 의료진과 협업
   - 2차 의견 요청

## References

- Multi-agent Debate Frameworks
- Clinical Decision Support Systems
- AI Safety in Healthcare
- Hallucination Detection in LLMs
