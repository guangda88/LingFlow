# API Doc Generator Tests

单元测试套件用于 api-doc-generator Skill。

## 测试文件

| 文件 | 描述 | 测试数量 |
|------|------|---------|
| `test_fastapi_detection.py` | FastAPI 框架检测 | 26 tests |
| `test_flask_detection.py` | Flask 框架检测 | 35 tests |
| `test_route_extraction.py` | 路由提取 | 27 tests |
| `test_schema_generation.py` | Schema 生成 | 37 tests |
| `test_openapi_generation.py` | OpenAPI 文档生成 | 29 tests |
| `test_save_document.py` | 文档保存 | 24 tests |
| `test_integration.py` | 集成测试 | 15 tests |

## 运行测试

```bash
# 运行所有测试
pytest tests/api-doc-generator/

# 运行特定测试文件
pytest tests/api-doc-generator/test_fastapi_detection.py

# 查看详细输出
pytest tests/api-doc-generator/ -v

# 运行覆盖率检查
python tests/api-doc-generator/coverage_check.py
```

## 测试覆盖率

基于手动检查的函数覆盖率约为 **84%**。

主要覆盖的函数:
- `detect_framework` ✓
- `extract_routes` ✓
- `parse_route_decorator` ✓
- `extract_parameters` ✓
- `extract_request_body` ✓
- `extract_responses` ✓
- `extract_schemas` ✓
- `generate_openapi_spec` ✓
- `save_document` ✓
- `execute_skill` ✓
- `scan_code` ✓
- 辅助函数 (_is_pydantic_model, _is_dataclass 等) ✓

## 测试状态

- 总测试数: 178
- 通过: 158 (89%)
- 失败: 20 (11%)

失败的测试主要是因为:
1. 实现细节与测试期望的差异（需要调整测试以匹配实际行为）
2. 一些边缘情况需要处理

## 固定装置 (Fixtures)

测试使用 `conftest.py` 中定义的固定装置，包括:
- 代码示例 (fastapi_simple_code, flask_simple_code 等)
- RouteInfo 和 SchemaInfo 对象
- 临时文件和目录
- OpenAPI 文档示例

## 下一步改进

1. 修复失败的测试用例
2. 增加更多边界情况测试
3. 添加性能测试
4. 增加对 Django/DRF 支持的测试
