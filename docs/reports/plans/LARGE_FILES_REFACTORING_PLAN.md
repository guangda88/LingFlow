# Large Files Refactoring Plan

**Date**: 2026-03-31
**Author**: LingFlow Development Team
**Version**: 1.0

## Executive Summary

This document outlines the refactoring strategy for three large files in the LingFlow project that exceed the recommended 500-line limit. The plan focuses on modularization, separation of concerns, and maintaining backward compatibility while improving code maintainability.

### Files Analyzed

| File | Lines | Status | Priority |
|------|-------|--------|----------|
| `skills/deployment-automation/implementation.py` | 1,264 | **Critical** | P0 |
| `lingflow_v4_example.py` | 1,041 | **High** | P1 |
| `skills/api-doc-generator/implementation.py` | 969 | **High** | P1 |

---

## 1. deployment-automation/implementation.py (1,264 lines)

### Current Structure Analysis

The file contains multiple responsibilities:

1. **Template Definitions** (Lines 31-727): ~700 lines
   - Dockerfile templates (5 variants)
   - Kubernetes manifests (7 templates)
   - Blue-green deployment templates
   - CI/CD pipeline templates (GitLab, GitHub)

2. **Core Functions** (Lines 730-1265): ~535 lines
   - `execute_skill()` - Main entry point
   - `_generate_dockerfile()` - Dockerfile generation
   - `_generate_k8s_configs()` - Kubernetes config generation
   - `_generate_blue_green()` - Blue-green deployment
   - `_generate_rollback_script()` - Rollback scripts
   - `_generate_ci_cd()` - CI/CD configuration
   - `detect_project_type()` - Project type detection

### Issues Identified

1. **Single Responsibility Violation**: Templates, generation logic, and orchestration mixed
2. **Hardcoded Templates**: Large template strings embedded in code
3. **Difficult Testing**: Cannot test templates independently
4. **Maintenance Burden**: Adding new template types requires modifying main file
5. **Code Duplication**: Similar formatting logic across different generators

### Refactoring Strategy

#### Phase 1: Extract Templates (Low Risk)

**Action**: Move all templates to separate files in a `templates/` subdirectory

**New Structure**:
```
skills/deployment-automation/
├── implementation.py          (~200 lines - orchestration only)
├── templates/
│   ├── __init__.py
│   ├── dockerfiles/
│   │   ├── __init__.py
│   │   ├── python.py
│   │   ├── nodejs.py
│   │   ├── go.py
│   │   ├── java.py
│   │   └── static.py
│   ├── kubernetes/
│   │   ├── __init__.py
│   │   ├── deployment.py
│   │   ├── service.py
│   │   ├── ingress.py
│   │   ├── hpa.py
│   │   ├── configmap.py
│   │   └── secret.py
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── blue_green.py
│   │   └── rolling.py
│   └── cicd/
│       ├── __init__.py
│       ├── gitlab.py
│       └── github.py
├── generators/
│   ├── __init__.py
│   ├── dockerfile.py
│   ├── kubernetes.py
│   ├── strategies.py
│   └── cicd.py
└── utils/
    ├── __init__.py
    └── detector.py
```

**Benefits**:
- Reduces main file by ~700 lines
- Templates can be edited independently
- Easier to add new templates
- Templates can be validated/tested separately

#### Phase 2: Extract Generators (Medium Risk)

**Action**: Create generator classes for each output type

**New File Structure**:

**`generators/dockerfile.py`** (~150 lines)
```python
class DockerfileGenerator:
    def __init__(self, project_type: str, config: Dict):
        self.project_type = project_type
        self.config = config
        self.template = self._load_template()

    def generate(self) -> str:
        # Render template with config
        pass

    def generate_dockerignore(self) -> str:
        # Generate .dockerignore
        pass
```

**`generators/kubernetes.py`** (~200 lines)
```python
class KubernetesGenerator:
    def __init__(self, config: Dict):
        self.config = config

    def generate_deployment(self) -> str:
        pass

    def generate_service(self) -> str:
        pass

    def generate_ingress(self) -> str:
        pass

    def generate_all(self) -> Dict[str, str]:
        pass
```

**`generators/strategies.py`** (~150 lines)
```python
class DeploymentStrategyGenerator:
    def generate_blue_green(self) -> Dict[str, str]:
        pass

    def generate_rollback(self) -> Dict[str, str]:
        pass
```

**`generators/cicd.py`** (~150 lines)
```python
class CICDGenerator:
    def generate_gitlab_ci(self) -> str:
        pass

    def generate_github_actions(self) -> str:
        pass
```

