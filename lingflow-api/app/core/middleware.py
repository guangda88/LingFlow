"""
中间件模块
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
import logging

from .metrics import request_count, request_duration
from .logging import logger

class MetricsMiddleware(BaseHTTPMiddleware):
    """指标收集中间件"""

    async def dispatch(self, request: Request, call_next):
        # 提取路径
        path = request.url.path
        method = request.method

        # 记录开始时间
        start_time = time.time()

        try:
            # 调用下一个中间件/路由
            response = await call_next(request)

            # 记录指标
            duration = time.time() - start_time
            status = "success"

            request_count.labels(
                method=method,
                endpoint=path,
                status=status
            ).inc()

            request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            return response

        except Exception as e:
            # 记录错误
            duration = time.time() - start_time
            status = "error"

            request_count.labels(
                method=method,
                endpoint=path,
                status=status
            ).inc()

            request_duration.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            # 记录日志
            logger.error(f"Request failed: {method} {path} - {str(e)}")

            # 返回错误响应
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "detail": str(e) if logger.level <= logging.DEBUG else "An error occurred"
                }
            )

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """错误处理中间件"""

    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception(f"Unhandled exception: {str(e)}")

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "Internal server error",
                    "detail": str(e)
                }
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # 记录请求
        logger.info(f"Request: {request.method} {request.url.path}")

        # 处理请求
        response = await call_next(request)

        # 记录响应
        duration = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"- {response.status_code} - {duration:.3f}s"
        )

        return response
