# Real-time Referee-Mediated Medical Diagnosis System: A Multi-Agent Approach with Circular Overlap Structure

## Abstract

We present a novel multi-agent medical diagnosis system that employs a circular overlap structure and referee-mediated debate protocol to achieve high-precision diagnosis while minimizing hallucinations. The system combines structured medical inquiry, dynamic specialist selection, and a five-stage debate protocol with real-time intervention mechanisms. Our approach addresses key challenges in AI-assisted medical diagnosis: hallucination prevention, bias mitigation, and consensus formation among multiple expert agents.

**Keywords:** Medical Diagnosis, Multi-Agent Systems, Debate Protocol, Hallucination Detection, AI Safety in Healthcare

---

## 1. Introduction

### 1.1 Background

The integration of artificial intelligence in medical diagnosis presents both opportunities and challenges. While large language models (LLMs) demonstrate impressive capabilities in medical knowledge retrieval and reasoning, they are prone to hallucinations and lack the multi-perspective analysis that characterizes human clinical decision-making.

### 1.2 Motivation

Traditional single-agent diagnostic systems suffer from:
- Overconfidence in incorrect diagnoses
- Lack of diverse perspectives
- Inability to detect and correct hallucinations
- Poor handling of ambiguous or complex cases

### 1.3 Contribution

We propose a system with the following novel contributions:

1. **Circular Overlap Structure**: Specialist agents organized in overlapping groups ensuring cross-validation
2. **Referee-Mediated Protocol**: Real-time intervention and hallucination detection
3. **Stagnation Resolution**: Automatic detection and handling of debate impasses
4. **Structured Inquiry Process**: One-question-at-a-time approach ensuring comprehensive information gathering

---

## 2. System Architecture

### 2.1 Overview

The system consists of four main components:

1. **Diagnostic Medicine Specialist (DMS)**: Conducts structured inquiry
2. **Specialist Agents**: Domain-specific medical experts
3. **Referee Agent**: Mediates debates and ensures quality
4. **Debate Engine**: Orchestrates the five-stage protocol

### 2.2 Circular Overlap Structure

Given specialists S = {S₁, S₂, ..., Sₙ}, groups are formed as:
- G₁ = (S₁, S₂)
- G₂ = (S₂, S₃)
- ...
- Gₙ = (Sₙ, S₁)

This ensures each specialist participates in exactly two groups, enabling cross-validation while maintaining diverse perspectives.

**Advantages:**
- Each specialist's opinion is validated by two different partners
- Reduces groupthink through diverse pairings
- Maintains computational efficiency (n groups for n specialists)

### 2.3 Five-Stage Debate Protocol

```
Stage 1: Opinion Formation
  - Each group independently analyzes patient data
  - Formulates initial diagnosis with confidence score

Stage 2: Referee Check
  - Validates medical reasoning
  - Detects hallucinations or unsupported claims
  - Requests corrections if needed

Stage 3: Cross-Counter
  - Groups challenge each other's diagnoses
  - Present alternative interpretations

Stage 4: Rebuttal
  - Groups defend their diagnoses
  - Address raised concerns

Stage 5: Final Judgment
  - Referee assesses consensus
  - Determines if agreement is reached
  - Decides on next round or termination
```

---

## 3. Methodology

### 3.1 Patient Information Gathering

The Diagnostic Medicine Specialist conducts structured inquiry:

**Required Fields:**
- Age and gender (demographic baseline)
- Chronic conditions (context for symptoms)
- Current medications (drug interactions, side effects)
- Family history (genetic predisposition)
- Presenting symptoms (diagnostic foundation)

**Protocol:**
- One question per interaction
- No compound questions
- Clear, concise language
- Adaptive follow-up based on responses

### 3.2 Specialist Selection

Algorithm:
```
Input: Patient symptoms S, Available specialists D
Output: Selected specialists T

1. For each symptom s in S:
   2. Identify relevant specialties R(s) from knowledge base
3. Aggregate all R(s) → T_candidate
4. Rank T_candidate by relevance score
5. Select top k specialists → T (where 2 ≤ k ≤ 6)
```

### 3.3 Hallucination Detection

The Referee Agent employs multiple detection strategies:

1. **Medical Knowledge Verification**
   - Check against established medical literature
   - Identify claims lacking evidence base

2. **Internal Consistency Check**
   - Detect contradictions within reasoning
   - Verify logical flow of argument

3. **Cross-Validation**
   - Compare across multiple specialist opinions
   - Flag outlier claims

4. **Confidence Calibration**
   - Assess if confidence matches evidence strength
   - Identify overconfident assertions

### 3.4 Stagnation Resolution

**Detection:**
If opinions remain unchanged for θ rounds (default θ = 10):
- System enters stagnation state

**Resolution:**
```
if unique_opinions == 2:
    terminate_debate()
    output_parallel_diagnoses()
elif unique_opinions ≥ 3:
    inject_third_perspective()
    reset_stagnation_counter()
    continue_debate()
```

---

## 4. Implementation

### 4.1 Technology Stack

- **Language:** Python 3.8+
- **LLM API:** Anthropic Claude (claude-sonnet-4-20250514)
- **Dependencies:** anthropic, python-dotenv

