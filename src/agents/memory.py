"""Agent memory for cross-run learning."""
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class AgentMemory:
    """Persistent memory for agents across runs."""
    
    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.memory_file = self.memory_dir / "agent_memory.json"
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Load memory from disk."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                pass
        
        return {
            "insights_history": [],
            "successful_patterns": [],
            "failed_hypotheses": [],
            "creative_performance": {},
            "run_count": 0
        }
    
    def save_memory(self):
        """Save memory to disk."""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2)
    
    def add_insight(self, insight: Dict[str, Any]):
        """Store successful insight."""
        # Convert numpy types to Python types for JSON serialization
        insight_clean = self._clean_for_json(insight)
        self.memory["insights_history"].append({
            "timestamp": datetime.now().isoformat(),
            "insight": insight_clean
        })
        self.memory["run_count"] += 1
        self.save_memory()
    
    def _clean_for_json(self, obj: Any) -> Any:
        """Clean object for JSON serialization."""
        import numpy as np
        
        if isinstance(obj, dict):
            return {k: self._clean_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._clean_for_json(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        return obj
    
    def add_pattern(self, pattern: Dict[str, Any]):
        """Store successful pattern."""
        self.memory["successful_patterns"].append(pattern)
        self.save_memory()
    
    def get_similar_insights(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve similar past insights."""
        # Simple keyword matching (can be enhanced with embeddings)
        query_lower = query.lower()
        similar = []
        
        for item in self.memory["insights_history"][-10:]:  # Last 10
            insight = item["insight"]
            if any(word in insight.get("hypothesis", "").lower() 
                   for word in query_lower.split()):
                similar.append(insight)
        
        return similar
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return {
            "total_runs": self.memory["run_count"],
            "total_insights": len(self.memory["insights_history"]),
            "successful_patterns": len(self.memory["successful_patterns"]),
            "failed_hypotheses": len(self.memory["failed_hypotheses"])
        }
