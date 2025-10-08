import asyncio
import time
from typing import Dict, Any, List
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Metrics for monitoring API performance"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time_ms: float = 0.0
    total_processing_time_ms: float = 0.0

    # Search method distribution
    search_methods_used: Dict[str, int] = field(default_factory=dict)

    # Effectiveness metrics
    average_effectiveness: float = 0.0
    total_matches: int = 0
    total_no_matches: int = 0

    # Error tracking
    error_types: Dict[str, int] = field(default_factory=dict)

    # Processing start time
    start_time: float = field(default_factory=time.time)

class MetricsCollector:
    """Collects and aggregates API performance metrics"""

    def __init__(self):
        self.metrics = ProcessingMetrics()
        self._lock = asyncio.Lock()

    async def record_request(
        self,
        success: bool,
        processing_time_ms: float,
        effectiveness: float,
        matches_count: int,
        no_matches_count: int,
        search_methods: List[str],
        error_type: str = None
    ):
        """Record metrics for a completed request"""
        async with self._lock:
            self.metrics.total_requests += 1

            if success:
                self.metrics.successful_requests += 1
                self.metrics.total_processing_time_ms += processing_time_ms
                self.metrics.average_processing_time_ms = (
                    self.metrics.total_processing_time_ms / self.metrics.successful_requests
                )

                # Update effectiveness metrics
                total_items = matches_count + no_matches_count
                if total_items > 0:
                    current_effectiveness = (matches_count / total_items) * 100
                    self.metrics.average_effectiveness = (
                        (self.metrics.average_effectiveness * (self.metrics.successful_requests - 1) + current_effectiveness)
                        / self.metrics.successful_requests
                    )

                self.metrics.total_matches += matches_count
                self.metrics.total_no_matches += no_matches_count

                # Track search methods
                for method in search_methods:
                    self.metrics.search_methods_used[method] = self.metrics.search_methods_used.get(method, 0) + 1

            else:
                self.metrics.failed_requests += 1
                if error_type:
                    self.metrics.error_types[error_type] = self.metrics.error_types.get(error_type, 0) + 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics as dictionary"""
        uptime_seconds = time.time() - self.metrics.start_time

        return {
            "uptime_seconds": uptime_seconds,
            "total_requests": self.metrics.total_requests,
            "successful_requests": self.metrics.successful_requests,
            "failed_requests": self.metrics.failed_requests,
            "success_rate": (
                self.metrics.successful_requests / self.metrics.total_requests * 100
                if self.metrics.total_requests > 0 else 0
            ),
            "average_processing_time_ms": self.metrics.average_processing_time_ms,
            "average_effectiveness": self.metrics.average_effectiveness,
            "total_matches": self.metrics.total_matches,
            "total_no_matches": self.metrics.total_no_matches,
            "search_methods_distribution": self.metrics.search_methods_used,
            "error_distribution": self.metrics.error_types,
            "requests_per_second": self.metrics.total_requests / uptime_seconds if uptime_seconds > 0 else 0
        }

    def reset_metrics(self):
        """Reset all metrics (for testing)"""
        self.metrics = ProcessingMetrics()

# Global metrics collector instance
metrics_collector = MetricsCollector()

class MonitoringService:
    """Service for monitoring and health checks"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        metrics = self.metrics_collector.get_metrics()

        # Determine health status based on metrics
        success_rate = metrics["success_rate"]
        avg_processing_time = metrics["average_processing_time_ms"]

        if success_rate < 80 or avg_processing_time > 5000:  # 5 seconds
            status = "unhealthy"
        elif success_rate < 95 or avg_processing_time > 2000:  # 2 seconds
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "timestamp": time.time(),
            "metrics": metrics,
            "version": "2.0.0"
        }

    async def get_detailed_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        return {
            "metrics": self.metrics_collector.get_metrics(),
            "top_search_methods": self._get_top_search_methods(),
            "error_analysis": self._analyze_errors(),
            "performance_trends": await self._get_performance_trends()
        }

    def _get_top_search_methods(self) -> List[Dict[str, Any]]:
        """Get most used search methods"""
        methods = self.metrics_collector.metrics.search_methods_used
        sorted_methods = sorted(methods.items(), key=lambda x: x[1], reverse=True)

        return [
            {"method": method, "count": count, "percentage": count / sum(methods.values()) * 100}
            for method, count in sorted_methods[:5]
        ]

    def _analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        error_types = self.metrics_collector.metrics.error_types

        return {
            "total_errors": sum(error_types.values()),
            "error_rate": sum(error_types.values()) / self.metrics_collector.metrics.total_requests * 100,
            "most_common_errors": sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]
        }

    async def _get_performance_trends(self) -> Dict[str, List[float]]:
        """Get performance trends (placeholder for future implementation)"""
        # In a real implementation, this would track metrics over time
        return {
            "processing_times": [],
            "effectiveness_trend": [],
            "request_volume": []
        }

# Global monitoring service instance
monitoring_service = MonitoringService(metrics_collector)