### 4.2 Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| max_rounds | 100 | Maximum debate iterations |
| stagnation_threshold | 10 | Rounds before intervention |
| min_specialists | 2 | Minimum experts to consult |
| max_specialists | 6 | Maximum experts to consult |
| consensus_threshold | 0.85 | Agreement level for consensus |

### 4.3 Data Structures

**PatientInfo:**
```python
age: int
gender: str
chronic_conditions: List[str]
medications: List[str]
symptoms: List[str]
family_history: List[str]
```

**DiagnosisOpinion:**
```python
specialist: str
diagnosis: str
confidence: float  # [0, 1]
reasoning: str
evidence: List[str]
```

---

## 5. Experimental Setup

### 5.1 Dataset

[To be completed with actual experimental data]

- Source: [Describe dataset]
- Size: N cases
- Conditions: [List medical conditions]
- Ground truth: [How diagnosis was verified]

### 5.2 Evaluation Metrics

1. **Diagnostic Accuracy**
   - Precision = TP / (TP + FP)
   - Recall = TP / (TP + FN)
   - F1 Score = 2 × (Precision × Recall) / (Precision + Recall)

2. **System Performance**
   - Average rounds to consensus
   - Stagnation rate
   - API cost per diagnosis

3. **Quality Metrics**
   - Hallucination rate
   - Referee intervention frequency
   - Inter-specialist agreement score

### 5.3 Baselines

Comparison with:
- Single-agent LLM diagnosis
- Traditional multi-agent voting
- Human expert diagnosis (gold standard)

---

## 6. Results

### 6.1 Diagnostic Performance

[Table: Comparison of accuracy metrics]

| System | Precision | Recall | F1 Score |
|--------|-----------|--------|----------|
| Proposed | - | - | - |
| Single-agent | - | - | - |
| Multi-agent voting | - | - | - |
| Human expert | - | - | - |

### 6.2 Hallucination Analysis

[Figure: Hallucination detection and correction rates]

### 6.3 Efficiency Analysis

[Table: Computational cost and time]

| Metric | Mean | Std Dev |
|--------|------|---------|
| Rounds to consensus | - | - |
| Total API calls | - | - |
| Processing time (min) | - | - |
| Cost per diagnosis ($) | - | - |

---

## 7. Discussion

### 7.1 Key Findings

1. **Circular Overlap Effectiveness**
   - [Analysis of how overlap structure improved results]

2. **Referee Impact**
   - [Analysis of intervention frequency and effectiveness]

3. **Stagnation Patterns**
   - [Common scenarios and resolution success]

### 7.2 Limitations

1. **Language Dependence**
   - Currently optimized for Korean language
   - May require adaptation for other languages

2. **Computational Cost**
   - Higher API usage compared to single-agent
   - Trade-off between accuracy and efficiency

3. **Specialist Selection**
   - Dependent on accurate symptom → specialty mapping
   - May miss rare or atypical presentations

### 7.3 Future Work

1. **Multi-modal Integration**
   - Incorporate medical imaging
   - Process lab results and vital signs

2. **Knowledge Base Enhancement**
   - Integration with medical literature databases
   - Real-time guideline updates

3. **Adaptive Learning**
   - Learn from feedback to improve accuracy
   - Personalize to clinical settings

4. **Scalability**
   - Parallel debate processing
   - Distributed system architecture

---

## 8. Conclusion

We presented a novel multi-agent medical diagnosis system employing circular overlap structure and referee-mediated debate. The system demonstrates [summary of key achievements]. While limitations exist, particularly in computational cost and language dependence, the approach shows promise for AI-assisted medical diagnosis with enhanced reliability and reduced hallucinations.

The code is open-source and available at: [GitHub URL]

---

## 9. References

[1] Brown, T., et al. (2020). Language Models are Few-Shot Learners. NeurIPS.

[2] Du, Y., et al. (2023). Improving Factuality and Reasoning in Language Models through Multiagent Debate. arXiv.

[3] Lee, P., et al. (2023). Benefits, Limits, and Risks of GPT-4 as an AI Chatbot for Medicine. NEJM.

[4] Singhal, K., et al. (2023). Large Language Models Encode Clinical Knowledge. Nature.

[5] Anthropic. (2024). Constitutional AI: Harmlessness from AI Feedback. Technical Report.

[Additional references to be added]

---

## Appendix A: Sample Diagnosis Session

[Include annotated example of complete diagnosis process]

## Appendix B: System Prompts

[Include key system prompts used for different agents]

## Appendix C: Evaluation Dataset Details

[Detailed description of test cases]

---

## Author Information

**Author:** [Your Name]  
**Affiliation:** [Your Institution]  
**Email:** [Your Email]  
**Date:** January 2026

## Acknowledgments

We thank Anthropic for providing API access and the medical professionals who provided feedback during system development.

## Ethics Statement

This system is designed for research purposes only and should not be used as a substitute for professional medical diagnosis. All experimental protocols were approved by [Ethics Committee Name].

## Code Availability

The complete implementation is available at:
- GitHub: https://github.com/yourusername/medical-diagnosis-system
- License: MIT

## Data Availability

[Statement about data availability and access]
