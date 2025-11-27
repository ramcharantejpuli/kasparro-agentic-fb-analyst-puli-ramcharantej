"""Creative Generator Agent - Generates new creative recommendations."""
import pandas as pd
from typing import Dict, Any, List
from collections import Counter
import re
from pathlib import Path


class CreativeGeneratorAgent:
    """Agent that generates creative recommendations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.low_ctr_threshold = config['analysis']['low_ctr_threshold']
        self.prompt_template = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load prompt template."""
        prompt_path = Path("prompts/creative_generator_prompt.md")
        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        return ""
    
    def generate_recommendations(self, validated_hypotheses: Dict[str, Any],
                                df: pd.DataFrame, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate creative recommendations."""
        # Get time period
        time_period = plan['time_period']
        current_start = pd.to_datetime(time_period['start_date'])
        current_end = pd.to_datetime(time_period['end_date'])
        
        current_df = df[(df['date'] >= current_start) & (df['date'] <= current_end)].copy()
        
        # Analyze creative patterns
        creative_analysis = self._analyze_creative_patterns(current_df)
        
        # Identify low-performing segments
        low_performers = self._identify_low_performers(current_df)
        
        # Generate recommendations
        recommendations = []
        
        for segment_info in low_performers[:3]:  # Top 3 segments needing help
            recs = self._generate_segment_recommendations(
                segment_info, creative_analysis, current_df
            )
            recommendations.append(recs)
        
        result = {
            "analysis_summary": {
                "low_ctr_threshold": self.low_ctr_threshold,
                "campaigns_needing_refresh": len(low_performers),
                "high_performing_patterns": creative_analysis
            },
            "recommendations": recommendations,
            "creative_principles": {
                "dos": [
                    "Use specific benefits not generic claims",
                    "Include urgency when appropriate",
                    "Leverage social proof",
                    "Match format to platform",
                    "Test multiple angles"
                ],
                "donts": [
                    "Avoid vague claims",
                    "Don't reuse fatigued messaging",
                    "Don't ignore platform best practices"
                ]
            },
            "expected_impact": {
                "ctr_improvement": "15-25% lift expected",
                "roas_improvement": "10-20% lift if CTR improves",
                "timeline_to_impact": "3-7 days"
            }
        }
        
        return result
    
    def _analyze_creative_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze high-performing creative patterns."""
        # Find best performing creative type
        creative_performance = df.groupby('creative_type').agg({
            'ctr': 'mean',
            'roas': 'mean',
            'spend': 'sum'
        }).round(4)
        
        best_creative = creative_performance['ctr'].idxmax()
        best_ctr = creative_performance.loc[best_creative, 'ctr']
        
        # Extract messaging themes from high-performing ads
        high_performers = df[df['ctr'] > df['ctr'].quantile(0.75)]
        messages = high_performers['creative_message'].dropna().tolist()
        
        themes = self._extract_themes(messages)
        ctas = self._extract_ctas(messages)
        
        return {
            "best_creative_type": str(best_creative),
            "best_avg_ctr": float(best_ctr),
            "top_messaging_themes": themes[:5],
            "top_ctas": ctas[:5]
        }
    
    def _extract_themes(self, messages: List[str]) -> List[str]:
        """Extract common themes from messages."""
        themes = []
        
        # Common patterns
        patterns = {
            "Urgency": r"(limited|deal ends|tonight|last chance|now)",
            "Value": r"(comfort|quality|premium|soft|breathable)",
            "Social Proof": r"(best-selling|rated|review|popular)",
            "Guarantee": r"(guarantee|free returns|risk-free)",
            "Discount": r"(\d+%\s*off|save|discount)"
        }
        
        theme_counts = Counter()
        for message in messages:
            message_lower = message.lower()
            for theme, pattern in patterns.items():
                if re.search(pattern, message_lower):
                    theme_counts[theme] += 1
        
        return [theme for theme, _ in theme_counts.most_common(5)]
    
    def _extract_ctas(self, messages: List[str]) -> List[str]:
        """Extract CTAs from messages."""
        cta_patterns = [
            "shop now", "try", "buy", "get", "upgrade", "discover",
            "limited offer", "deal", "save"
        ]
        
        cta_counts = Counter()
        for message in messages:
            message_lower = message.lower()
            for cta in cta_patterns:
                if cta in message_lower:
                    cta_counts[cta] += 1
        
        return [cta.title() for cta, _ in cta_counts.most_common(5)]
    
    def _identify_low_performers(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify segments needing creative refresh."""
        low_performers = []
        
        # By creative_type
        creative_perf = df.groupby('creative_type').agg({
            'ctr': 'mean',
            'roas': 'mean',
            'campaign_name': 'first'
        }).reset_index()
        
        for _, row in creative_perf.iterrows():
            if row['ctr'] < self.low_ctr_threshold:
                low_performers.append({
                    "segment_type": "creative_type",
                    "segment_value": row['creative_type'],
                    "campaign": row['campaign_name'],
                    "ctr": row['ctr'],
                    "roas": row['roas']
                })
        
        # By platform
        platform_perf = df.groupby('platform').agg({
            'ctr': 'mean',
            'roas': 'mean',
            'campaign_name': 'first'
        }).reset_index()
        
        for _, row in platform_perf.iterrows():
            if row['ctr'] < self.low_ctr_threshold:
                low_performers.append({
                    "segment_type": "platform",
                    "segment_value": row['platform'],
                    "campaign": row['campaign_name'],
                    "ctr": row['ctr'],
                    "roas": row['roas']
                })
        
        return sorted(low_performers, key=lambda x: x['ctr'])
    
    def _generate_segment_recommendations(self, segment_info: Dict[str, Any],
                                         creative_analysis: Dict[str, Any],
                                         df: pd.DataFrame) -> Dict[str, Any]:
        """Generate recommendations for a specific segment."""
        segment_type = segment_info['segment_type']
        segment_value = segment_info['segment_value']
        
        # Generate creative variations
        new_creatives = []
        
        # Creative 1: Urgency + Value
        new_creatives.append({
            "creative_id": "C1",
            "format": "Image",
            "headline": "Last Chance: Premium Comfort at 30% Off",
            "message": "Ultra-soft bamboo fabric that moves with you. Limited stock on best-selling men's briefs. Upgrade your comfort today.",
            "cta": "Shop Now - 30% Off",
            "messaging_angle": "Urgency + Value",
            "rationale": "Combines urgency with value proposition. High-performing pattern from data.",
            "inspiration_from_data": f"Top themes: {', '.join(creative_analysis['top_messaging_themes'][:2])}"
        })
        
        # Creative 2: Social Proof
        new_creatives.append({
            "creative_id": "C2",
            "format": "Video",
            "headline": "10,000+ Men Switched. Here's Why.",
            "message": "See why our breathable mesh boxers are rated 4.9/5. No ride-up guarantee. Free returns.",
            "cta": "Watch & Shop",
            "messaging_angle": "Social proof + Risk reversal",
            "rationale": f"Video format performs best (CTR: {creative_analysis['best_avg_ctr']:.4f}). Social proof builds trust.",
            "inspiration_from_data": "Video creative_type has highest CTR"
        })
        
        # Creative 3: UGC
        new_creatives.append({
            "creative_id": "C3",
            "format": "UGC",
            "headline": "Finally, Underwear That Actually Fits",
            "message": "Real customer: 'Most comfortable briefs I've owned. The cooling mesh is a game-changer.' - Mike, verified buyer",
            "cta": "Read Reviews & Shop",
            "messaging_angle": "Authenticity + Specific benefit",
            "rationale": "UGC format builds credibility. Specific benefits resonate.",
            "inspiration_from_data": "Cooling mesh and comfort are recurring themes"
        })
        
        # Creative 4: Bundle offer
        new_creatives.append({
            "creative_id": "C4",
            "format": "Carousel",
            "headline": "3-Pack Bundle: Save 40% + Free Shipping",
            "message": "Mix & match: Briefs, Boxers, Trunks. Premium organic cotton. Best value of the year.",
            "cta": "Build Your Bundle",
            "messaging_angle": "Value + Choice",
            "rationale": "Bundle offers increase AOV. Carousel showcases variety.",
            "inspiration_from_data": "3-pack messaging has high engagement"
        })
        
        return {
            "campaign": segment_info['campaign'],
            "segment": f"{segment_type}={segment_value}",
            "current_performance": {
                "avg_ctr": round(segment_info['ctr'], 4),
                "avg_roas": round(segment_info['roas'], 2),
                "issue": f"CTR below threshold ({self.low_ctr_threshold})"
            },
            "new_creatives": new_creatives,
            "testing_recommendation": {
                "approach": "A/B test all 4 creatives",
                "budget_allocation": "Equal split for first 3 days",
                "success_metric": f"CTR > {self.low_ctr_threshold}",
                "timeline": "7-day test period"
            }
        }