#### Phase 3: Simplify Main Implementation (Low Risk)

**New `implementation.py`** (~200 lines):
```python
"""Deployment automation skill - refactored version"""

from .generators.dockerfile import DockerfileGenerator
from .generators.kubernetes import KubernetesGenerator
from .generators.strategies import DeploymentStrategyGenerator
from .generators.cicd import CICDGenerator
from .utils.detector import ProjectTypeDetector

def execute_skill(params: Dict) -> Dict:
    """Orchestrate deployment file generation"""
    # Validate input (already has Pydantic)
    # Detect project type
    # Call appropriate generators
    # Return results
```

### Implementation Steps

1. **Step 1** (1 day): Create directory structure and move templates
2. **Step 2** (1 day): Create template loader utility
3. **Step 3** (2 days): Extract Dockerfile generator
4. **Step 4** (2 days): Extract Kubernetes generators
5. **Step 5** (1 day): Extract CI/CD generators
6. **Step 6** (1 day): Extract strategy generators
7. **Step 7** (1 day): Update main implementation
8. **Step 8** (1 day): Update tests and verify

**Total Estimated Time**: 10 days

### Testing Strategy

- Existing tests in `tests/deployment-automation/` must continue passing
- Add new tests for each generator class
- Test template loading independently
- Integration test for full workflow

### Rollback Plan

- Keep old implementation as `implementation.py.bak`
- Feature flag to switch between old/new implementation
- Git branch for easy revert

---

## 2. lingflow_v4_example.py (1,041 lines)

### Current Structure Analysis

This is a **demo/example file**, not production code. It contains:

1. **Result Type** (Lines 33-184): ~150 lines
2. **Exception Hierarchy** (Lines 187-231): ~45 lines
3. **Configuration System** (Lines 234-367): ~135 lines
4. **Skill Base Classes** (Lines 370-460): ~90 lines
5. **Cache Manager** (Lines 463-575): ~115 lines
6. **Monitor System** (Lines 578-638): ~60 lines
7. **Skill Service** (Lines 641-736): ~95 lines
8. **Example Skills** (Lines 739-810): ~70 lines
9. **Test Functions** (Lines 813-1006): ~195 lines
10. **Main Entry** (Lines 1008-1041): ~35 lines

### Issues Identified

1. **Mixed Purpose**: Contains library code AND examples/tests
2. **Reusable Components**: Result type, config, cache, monitor are useful
3. **Not in Proper Location**: Should be in `lingflow/` package, not root
4. **No Module Separation**: All components in one file

### Refactoring Strategy

#### Option A: Move to lingflow-core Package (Recommended)

Since this contains useful core components, extract them to the main package:

**New Structure**:
```
lingflow/
├── core/
│   ├── __init__.py
│   ├── result.py          # Result type + factories
│   ├── errors.py          # Exception hierarchy
│   ├── config.py          # Config + builder
│   ├── cache.py           # CacheManager
│   ├── monitoring.py      # Monitor
│   └── skill_base.py      # BaseSkill, SkillContext, SkillResult
├── services/
│   ├── __init__.py
│   └── skill_service.py   # SimpleSkillService
└── examples/
    └── v4_demo.py         # Demo/test code only
```

**File Size Distribution**:
- `result.py`: ~150 lines
- `errors.py`: ~45 lines
- `config.py`: ~135 lines
- `cache.py`: ~115 lines
- `monitoring.py`: ~60 lines
- `skill_base.py`: ~90 lines
- `skill_service.py`: ~95 lines
- `v4_demo.py`: ~250 lines (tests + examples)

#### Option B: Delete and Document (Alternative)

If these components are already implemented elsewhere in the codebase:

1. Delete the file
2. Add documentation pointing to actual implementations
3. Keep as reference in `docs/examples/`

### Implementation Steps (Option A)

1. **Step 1** (0.5 days): Create `lingflow/core/` directory
2. **Step 2** (0.5 days): Extract Result type
3. **Step 3** (0.5 days): Extract exception hierarchy
4. **Step 4** (0.5 days): Extract config system
5. **Step 5** (0.5 days): Extract cache manager
6. **Step 6** (0.5 days): Extract monitoring
7. **Step 7** (0.5 days): Extract skill base classes
8. **Step 8** (0.5 days): Extract skill service
9. **Step 9** (1 day): Update all imports across project
10. **Step 10** (0.5 days): Create demo file
11. **Step 11** (1 day): Update tests

**Total Estimated Time**: 7 days

### Dependencies to Check

