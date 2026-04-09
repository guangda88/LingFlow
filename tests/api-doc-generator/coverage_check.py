#!/usr/bin/env python3
"""Quick coverage check for api-doc-generator"""

import ast
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "skills" / "api-doc-generator"))

from implementation import (
    RouteInfo,
    SchemaInfo,
    _has_default,
    _is_dataclass,
    _is_pydantic_model,
    _unparse,
    detect_framework,
    execute_skill,
    extract_parameters,
    extract_request_body,
    extract_responses,
    extract_routes,
    extract_schemas,
    generate_openapi_spec,
    infer_type_from_annotation,
    map_flask_type,
    parse_docstring,
    parse_route_decorator,
    save_document,
    scan_code,
    to_simple_yaml,
)

# Track covered functions
covered_functions = set()

# Test detect_framework
code = """
from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def index():
    return {}
"""
tree = ast.parse(code)
assert detect_framework(tree) == "fastapi"
covered_functions.add("detect_framework")

# Test extract_routes
routes = extract_routes(tree, code, "test.py", "fastapi")
assert len(routes) >= 1
covered_functions.add("extract_routes")

# Test parse_route_decorator
func_node = tree.body[2]  # The function
routes = parse_route_decorator(func_node, "fastapi")
assert len(routes) >= 1
covered_functions.add("parse_route_decorator")

# Test extract_parameters
params = extract_parameters(func_node, "fastapi", "/")
covered_functions.add("extract_parameters")

# Test extract_request_body
body = extract_request_body(func_node, "fastapi")
covered_functions.add("extract_request_body")

# Test extract_responses
responses = extract_responses(func_node, "")
covered_functions.add("extract_responses")

# Test parse_docstring
summary, desc = parse_docstring("Summary\\n\\nDescription")
covered_functions.add("parse_docstring")

# Test infer_type_from_annotation
annotation = ast.parse("x: int").body[0].annotation
typ = infer_type_from_annotation(annotation)
covered_functions.add("infer_type_from_annotation")

# Test map_flask_type
mapped = map_flask_type("int")
covered_functions.add("map_flask_type")

# Test _unparse
unp = _unparse(tree)
covered_functions.add("_unparse")

# Test _has_default
node = ast.parse("x: int = 5").body[0]
has_def = _has_default(node)
covered_functions.add("_has_default")

# Test extract_schemas
code = """
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
"""
tree = ast.parse(code)
schemas = extract_schemas(tree, code)
covered_functions.add("extract_schemas")

# Test _is_pydantic_model
class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
is_pyd = _is_pydantic_model(class_node, code)
covered_functions.add("_is_pydantic_model")

# Test _is_dataclass
is_dc = _is_dataclass(class_node)
covered_functions.add("_is_dataclass")

# Test generate_openapi_spec
doc = generate_openapi_spec([], {}, "API", "1.0.0", "")
covered_functions.add("generate_openapi_spec")

# Test to_simple_yaml
yaml_out = to_simple_yaml({"key": "value"})
covered_functions.add("to_simple_yaml")

# Test RouteInfo
route = RouteInfo(path="/", method="GET", handler_name="test")
covered_functions.add("RouteInfo")

# Test SchemaInfo
schema = SchemaInfo(name="Test", type="object")
covered_functions.add("SchemaInfo")

# Test scan_code
import tempfile

with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
    f.write("""
from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def index():
    return {}
""")
    f.flush()
    temp_path = f.name

try:
    routes, schemas = scan_code(temp_path, "fastapi")
    covered_functions.add("scan_code")
finally:
    Path(temp_path).unlink()

# Test execute_skill
with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
    f.write("""
from fastapi import FastAPI
app = FastAPI()
@app.get("/")
def index():
    return {}
""")
    f.flush()
    temp_path = f.name

try:
    result = execute_skill({"input": temp_path})
    covered_functions.add("execute_skill")
finally:
    Path(temp_path).unlink()

# Test save_document
with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    temp_path = f.name

try:
    save_document({"test": "data"}, temp_path, "json")
    covered_functions.add("save_document")
finally:
    Path(temp_path).unlink()

# Print results
total_functions = 25  # Approximate count
covered = len(covered_functions)

print(f"=== Coverage Check Results ===")
print(f"Functions covered: {covered}/{total_functions}")
print(f"Coverage: {covered/total_functions*100:.1f}%")
print()
print("Covered functions:")
for f in sorted(covered_functions):
    print(f"  ✓ {f}")

# List remaining functions
all_funcs = [
    "detect_framework",
    "extract_routes",
    "parse_route_decorator",
    "extract_parameters",
    "extract_request_body",
    "extract_responses",
    "extract_schemas",
    "generate_openapi_spec",
    "save_document",
    "execute_skill",
    "scan_code",
    "parse_docstring",
    "infer_type_from_annotation",
    "map_flask_type",
    "_unparse",
    "_has_default",
    "_is_pydantic_model",
    "_is_dataclass",
    "to_simple_yaml",
    "RouteInfo",
    "SchemaInfo",
]

remaining = set(all_funcs) - covered_functions
if remaining:
    print()
    print("Remaining functions (not directly tested):")
    for f in sorted(remaining):
        print(f"  - {f}")
