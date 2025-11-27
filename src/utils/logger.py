"""Logging utility for agent execution traces."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class AgentLogger:
    """Logger for agent execution traces."""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs = []
    
    def log_agent_execution(self, agent_name: str, input_data: Any, 
                           output_data: Any, metadata: Dict = None):
        """Log an agent execution."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "input": self._serialize(input_data),
            "output": self._serialize(output_data),
            "metadata": metadata or {}
        }
        self.logs.append(log_entry)
    
    def log_error(self, agent_name: str, error: Exception, context: Dict = None):
        """Log an error."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context or {}
        }
        self.logs.append(log_entry)
    
    def save(self):
        """Save logs to file."""
        log_file = self.logs_dir / f"execution_{self.session_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": self.session_id,
                "logs": self.logs
            }, f, indent=2)
        return str(log_file)
    
    def _serialize(self, data: Any) -> Any:
        """Serialize data for JSON logging."""
        if isinstance(data, (str, int, float, bool, type(None))):
            return data
        if isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [self._serialize(item) for item in data]
        return str(data)
