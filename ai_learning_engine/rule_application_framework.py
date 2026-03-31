"""
规则应用框架

管理规则的应用过程，支持自动应用和人工审核，确保规则的安全部署。
"""

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import uuid

from .rule_learning_engine import LearnedRule, LearningStatus
from .rule_validation_system import ValidationManager, ValidationType, ValidationReport

logger = logging.getLogger(__name__)


class ApplicationMode(Enum):
    """应用模式"""
    AUTO = "auto"            # 自动应用
    MANUAL_REVIEW = "manual"  # 人工审核
    HYBRID = "hybrid"        # 混合模式（低优先级自动，高优先级人工）


class ApplicationStatus(Enum):
    """应用状态"""
    PENDING = "pending"      # 等待应用
    QUEUED = "queued"        # 已排队
    PROCESSING = "processing" # 处理中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 应用失败
    ROLLED_BACK = "rolled_back" # 已回滚


@dataclass
class ApplicationRequest:
    """应用请求"""
    id: str
    rule_id: str
    target_files: List[str]
    mode: ApplicationMode
    priority: int
    requested_by: str
    created_at: datetime = field(default_factory=datetime.now)
    status: ApplicationStatus = ApplicationStatus.PENDING
    execution_log: List[str] = field(default_factory=list)
    validation_results: Dict[str, ValidationReport] = field(default_factory=dict)
    rollback_info: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'target_files': self.target_files,
            'mode': self.mode.value,
            'priority': self.priority,
            'requested_by': self.requested_by,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'execution_log': self.execution_log,
            'validation_results': {
                k: v.to_dict() for k, v in self.validation_results.items()
            },
            'rollback_info': self.rollback_info
        }


@dataclass
class ApplicationResult:
    """应用结果"""
    request_id: str
    success: bool
    applied_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    changes_made: int = 0
    errors: List[str] = field(default_factory=list)
    rollback_required: bool = False


class RuleApplier(ABC):
    """规则应用器抽象基类"""

    @abstractmethod
    def apply_rule(self, rule: LearnedRule, file_path: str) -> Tuple[bool, str]:
        """应用规则到单个文件"""
        pass

    @abstractmethod
    def get_rule_diff(self, rule: LearnedRule, file_path: str) -> str:
        """获取应用规则后的代码差异"""
        pass


