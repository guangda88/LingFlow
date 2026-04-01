"""MCP 运维监控工具

提供系统健康检查、性能指标和异常检测功能。
"""

import asyncio
import logging
import os
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.metrics_history = []
        self.max_history = 100

    async def get_health_status(
        self,
        checks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """获取系统健康状态

        Args:
            checks: 要执行的检查列表（可选）

        Returns:
            健康状态报告
        """
        if checks is None:
            checks = ["disk", "memory", "cpu", "python", "lingflow"]

        results = {}
        overall_status = "healthy"

        for check in checks:
            try:
                if check == "disk":
                    result = await self._check_disk()
                elif check == "memory":
                    result = await self._check_memory()
                elif check == "cpu":
                    result = await self._check_cpu()
                elif check == "python":
                    result = await self._check_python()
                elif check == "lingflow":
                    result = await self._check_lingflow()
                else:
                    result = {
                        "status": "unknown",
                        "message": f"未知检查类型: {check}",
                    }

                results[check] = result

                if result.get("status") in ["warning", "critical"]:
                    overall_status = result["status"]

            except Exception as e:
                logger.error(f"健康检查失败 {check}: {e}")
                results[check] = {
                    "status": "error",
                    "error": str(e),
                }
                overall_status = "critical"

        return {
            "success": True,
            "overall_status": overall_status,
            "checks": results,
            "timestamp": datetime.now().isoformat(),
        }

    async def _check_disk(self) -> Dict[str, Any]:
        """检查磁盘状态"""
        try:
            disk = psutil.disk_usage('/')

            used_percent = (disk.used / disk.total) * 100

            if used_percent > 90:
                status = "critical"
            elif used_percent > 75:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "used_percent": round(used_percent, 2),
                "free_gb": round(disk.free / (1024**3), 2),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _check_memory(self) -> Dict[str, Any]:
        """检查内存状态"""
        try:
            mem = psutil.virtual_memory()

            if mem.percent > 90:
                status = "critical"
            elif mem.percent > 75:
                status = "warning"
            else:
                status = "healthy"

            return {
                "status": status,
                "used_gb": round(mem.used / (1024**3), 2),
                "total_gb": round(mem.total / (1024**3), 2),
                "used_percent": mem.percent,
                "available_gb": round(mem.available / (1024**3), 2),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _check_cpu(self) -> Dict[str, Any]:
        """检查 CPU 状态"""
        try:
            # 获取 CPU 使用率（1秒平均值）
            cpu_percent = psutil.cpu_percent(interval=1)

            if cpu_percent > 90:
                status = "critical"
            elif cpu_percent > 75:
                status = "warning"
            else:
                status = "healthy"

            # 获取 CPU 核心数
            cpu_count = psutil.cpu_count()

            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _check_python(self) -> Dict[str, Any]:
        """检查 Python 环境"""
        try:
            import sys

            version = sys.version_info

            return {
                "status": "healthy",
                "python_version": f"{version.major}.{version.minor}.{version.micro}",
                "executable": sys.executable,
                "path": sys.path[:3],  # 前3个路径
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _check_lingflow(self) -> Dict[str, Any]:
        """检查 LingFlow 状态"""
        try:
            # 尝试导入 LingFlow
            from lingflow import __version__

            # 检查工作目录
            work_dir = Path.cwd()

            # 检查配置文件
            config_files = [
                work_dir / ".lingflow" / "config.yaml",
                work_dir / "lingflow.yaml",
            ]

            config_exists = any(f.exists() for f in config_files)

            return {
                "status": "healthy",
                "version": __version__,
                "work_directory": str(work_dir),
                "config_exists": config_exists,
            }

        except ImportError as e:
            return {
                "status": "warning",
                "error": "LingFlow 未安装",
                "details": str(e),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def get_metrics(
        self,
        metric_names: Optional[List[str]] = None,
        time_range: str = "1h",
    ) -> Dict[str, Any]:
        """获取性能指标

        Args:
            metric_names: 指标名称列表（可选）
            time_range: 时间范围 (1h, 6h, 24h)

        Returns:
            性能指标数据
        """
        try:
            if metric_names is None:
                metric_names = ["cpu", "memory", "disk", "process"]

            metrics = {}

            for name in metric_names:
                if name == "cpu":
                    metrics[name] = await self._get_cpu_metrics()
                elif name == "memory":
                    metrics[name] = await self._get_memory_metrics()
                elif name == "disk":
                    metrics[name] = await self._get_disk_metrics()
                elif name == "process":
                    metrics[name] = await self._get_process_metrics()
                else:
                    metrics[name] = {"error": f"未知指标: {name}"}

            # 保存到历史
            self.metrics_history.append({
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
            })

            # 限制历史大小
            if len(self.metrics_history) > self.max_history:
                self.metrics_history = self.metrics_history[-self.max_history:]

            return {
                "success": True,
                "metrics": metrics,
                "time_range": time_range,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"获取指标失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _get_cpu_metrics(self) -> Dict[str, Any]:
        """获取 CPU 指标"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # 获取每个核心的使用率
        cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

        return {
            "overall_percent": cpu_percent,
            "core_count": cpu_count,
            "per_core": cpu_per_core,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
        }

    async def _get_memory_metrics(self) -> Dict[str, Any]:
        """获取内存指标"""
        mem = psutil.virtual_memory()

        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent": mem.percent,
            "cached_gb": round(mem.cached / (1024**3), 2) if hasattr(mem, 'cached') else 0,
        }

    async def _get_disk_metrics(self) -> Dict[str, Any]:
        """获取磁盘指标"""
        disk = psutil.disk_usage('/')

        # 获取 I/O 统计
        try:
            io_counters = psutil.disk_io_counters()
            io_stats = {
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count,
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes,
            }
        except:
            io_stats = {}

        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": (disk.used / disk.total) * 100,
            "io_stats": io_stats,
        }

    async def _get_process_metrics(self) -> Dict[str, Any]:
        """获取进程指标"""
        process = psutil.Process()

        return {
            "pid": process.pid,
            "name": process.name(),
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "num_threads": process.num_threads(),
            "create_time": datetime.fromtimestamp(process.create_time()).isoformat(),
        }

    async def detect_anomaly(
        self,
        metric_name: str,
        value: Optional[float] = None,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """检测异常

        Args:
            metric_name: 指标名称
            value: 当前值（可选，如果不提供则自动获取）
            threshold: 阈值（可选）

        Returns:
            异常检测结果
        """
        try:
            # 获取当前值（如果未提供）
            if value is None:
                metrics = await self.get_metrics(metric_names=[metric_name])
                metric_data = metrics["metrics"].get(metric_name, {})

                if metric_name == "cpu":
                    value = metric_data.get("overall_percent", 0)
                elif metric_name == "memory":
                    value = metric_data.get("percent", 0)
                elif metric_name == "disk":
                    value = metric_data.get("percent", 0)
                else:
                    return {
                        "success": False,
                        "error": f"无法自动获取指标: {metric_name}",
                    }

            # 分析历史数据
            if len(self.metrics_history) >= 5:
                recent_values = [
                    m["metrics"].get(metric_name, {}).get("value", value)
                    for m in self.metrics_history[-5:]
                ]

                # 计算平均值和标准差
                import statistics

                avg = statistics.mean(recent_values)
                stdev = statistics.stdev(recent_values) if len(recent_values) > 1 else 0

                # 检测异常（3-sigma 规则）
                if stdev > 0:
                    z_score = abs((value - avg) / stdev)
                    is_anomaly = z_score > 3
                else:
                    z_score = 0
                    is_anomaly = False

                # 阈值检测
                if threshold is not None:
                    threshold_exceeded = value > threshold
                else:
                    threshold_exceeded = False

                # 综合判断
                is_anomaly = is_anomaly or threshold_exceeded

                return {
                    "success": True,
                    "metric_name": metric_name,
                    "current_value": value,
                    "is_anomaly": is_anomaly,
                    "analysis": {
                        "average": round(avg, 2),
                        "stdev": round(stdev, 2),
                        "z_score": round(z_score, 2),
                        "threshold_exceeded": threshold_exceeded,
                    },
                    "recommendation": self._get_recommendation(metric_name, value),
                }

            else:
                # 历史数据不足，使用简单阈值
                return {
                    "success": True,
                    "metric_name": metric_name,
                    "current_value": value,
                    "is_anomaly": False,
                    "message": "历史数据不足，无法进行异常检测",
                }

        except Exception as e:
            logger.error(f"异常检测失败: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _get_recommendation(self, metric_name: str, value: float) -> str:
        """获取优化建议"""
        recommendations = {
            "cpu": {
                "high": "CPU 使用率过高，建议检查是否有计算密集型进程",
                "medium": "CPU 使用率较高，建议优化算法或增加并行度",
            },
            "memory": {
                "high": "内存使用率过高，建议检查内存泄漏或增加内存",
                "medium": "内存使用率较高，建议优化内存使用",
            },
            "disk": {
                "high": "磁盘使用率过高，建议清理日志文件或扩展存储",
                "medium": "磁盘使用率较高，建议关注剩余空间",
            },
        }

        if metric_name in recommendations:
            if value > 90:
                return recommendations[metric_name]["high"]
            elif value > 75:
                return recommendations[metric_name]["medium"]

        return "指标正常"
