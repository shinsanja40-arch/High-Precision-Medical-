# ⚠️ 사용자 주의사항 및 FAQ

## 📋 개요

이 문서는 Multi-AI Medical Diagnosis System을 사용할 때 알아야 할 중요한 주의사항과 자주 묻는 질문을 다룹니다.

---

## 🔴 중요 주의사항

### 1. API 의존성

#### ⚠️ 필수 요구사항

**라이브러리**:
```bash
pip install anthropic      # Claude 사용 시
pip install openai         # GPT 또는 Grok 사용 시
pip install google-generativeai  # Gemini 사용 시
```

**API 키**:
- 최소 **1개 이상**의 유효한 API 키 필요
- `.env` 파일에 정확히 입력해야 함
- 빈 문자열(`""`)은 유효하지 않음

#### ✅ 올바른 설정

```bash
# .env 파일
OPENAI_API_KEY=sk-proj-abc123def456...
ANTHROPIC_API_KEY=sk-ant-xyz789...
GOOGLE_API_KEY=AIza...
```

#### ❌ 잘못된 설정

```bash
# 잘못된 예시들
OPENAI_API_KEY=              # 빈 값 (오류!)
OPENAI_API_KEY=""            # 빈 문자열 (오류!)
OPENAI_API_KEY=your_key      # 문자 그대로 (오류!)
```

#### 🔍 에러 발생 시

시스템이 자동으로 상세한 에러 메시지를 표시합니다:

```
❌ No AI providers available.

📦 Missing libraries:
  • anthropic (pip install anthropic)

🔑 Missing or empty API keys:
  • openai/gpt

💡 To fix:
  1. Install required libraries: pip install -r requirements.txt
  2. Create .env file with your API keys:
     OPENAI_API_KEY=sk-...
     ANTHROPIC_API_KEY=sk-ant-...
  3. At least ONE valid API key is required.
```

**해결 방법**:
1. 표시된 라이브러리 설치
2. 표시된 API 키 확인 및 입력
3. 다시 실행

---

### 2. 짧은 문장 반복 감지

#### ⚠️ 제약사항

`RepetitionDetector`는 **최소 2개 이상**의 의미 있는 키워드가 필요합니다.

#### 감지 가능한 경우

```python
✅ "lupus syndrome"                    # 2개 키워드
✅ "lupus antibody syndrome"           # 3개 키워드
✅ "confirmed pneumonia diagnosis"     # 3개 키워드
✅ "감염 진단"                          # 2개 키워드 (한국어)
```

#### 감지 불가능한 경우

```python
❌ "lupus"                             # 1개만
❌ "confirmed"                         # 1개만
❌ "진단"                              # 1개만 (한국어)
```

#### 🔧 조정 방법

시스템 초기화 시 설정을 변경할 수 있습니다:

```python
# 기본 설정 (권장)
system = MultiAIDiagnosisSystem(
    api_keys=api_keys,
    language='ko'
)
# min_keywords=2 (짧은 문장도 감지)

# 만약 직접 설정하려면:
system.repetition_detector = RepetitionDetector(
    max_history=10,
    similarity_threshold=0.85,
    min_keywords=2  # 1-4 사이 권장
)
```

**설정값 의미**:
- `min_keywords=1`: 매우 민감 (거의 모든 반복 감지, False positive 증가)
- `min_keywords=2`: 균형잡힘 (권장)
- `min_keywords=3`: 엄격 (False positive 최소화)
- `min_keywords=4`: 매우 엄격 (긴 문장만 감지)

---

## 💡 자주 묻는 질문 (FAQ)

### Q1: "No AI providers available" 오류가 발생해요

**A**: 다음을 확인하세요:

1. **라이브러리 설치 확인**
   ```bash
   pip list | grep anthropic
   pip list | grep openai
   pip list | grep google-generativeai
   ```

2. **.env 파일 확인**
   ```bash
   cat .env  # 파일 내용 확인
   ```

3. **API 키 유효성**
   - 키가 실제로 입력되어 있는가?
   - 빈 문자열이 아닌가?
   - 따옴표 없이 입력했는가?

4. **환경 변수 로드 확인**
   ```python
   import os
   from dotenv import load_dotenv
   
   load_dotenv()
   print(os.getenv('OPENAI_API_KEY'))  # None이면 문제!
   ```

---

### Q2: 짧은 문장이 반복되는데 감지가 안 돼요

**A**: 다음을 확인하세요:

1. **키워드 개수**
   - 문장에 의미 있는 단어가 2개 이상인가?
   - "the", "a", "is" 같은 일반 단어는 제외됨

2. **한국어의 경우**
   - "입니다", "합니다" 같은 어미는 자동 제거됨
   - "감염입니다" → "감염" (1개)
   - "감염 진단입니다" → "감염", "진단" (2개) ✅

3. **설정 조정**
   ```python
   # min_keywords를 낮춰보세요
   system.repetition_detector.min_keywords = 1  # 가장 민감
   ```

**예시**:
```
문장: "lupus"
→ 키워드: ['lupus'] (1개만)
→ min_keywords=2 설정
→ 감지 안됨 (정상)

해결: min_keywords=1로 낮추거나, 더 긴 문장 사용
```

---

### Q3: False positive가 너무 많아요

**A**: 설정을 더 엄격하게 조정하세요:

```python
system.repetition_detector = RepetitionDetector(
    max_history=10,
    similarity_threshold=0.90,  # 0.85 → 0.90 (더 엄격)
    min_keywords=3              # 2 → 3 (더 엄격)
)
```

