"""Planner Agent - Decomposes user queries into subtasks."""
import json
from datetime import datetime, timedelta
from typing import Dict, Any
from pathlib import Path


class PlannerAgent:
    """Agent that plans analysis workflow."""
    
    def __init__(self, config: Dict[str, Any], llm_client=None):
        self.config = config
        self.llm_client = llm_client
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load prompt template."""
        prompt_path = Path("prompts/planner_prompt.md")
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""
    
    def plan(self, user_query: str, data_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create analysis plan from user query."""
        # For this implementation, use rule-based planning
        # In production, this would use LLM
        
        plan = self._create_plan(user_query, data_info)
        return plan
    
    def _create_plan(self, query: str, data_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create structured plan."""
        query_lower = query.lower()
        
        # Determine primary metric
        if 'roas' in query_lower:
            primary_metric = 'roas'
        elif 'ctr' in query_lower:
            primary_metric = 'ctr'
        elif 'revenue' in query_lower:
            primary_metric = 'revenue'
        else:
            primary_metric = 'roas'  # default
        
        # Determine time period
        lookback_days = self.config['analysis']['lookback_days']
        
        if 'last week' in query_lower or 'last 7 days' in query_lower:
            lookback_days = 7
        elif 'last month' in query_lower or 'last 30 days' in query_lower:
            lookback_days = 30
        
        # Get date ranges
        max_date = datetime.strptime(data_info['max_date'], "%Y-%m-%d")
        current_end = max_date
        current_start = max_date - timedelta(days=lookback_days - 1)
        comparison_end = current_start - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=lookback_days - 1)
        
        plan = {
            "query_interpretation": f"Analyze {primary_metric.upper()} performance in the most recent {lookback_days}-day period",
            "primary_metric": primary_metric,
            "time_period": {
                "start_date": current_start.strftime("%Y-%m-%d"),
                "end_date": current_end.strftime("%Y-%m-%d"),
                "comparison_start": comparison_start.strftime("%Y-%m-%d"),
                "comparison_end": comparison_end.strftime("%Y-%m-%d"),
                "lookback_days": lookback_days
            },
            "segments_to_analyze": ["creative_type", "platform", "audience_type"],
            "subtasks": [
                {
                    "task_id": "T1",
                    "description": "Load and validate data for specified periods",
                    "agent": "data_agent",
                    "priority": 1
                },
                {
                    "task_id": "T2",
                    "description": f"Generate hypotheses for {primary_metric.upper()} patterns",
                    "agent": "insight_agent",
                    "priority": 2,
                    "depends_on": ["T1"]
                },
                {
                    "task_id": "T3",
                    "description": "Validate hypotheses with statistical tests",
                    "agent": "evaluator",
                    "priority": 3,
                    "depends_on": ["T2"]
                },
                {
                    "task_id": "T4",
                    "description": "Generate creative recommendations for underperforming segments",
                    "agent": "creative_generator",
                    "priority": 4,
                    "depends_on": ["T3"]
                }
            ],
            "success_criteria": f"Identify validated reasons for {primary_metric.upper()} changes with confidence >0.6 and provide actionable recommendations"
        }
        
        return plan
