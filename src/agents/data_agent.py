"""Data Agent - Loads and summarizes dataset."""
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.data_utils import (
    load_data, compute_summary_stats, detect_anomalies, 
    compute_trend, segment_analysis
)


class DataAgent:
    """Agent that loads and summarizes data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.df = None
    
    def load_and_summarize(self, plan: Dict[str, Any], data_path: str) -> Dict[str, Any]:
        """Load data and create summary."""
        # Load data
        self.df = load_data(data_path)
        
        # Get time periods from plan
        time_period = plan['time_period']
        current_start = pd.to_datetime(time_period['start_date'])
        current_end = pd.to_datetime(time_period['end_date'])
        comp_start = pd.to_datetime(time_period['comparison_start'])
        comp_end = pd.to_datetime(time_period['comparison_end'])
        
        # Filter data
        current_df = self.df[
            (self.df['date'] >= current_start) & 
            (self.df['date'] <= current_end)
        ].copy()
        
        comparison_df = self.df[
            (self.df['date'] >= comp_start) & 
            (self.df['date'] <= comp_end)
        ].copy()
        
        # Data quality check
        data_quality = self._check_data_quality(self.df)
        
        # Compute summaries
        overall_stats = compute_summary_stats(self.df)
        current_stats = compute_summary_stats(current_df)
        comparison_stats = compute_summary_stats(comparison_df)
        
        # Segment analysis
        segments_to_analyze = plan.get('segments_to_analyze', [])
        segment_breakdown = {}
        
        for segment in segments_to_analyze:
            if segment in current_df.columns:
                segment_breakdown[f'by_{segment}'] = segment_analysis(
                    current_df, segment, plan['primary_metric']
                )
        
        # Trends
        primary_metric = plan['primary_metric']
        trends = {
            f'{primary_metric}_trend': compute_trend(current_df, primary_metric)['trend'],
            f'{primary_metric}_change_pct': self._compute_change(
                current_stats.get(f'avg_{primary_metric}', current_stats.get('avg_roas')),
                comparison_stats.get(f'avg_{primary_metric}', comparison_stats.get('avg_roas'))
            ),
            'ctr_trend': compute_trend(current_df, 'ctr')['trend'],
            'ctr_change_pct': self._compute_change(
                current_stats['avg_ctr'],
                comparison_stats['avg_ctr']
            )
        }
        
        # Anomalies
        anomalies = detect_anomalies(current_df, primary_metric)
        
        summary = {
            "data_quality": data_quality,
            "summary_statistics": {
                "overall": overall_stats,
                "by_period": {
                    "current": {
                        "period": f"{time_period['start_date']} to {time_period['end_date']}",
                        **current_stats
                    },
                    "comparison": {
                        "period": f"{time_period['comparison_start']} to {time_period['comparison_end']}",
                        **comparison_stats
                    }
                }
            },
            "segment_breakdown": segment_breakdown,
            "trends": trends,
            "anomalies": anomalies
        }
        
        return summary
    
    def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Check data quality."""
        missing_values = {}
        for col in ['spend', 'clicks', 'revenue', 'purchases']:
            if col in df.columns:
                missing_values[col] = int(df[col].isna().sum())
        
        total_rows = len(df)
        total_missing = sum(missing_values.values())
        quality_score = 1.0 - (total_missing / (total_rows * len(missing_values)))
        
        return {
            "total_rows": total_rows,
            "date_range": f"{df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}",
            "missing_values": missing_values,
            "quality_score": round(quality_score, 2)
        }
    
    def _compute_change(self, current: float, previous: float) -> float:
        """Compute percentage change."""
        if previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 1)
    
    def get_raw_data(self) -> pd.DataFrame:
        """Get raw dataframe for detailed analysis."""
        return self.df
