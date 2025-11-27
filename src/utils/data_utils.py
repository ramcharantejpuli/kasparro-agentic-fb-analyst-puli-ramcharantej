"""Data processing utilities."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any


def load_data(csv_path: str) -> pd.DataFrame:
    """Load Facebook Ads data from CSV."""
    df = pd.read_csv(csv_path)
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_date_range(df: pd.DataFrame, lookback_days: int = 7) -> Tuple[str, str, str, str]:
    """Get current and comparison date ranges."""
    max_date = df['date'].max()
    current_start = max_date - timedelta(days=lookback_days - 1)
    current_end = max_date
    
    comparison_end = current_start - timedelta(days=1)
    comparison_start = comparison_end - timedelta(days=lookback_days - 1)
    
    return (
        current_start.strftime("%Y-%m-%d"),
        current_end.strftime("%Y-%m-%d"),
        comparison_start.strftime("%Y-%m-%d"),
        comparison_end.strftime("%Y-%m-%d")
    )


def compute_summary_stats(df: pd.DataFrame, group_by: List[str] = None) -> Dict[str, Any]:
    """Compute summary statistics."""
    if group_by:
        grouped = df.groupby(group_by)
        return {
            'total_spend': float(grouped['spend'].sum().sum()),
            'total_revenue': float(grouped['revenue'].sum().sum()),
            'avg_roas': float((grouped['revenue'].sum() / grouped['spend'].sum()).mean()),
            'avg_ctr': float(grouped['ctr'].mean().mean()),
            'total_purchases': int(grouped['purchases'].sum().sum())
        }
    else:
        return {
            'total_spend': float(df['spend'].sum()),
            'total_revenue': float(df['revenue'].sum()),
            'avg_roas': float(df['revenue'].sum() / df['spend'].sum()) if df['spend'].sum() > 0 else 0,
            'avg_ctr': float(df['ctr'].mean()),
            'total_purchases': int(df['purchases'].sum())
        }


def detect_anomalies(df: pd.DataFrame, metric: str = 'roas', threshold: float = 3.0) -> List[Dict]:
    """Detect anomalies using z-score method."""
    anomalies = []
    values = df[metric].dropna()
    
    if len(values) < 10:
        return anomalies
    
    mean = values.mean()
    std = values.std()
    
    if std == 0:
        return anomalies
    
    df['z_score'] = (df[metric] - mean) / std
    anomaly_rows = df[abs(df['z_score']) > threshold]
    
    for _, row in anomaly_rows.iterrows():
        anomalies.append({
            'date': row['date'].strftime("%Y-%m-%d"),
            'metric': metric,
            'value': float(row[metric]),
            'z_score': float(row['z_score']),
            'note': f"Unusually {'high' if row['z_score'] > 0 else 'low'} {metric}"
        })
    
    return anomalies[:5]  # Return top 5


def compute_trend(df: pd.DataFrame, metric: str = 'roas') -> Dict[str, Any]:
    """Compute trend direction and magnitude."""
    df_sorted = df.sort_values('date')
    values = df_sorted[metric].dropna()
    
    if len(values) < 2:
        return {'trend': 'insufficient_data', 'change_pct': 0}
    
    first_half = values[:len(values)//2].mean()
    second_half = values[len(values)//2:].mean()
    
    if first_half == 0:
        return {'trend': 'undefined', 'change_pct': 0}
    
    change_pct = ((second_half - first_half) / first_half) * 100
    
    if abs(change_pct) < 5:
        trend = 'stable'
    elif change_pct > 0:
        trend = 'increasing'
    else:
        trend = 'declining'
    
    return {
        'trend': trend,
        'change_pct': round(change_pct, 1)
    }


def segment_analysis(df: pd.DataFrame, segment_col: str, metric: str = 'roas') -> List[Dict]:
    """Analyze performance by segment."""
    segments = []
    
    for segment_value in df[segment_col].unique():
        segment_df = df[df[segment_col] == segment_value]
        
        if len(segment_df) < 5:
            continue
        
        segments.append({
            segment_col: str(segment_value),
            f'avg_{metric}': float(segment_df[metric].mean()),
            'avg_ctr': float(segment_df['ctr'].mean()),
            'spend_share': float(segment_df['spend'].sum() / df['spend'].sum()),
            'n': len(segment_df)
        })
    
    return sorted(segments, key=lambda x: x[f'avg_{metric}'], reverse=True)
