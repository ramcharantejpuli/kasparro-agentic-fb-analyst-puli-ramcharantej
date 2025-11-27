"""Workflow orchestrator for multi-agent system."""
import json
from pathlib import Path
from typing import Dict, Any
import sys
sys.path.append(str(Path(__file__).parent.parent))

from agents.planner import PlannerAgent
from agents.data_agent import DataAgent
from agents.insight_agent import InsightAgent
from agents.evaluator import EvaluatorAgent
from agents.creative_generator import CreativeGeneratorAgent
from utils.logger import AgentLogger
from utils.config_loader import load_config, get_data_path


class AgenticWorkflow:
    """Orchestrates the multi-agent workflow."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = load_config(config_path)
        self.logger = AgentLogger(self.config['output']['logs_dir'])
        
        # Initialize agents
        self.planner = PlannerAgent(self.config)
        self.data_agent = DataAgent(self.config)
        self.insight_agent = InsightAgent(self.config)
        self.evaluator = EvaluatorAgent(self.config)
        self.creative_generator = CreativeGeneratorAgent(self.config)
        
        self.reports_dir = Path(self.config['output']['reports_dir'])
        self.reports_dir.mkdir(exist_ok=True)
    
    def run(self, user_query: str) -> Dict[str, Any]:
        """Execute the full workflow."""
        print(f"\n🚀 Starting Agentic Analysis")
        print(f"Query: {user_query}\n")
        
        try:
            # Step 1: Planning
            print("📋 Step 1: Planning...")
            data_path = get_data_path(self.config)
            df = self.data_agent.load_and_summarize.__self__.df = None  # Reset
            
            # Load data to get info
            import pandas as pd
            temp_df = pd.read_csv(data_path)
            temp_df['date'] = pd.to_datetime(temp_df['date'])
            
            data_info = {
                'max_date': temp_df['date'].max().strftime("%Y-%m-%d"),
                'min_date': temp_df['date'].min().strftime("%Y-%m-%d"),
                'columns': list(temp_df.columns)
            }
            
            plan = self.planner.plan(user_query, data_info)
            self.logger.log_agent_execution("planner", user_query, plan)
            print(f"✓ Plan created: {plan['query_interpretation']}")
            
            # Step 2: Data Loading
            print("\n📊 Step 2: Loading and summarizing data...")
            data_summary = self.data_agent.load_and_summarize(plan, data_path)
            self.logger.log_agent_execution("data_agent", plan, data_summary)
            print(f"✓ Data loaded: {data_summary['data_quality']['total_rows']} rows")
            print(f"  Quality score: {data_summary['data_quality']['quality_score']}")
            
            # Step 3: Insight Generation
            print("\n💡 Step 3: Generating hypotheses...")
            insights = self.insight_agent.generate_hypotheses(plan, data_summary)
            self.logger.log_agent_execution("insight_agent", data_summary, insights)
            print(f"✓ Generated {len(insights['hypotheses'])} hypotheses")
            
            # Step 4: Validation
            print("\n🔬 Step 4: Validating hypotheses...")
            df = self.data_agent.get_raw_data()
            validated = self.evaluator.validate_hypotheses(insights, df, plan)
            self.logger.log_agent_execution("evaluator", insights, validated)
            print(f"✓ Validated: {validated['summary']['high_confidence']} high-confidence insights")
            
            # Step 5: Creative Generation
            print("\n🎨 Step 5: Generating creative recommendations...")
            creatives = self.creative_generator.generate_recommendations(validated, df, plan)
            self.logger.log_agent_execution("creative_generator", validated, creatives)
            print(f"✓ Generated recommendations for {len(creatives['recommendations'])} segments")
            
            # Step 6: Generate Reports
            print("\n📝 Step 6: Generating reports...")
            self._save_insights(validated)
            self._save_creatives(creatives)
            self._generate_report(user_query, plan, data_summary, validated, creatives)
            
            # Save logs
            log_file = self.logger.save()
            print(f"\n✅ Analysis complete!")
            print(f"\nOutputs:")
            print(f"  - Report: reports/report.md")
            print(f"  - Insights: reports/insights.json")
            print(f"  - Creatives: reports/creatives.json")
            print(f"  - Logs: {log_file}")
            
            return {
                "plan": plan,
                "data_summary": data_summary,
                "insights": insights,
                "validated": validated,
                "creatives": creatives
            }
            
        except Exception as e:
            self.logger.log_error("workflow", e, {"query": user_query})
            self.logger.save()
            raise
    
    def _save_insights(self, validated: Dict[str, Any]):
        """Save insights to JSON."""
        output = {
            "hypotheses": [
                {
                    "id": h['id'],
                    "hypothesis": h['hypothesis'],
                    "confidence": h['confidence_score'],
                    "evidence": h['quantitative_evidence'],
                    "actionable": h['actionable'],
                    "recommended_action": h['recommended_action']
                }
                for h in validated['validated_hypotheses']
            ],
            "summary": validated['summary']
        }
        
        with open(self.reports_dir / "insights.json", 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
    
    def _save_creatives(self, creatives: Dict[str, Any]):
        """Save creative recommendations to JSON."""
        with open(self.reports_dir / "creatives.json", 'w', encoding='utf-8') as f:
            json.dump(creatives, f, indent=2)
    
    def _generate_report(self, query: str, plan: Dict, data_summary: Dict,
                        validated: Dict, creatives: Dict):
        """Generate markdown report."""
        report = f"""# Facebook Ads Performance Analysis Report