```bash
# Check if anything imports from v4_example
grep -r "lingflow_v4_example" /home/ai/LingFlow --include="*.py"
```

---

## 3. api-doc-generator/implementation.py (969 lines)

### Current Structure Analysis

The file contains multiple concerns:

1. **Data Structures** (Lines 38-65): ~30 lines
   - RouteInfo, SchemaInfo dataclasses

2. **Type Mapping** (Lines 67-85): ~20 lines
   - PYTHON_TYPE_TO_JSON mapping

3. **Main Function** (Lines 88-208): ~120 lines
   - execute_skill() - entry point

4. **Code Scanning** (Lines 211-303): ~95 lines
   - scan_code() - main scanner
   - extract_route_prefixes() - prefix extraction
   - detect_framework() - framework detection

5. **Route Extraction** (Lines 305-460): ~155 lines
   - extract_routes() - route extraction
   - parse_route_decorator() - decorator parsing
   - _extract_decorator_tags() - tag extraction

6. **Parameter/Body Extraction** (Lines 462-632): ~170 lines
   - extract_parameters()
   - extract_request_body()
   - extract_responses()

7. **Schema Extraction** (Lines 635-716): ~80 lines
   - extract_schemas() - Pydantic/dataclass extraction

8. **OpenAPI Generation** (Lines 719-778): ~60 lines
   - generate_openapi_spec()

9. **Output/Utility** (Lines 781-969): ~190 lines
   - save_document()
   - Helper functions (_unparse, infer_type, etc.)
   - YAML conversion

### Issues Identified

1. **Complex AST Parsing**: Multiple traversal functions
2. **Framework-Specific Logic**: FastAPI vs Flask mixed
3. **YAML Implementation**: Custom YAML converter (reinventing wheel)
4. **Large Functions**: Some functions >50 lines
5. **Deep Nesting**: Multiple nested loops in extractors

### Refactoring Strategy

#### Phase 1: Extract Parsers (Low Risk)

**New Structure**:
```
skills/api-doc-generator/
├── implementation.py          (~150 lines - orchestration)
├── parsers/
│   ├── __init__.py
│   ├── base.py               # Base parser interface
│   ├── fastapi.py            # FastAPI specific parser (~200 lines)
│   ├── flask.py              # Flask specific parser (~180 lines)
│   └── ast_utils.py          # AST utility functions (~100 lines)
├── extractors/
│   ├── __init__.py
│   ├── parameters.py         # Parameter extraction (~120 lines)
│   ├── schemas.py            # Schema extraction (~150 lines)
│   └── responses.py          # Response extraction (~80 lines)
├── generators/
│   ├── __init__.py
│   ├── openapi.py            # OpenAPI spec generation (~100 lines)
│   └── output.py             # File output handling (~80 lines)
└── utils/
    ├── __init__.py
    ├── type_mapping.py       # Type conversion utilities (~60 lines)
    └── yaml_helper.py        # YAML/JSON output (~50 lines)
```

#### Phase 2: Create Parser Classes

**`parsers/fastapi.py`** (~200 lines):
```python
class FastAPIParser:
    def __init__(self):
        self.framework = 'fastapi'

    def parse_routes(self, tree, content, file_path) -> List[RouteInfo]:
        pass

    def parse_parameters(self, node, path) -> List[Dict]:
        pass

    def parse_request_body(self, node) -> Optional[Dict]:
        pass
```

**`parsers/flask.py`** (~180 lines):
```python
class FlaskParser:
    # Similar structure for Flask
```

#### Phase 3: Extract Schema Handling

**`extractors/schemas.py`** (~150 lines):
```python
class SchemaExtractor:
    def extract_from_pydantic(self, node) -> SchemaInfo:
        pass

    def extract_from_dataclass(self, node) -> SchemaInfo:
        pass

    def handle_inheritance(self, schemas) -> Dict:
        pass
```

#### Phase 4: Simplify YAML Output

Replace custom YAML implementation with proper library:

**Before**: Custom `to_simple_yaml()` function (~150 lines)
**After**:
```python
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

def save_document(doc, output_path, format):
    if format == 'yaml':
        if YAML_AVAILABLE:
            import yaml
            with open(output_path, 'w') as f:
                yaml.dump(doc, f)
        else:
            # Fallback to custom implementation
            ...
```

### Implementation Steps

1. **Step 1** (1 day): Create new directory structure
2. **Step 2** (1 day): Extract AST utilities
3. **Step 3** (2 days): Create FastAPI parser
4. **Step 4** (2 days): Create Flask parser
5. **Step 5** (2 days): Extract parameter/schema extractors
6. **Step 6** (1 day): Create OpenAPI generator
7. **Step 7** (1 day): Simplify YAML handling
8. **Step 8** (1 day): Update main implementation
9. **Step 9** (2 days): Update tests

