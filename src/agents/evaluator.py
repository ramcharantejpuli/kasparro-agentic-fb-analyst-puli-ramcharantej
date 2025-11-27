"""Evaluator Agent - Validates hypotheses quantitatively."""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, List
from pathlib import Path


class EvaluatorAgent:
    """Agent that validates hypotheses with statistical tests."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.min_confidence = config['validation']['min_confidence_retry']
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load prompt template."""
        prompt_path = Path("prompts/evaluator_prompt.md")
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""
    
    def validate_hypotheses(self, hypotheses_data: Dict[str, Any], 
                           df: pd.DataFrame, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate hypotheses with statistical tests."""
        validated = []
        retry_recommendations = []
        
        # Get time periods
        time_period = plan['time_period']
        current_start = pd.to_datetime(time_period['start_date'])
        current_end = pd.to_datetime(time_period['end_date'])
        comp_start = pd.to_datetime(time_period['comparison_start'])
        comp_end = pd.to_datetime(time_period['comparison_end'])
        
        current_df = df[(df['date'] >= current_start) & (df['date'] <= current_end)].copy()
        comparison_df = df[(df['date'] >= comp_start) & (df['date'] <= comp_end)].copy()
        
        primary_metric = plan['primary_metric']
        
        for hyp in hypotheses_data.get('hypotheses', []):
            validated_hyp = self._validate_hypothesis(
                hyp, current_df, comparison_df, primary_metric
            )
            validated.append(validated_hyp)
            
            if validated_hyp['confidence_score'] < self.min_confidence:
                retry_recommendations.append({
                    "hypothesis_id": hyp['id'],
                    "issue": f"Low confidence ({validated_hyp['confidence_score']:.2f})",
                    "suggested_alternative": "Consider alternative explanations or gather more data",
                    "additional_analysis_needed": "More granular segment analysis"
                })
        
        # Sort by confidence
        validated.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        summary = {
            "total_hypotheses": len(validated),
            "high_confidence": sum(1 for h in validated if h['confidence_score'] >= 0.7),
            "medium_confidence": sum(1 for h in validated if 0.5 <= h['confidence_score'] < 0.7),
            "low_confidence": sum(1 for h in validated if h['confidence_score'] < 0.5),
            "actionable_insights": sum(1 for h in validated if h.get('actionable', False))
        }
        
        return {
            "validated_hypotheses": validated,
            "summary": summary,
            "retry_recommendations": retry_recommendations
        }
    
    def _validate_hypothesis(self, hyp: Dict[str, Any], current_df: pd.DataFrame,
                            comparison_df: pd.DataFrame, primary_metric: str) -> Dict[str, Any]:
        """Validate a single hypothesis."""
        hypothesis_text = hyp['hypothesis']
        affected_segments = hyp.get('affected_segments', [])
        
        # Parse segment filter
        segment_filter = self._parse_segment(affected_segments[0]) if affected_segments else None
        
        if segment_filter:
            segment_col, segment_val = segment_filter
            current_segment = current_df[current_df[segment_col] == segment_val].copy()
            comparison_segment = comparison_df[comparison_df[segment_col] == segment_val].copy()
            
            # Also get control segment (other values)
            current_control = current_df[current_df[segment_col] != segment_val].copy()
        else:
            current_segment = current_df.copy()
            comparison_segment = comparison_df.copy()
            current_control = None
        
        # Statistical tests
        statistical_tests = []
        
        # Test 1: Compare current vs previous for affected segment
        if len(current_segment) > 5 and len(comparison_segment) > 5:
            current_values = current_segment[primary_metric].dropna()
            comparison_values = comparison_segment[primary_metric].dropna()
            
            if len(current_values) > 0 and len(comparison_values) > 0:
                t_stat, p_value = stats.ttest_ind(current_values, comparison_values)
                
                # Effect size (Cohen's d)
                pooled_std = np.sqrt(
                    ((len(current_values)-1)*current_values.std()**2 + 
                     (len(comparison_values)-1)*comparison_values.std()**2) /
                    (len(current_values) + len(comparison_values) - 2)
                )
                cohens_d = abs((current_values.mean() - comparison_values.mean()) / pooled_std) if pooled_std > 0 else 0
                
                effect_size_label = "small"
                if cohens_d > 0.8:
                    effect_size_label = "large"
                elif cohens_d > 0.5:
                    effect_size_label = "medium"
                
                statistical_tests.append({
                    "test_name": "Two-sample t-test",
                    "comparison": f"{segment_filter[1] if segment_filter else 'Overall'} {primary_metric.upper()} (current vs previous)",
                    "statistic": round(float(t_stat), 2),
                    "p_value": round(float(p_value), 4),
                    "significant": p_value < 0.05,
                    "effect_size": f"{effect_size_label} (Cohen's d = {cohens_d:.2f})"
                })
        
        # Quantitative evidence
        current_mean = current_segment[primary_metric].mean()
        comparison_mean = comparison_segment[primary_metric].mean()
        
        quantitative_evidence = {
            "metric_change": {
                "metric": primary_metric.upper(),
                "current": round(float(current_mean), 2),
                "previous": round(float(comparison_mean), 2),
                "absolute_change": round(float(current_mean - comparison_mean), 2),
                "percent_change": round(float((current_mean - comparison_mean) / comparison_mean * 100), 1) if comparison_mean != 0 else 0,
                "direction": "decline" if current_mean < comparison_mean else "increase"
            },
            "sample_size": {
                "current_n": len(current_segment),
                "previous_n": len(comparison_segment),
                "sufficient": len(current_segment) >= 10 and len(comparison_segment) >= 10
            }
        }
        
        # Add segment specificity if applicable
        if segment_filter and current_control is not None and len(current_control) > 5:
            control_mean = current_control[primary_metric].mean()
            quantitative_evidence["segment_specificity"] = {
                "affected_segment": segment_filter[1],
                "affected_value": round(float(current_mean), 2),
                "control_segment": f"other {segment_filter[0]}",
                "control_value": round(float(control_mean), 2),
                "differential": round(float(current_mean - control_mean), 2)
            }
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(
            statistical_tests, quantitative_evidence, hyp['initial_confidence']
        )
        
        # Determine actionability
        actionable = confidence_score >= self.min_confidence
        
        return {
            "id": hyp['id'],
            "hypothesis": hypothesis_text,
            "validation_method": "Statistical testing + segment comparison",
            "statistical_tests": statistical_tests,
            "quantitative_evidence": quantitative_evidence,
            "confidence_score": confidence_score,
            "confidence_rationale": self._generate_rationale(statistical_tests, quantitative_evidence, confidence_score),
            "limitations": [
                "Limited to available data dimensions",
                "Cannot account for external factors"
            ],
            "actionable": actionable,
            "recommended_action": self._generate_action(hyp, confidence_score)
        }
    
    def _parse_segment(self, segment_str: str):
        """Parse segment string like 'creative_type=Image'."""
        if '=' in segment_str:
            parts = segment_str.split('=')
            return (parts[0], parts[1])
        return None
    
    def _calculate_confidence(self, tests: List[Dict], evidence: Dict, initial: float) -> float:
        """Calculate confidence score."""
        score = initial
        
        # Adjust based on statistical significance
        if tests:
            for test in tests:
                if test.get('significant'):
                    if 'large' in test.get('effect_size', ''):
                        score += 0.10
                    elif 'medium' in test.get('effect_size', ''):
                        score += 0.05
                    
                    if test.get('p_value', 1.0) < 0.01:
                        score += 0.05
        
        # Adjust based on sample size
        if not evidence['sample_size']['sufficient']:
            score -= 0.15
        
        # Cap at 0-1
        return max(0.0, min(1.0, round(score, 2)))
    
    def _generate_rationale(self, tests: List[Dict], evidence: Dict, score: float) -> str:
        """Generate confidence rationale."""
        if score >= 0.8:
            return "Strong statistical evidence with large effect size and sufficient sample"
        elif score >= 0.6:
            return "Moderate statistical evidence with adequate sample size"
        else:
            return "Limited statistical evidence or insufficient sample size"
    
    def _generate_action(self, hyp: Dict, confidence: float) -> str:
        """Generate recommended action."""
        if confidence < 0.6:
            return "Monitor trend; gather more data before taking action"
        
        hypothesis_text = hyp['hypothesis'].lower()
        
        if 'creative' in hypothesis_text or 'fatigue' in hypothesis_text:
            return "Refresh creative with new messaging and visuals"
        elif 'audience' in hypothesis_text or 'saturation' in hypothesis_text:
            return "Expand audience targeting or reduce frequency"
        elif 'platform' in hypothesis_text:
            return "Test platform-optimized creative variations"
        else:
            return "Investigate further and test solutions"
