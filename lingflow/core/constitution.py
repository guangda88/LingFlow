"""
Constitutional Constraint System

This module implements machine-readable security principles with CWE mappings,
based on the Constitutional Spec-Driven Development research paper.

Key Features:
- Machine-readable security constitution
- CWE/MITRE Top 25 mappings
- Compliance validation
- Multi-level enforcement (MUST/SHOULD/MAY)
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class EnforcementLevel(Enum):
    """Enforcement level for security principles"""

    MUST = "MUST"  # Non-negotiable requirements
    SHOULD = "SHOULD"  # Recommended but with exceptions
    MAY = "MAY"  # Optional guidelines


@dataclass
class ConstitutionalPrinciple:
    """A single constitutional security principle"""

    id: str
    cwe: str
    name: str
    level: EnforcementLevel
    constraint: str
    implementation_pattern: str
    rationale: str

    def __str__(self):
        return f"{self.id}: {self.name} ({self.level.value})"


@dataclass
class Violation:
    """A compliance violation"""

    principle_id: str
    principle_name: str
    severity: EnforcementLevel
    description: str
    location: Optional[str] = None
    line_number: Optional[int] = None
    suggested_fix: Optional[str] = None


@dataclass
class ComplianceReport:
    """Report of compliance validation"""

    is_compliant: bool
    total_principles: int
    compliant_principles: int
    violations: List[Violation] = field(default_factory=list)
    coverage: float = 0.0

    def add_violation(self, violation: Violation):
        """Add a violation to the report"""
        self.violations.append(violation)
        self.is_compliant = False

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "is_compliant": self.is_compliant,
            "total_principles": self.total_principles,
            "compliant_principles": self.compliant_principles,
            "violations_count": len(self.violations),
            "coverage": f"{self.coverage:.2%}",
            "must_violations": sum(
                1 for v in self.violations if v.severity == EnforcementLevel.MUST
            ),
            "should_violations": sum(
                1 for v in self.violations if v.severity == EnforcementLevel.SHOULD
            ),
            "may_violations": sum(1 for v in self.violations if v.severity == EnforcementLevel.MAY),
        }


class Constitution:
    """
    Machine-readable security constitution

    Based on Constitutional Spec-Driven Development research:
    - 73% reduction in security vulnerabilities
    - 4.3x improvement in compliance documentation
    """

    DEFAULT_PRINCIPLES = [
        ConstitutionalPrinciple(
            id="SEC-001",
            cwe="CWE-79",
            name="Cross-Site Scripting (XSS)",
            level=EnforcementLevel.MUST,
            constraint="All user-supplied data MUST be contextually encoded before rendering",
            implementation_pattern="Use JSX auto-escaping, DOMPurify, or equivalent",
            rationale="Prevents malicious script injection through user input",
        ),
        ConstitutionalPrinciple(
            id="SEC-002",
            cwe="CWE-89",
            name="SQL Injection",
            level=EnforcementLevel.MUST,
            constraint="Database queries MUST use parameterized statements or ORM methods exclusively",
            implementation_pattern="SQLAlchemy, parameterized queries, prepared statements",
            rationale="Prevents arbitrary SQL command execution via user input",
        ),
        ConstitutionalPrinciple(
            id="SEC-003",
            cwe="CWE-352",
            name="CSRF",
            level=EnforcementLevel.MUST,
            constraint="All state-changing operations MUST include valid CSRF tokens",
            implementation_pattern="Use SameSite cookies, CSRF token validation",
            rationale="Prevents unauthorized state changes from malicious sites",
        ),
        ConstitutionalPrinciple(
            id="SEC-004",
            cwe="CWE-327",
            name="Weak Cryptographic Algorithms",
            level=EnforcementLevel.MUST,
            constraint="MUST use strong cryptographic algorithms (AES-256, RSA-2048+)",
            implementation_pattern="Use cryptography library, avoid self-implemented encryption",
            rationale="Weak encryption can be easily broken by attackers",
        ),
        ConstitutionalPrinciple(
            id="SEC-005",
            cwe="CWE-798",
            name="Hardcoded Credentials",
            level=EnforcementLevel.MUST,
            constraint="MUST NOT hardcode any credentials or keys in code",
            implementation_pattern="Use environment variables, key management services",
            rationale="Hardcoded credentials are easily discovered and exploited",
        ),
        ConstitutionalPrinciple(
            id="SEC-006",
            cwe="CWE-22",
            name="Path Traversal",
            level=EnforcementLevel.MUST,
            constraint="MUST validate and sanitize all file path inputs",
            implementation_pattern="Use os.path.abspath, validate file paths against allowed directories",
            rationale="Prevents unauthorized file system access",
        ),
        ConstitutionalPrinciple(
            id="SEC-007",
            cwe="CWE-400",
            name="Uncontrolled Resource Consumption",
            level=EnforcementLevel.SHOULD,
            constraint="SHOULD implement rate limiting and resource quotas",
            implementation_pattern="Use rate limiting middleware, set resource limits",
            rationale="Prevents DoS attacks and resource exhaustion",
        ),
        ConstitutionalPrinciple(
            id="SEC-008",
            cwe="CWE-502",
            name="Deserialization of Untrusted Data",
            level=EnforcementLevel.MUST,
            constraint="MUST avoid deserializing untrusted data",
            implementation_pattern="Use safe serialization formats (JSON), validate serialized data",
            rationale="Deserialization can lead to arbitrary code execution",
        ),
        ConstitutionalPrinciple(
            id="SEC-009",
            cwe="CWE-287",
            name="Improper Authentication",
            level=EnforcementLevel.MUST,
            constraint="MUST implement proper authentication mechanisms",
            implementation_pattern="Use session-based or token-based authentication with timeouts",
            rationale="Weak authentication allows unauthorized access",
        ),
        ConstitutionalPrinciple(
            id="SEC-010",
            cwe="CWE-20",
            name="Input Validation",
            level=EnforcementLevel.SHOULD,
            constraint="SHOULD validate all inputs against expected patterns",
            implementation_pattern="Use regex validation, schema validation (e.g., Pydantic)",
            rationale="Input validation reduces attack surface",
        ),
    ]

    def __init__(self, constitution_path: Optional[str] = None):
        """
        Initialize constitution from file or use defaults

        Args:
            constitution_path: Path to YAML constitution file
        """
        self.path = constitution_path
        self.principles: List[ConstitutionalPrinciple] = []

        if constitution_path and Path(constitution_path).exists():
            self._load_from_file(constitution_path)
        else:
            self.principles = self.DEFAULT_PRINCIPLES.copy()

        # Build lookup indexes
        self._principle_by_id = {p.id: p for p in self.principles}
        self._principles_by_cwe = {}
        for p in self.principles:
            if p.cwe not in self._principles_by_cwe:
                self._principles_by_cwe[p.cwe] = []
            self._principles_by_cwe[p.cwe].append(p)
        
        # Cache for compiled regex patterns
        self._compiled_patterns: Dict[str, re.Pattern] = {}

    def _compile_pattern(self, pattern: str) -> re.Pattern:
        """Compile and cache regex patterns for performance"""
        if pattern not in self._compiled_patterns:
            self._compiled_patterns[pattern] = re.compile(pattern, re.IGNORECASE)
        return self._compiled_patterns[pattern]

    def _load_from_file(self, path: str):
        """Load constitution from YAML file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if "principles" in data:
                self.principles = []
                for p_data in data["principles"]:
                    principle = ConstitutionalPrinciple(
                        id=p_data["id"],
                        cwe=p_data["cwe"],
                        name=p_data["name"],
                        level=EnforcementLevel(p_data["level"]),
                        constraint=p_data["constraint"],
                        implementation_pattern=p_data["implementation_pattern"],
                        rationale=p_data["rationale"],
                    )
                    self.principles.append(principle)
        except Exception as e:
            logger.error(f"Error loading constitution from {path}: {e}")
            logger.info("Using default principles")
            self.principles = self.DEFAULT_PRINCIPLES.copy()

    def get_principles(
        self, level: Optional[EnforcementLevel] = None
    ) -> List[ConstitutionalPrinciple]:
        """
        Get principles by enforcement level

        Args:
            level: Filter by enforcement level (MUST/SHOULD/MAY), None for all

        Returns:
            List of principles
        """
        if level:
            return [p for p in self.principles if p.level == level]
        return self.principles.copy()

    def get_principle_by_id(self, principle_id: str) -> Optional[ConstitutionalPrinciple]:
        """Get principle by ID"""
        return self._principle_by_id.get(principle_id)

    def get_principles_by_cwe(self, cwe_id: str) -> List[ConstitutionalPrinciple]:
        """Get principles by CWE identifier"""
        return self._principles_by_cwe.get(cwe_id, [])

    def check_compliance(self, code: str, file_path: str) -> ComplianceReport:
        """
        Check code against constitutional principles

        This performs static analysis to detect violations of security principles.

        Args:
            code: Source code to validate
            file_path: Path to the file (for context)

        Returns:
            ComplianceReport with violations
        """
        report = ComplianceReport(
            is_compliant=True, total_principles=len(self.principles), compliant_principles=0
        )

        # Check each MUST principle (non-negotiable)
        must_principles = self.get_principles(EnforcementLevel.MUST)

        for principle in must_principles:
            violations = self._check_principle(code, principle, file_path)
            if violations:
                for violation in violations:
                    report.add_violation(violation)
            else:
                report.compliant_principles += 1

        # Check SHOULD principles (recommended)
        should_principles = self.get_principles(EnforcementLevel.SHOULD)
        for principle in should_principles:
            violations = self._check_principle(code, principle, file_path)
            if violations:
                for violation in violations:
                    report.add_violation(violation)
            else:
                report.compliant_principles += 1

        # Calculate coverage
        report.coverage = (
            report.compliant_principles / report.total_principles
            if report.total_principles > 0
            else 0
        )

        return report

    def _check_principle(
        self, code: str, principle: ConstitutionalPrinciple, file_path: str
    ) -> List[Violation]:
        """
        Check a single principle against code

        This uses pattern matching to detect violations.
        In production, this would be enhanced with more sophisticated static analysis.

        Args:
            code: Source code
            principle: Principle to check
            file_path: File path for context

        Returns:
            List of violations (empty if compliant)
        """
        violations = []

        # Principle-specific checks
        if principle.cwe == "CWE-79":  # XSS
            violations.extend(self._check_xss(code, principle, file_path))
        elif principle.cwe == "CWE-89":  # SQL Injection
            violations.extend(self._check_sql_injection(code, principle, file_path))
        elif principle.cwe == "CWE-798":  # Hardcoded Credentials
            violations.extend(self._check_hardcoded_credentials(code, principle, file_path))
        elif principle.cwe == "CWE-22":  # Path Traversal
            violations.extend(self._check_path_traversal(code, principle, file_path))
        elif principle.cwe == "CWE-327":  # Weak Crypto
            violations.extend(self._check_weak_crypto(code, principle, file_path))

        return violations

    def _check_xss(
        self, code: str, principle: ConstitutionalPrinciple, file_path: str
    ) -> List[Violation]:
        """Check for XSS vulnerabilities"""
        violations = []

        # Check for dangerous patterns
        dangerous_patterns = [
            r"dangerouslySetInnerHTML",
            r"innerHTML\s*=.*\+",  # innerHTML with user input
            r"document\.write\s*\(",
            r"eval\s*\(",
            r"<script[^>]*>",  # Script tags
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        Violation(
                            principle_id=principle.id,
                            principle_name=principle.name,
                            severity=principle.level,
                            description=f"Potential XSS vulnerability detected: {pattern}",
                            location=file_path,
                            line_number=i,
                            suggested_fix=principle.implementation_pattern,
                        )
                    )
                    break  # One violation per line

        return violations

    def _check_sql_injection(
        self, code: str, principle: ConstitutionalPrinciple, file_path: str
    ) -> List[Violation]:
        """Check for SQL injection vulnerabilities - Enhanced version"""
        violations = []

        # Enhanced dangerous patterns for SQL injection
        dangerous_patterns = [
            # String concatenation
            r'execute\s*\(\s*["\'].*SELECT.*\+\s*\w',
            r'query\s*\(\s*["\'].*SELECT.*\+\s*\w',
            r'cursor\.execute\s*\(\s*["\'].*\+\s*',
            # f-strings with SQL
            r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER).*\{',
            # format method
            r'\.format\s*\(\s*.*(?:SELECT|INSERT|UPDATE|DELETE)',
            # % formatting
            r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE).*%\s*\w',
        ]

        # Safe patterns (parameterized queries)
        safe_patterns = [
            r'%s',           # PostgreSQL/MySQL placeholder
            r'%\(\w+\)s',  # Named placeholder
            r':\w+',         # SQLite/PostgreSQL named param
            r'\?',           # SQLite/MySQL positional param
            r'\$\d+',        # PostgreSQL positional param
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in dangerous_patterns:
                compiled = self._compile_pattern(pattern)
                if compiled.search(line):
                    # Check if it's a safe parameterized query
                    is_safe = any(re.search(safe, line) for safe in safe_patterns)
                    
                    # Also check for common safe function names
                    if any(safe_func in line for safe_func in ['escape', 'quote', 'parameterize']):
                        is_safe = True
                    
                    if not is_safe:
                        violations.append(
                            Violation(
                                principle_id=principle.id,
                                principle_name=principle.name,
                                severity=principle.level,
                                description=f"Potential SQL injection vulnerability: {line.strip()}",
                                location=file_path,
                                line_number=i,
                                suggested_fix=principle.implementation_pattern,
                            )
                        )
                    break

        return violations

    def _check_hardcoded_credentials(
        self, code: str, principle: ConstitutionalPrinciple, file_path: str
    ) -> List[Violation]:
        """Check for hardcoded credentials"""
        violations = []

        # Check for suspicious patterns
        dangerous_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',  # password = "value"
            r'secret\s*=\s*["\'][^"\']+["\']',  # secret = "value"
            r'api_key\s*=\s*["\'][^"\']+["\']',  # api_key = "value"
            r'token\s*=\s*["\'][^"\']+["\']',  # token = "value"
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Skip comments and environment variable references
                    if "#" in line or "$" in line or "os.environ" in line:
                        continue

                    violations.append(
                        Violation(
                            principle_id=principle.id,
                            principle_name=principle.name,
                            severity=principle.level,
                            description="Potential hardcoded credential detected",
                            location=file_path,
                            line_number=i,
                            suggested_fix=principle.implementation_pattern,
                        )
                    )
                    break

        return violations

    def _check_path_traversal(
        self, code: str, principle: ConstitutionalPrinciple, file_path: str
    ) -> List[Violation]:
        """Check for path traversal vulnerabilities"""
        violations = []

        # Check for dangerous file operations
        dangerous_patterns = [
            r"open\s*\(\s*\+\s*",  # open( + variable)
            r'open\s*\(\s*["\'].*\+\s*',  # open("path" + variable)
            r"\.read\s*\(\s*\+\s*",  # read( + variable)
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for pattern in dangerous_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    # Check if there's validation
                    if "validate" in line or "sanitize" in line or "os.path.abspath" in line:
                        continue

                    violations.append(
                        Violation(
                            principle_id=principle.id,
                            principle_name=principle.name,
                            severity=principle.level,
                            description="Potential path traversal vulnerability detected",
                            location=file_path,
                            line_number=i,
                            suggested_fix=principle.implementation_pattern,
                        )
                    )
                    break

        return violations

    def _check_weak_crypto(
        self, code: str, principle: ConstitutionalPrinciple, file_path: str
    ) -> List[Violation]:
        """Check for weak cryptographic algorithms"""
        violations = []

        # Check for weak algorithms
        weak_algorithms = [
            r"MD5",
            r"SHA1",
            r"DES",
            r"RC4",
            r"Blowfish",
        ]

        lines = code.split("\n")
        for i, line in enumerate(lines, 1):
            for algo in weak_algorithms:
                if re.search(algo, line, re.IGNORECASE):
                    # Skip comments
                    if "#" in line:
                        continue

                    violations.append(
                        Violation(
                            principle_id=principle.id,
                            principle_name=principle.name,
                            severity=principle.level,
                            description=f"Weak cryptographic algorithm detected: {algo}",
                            location=file_path,
                            line_number=i,
                            suggested_fix=principle.implementation_pattern,
                        )
                    )
                    break

        return violations

    def get_applicable_principles(self, context: Dict[str, Any]) -> List[ConstitutionalPrinciple]:
        """
        Get principles applicable to a specific context

        Args:
            context: Context information (e.g., file type, technology stack)

        Returns:
            List of applicable principles
        """
        # Filter based on context
        # For now, return all principles
        # In production, this would be smarter (e.g., web apps need XSS protection)
        return self.principles.copy()

    def generate_compliance_documentation(self, code: str, file_path: str) -> str:
        """
        Generate compliance documentation for code

        This is useful for audit trails and demonstrating compliance.

        Args:
            code: Source code
            file_path: File path

        Returns:
            Markdown-formatted compliance documentation
        """
        report = self.check_compliance(code, file_path)

        lines = [
            f"# Compliance Report for {file_path}",
            "",
            f"**Generated**: {report.is_compliant}",
            f"**Coverage**: {report.coverage:.2%}",
            f"**Compliant Principles**: {report.compliant_principles}/{report.total_principles}",
            "",
            "## Violations",
            "",
        ]

        if not report.violations:
            lines.append("✅ No violations detected")
        else:
            for violation in report.violations:
                lines.extend(
                    [
                        f"### {violation.principle_id}: {violation.principle_name}",
                        f"- **Severity**: {violation.severity.value}",
                        f"- **Location**: {violation.location}:{violation.line_number}",
                        f"- **Description**: {violation.description}",
                        f"- **Suggested Fix**: {violation.suggested_fix}",
                        "",
                    ]
                )

        return "\n".join(lines)