## Query
{query}

## Executive Summary

**Analysis Period:** {plan['time_period']['start_date']} to {plan['time_period']['end_date']}  
**Primary Metric:** {plan['primary_metric'].upper()}  
**Data Quality:** {data_summary['data_quality']['quality_score']} ({data_summary['data_quality']['total_rows']} rows analyzed)

### Key Findings

"""
        
        # Add top insights
        high_conf_hypotheses = [h for h in validated['validated_hypotheses'] if h['confidence_score'] >= 0.7]
        
        for i, hyp in enumerate(high_conf_hypotheses[:3], 1):
            report += f"""
#### {i}. {hyp['hypothesis']}
- **Confidence:** {hyp['confidence_score']:.0%}
- **Evidence:** {hyp['quantitative_evidence']['metric_change']['metric']} changed {hyp['quantitative_evidence']['metric_change']['percent_change']:+.1f}%
- **Action:** {hyp['recommended_action']}
"""
        
        # Performance metrics
        current = data_summary['summary_statistics']['by_period']['current']
        comparison = data_summary['summary_statistics']['by_period']['comparison']
        
        report += f"""

## Performance Metrics

### Current Period
- **ROAS:** {current['avg_roas']:.2f}
- **CTR:** {current['avg_ctr']:.4f}
- **Spend:** ${current['total_spend']:,.2f}
- **Revenue:** ${current['total_revenue']:,.2f}
- **Purchases:** {current['total_purchases']:,}

### Comparison Period
- **ROAS:** {comparison['avg_roas']:.2f}
- **CTR:** {comparison['avg_ctr']:.4f}
- **Spend:** ${comparison['total_spend']:,.2f}
- **Revenue:** ${comparison['total_revenue']:,.2f}
- **Purchases:** {comparison['total_purchases']:,}

### Changes
- **ROAS:** {data_summary['trends']['roas_change_pct']:+.1f}%
- **CTR:** {data_summary['trends']['ctr_change_pct']:+.1f}%

## Segment Analysis

"""
        
        # Add segment breakdowns
        for segment_name, segment_data in data_summary['segment_breakdown'].items():
            report += f"\n### {segment_name.replace('_', ' ').title()}\n\n"
            for seg in segment_data[:3]:
                seg_key = list(seg.keys())[0]
                report += f"- **{seg[seg_key]}:** ROAS {seg.get('avg_roas', 0):.2f}, CTR {seg['avg_ctr']:.4f}\n"
        
        # Creative recommendations
        report += f"""

## Creative Recommendations

{len(creatives['recommendations'])} segments identified for creative refresh.

"""
        
        for rec in creatives['recommendations'][:2]:
            report += f"""
### {rec['segment']}
**Current Performance:** CTR {rec['current_performance']['avg_ctr']:.4f}, ROAS {rec['current_performance']['avg_roas']:.2f}

**Top Recommendations:**
"""
            for creative in rec['new_creatives'][:2]:
                report += f"""
- **{creative['format']}:** {creative['headline']}
  - Message: {creative['message']}
  - Angle: {creative['messaging_angle']}
  - Rationale: {creative['rationale']}
"""
        
        report += f"""

## Next Steps

1. Implement top creative recommendations
2. Monitor performance for 7 days
3. Adjust budget allocation based on results
4. Re-run analysis to measure impact

---
*Generated by Kasparro Agentic FB Analyst*
"""
        
        with open(self.reports_dir / "report.md", 'w', encoding='utf-8') as f:
            f.write(report)
