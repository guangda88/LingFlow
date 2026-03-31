"""
AI反馈接口模块

标准化处理来自各种AI工具的反馈，提取有效信息供学习引擎使用。
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolType(Enum):
    """支持的AI工具类型"""
    STATIC_ANALYZER = "static_analyzer"    # 静态分析工具（SonarQube、CodeQL）
    CODE_REVIEW = "code_review"             # 代码审查工具
    SECURITY_SCANNER = "security_scanner"  # 安全扫描工具（Bandit、Snyk）
    PERFORMANCE_ANALYZER = "performance_analyzer"  # 性能分析工具
    LINTING = "linting"                     # 代码规范检查（Pylint、ESLint）
    CUSTOM = "custom"                       # 自定义工具


class SeverityLevel(Enum):
    """问题严重程度"""
    CRITICAL = "critical"   # 严重（安全漏洞、系统崩溃风险）
    HIGH = "high"          # 高（重要功能问题）
    MEDIUM = "medium"      # 中（性能问题、代码质量）
    LOW = "low"            # 低（代码风格、文档）
    INFO = "info"          # 信息（建议、最佳实践）


class FeedbackCategory(Enum):
    """反馈类别"""
    SECURITY = "security"           # 安全相关
    PERFORMANCE = "performance"     # 性能优化
    CODE_QUALITY = "code_quality"   # 代码质量
    MAINTAINABILITY = "maintainability"  # 可维护性
    BEST_PRACTICE = "best_practice"  # 最佳实践
    STYLE = "style"                # 代码风格


@dataclass
class FeedbackItem:
    """单个反馈项"""
    tool_name: str
    tool_type: ToolType
    rule_id: str
    rule_name: str
    category: FeedbackCategory
    severity: SeverityLevel
    message: str
    file_path: str
    line: int
    column: Optional[int] = None
    snippet: Optional[str] = None
    suggestion: Optional[str] = None
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        # 确保时间戳是UTC
        if self.timestamp.tzinfo is None:
            self.timestamp = self.timestamp.replace(tzinfo=datetime.now().astimezone().tzinfo)


class ToolAdapter(ABC):
    """工具适配器抽象基类"""

    @abstractmethod
    def can_handle(self, tool_name: str) -> bool:
        """判断是否可以处理指定的工具"""
        pass

    @abstractmethod
    def parse_feedback(self, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        """解析原始反馈数据"""
        pass

    @abstractmethod
    def get_tool_config(self) -> Dict[str, Any]:
        """获取工具配置"""
        pass


class SonarQubeAdapter(ToolAdapter):
    """SonarQube适配器"""

    def can_handle(self, tool_name: str) -> bool:
        return tool_name.lower() in ['sonarqube', 'sonarcloud']

    def parse_feedback(self, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        """解析SonarQube反馈"""
        items = []

        # 假设raw_data包含issues数组
        for issue in raw_data.get('issues', []):
            try:
                category = self._map_category(issue.get('type', 'CODE_SMELL'))
                severity = self._map_severity(issue.get('severity', 'MINOR'))

                item = FeedbackItem(
                    tool_name='SonarQube',
                    tool_type=ToolType.STATIC_ANALYZER,
                    rule_id=issue.get('rule', ''),
                    rule_name=issue.get('message', ''),
                    category=category,
                    severity=severity,
                    message=issue.get('message', ''),
                    file_path=issue.get('component', '').replace(':', '/'),
                    line=issue.get('line', 1),
                    column=issue.get('column'),
                    snippet=issue.get('context', {}).get('snippet'),
                    suggestion=issue.get('effort', 'No suggestion available'),
                    confidence=0.9,  # SonarQube置信度较高
                    metadata=issue.get('flows', {})
                )
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse SonarQube issue: {e}")

        return items

    def _map_category(self, sonar_type: str) -> FeedbackCategory:
        """映射SonarQube类型到FeedbackCategory"""
        mapping = {
            'BUG': FeedbackCategory.CODE_QUALITY,
            'VULNERABILITY': FeedbackCategory.SECURITY,
            'CODE_SMELL': FeedbackCategory.CODE_QUALITY,
            'SECURITY_HOTSPOT': FeedbackCategory.SECURITY
        }
        return mapping.get(sonar_type, FeedbackCategory.CODE_QUALITY)

    def _map_severity(self, severity: str) -> SeverityLevel:
        """映射SonarQube严重程度"""
        mapping = {
            'BLOCKER': SeverityLevel.CRITICAL,
            'CRITICAL': SeverityLevel.CRITICAL,
            'MAJOR': SeverityLevel.HIGH,
            'MINOR': SeverityLevel.MEDIUM,
            'INFO': SeverityLevel.LOW
        }
        return mapping.get(severity, SeverityLevel.MEDIUM)


class PylintAdapter(ToolAdapter):
    """Pylint适配器"""

    def can_handle(self, tool_name: str) -> bool:
        return tool_name.lower() in ['pylint', 'pylint3']

    def parse_feedback(self, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        """解析Pylint反馈"""
        items = []

        # Pylint输出通常是文本格式，这里假设已解析为JSON
        for message in raw_data.get('messages', []):
            try:
                category = self._map_category(message.get('type', 'convention'))
                severity = self._map_severity(message.get('symbol', 'C0111'))

                item = FeedbackItem(
                    tool_name='Pylint',
                    tool_type=ToolType.LINTING,
                    rule_id=message.get('symbol', ''),
                    rule_name=message.get('message', ''),
                    category=category,
                    severity=severity,
                    message=message.get('message', ''),
                    file_path=message.get('path', ''),
                    line=message.get('line', 1),
                    column=message.get('column', 0),
                    snippet=message.get('text', ''),
                    suggestion=message.get('message', ''),
                    confidence=0.8,  # Pylint置信度中等
                    metadata={
                        'module': message.get('module', ''),
                        'obj': message.get('obj', '')
                    }
                )
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse Pylint message: {e}")

        return items

    def _map_category(self, pylint_type: str) -> FeedbackCategory:
        """映射Pylint类型到FeedbackCategory"""
        mapping = {
            'error': FeedbackCategory.CODE_QUALITY,
            'warning': FeedbackCategory.CODE_QUALITY,
            'refactor': FeedbackCategory.MAINTAINABILITY,
            'convention': FeedbackCategory.STYLE
        }
        return mapping.get(pylint_type, FeedbackCategory.CODE_QUALITY)

    def _map_severity(self, symbol: str) -> SeverityLevel:
        """映射Pylint符号到严重程度"""
        if symbol.startswith('E'):
            return SeverityLevel.HIGH
        elif symbol.startswith('W'):
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW


class BanditAdapter(ToolAdapter):
    """Bandit安全扫描适配器"""

    def can_handle(self, tool_name: str) -> bool:
        return tool_name.lower() in ['bandit', 'bandit-security']

    def parse_feedback(self, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        """解析Bandit反馈"""
        items = []

        for result in raw_data.get('results', []):
            try:
                severity = self._map_severity(result.get('issue_severity', 'MEDIUM'))

                item = FeedbackItem(
                    tool_name='Bandit',
                    tool_type=ToolType.SECURITY_SCANNER,
                    rule_id=result.get('test_id', ''),
                    rule_name=result.get('test_name', ''),
                    category=FeedbackCategory.SECURITY,
                    severity=severity,
                    message=result.get('issue_text', ''),
                    file_path=result.get('filename', ''),
                    line=result.get('line_number', 1),
                    column=result.get('col_offset', 0),
                    snippet=result.get('code', ''),
                    suggestion=result.get('issue_confidence', 'Medium'),
                    confidence=0.95,  # Bandit专门用于安全，置信度高
                    metadata={
                        'confidence': result.get('issue_confidence', 'High'),
                        'more_info': result.get('more_info', '')
                    }
                )
                items.append(item)
            except Exception as e:
                logger.warning(f"Failed to parse Bandit result: {e}")

        return items

    def _map_severity(self, severity: str) -> SeverityLevel:
        """映射Bandit严重程度"""
        mapping = {
            'HIGH': SeverityLevel.CRITICAL,
            'MEDIUM': SeverityLevel.HIGH,
            'LOW': SeverityLevel.MEDIUM
        }
        return mapping.get(severity, SeverityLevel.MEDIUM)


class FeedbackProcessor:
    """反馈处理器"""

    def __init__(self):
        self.adapters: List[ToolAdapter] = [
            SonarQubeAdapter(),
            PylintAdapter(),
            BanditAdapter(),
        ]

    def register_adapter(self, adapter: ToolAdapter):
        """注册新的工具适配器"""
        self.adapters.append(adapter)
        logger.info(f"Registered adapter for {adapter.__class__.__name__}")

    def process_feedback(self, tool_name: str, raw_data: Dict[str, Any]) -> List[FeedbackItem]:
        """处理来自指定工具的反馈"""
        # 查找合适的适配器
        adapter = None
        for a in self.adapters:
            if a.can_handle(tool_name):
                adapter = a
                break

        if not adapter:
            logger.warning(f"No adapter found for tool: {tool_name}")
            return []

        # 解析反馈
        try:
            items = adapter.parse_feedback(raw_data)
            logger.info(f"Processed {len(items)} feedback items from {tool_name}")
            return items
        except Exception as e:
            logger.error(f"Error processing feedback from {tool_name}: {e}")
            return []

    def save_feedback(self, items: List[FeedbackItem], file_path: str):
        """保存反馈到文件"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_items': len(items),
            'items': [item.__dict__ for item in items]
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Saved {len(items)} feedback items to {file_path}")

    def load_feedback(self, file_path: str) -> List[FeedbackItem]:
        """从文件加载反馈"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            items = []
            for item_data in data.get('items', []):
                # 恢复枚举类型
                item_data['tool_type'] = ToolType(item_data['tool_type'])
                item_data['severity'] = SeverityLevel(item_data['severity'])
                item_data['category'] = FeedbackCategory(item_data['category'])
                item_data['timestamp'] = datetime.fromisoformat(item_data['timestamp'])

                items.append(FeedbackItem(**item_data))

            return items
        except Exception as e:
            logger.error(f"Error loading feedback from {file_path}: {e}")
            return []


class FeedbackPriorityCalculator:
    """反馈优先级计算器"""

    def __init__(self):
        # 工具权重（基于历史表现和可信度）
        self.tool_weights = {
            'SonarQube': 1.0,
            'CodeQL': 1.0,
            'Bandit': 1.0,
            'Pylint': 0.9,
            'ESLint': 0.8,
            'Custom': 0.7
        }

        # 类别权重
        self.category_weights = {
            FeedbackCategory.SECURITY: 1.2,
            FeedbackCategory.PERFORMANCE: 1.0,
            FeedbackCategory.CODE_QUALITY: 0.9,
            FeedbackCategory.MAINTAINABILITY: 0.8,
            FeedbackCategory.BEST_PRACTICE: 0.7,
            FeedbackCategory.STYLE: 0.5
        }

    def calculate_priority(self, item: FeedbackItem, frequency: int = 1) -> float:
        """计算反馈优先级分数"""
        # 基础严重程度分数
        severity_scores = {
            SeverityLevel.CRITICAL: 100,
            SeverityLevel.HIGH: 80,
            SeverityLevel.MEDIUM: 60,
            SeverityLevel.LOW: 40,
            SeverityLevel.INFO: 20
        }

        base_score = severity_scores.get(item.severity, 50)

        # 工具权重调整
        tool_weight = self.tool_weights.get(item.tool_name, 0.7)

        # 类别权重调整
        category_weight = self.category_weights.get(item.category, 1.0)

        # 频率因素（相同问题多次出现增加优先级）
        frequency_factor = 1 + (frequency - 1) * 0.3

        # 置信度调整
        confidence_factor = item.confidence

        # 最终分数
        priority_score = (
            base_score *
            tool_weight *
            category_weight *
            frequency_factor *
            confidence_factor
        )

        return round(priority_score, 2)

    def get_tool_weight(self, tool_name: str) -> float:
        """获取工具权重"""
        return self.tool_weights.get(tool_name, 0.7)

    def update_tool_weight(self, tool_name: str, weight: float):
        """更新工具权重"""
        if 0 <= weight <= 1:
            self.tool_weights[tool_name] = weight
            logger.info(f"Updated weight for {tool_name}: {weight}")


def main():
    """测试反馈接口"""
    processor = FeedbackProcessor()
    calculator = FeedbackPriorityCalculator()

    # 模拟SonarQube反馈
    sonar_data = {
        'issues': [
            {
                'rule': 'S1481',
                'message': 'Remove this unused private method',
                'type': 'CODE_SMELL',
                'severity': 'MAJOR',
                'component': 'src/main.py',
                'line': 45,
                'column': 5,
                'context': {'snippet': 'def calculateComplexity(self):'},
                'effort': '30min'
            }
        ]
    }

    # 处理反馈
    items = processor.process_feedback('SonarQube', sonar_data)

    # 计算优先级
    for item in items:
        priority = calculator.calculate_priority(item)
        print(f"Rule: {item.rule_name}, Priority: {priority}")

    # 保存反馈
    processor.save_feedback(items, 'sample_feedback.json')


if __name__ == '__main__':
    main()