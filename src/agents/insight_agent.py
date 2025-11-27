"""Insight Agent - Generates hypotheses."""
import json
from typing import Dict, Any, List
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from agents.llm_client import LLMClient
from agents.memory import AgentMemory


class InsightAgent:
    """Agent that generates hypotheses about performance patterns."""
    
    def __init__(self, config: Dict[str, Any], llm_client=None):
        self.config = config
        self.llm_client = llm_client or LLMClient(
            model=config['model']['name'],
            temperature=config['model']['temperature']
        )
        self.memory = AgentMemory()
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load prompt template."""
        prompt_path = Path("prompts/insight_agent_prompt.md")
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""
    
    def generate_hypotheses(self, plan: Dict[str, Any], 
                           data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hypotheses from data summary."""
        # Try LLM-powered generation first
        if self.llm_client.is_available():
            return self._generate_with_llm(plan, data_summary)
        
        # Fallback to rule-based generation
        return self._generate_rule_based(plan, data_summary)
    
    def _generate_with_llm(self, plan: Dict[str, Any], 
                          data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hypotheses using LLM."""
        # Get similar past insights from memory
        similar_insights = self.memory.get_similar_insights(plan['query_interpretation'])
        
        # Construct prompt
        prompt = f"""
You are an expert marketing analyst. Analyze this Facebook Ads performance data and generate hypotheses.

QUERY: {plan['query_interpretation']}
PRIMARY METRIC: {plan['primary_metric']}

DATA SUMMARY:
{json.dumps(data_summary, indent=2)}

PAST INSIGHTS (for context):
{json.dumps(similar_insights[-3:], indent=2) if similar_insights else "None"}

Generate 3-5 hypotheses following this structure:
- Use Think → Analyze → Conclude reasoning
- Provide specific evidence from data
- Assign initial confidence (0-1)
- Make hypotheses testable

Return JSON with this schema:
{{
  "analysis_context": {{
    "primary_observation": "string",
    "time_period": "string",
    "key_metrics_affected": ["string"]
  }},
  "hypotheses": [
    {{
      "id": "H1",
      "hypothesis": "string",
      "reasoning": {{
        "think": "string",
        "analyze": "string",
        "conclude": "string"
      }},
      "supporting_evidence": ["string"],
      "affected_segments": ["string"],
      "initial_confidence": 0.75,
      "testable": true,
      "test_method": "string"
    }}
  ]
}}
"""
        
        result = self.llm_client.generate(
            prompt=prompt,
            system_prompt=self.prompt_template,
            response_format="json"
        )
        
        if result.get("status") == "fallback":
            return self._generate_rule_based(plan, data_summary)
        
        # Store successful insights in memory
        for hyp in result.get("hypotheses", []):
            if hyp.get("initial_confidence", 0) > 0.7:
                self.memory.add_insight(hyp)
        
        return result
    
    def _generate_rule_based(self, plan: Dict[str, Any], 
                            data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hypotheses using rule-based logic."""
        hypotheses = []
        primary_metric = plan['primary_metric']
        
        # Extract key metrics
        current = data_summary['summary_statistics']['by_period']['current']
        comparison = data_summary['summary_statistics']['by_period']['comparison']
        trends = data_summary['trends']
        segments = data_summary['segment_breakdown']
        
        # Hypothesis 1: Creative type performance
        if 'by_creative_type' in segments:
            creative_segments = segments['by_creative_type']
            if len(creative_segments) >= 2:
                worst = min(creative_segments, key=lambda x: x[f'avg_{primary_metric}'])
                best = max(creative_segments, key=lambda x: x[f'avg_{primary_metric}'])
                
                if worst[f'avg_{primary_metric}'] < best[f'avg_{primary_metric}'] * 0.7:
                    hypotheses.append({
                        "id": "H1",
                        "hypothesis": f"Creative fatigue in {worst['creative_type']} ads causing performance decline",
                        "reasoning": {
                            "think": f"{worst['creative_type']} ads show significantly lower {primary_metric.upper()} than {best['creative_type']}",
                            "analyze": f"{worst['creative_type']}: {primary_metric.upper()} {worst[f'avg_{primary_metric}']:.2f} vs {best['creative_type']}: {best[f'avg_{primary_metric}']:.2f}",
                            "conclude": f"{worst['creative_type']} creative likely experiencing audience fatigue"
                        },
                        "supporting_evidence": [
                            f"{worst['creative_type']} {primary_metric.upper()} is {((best[f'avg_{primary_metric}'] - worst[f'avg_{primary_metric}']) / best[f'avg_{primary_metric}'] * 100):.0f}% lower than {best['creative_type']}",
                            f"{worst['creative_type']} represents {worst['spend_share']*100:.0f}% of spend"
                        ],
                        "affected_segments": [f"creative_type={worst['creative_type']}"],
                        "initial_confidence": 0.75,
                        "testable": True,
                        "test_method": f"Compare {primary_metric.upper()} trends by creative_type over time"
                    })
        
        # Hypothesis 2: Audience type performance
        if 'by_audience_type' in segments:
            audience_segments = segments['by_audience_type']
            if len(audience_segments) >= 2:
                worst_aud = min(audience_segments, key=lambda x: x[f'avg_{primary_metric}'])
                
                if worst_aud[f'avg_{primary_metric}'] < current[f'avg_{primary_metric}'] * 0.8:
                    hypotheses.append({
                        "id": "H2",
                        "hypothesis": f"Audience saturation in {worst_aud['audience_type']} campaigns",
                        "reasoning": {
                            "think": f"{worst_aud['audience_type']} audience may be exhausted",
                            "analyze": f"{worst_aud['audience_type']} {primary_metric.upper()}: {worst_aud[f'avg_{primary_metric}']:.2f} vs overall: {current[f'avg_{primary_metric}']:.2f}",
                            "conclude": f"{worst_aud['audience_type']} pool likely saturated"
                        },
                        "supporting_evidence": [
                            f"{worst_aud['audience_type']} {primary_metric.upper()} below average",
                            f"Represents {worst_aud['spend_share']*100:.0f}% of spend"
                        ],
                        "affected_segments": [f"audience_type={worst_aud['audience_type']}"],
                        "initial_confidence": 0.70,
                        "testable": True,
                        "test_method": "Compare audience_type performance trends"
                    })
        
        # Hypothesis 3: Platform performance
        if 'by_platform' in segments:
            platform_segments = segments['by_platform']
            if len(platform_segments) >= 2:
                worst_plat = min(platform_segments, key=lambda x: x[f'avg_{primary_metric}'])
                best_plat = max(platform_segments, key=lambda x: x[f'avg_{primary_metric}'])
                
                if worst_plat[f'avg_{primary_metric}'] < best_plat[f'avg_{primary_metric}'] * 0.8:
                    hypotheses.append({
                        "id": "H3",
                        "hypothesis": f"Platform-specific issues on {worst_plat['platform']}",
                        "reasoning": {
                            "think": f"{worst_plat['platform']} performance diverged from {best_plat['platform']}",
                            "analyze": f"{worst_plat['platform']} {primary_metric.upper()}: {worst_plat[f'avg_{primary_metric}']:.2f} vs {best_plat['platform']}: {best_plat[f'avg_{primary_metric}']:.2f}",
                            "conclude": "Platform-specific issue or creative-platform mismatch"
                        },
                        "supporting_evidence": [
                            f"{worst_plat['platform']} underperforming {best_plat['platform']} by {((best_plat[f'avg_{primary_metric}'] - worst_plat[f'avg_{primary_metric}']) / best_plat[f'avg_{primary_metric}'] * 100):.0f}%"
                        ],
                        "affected_segments": [f"platform={worst_plat['platform']}"],
                        "initial_confidence": 0.65,
                        "testable": True,
                        "test_method": "Compare platform performance trends"
                    })
        
        # Hypothesis 4: Overall trend (always generate if change > 2%)
        metric_change = trends.get(f'{primary_metric}_change_pct', 0)
        if abs(metric_change) > 2:
            direction = "decline" if metric_change < 0 else "increase"
            hypotheses.append({
                "id": f"H{len(hypotheses)+1}",
                "hypothesis": f"Overall {primary_metric.upper()} {direction} of {abs(metric_change):.0f}%",
                "reasoning": {
                    "think": f"Significant {direction} in {primary_metric.upper()} across campaign",
                    "analyze": f"Current: {current[f'avg_{primary_metric}']:.2f} vs Previous: {comparison[f'avg_{primary_metric}']:.2f}",
                    "conclude": f"Broad performance {direction} affecting multiple segments"
                },
                "supporting_evidence": [
                    f"{primary_metric.upper()} changed {metric_change:.1f}%",
                    f"Trend: {trends.get(f'{primary_metric}_trend', 'unknown')}"
                ],
                "affected_segments": ["all"],
                "initial_confidence": 0.80,
                "testable": True,
                "test_method": "Time series analysis"
            })
        
        result = {
            "analysis_context": {
                "primary_observation": f"{primary_metric.upper()} changed {metric_change:.1f}%",
                "time_period": f"{plan['time_period']['start_date']} to {plan['time_period']['end_date']}",
                "key_metrics_affected": [primary_metric, "ctr"]
            },
            "hypotheses": hypotheses[:5],  # Top 5
            "additional_considerations": [
                "Seasonality effects may be present",
                "External market factors not visible in dataset",
                "Data quality issues may affect some segments"
            ],
            "recommended_next_steps": [
                "Validate hypotheses with statistical tests",
                "Test new creative variations",
                "Adjust audience targeting"
            ]
        }
        
        return result
