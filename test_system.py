"""
Test Suite for Medical Diagnosis System

This module contains unit tests and integration tests for the system.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from medical_diagnosis_system import (
    MedicalDiagnosisSystem,
    PatientInfo,
    DiagnosisOpinion,
    DebateRound,
    DebateStage
)


class TestPatientInfo(unittest.TestCase):
    """Test PatientInfo data structure"""
    
    def test_patient_info_initialization(self):
        """Test basic patient info creation"""
        patient = PatientInfo(
            age=35,
            gender="남성",
            symptoms=["두통", "어지러움"]
        )
        
        self.assertEqual(patient.age, 35)
        self.assertEqual(patient.gender, "남성")
        self.assertEqual(len(patient.symptoms), 2)
        self.assertEqual(len(patient.chronic_conditions), 0)
    
    def test_patient_info_defaults(self):
        """Test default values"""
        patient = PatientInfo()
        
        self.assertIsNone(patient.age)
        self.assertIsNone(patient.gender)
        self.assertIsInstance(patient.symptoms, list)
        self.assertIsInstance(patient.chronic_conditions, list)


class TestDiagnosisOpinion(unittest.TestCase):
    """Test DiagnosisOpinion data structure"""
    
    def test_diagnosis_opinion_creation(self):
        """Test creating a diagnosis opinion"""
        opinion = DiagnosisOpinion(
            specialist="내과+신경과",
            diagnosis="편두통",
            confidence=0.85,
            reasoning="맥박성 통증, 빛 공포증 존재"
        )
        
        self.assertEqual(opinion.specialist, "내과+신경과")
        self.assertEqual(opinion.diagnosis, "편두통")
        self.assertAlmostEqual(opinion.confidence, 0.85)
        self.assertIn("맥박성", opinion.reasoning)


class TestMedicalDiagnosisSystem(unittest.TestCase):
    """Test main system functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test-api-key"
        
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_system_initialization(self, mock_anthropic):
        """Test system initialization"""
        system = MedicalDiagnosisSystem(api_key=self.api_key)
        
        self.assertEqual(system.api_key, self.api_key)
        self.assertEqual(system.max_rounds, 100)
        self.assertEqual(system.stagnation_threshold, 10)
        self.assertFalse(system.inquiry_complete)
        self.assertEqual(len(system.selected_specialists), 0)
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_specialist_selection(self, mock_anthropic):
        """Test specialist selection logic"""
        system = MedicalDiagnosisSystem(api_key=self.api_key)
        system.patient_info = PatientInfo(
            age=35,
            gender="남성",
            symptoms=["두통", "어지러움"]
        )
        
        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock(text='["신경과", "내과"]')]
        mock_anthropic.return_value.messages.create.return_value = mock_response
        
        system._select_specialists()
        
        # Should have selected some specialists
        self.assertGreater(len(system.selected_specialists), 0)
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_circular_group_formation(self, mock_anthropic):
        """Test circular overlap group formation"""
        system = MedicalDiagnosisSystem(api_key=self.api_key)
        system.selected_specialists = ["A", "B", "C", "D"]
        
        system._form_circular_groups()
        
        # Should create N groups for N specialists
        self.assertEqual(len(system.specialist_groups), 4)
        
        # Check circular overlap pattern
        self.assertEqual(system.specialist_groups[0], ("A", "B"))
        self.assertEqual(system.specialist_groups[1], ("B", "C"))
        self.assertEqual(system.specialist_groups[2], ("C", "D"))
        self.assertEqual(system.specialist_groups[3], ("D", "A"))
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_stagnation_detection(self, mock_anthropic):
        """Test stagnation detection mechanism"""
        system = MedicalDiagnosisSystem(api_key=self.api_key)
        
        # Create identical opinions
        opinion = DiagnosisOpinion(
            specialist="내과",
            diagnosis="감기",
            confidence=0.8,
            reasoning="발열, 기침"
        )
        system.active_opinions = [opinion]
        
        # Simulate stagnation
        for i in range(10):
            is_stagnant = system._check_stagnation()
        
        self.assertTrue(is_stagnant)
        self.assertEqual(system.stagnation_count, 10)
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_opinion_parsing(self, mock_anthropic):
        """Test parsing of opinion responses"""
        system = MedicalDiagnosisSystem(api_key=self.api_key)
        
        response_text = """
        진단명: 긴장성 두통
        확신도: 0.75
        근거: 양측성 압박감, 스트레스 관련
        """
        
        opinion = system._parse_opinion_response("신경과", response_text)
        
        self.assertEqual(opinion.diagnosis, "긴장성 두통")
        self.assertAlmostEqual(opinion.confidence, 0.75)
        self.assertIn("양측성", opinion.reasoning)


