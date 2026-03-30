"""
code-review-js 技能

JavaScript/TypeScript 代码审查技能
"""

from .implementation import (
    JavaScriptCodeReviewSkill,
    SeverityLevel,
    review_javascript,
    review_typescript
)

__version__ = "1.0.0"
__author__ = "LingFlow Team"

__all__ = [
    "JavaScriptCodeReviewSkill",
    "SeverityLevel",
    "review_javascript",
    "review_typescript"
]
