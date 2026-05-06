import time
import psutil
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class PerformanceMetrics:
    """Performance metrics data."""
    component: str
    start_time: datetime
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    memory_used: float = 0.0
    cpu_percent: float = 0.0


class PerformanceMonitor:
    """Monitor performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.process = psutil.Process(os.getpid())
    
    def start_monitoring(self, component: str):
        """Start monitoring component."""
        self.metrics[component] = PerformanceMetrics(
            component=component,
            start_time=datetime.now()
        )
    
    def stop_monitoring(self, component: str) -> Dict[str, Any]:
        """Stop monitoring and get metrics."""
        if component not in self.metrics:
            return {}
        
        metric = self.metrics[component]
        metric.end_time = datetime.now()
        metric.execution_time = (
            metric.end_time - metric.start_time
        ).total_seconds()
        
        try:
            memory_info = self.process.memory_info()
            metric.memory_used = memory_info.rss / (1024 * 1024)  # MB
            metric.cpu_percent = self.process.cpu_percent(interval=0.1)
        except:
            pass
        
        return {
            "execution_time": metric.execution_time,
            "memory_usage": metric.memory_used,
            "cpu_percent": metric.cpu_percent
        }
    
    def get_metrics(self, component: str) -> Optional[PerformanceMetrics]:
        """Get metrics for component."""
        return self.metrics.get(component)
    
    def get_all_metrics(self) -> Dict[str, PerformanceMetrics]:
        """Get all metrics."""
        return self.metrics
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        metrics_list = list(self.metrics.values())
        
        if not metrics_list:
            return {}
        
        total_time = sum(m.execution_time for m in metrics_list)
        avg_time = total_time / len(metrics_list)
        
        return {
            "total_monitored_components": len(metrics_list),
            "total_execution_time": total_time,
            "average_execution_time": avg_time,
            "max_execution_time": max(m.execution_time for m in metrics_list),
            "total_memory_used": sum(m.memory_used for m in metrics_list),
            "average_memory_used": sum(m.memory_used for m in metrics_list) / len(metrics_list)
        }