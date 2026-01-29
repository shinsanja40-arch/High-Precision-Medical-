# Real-time Referee-Mediated Medical Diagnosis System
# 실시간 심판 개입 및 순환 중첩 구조 기반 고정밀 의료 진단 시스템

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Overview

This system implements an advanced medical diagnosis framework using:
- **Circular Overlap Structure**: Multiple specialist groups with overlapping expertise
- **Referee-Mediated Debate**: Asymmetric debate protocol with strict hallucination control
- **Multi-agent Collaboration**: Neutral medical specialists working in coordinated groups

### Key Features

- ✅ Structured medical inquiry (one question at a time)
- ✅ Dynamic specialist selection based on symptoms
- ✅ Circular overlap group formation (e.g., Group1: A+B, Group2: B+C)
- ✅ 5-stage debate protocol with referee intervention
- ✅ Automatic hallucination detection and correction
- ✅ Stagnation detection (10-round repetition check)
- ✅ Maximum 100 rounds with parallel output on disagreement
- ✅ Persona reset mechanism for non-compliant agents

## 🏗️ System Architecture

```
User Input
    ↓
Diagnostic Medicine Specialist (문진)
    ↓
Specialist Selection & Group Formation
    ↓
Circular Overlap Debate Groups
    ↓
5-Stage Debate Protocol
    ├── Opinion
    ├── Referee Check
    ├── Cross-Counter
    ├── Rebuttal
    └── Final Judgment
    ↓
Diagnosis Output
```

## 🚀 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/medical-diagnosis-system.git
cd medical-diagnosis-system

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your Anthropic API key
```

## 📦 Requirements

- Python 3.8+
- anthropic>=0.25.0
- python-dotenv>=1.0.0

## 💻 Usage

### Basic Usage

```python
from medical_diagnosis_system import MedicalDiagnosisSystem

# Initialize the system
system = MedicalDiagnosisSystem(api_key="your-api-key")

# Start diagnosis
system.start_diagnosis()
```

### Command Line Interface

```bash
python main.py
```

### Example Interaction

```
[진단의학과] 안녕하세요. 진단을 시작하겠습니다.
먼저 나이와 성별을 알려주시겠습니까?

> 35세 남성입니다

[진단의학과] 현재 복용 중인 약이나 진단받은 만성 질환이 있으십니까?

> 없습니다

[진단의학과] 어떤 증상으로 방문하셨습니까?

> 두통과 어지러움이 있습니다
...
```

## 📚 System Components

### 1. Diagnostic Medicine Specialist (문진 담당)
- Conducts structured medical inquiry
- Asks one question at a time
- Mandatory checks: age, gender, chronic conditions, medications, family history

### 2. Referee Agent (심판)
- Monitors all debates for hallucinations
- Enforces debate protocol
- Intervenes on stagnation (10-round repetition)
- Resets non-compliant agents

### 3. Specialist Agents (전문의)
- Neutral expert stance (no bias)
- Circular overlap group participation
- 5-stage debate participation

### 4. Debate Protocol

**Stage 1: Opinion**
- Each specialist presents initial diagnosis

**Stage 2: Referee Check**
- Validates opinions against medical evidence
- Flags hallucinations or unsupported claims

**Stage 3: Cross-Counter**
- Specialists challenge each other's opinions

**Stage 4: Rebuttal**
- Defense against challenges

**Stage 5: Final Judgment**
- Referee determines consensus or valid disagreements

## ⚙️ Configuration

Edit `config.yaml` to customize:

```yaml
max_debate_rounds: 100
stagnation_threshold: 10
min_specialists: 2
max_specialists: 6
debate_detail_output: false  # Hide internal debate by default
```

## 🔬 Research & Citation

If you use this system in your research, please cite:

```bibtex
@software{medical_diagnosis_system,
  title={Real-time Referee-Mediated Medical Diagnosis System},
  author={Your Name},
  year={2026},
  url={https://github.com/yourusername/medical-diagnosis-system}
}
```

## ⚠️ Disclaimer

This system is designed for research purposes and should not replace professional medical diagnosis. Always consult qualified healthcare providers for medical decisions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📧 Contact

For questions or collaboration inquiries, please open an issue on GitHub.

## 🙏 Acknowledgments

- Based on multi-agent debate frameworks
- Inspired by clinical diagnostic protocols
- Built with Anthropic's Claude API