class SimpleRuleApplier(RuleApplier):
    """简单规则应用器"""

    def apply_rule(self, rule: LearnedRule, file_path: str) -> Tuple[bool, str]:
        """应用规则"""
        try:
            with open(file_path, 'r') as f:
                original_content = f.read()

            # 应用规则
            modified_content = self._apply_rule_to_content(original_content, rule)

            if original_content == modified_content:
                return True, "No changes needed"

            # 写入文件
            with open(file_path, 'w') as f:
                f.write(modified_content)

            return True, "Rule applied successfully"

        except Exception as e:
            return False, f"Failed to apply rule: {str(e)}"

    def get_rule_diff(self, rule: LearnedRule, file_path: str) -> str:
        """获取代码差异"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            modified_content = self._apply_rule_to_content(content, rule)

            # 使用difflib生成差异
            import difflib
            diff = difflib.unified_diff(
                content.splitlines(keepends=True),
                modified_content.splitlines(keepends=True),
                fromfile='original',
                tofile='modified'
            )
            return ''.join(diff)

        except Exception as e:
            return f"Error generating diff: {str(e)}"

    def _apply_rule_to_content(self, content: str, rule: LearnedRule) -> str:
        """应用规则到内容"""
        # 根据规则类型应用相应的修改
        if rule.category.value == "code_quality":
            return self._apply_quality_rule(content, rule)
        elif rule.category.value == "security":
            return self._apply_security_rule(content, rule)
        else:
            # 默认不修改内容
            return content

    def _apply_quality_rule(self, content: str, rule: LearnedRule) -> str:
        """应用代码质量规则"""
        lines = content.split('\n')
        new_lines = []

        i = 0
        while i < len(lines):
            line = lines[i]

            # 移除空函数
            if line.strip().startswith('def ') and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line == '' or next_line.startswith('#'):
                    # 找到函数的结束位置
                    j = i + 1
                    while j < len(lines) and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                        j += 1

                    # 跳过空函数
                    i = j
                    continue

            new_lines.append(line)
            i += 1

        return '\n'.join(new_lines)

    def _apply_security_rule(self, content: str, rule: LearnedRule) -> str:
        """应用安全规则"""
        # 替换eval为ast.literal_eval
        content = content.replace('eval(', 'ast.literal_eval(')
        return content


class ReviewRequest:
    """人工审核请求"""

    def __init__(self, request: ApplicationRequest):
        self.request = request
        self.created_at = datetime.now()
        self.status = "pending"
        self.reviewer = None
        self.review_notes = ""
        self.approved = False
        self.rejection_reason = ""

    def approve(self, reviewer: str, notes: str = ""):
        """批准申请"""
        self.status = "approved"
        self.reviewer = reviewer
        self.review_notes = notes
        self.approved = True
        self.request.status = ApplicationStatus.QUEUED

    def reject(self, reviewer: str, reason: str):
        """拒绝申请"""
        self.status = "rejected"
        self.reviewer = reviewer
        self.rejection_reason = reason
        self.request.status = ApplicationStatus.FAILED


class ManualReviewSystem:
    """人工审核系统"""

    def __init__(self):
        self.pending_requests: Dict[str, ReviewRequest] = {}
        self.reviewer_pool: List[str] = []

    def create_review_request(self, request: ApplicationRequest) -> ReviewRequest:
        """创建审核请求"""
        review_request = ReviewRequest(request)
        self.pending_requests[request.id] = review_request
        return review_request

    def get_pending_requests(self, reviewer: str = None) -> List[ReviewRequest]:
        """获取待审核请求"""
        if reviewer:
            return [req for req in self.pending_requests.values()
                    if req.status == "pending"]
        return [req for req in self.pending_requests.values()
                if req.status == "pending"]

    def get_request_details(self, request_id: str) -> Optional[ReviewRequest]:
        """获取审核请求详情"""
        return self.pending_requests.get(request_id)

    def approve_request(self, request_id: str, reviewer: str, notes: str = ""):
        """批准审核请求"""
        if request_id in self.pending_requests:
            self.pending_requests[request_id].approve(reviewer, notes)

    def reject_request(self, request_id: str, reviewer: str, reason: str):
        """拒绝审核请求"""
        if request_id in self.pending_requests:
            self.pending_requests[request_id].reject(reviewer, reason)

    def get_review_statistics(self) -> Dict[str, Any]:
        """获取审核统计"""
        total = len(self.pending_requests)
        approved = sum(1 for req in self.pending_requests.values() if req.approved)
        rejected = sum(1 for req in self.pending_requests.values() if not req.approved)

        return {
            'total_requests': total,
            'approved': approved,
            'rejected': rejected,
            'pending': total - approved - rejected,
            'approval_rate': approved / total if total > 0 else 0
        }


class ApplicationScheduler:
    """应用调度器"""

    def __init__(self):
        self.queue: List[ApplicationRequest] = []
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()

    def schedule_application(self, request: ApplicationRequest):
        """安排规则应用"""
        with self.lock:
            # 根据优先级插入队列
            inserted = False
            for i, existing in enumerate(self.queue):
                if request.priority > existing.priority:
                    self.queue.insert(i, request)
                    inserted = True
                    break

            if not inserted:
                self.queue.append(request)

            if not self.running:
                self.start_worker()

        logger.info(f"Scheduled application request {request.id} with priority {request.priority}")

    def start_worker(self):
        """启动工作线程"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_queue)
            self.worker_thread.daemon = True
            self.worker_thread.start()

    def _process_queue(self):
        """处理应用队列"""
        while self.running:
            with self.lock:
                if not self.queue:
                    time.sleep(1)
                    continue

                request = self.queue.pop(0)

            # 处理应用请求
            self._process_application(request)

    def _process_application(self, request: ApplicationRequest):
        """处理单个应用请求"""
        logger.info(f"Processing application request {request.id}")

        request.status = ApplicationStatus.PROCESSING
        request.execution_log.append(f"Started processing at {datetime.now().isoformat()}")

        try:
            # 执行应用
            applier = SimpleRuleApplier()
            results = []

            for file_path in request.target_files:
                start_time = time.time()
                success, message = applier.apply_rule(request.rule_id, file_path)
                execution_time = time.time() - start_time

                result = {
                    'file': file_path,
                    'success': success,
                    'message': message,
                    'execution_time': execution_time
                }
                results.append(result)

                request.execution_log.append(f"Applied to {file_path}: {'SUCCESS' if success else 'FAILED'} - {message}")

            # 记录结果
            success_count = sum(1 for r in results if r['success'])
            request.execution_log.append(f"Completed: {success_count}/{len(request.target_files)} files processed")

            # 更新状态
            if success_count == len(request.target_files):
                request.status = ApplicationStatus.COMPLETED
            else:
                request.status = ApplicationStatus.FAILED

        except Exception as e:
            request.status = ApplicationStatus.FAILED
            request.execution_log.append(f"Error: {str(e)}")

    def stop_worker(self):
        """停止工作线程"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join()


class RuleApplicationManager:
    """规则应用管理器"""

    def __init__(self, auto_apply_threshold: float = 0.8):
        self.auto_apply_threshold = auto_apply_threshold
        self.validation_manager = ValidationManager()
        self.scheduler = ApplicationScheduler()
        self.manual_review_system = ManualReviewSystem()
        self.applier = SimpleRuleApplier()
        self.request_history: Dict[str, ApplicationRequest] = {}

    def submit_application_request(self, rule: LearnedRule, target_files: List[str],
                                  mode: ApplicationMode = ApplicationMode.HYBRID,
                                  requested_by: str = "system") -> str:
        """提交应用请求"""
        # 创建请求ID
        request_id = str(uuid.uuid4())

        # 创建应用请求
        request = ApplicationRequest(
            id=request_id,
            rule_id=rule.id,
            target_files=target_files,
            mode=mode,
            priority=self._calculate_priority(rule),
            requested_by=requested_by
        )

        # 保存到历史记录
        self.request_history[request_id] = request

        # 根据模式处理
        if mode == ApplicationMode.AUTO:
            # 自动应用前需要验证
            validation_results = self.validation_manager.validate_rule(rule)
            request.validation_results = validation_results

            # 检查是否可以通过自动验证
            if self._should_auto_apply(rule, validation_results):
                self.scheduler.schedule_application(request)
            else:
                request.status = ApplicationStatus.FAILED
                request.execution_log.append("Auto application rejected by validation")

        elif mode == ApplicationMode.MANUAL_REVIEW:
            # 创建人工审核请求
            review_request = self.manual_review_system.create_review_request(request)
            request.status = ApplicationStatus.QUEUED

        else:  # HYBRID
            # 混合模式：低优先级自动，高优先级人工
            validation_results = self.validation_manager.validate_rule(rule)
            request.validation_results = validation_results

            if rule.quality_score >= self.auto_apply_threshold and \
               self._validation_passed(validation_results):
                self.scheduler.schedule_application(request)
            else:
                review_request = self.manual_review_system.create_review_request(request)
                request.status = ApplicationStatus.QUEUED

        return request_id

    def _calculate_priority(self, rule: LearnedRule) -> int:
        """计算应用优先级"""
        # 基础优先级
        base_priority = 50

        # 根据质量分数调整
        quality_priority = int(rule.quality_score * 30)

        # 根据频率调整
        frequency_priority = min(rule.frequency * 2, 20)

        # 根据类别调整
        category_priority = {
            "security": 30,
            "performance": 20,
            "code_quality": 15,
            "maintainability": 10,
            "best_practice": 5,
            "style": 0
        }.get(rule.category.value, 10)

        total_priority = base_priority + quality_priority + frequency_priority + category_priority

        return min(total_priority, 100)

    def _should_auto_apply(self, rule: LearnedRule, validation_results: Dict) -> bool:
        """判断是否自动应用"""
        # 检查验证结果
        if not self._validation_passed(validation_results):
            return False

        # 检查规则质量
        if rule.quality_score < self.auto_apply_threshold:
            return False

        # 安全性必须通过
        safety_result = validation_results.get(ValidationType.SAFETY)
        if safety_result and not safety_result.is_safe:
            return False

        return True

    def _validation_passed(self, validation_results: Dict) -> bool:
        """检查验证是否通过"""
        for report in validation_results.values():
            if report.status.value == "failed":
                return False
        return True

    def get_application_status(self, request_id: str) -> Optional[ApplicationRequest]:
        """获取应用状态"""
        return self.request_history.get(request_id)

    def cancel_application(self, request_id: str) -> bool:
        """取消应用"""
        request = self.request_history.get(request_id)
        if request and request.status in [ApplicationStatus.PENDING, ApplicationStatus.QUEUED]:
            request.status = ApplicationStatus.FAILED
            request.execution_log.append("Application cancelled")
            return True
        return False

    def review_application(self, request_id: str, reviewer: str, approved: bool, notes: str = "") -> bool:
        """审核应用请求"""
        request = self.request_history.get(request_id)
        if not request:
            return False

        if approved:
            self.manual_review_system.approve_request(request_id, reviewer, notes)
            self.scheduler.schedule_application(request)
        else:
            self.manual_review_system.reject_request(request_id, reviewer, notes)

        return True

    def get_application_history(self, limit: int = 50) -> List[Dict]:
        """获取应用历史"""
        # 按时间排序
        sorted_requests = sorted(
            self.request_history.values(),
            key=lambda r: r.created_at,
            reverse=True
        )

        # 返回指定数量的结果
        return [req.to_dict() for req in sorted_requests[:limit]]

    def get_system_statistics(self) -> Dict[str, Any]:
        """获取系统统计"""
        total_requests = len(self.request_history)
        completed = sum(1 for r in self.request_history.values() if r.status == ApplicationStatus.COMPLETED)
        failed = sum(1 for r in self.request_history.values() if r.status == ApplicationStatus.FAILED)

        # 获取审核统计
        review_stats = self.manual_review_system.get_review_statistics()

        return {
            'total_requests': total_requests,
            'completed_requests': completed,
            'failed_requests': failed,
            'success_rate': completed / total_requests if total_requests > 0 else 0,
            'review_statistics': review_stats,
            'queue_size': len(self.scheduler.queue)
        }


def main():
    """测试应用框架"""
    # 创建应用管理器
    manager = RuleApplicationManager()

    # 创建测试规则
    from .rule_learning_engine import LearnedRule, Pattern, FeedbackCategory

    rule = LearnedRule(
        id="TEST001",
        name="Remove Unused Functions",
        description="Remove unused functions to improve code quality",
        category=FeedbackCategory.CODE_QUALITY,
        pattern=Pattern(file_patterns=["py"], code_patterns=["def "]),
        tools=["SonarQube"],
        frequency=10,
        confidence=0.9,
        status=LearningStatus.VALIDATED,
        quality_score=0.85
    )

    # 提交应用请求
    request_id = manager.submit_application_request(
        rule,
        ["test_file.py"],
        mode=ApplicationMode.MANUAL_REVIEW,
        requested_by="developer"
    )

    print(f"Submitted application request: {request_id}")

    # 模拟审核
    time.sleep(2)  # 等待处理

    # 获取状态
    status = manager.get_application_status(request_id)
    if status:
        print(f"Request status: {status.status.value}")

    # 获取系统统计
    stats = manager.get_system_statistics()
    print(f"System statistics: {stats}")


if __name__ == '__main__':
    main()