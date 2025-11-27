"""Tests for Evaluator Agent."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.evaluator import EvaluatorAgent


@pytest.fixture
def config():
    """Test configuration."""
    return {
        'validation': {
            'min_confidence_retry': 0.6,
            'max_retries': 2,
            'statistical_significance': 0.05
        }
    }


@pytest.fixture
def sample_data():
    """Create sample data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2025-03-01', '2025-03-31', freq='D')
    
    data = []
    for date in dates:
        for creative_type in ['Image', 'Video']:
            # Image has lower ROAS
            if creative_type == 'Image':
                roas = np.random.normal(2.5, 0.5)
                ctr = np.random.normal(0.012, 0.002)
            else:
                roas = np.random.normal(4.0, 0.5)
                ctr = np.random.normal(0.018, 0.002)
            
            data.append({
                'date': date,
                'creative_type': creative_type,
                'roas': max(0, roas),
                'ctr': max(0, ctr),
                'spend': np.random.uniform(100, 500),
                'revenue': max(0, roas) * np.random.uniform(100, 500)
            })
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_hypothesis():
    """Sample hypothesis to validate."""
    return {
        'id': 'H1',
        'hypothesis': 'Image creative underperforming',
        'affected_segments': ['creative_type=Image'],
        'initial_confidence': 0.70
    }


@pytest.fixture
def sample_plan():
    """Sample analysis plan."""
    return {
        'primary_metric': 'roas',
        'time_period': {
            'start_date': '2025-03-25',
            'end_date': '2025-03-31',
            'comparison_start': '2025-03-18',
            'comparison_end': '2025-03-24'
        }
    }


def test_evaluator_initialization(config):
    """Test evaluator initializes correctly."""
    evaluator = EvaluatorAgent(config)
    assert evaluator.min_confidence == 0.6
    assert evaluator.config == config


def test_validate_hypothesis_structure(config, sample_data, sample_hypothesis, sample_plan):
    """Test that validation returns correct structure."""
    evaluator = EvaluatorAgent(config)
    
    hypotheses_data = {'hypotheses': [sample_hypothesis]}
    result = evaluator.validate_hypotheses(hypotheses_data, sample_data, sample_plan)
    
    assert 'validated_hypotheses' in result
    assert 'summary' in result
    assert 'retry_recommendations' in result
    
    assert len(result['validated_hypotheses']) == 1
    validated = result['validated_hypotheses'][0]
    
    assert 'id' in validated
    assert 'confidence_score' in validated
    assert 'statistical_tests' in validated
    assert 'quantitative_evidence' in validated
    assert 'actionable' in validated


def test_confidence_score_range(config, sample_data, sample_hypothesis, sample_plan):
    """Test that confidence scores are in valid range."""
    evaluator = EvaluatorAgent(config)
    
    hypotheses_data = {'hypotheses': [sample_hypothesis]}
    result = evaluator.validate_hypotheses(hypotheses_data, sample_data, sample_plan)
    
    for hyp in result['validated_hypotheses']:
        assert 0.0 <= hyp['confidence_score'] <= 1.0


def test_statistical_tests_present(config, sample_data, sample_hypothesis, sample_plan):
    """Test that statistical tests are performed."""
    evaluator = EvaluatorAgent(config)
    
    hypotheses_data = {'hypotheses': [sample_hypothesis]}
    result = evaluator.validate_hypotheses(hypotheses_data, sample_data, sample_plan)
    
    validated = result['validated_hypotheses'][0]
    assert len(validated['statistical_tests']) > 0
    
    test = validated['statistical_tests'][0]
    assert 'test_name' in test
    assert 'p_value' in test
    assert 'significant' in test


def test_quantitative_evidence(config, sample_data, sample_hypothesis, sample_plan):
    """Test that quantitative evidence is computed."""
    evaluator = EvaluatorAgent(config)
    
    hypotheses_data = {'hypotheses': [sample_hypothesis]}
    result = evaluator.validate_hypotheses(hypotheses_data, sample_data, sample_plan)
    
    validated = result['validated_hypotheses'][0]
    evidence = validated['quantitative_evidence']
    
    assert 'metric_change' in evidence
    assert 'sample_size' in evidence
    
    metric_change = evidence['metric_change']
    assert 'current' in metric_change
    assert 'previous' in metric_change
    assert 'percent_change' in metric_change


def test_retry_recommendations_for_low_confidence(config, sample_data, sample_plan):
    """Test that low confidence hypotheses trigger retry recommendations."""
    evaluator = EvaluatorAgent(config)
    
    # Create hypothesis that will have low confidence
    low_conf_hyp = {
        'id': 'H1',
        'hypothesis': 'Weak hypothesis',
        'affected_segments': ['creative_type=NonExistent'],
        'initial_confidence': 0.30
    }
    
    hypotheses_data = {'hypotheses': [low_conf_hyp]}
    result = evaluator.validate_hypotheses(hypotheses_data, sample_data, sample_plan)
    
    # Should have retry recommendations if confidence < threshold
    validated = result['validated_hypotheses'][0]
    if validated['confidence_score'] < config['validation']['min_confidence_retry']:
        assert len(result['retry_recommendations']) > 0


def test_summary_statistics(config, sample_data, sample_plan):
    """Test that summary statistics are correct."""
    evaluator = EvaluatorAgent(config)
    
    hypotheses = [
        {'id': 'H1', 'hypothesis': 'Test 1', 'affected_segments': ['creative_type=Image'], 'initial_confidence': 0.8},
        {'id': 'H2', 'hypothesis': 'Test 2', 'affected_segments': ['creative_type=Video'], 'initial_confidence': 0.5}
    ]
    
    hypotheses_data = {'hypotheses': hypotheses}
    result = evaluator.validate_hypotheses(hypotheses_data, sample_data, sample_plan)
    
    summary = result['summary']
    assert summary['total_hypotheses'] == 2
    assert summary['high_confidence'] + summary['medium_confidence'] + summary['low_confidence'] == 2


def test_parse_segment():
    """Test segment parsing."""
    config = {'validation': {'min_confidence_retry': 0.6, 'max_retries': 2, 'statistical_significance': 0.05}}
    evaluator = EvaluatorAgent(config)
    
    result = evaluator._parse_segment('creative_type=Image')
    assert result == ('creative_type', 'Image')
    
    result = evaluator._parse_segment('platform=Facebook')
    assert result == ('platform', 'Facebook')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
