"""
Prometheus 指标导出模块
"""
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from typing import Dict

# 定义指标
request_count = Counter(
    'lingflow_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'lingflow_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint']
)

skill_execution_count = Counter(
    'lingflow_skill_executions_total',
    'Total skill executions',
    ['skill_name', 'status']
)

skill_execution_duration = Histogram(
    'lingflow_skill_execution_duration_seconds',
    'Skill execution duration',
    ['skill_name']
)

workflow_execution_count = Counter(
    'lingflow_workflow_executions_total',
    'Total workflow executions',
    ['workflow_id', 'status']
)

active_tasks = Gauge(
    'lingflow_active_tasks',
    'Number of active tasks'
)

# 存储开始时间
request_start_time: Dict[str, float] = {}

def metrics_handler() -> Response:
    """Prometheus metrics 端点"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# 上下文管理器
class RequestMetrics:
    """请求指标上下文管理器"""

    def __init__(self, method: str, endpoint: str):
        self.method = method
        self.endpoint = endpoint
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = "success" if exc_type is None else "error"

        request_count.labels(
            method=self.method,
            endpoint=self.endpoint,
            status=status
        ).inc()

        request_duration.labels(
            method=self.method,
            endpoint=self.endpoint
        ).observe(duration)