**효과**:
- `similarity_threshold ↑` → 더 유사해야만 반복으로 간주
- `min_keywords ↑` → 더 긴 문장만 비교

---

### Q4: 심판이 반복을 감지하는데도 계속 진행돼요

**A**: 이것은 정상입니다:

1. **감지** → 심판이 alert 받음
2. **경고** → 심판이 의사에게 새로운 접근 요구
3. **대응** → 의사가 새로운 증거 제시하면 계속 진행

**확인 방법**:
```
⚠️ REPETITION ALERT Dr. A - 95% similar to round 1
→ 심판: "Dr. A, provide NEW evidence or alternative approach"
→ Dr. A: "ANA titer 1:640, anti-dsDNA positive..." (새로운 증거)
→ 진행 계속 (정상)
```

만약 의사가 계속 같은 주장만 하면 심판이 강하게 개입합니다.

---

### Q5: Context window overflow 오류가 발생해요

**A**: 다음을 확인하세요:

1. **라운드 수**
   - 현재 몇 라운드인가?
   - 30라운드 이상이면 정상적으로 긴 토론

2. **요약 기능 작동**
   ```python
   # 코드에서 확인
   print(system.max_referee_memory)  # 5여야 함
   print(len(system.repetition_detector.argument_history))  # 10 이하
   ```

3. **강제 종료**
   - 10라운드 정체 시 자동 종료됨
   - 수동 종료: Ctrl+C

---

### Q6: 한국어 처리가 이상해요

**A**: 다음을 확인하세요:

1. **언어 설정**
   ```bash
   python cli.py --language ko  # 반드시 ko
   ```

2. **형태소 처리**
   - "감염입니다"와 "감염성"은 같은 것으로 처리됨 (정상)
   - 이것이 의도된 동작입니다

3. **API 응답**
   - AI가 한국어로 응답하지 않으면 API 문제
   - 시스템 프롬프트에 "한국어로 응답" 포함됨

---

### Q7: 웹 검색이 실패해요

**A**: 다음을 확인하세요:

1. **인터넷 연결**
   ```bash
   ping google.com
   ```

2. **requests 라이브러리**
   ```bash
   pip install requests
   ```

3. **재시도 메커니즘**
   - 시스템이 자동으로 3회 재시도
   - 3개 검색 엔진 순차 시도 (Bing → DuckDuckGo → Yahoo)
   - 모두 실패해도 시스템은 계속 작동 (검색 없이)

---

### Q8: API 비용이 너무 많이 나와요

**A**: 비용 절감 방법:

1. **단일 AI 사용**
   ```bash
   python cli.py --provider gpt  # GPT만
   ```

2. **짧은 토론**
   - 정체 감지를 5라운드로 줄이기
   - 코드 수정 필요

3. **웹 검색 제한**
   - 필요시에만 검색
   - 코드에서 `use_web_search=False` 설정

4. **저렴한 모델 사용**
   - GPT-3.5-turbo (GPT-4보다 저렴)
   - Gemini (무료 할당량 있음)

---

## 🔧 고급 설정

### RepetitionDetector 커스터마이징

```python
from multi_ai_medical_diagnosis import RepetitionDetector

# 초민감 설정 (모든 반복 감지)
detector = RepetitionDetector(
    max_history=20,           # 20라운드 기억
    similarity_threshold=0.75, # 75%만 유사해도 반복
    min_keywords=1            # 1개 키워드만 있어도 비교
)

# 초엄격 설정 (False positive 최소)
detector = RepetitionDetector(
    max_history=5,            # 최근 5라운드만
    similarity_threshold=0.95, # 95% 유사해야 반복
    min_keywords=4            # 4개 이상 키워드 필요
)

# 시스템에 적용
system.repetition_detector = detector
```

### 메모리 관리 조정

```python
# 심판 메모리 크기 조정
system.max_referee_memory = 8  # 기본 5 → 8

# 장점: 더 많은 컨텍스트 유지
# 단점: Context window 사용량 증가
```

---

## 📊 성능 최적화

### 빠른 진단 (비용 절감)

```bash
python cli.py --provider gpt --language ko
```

**특징**:
- 단일 AI만 사용
- 빠른 응답
- 낮은 비용
- 정확도 약간 낮음

### 정확한 진단 (품질 우선)

```bash
python cli.py --multi-ai --verbose --language ko
```

**특징**:
- 여러 AI 교차 검증
- 상세한 토론 과정
- 높은 비용
- 최고 정확도

---

## 🆘 문제 해결

### 일반적인 문제 체크리스트

```
□ Python 3.8 이상 설치됨
□ requirements.txt로 라이브러리 설치함
□ .env 파일이 프로젝트 폴더에 있음
□ API 키가 .env에 정확히 입력됨
□ API 키가 빈 문자열이 아님
□ 인터넷 연결됨
□ 방화벽이 API 호출을 차단하지 않음
```

### 로그 확인

```bash
# 상세 로그 보기
python cli.py --verbose

# 특정 오류 찾기
python cli.py 2>&1 | grep -i error
```

---

## 📞 지원

### 자가 진단

1. 이 문서의 FAQ 확인
2. 에러 메시지 읽기 (매우 상세함)
3. 체크리스트 확인

### 추가 도움

- GitHub Issues
- 문서 참조
- 커뮤니티 포럼

---

## ⚖️ 법적 고지

**중요**: 
- 이 시스템은 **연구 및 교육 목적**입니다
- **실제 의료 진단을 대체할 수 없습니다**
- 반드시 **전문의와 상담**하세요
- AI의 진단은 **참고용**입니다

---

**최종 업데이트**: 2026-02-02  
**버전**: 2.2