**Total Estimated Time**: 13 days

---

## Risk Assessment Matrix

| File | Risk Level | Complexity | Breaking Changes | Rollback Difficulty |
|------|------------|------------|------------------|---------------------|
| deployment-automation | Medium | High | Low (internal only) | Easy |
| lingflow_v4_example | Low | Medium | Medium (if imported) | Easy |
| api-doc-generator | Medium | High | Low (internal only) | Medium |

### Mitigation Strategies

1. **Incremental Changes**: One module at a time
2. **Backward Compatibility**: Keep old interfaces working
3. **Comprehensive Testing**: Test after each extraction
4. **Code Review**: Review each extraction before merging
5. **Feature Flags**: Allow switching between old/new

---

## Over-Development Metrics

### Current State vs Guidelines

| Metric | Guideline | deployment-automation | api-doc-generator | lingflow_v4_example |
|--------|-----------|----------------------|-------------------|---------------------|
| File Lines | <500 | 1,264 ❌ | 969 ❌ | 1,041 ❌ |
| Function Complexity | <15 | Mixed ⚠️ | High ❌ | Mixed ⚠️ |
| Responsibilities | Single | Multiple ❌ | Multiple ❌ | Multiple ❌ |

### Function Complexity Analysis

**deployment-automation**:
- `_generate_k8s_configs()`: ~130 lines
- `_generate_blue_green()`: ~100 lines
- `_generate_ci_cd()`: ~30 lines (acceptable)

**api-doc-generator**:
- `extract_schemas()`: ~80 lines
- `extract_routes()`: ~40 lines
- `scan_code()`: ~55 lines

---

## Testing Requirements

### Existing Test Coverage

```
tests/deployment-automation/      (✓ exists)
tests/api-doc-generator/         (needs verification)
tests/lingflow_v4_example/       (likely none)
```

### New Test Requirements

1. **Unit Tests**: Each new module
2. **Integration Tests**: Full workflow
3. **Regression Tests**: Ensure no breaking changes
4. **Performance Tests**: Verify no degradation

---

## Implementation Priority

### Sprint 1 (Week 1-2): P0 - deployment-automation
- Extract templates to files
- Create generator classes
- Update main implementation

### Sprint 2 (Week 3-4): P1 - api-doc-generator
- Extract parsers
- Create extractor classes
- Simplify YAML handling

### Sprint 3 (Week 5): P2 - lingflow_v4_example
- Move to lingflow/core or delete
- Update imports
- Create proper examples

---

## Success Criteria

1. All files <500 lines ✅
2. All functions <15 cyclomatic complexity ✅
3. Single responsibility per module ✅
4. Test coverage maintained ✅
5. No breaking changes to public API ✅
6. Documentation updated ✅

---

## Post-Refactoring Maintenance

### Code Review Guidelines

1. No file exceeds 500 lines
2. No function exceeds 15 complexity
3. Each module has single responsibility
4. Templates in separate files
5. Comprehensive test coverage

### CI/CD Integration

Add pre-commit hooks:
```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: check-file-length
        name: Check file length
        entry: scripts/check_file_length.sh
        language: script
```

---

## Appendix

### A. File Size Monitoring Script

```bash
#!/bin/bash
# scripts/check_file_length.sh

find /home/ai/LingFlow -name "*.py" -not -path "*/venv/*" | while read file; do
    lines=$(wc -l < "$file")
    if [ $lines -gt 500 ]; then
        echo "WARNING: $file is $lines lines"
    fi
done
```

### B. Complexity Analysis Tool

```bash
# Install radon for complexity analysis
pip install radon

# Analyze complexity
radon cc skills/deployment-automation/implementation.py -a
```

### C. Dependency Graph

```
deployment-automation
├── templates (new)
├── generators (new)
└── utils (new)

api-doc-generator
├── parsers (new)
├── extractors (new)
├── generators (new)
└── utils (new)

lingflow_v4_example
└── lingflow/core (new)
```

---

## Conclusion

This refactoring plan provides a structured approach to reducing file sizes while improving maintainability. The phased approach allows for incremental changes with minimal risk.

**Next Steps**:
1. Get approval from team lead
2. Create feature branches for each file
3. Begin with deployment-automation (P0)
4. Track progress in project board

**Contact**: For questions or clarifications, please open an issue or discussion.