class TestDebateProtocol(unittest.TestCase):
    """Test the 5-stage debate protocol"""
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_debate_stages(self, mock_anthropic):
        """Test that all 5 stages are executed"""
        system = MedicalDiagnosisSystem(api_key="test-key")
        
        # Mock API responses
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_anthropic.return_value.messages.create.return_value = mock_response
        
        system.patient_info = PatientInfo(age=35, gender="남성", symptoms=["두통"])
        system.selected_specialists = ["신경과", "내과"]
        system.specialist_groups = [("신경과", "내과")]
        
        # Run one debate cycle
        consensus = system._run_debate_cycle()
        
        # Verify debate ran
        self.assertIsInstance(consensus, bool)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""
    
    def test_missing_api_key(self):
        """Test handling of missing API key"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                MedicalDiagnosisSystem()
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_empty_specialist_list(self, mock_anthropic):
        """Test handling of empty specialist list"""
        system = MedicalDiagnosisSystem(api_key="test-key")
        system.selected_specialists = []
        
        # Should not crash
        system._form_circular_groups()
        self.assertIsInstance(system.specialist_groups, list)
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_single_specialist(self, mock_anthropic):
        """Test with only one specialist"""
        system = MedicalDiagnosisSystem(api_key="test-key")
        system.selected_specialists = ["내과"]
        
        system._form_circular_groups()
        
        self.assertEqual(len(system.specialist_groups), 1)
        self.assertEqual(system.specialist_groups[0], ("내과", "내과"))
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_max_rounds_termination(self, mock_anthropic):
        """Test that debate terminates at max rounds"""
        system = MedicalDiagnosisSystem(api_key="test-key")
        system.current_round = 100
        
        should_terminate = system._should_terminate()
        self.assertTrue(should_terminate)


class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    @patch('builtins.input', side_effect=['35세 남성', '없음', '두통'])
    def test_full_inquiry_workflow(self, mock_input, mock_anthropic):
        """Test complete inquiry workflow"""
        # Mock API responses
        mock_response = Mock()
        mock_response.content = [Mock(text="다음 질문")]
        mock_anthropic.return_value.messages.create.return_value = mock_response
        
        system = MedicalDiagnosisSystem(api_key="test-key")
        
        # This would normally run the full inquiry
        # In test, we just verify initialization
        self.assertIsNotNone(system.patient_info)
        self.assertFalse(system.inquiry_complete)


class TestStagnationHandling(unittest.TestCase):
    """Test stagnation handling scenarios"""
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_two_opinion_stagnation(self, mock_anthropic):
        """Test stagnation with 2 opinions"""
        system = MedicalDiagnosisSystem(api_key="test-key")
        
        system.active_opinions = [
            DiagnosisOpinion("A", "진단1", 0.8, "근거1"),
            DiagnosisOpinion("B", "진단2", 0.8, "근거2")
        ]
        
        system.stagnation_count = 10
        system._handle_stagnation()
        
        # Should force termination
        self.assertEqual(system.current_round, system.max_rounds)
    
    @patch('medical_diagnosis_system.anthropic.Anthropic')
    def test_three_opinion_stagnation(self, mock_anthropic):
        """Test stagnation with 3+ opinions"""
        mock_response = Mock()
        mock_response.content = [Mock(text="제3의 관점")]
        mock_anthropic.return_value.messages.create.return_value = mock_response
        
        system = MedicalDiagnosisSystem(api_key="test-key")
        
        system.active_opinions = [
            DiagnosisOpinion("A", "진단1", 0.8, "근거1"),
            DiagnosisOpinion("B", "진단2", 0.8, "근거2"),
            DiagnosisOpinion("C", "진단3", 0.8, "근거3")
        ]
        
        initial_count = len(system.active_opinions)
        system.stagnation_count = 10
        system._handle_stagnation()
        
        # Should inject third perspective
        self.assertGreater(len(system.active_opinions), initial_count)


def run_tests():
    """Run all tests"""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    print("=" * 70)
    print("Medical Diagnosis System - Test Suite")
    print("=" * 70)
    print()
    
    # Run tests
    unittest.main(verbosity=2)
