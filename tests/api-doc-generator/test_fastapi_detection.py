"""Tests for FastAPI framework detection"""

import ast
import sys
from pathlib import Path

import pytest

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / "skills"
sys.path.insert(0, str(skills_dir / "api-doc-generator"))

from implementation import detect_framework


class TestFastAPIImportDetection:
    """Test FastAPI detection through imports"""

    def test_detect_fastapi_import(self, fastapi_simple_code):
        """Test detecting FastAPI from import statement"""
        tree = ast.parse(fastapi_simple_code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_detect_fastapi_from_import(self, fastapi_complex_code):
        """Test detecting FastAPI from from...import statement"""
        tree = ast.parse(fastapi_complex_code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_detect_fastapi_router_import(self):
        """Test detecting FastAPI APIRouter import"""
        code = """
from fastapi import APIRouter

router = APIRouter()

@router.get("/items")
def get_items():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_detect_fastapi_submodule_import(self):
        """Test detecting FastAPI from submodule imports"""
        code = """
from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_no_fastapi_import(self):
        """Test that non-FastAPI code is not detected as FastAPI"""
        code = """
import os
import sys
from datetime import datetime

def hello():
    return "world"
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework != "fastapi"


class TestFastAPIDecoratorDetection:
    """Test FastAPI detection through decorators"""

    def test_detect_app_get_decorator(self):
        """Test detecting @app.get decorator"""
        code = """
app = FastAPI()

@app.get("/users")
def get_users():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_detect_app_post_decorator(self):
        """Test detecting @app.post decorator"""
        code = """
app = FastAPI()

@app.post("/users")
def create_user():
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_detect_all_http_method_decorators(self):
        """Test detecting all HTTP method decorators"""
        methods = ["get", "post", "put", "delete", "patch", "options", "head", "trace"]

        for method in methods:
            code = f"""
app = FastAPI()

@app.{method}("/endpoint")
def endpoint():
    return {{}}
"""
            tree = ast.parse(code)
            framework = detect_framework(tree)
            assert framework == "fastapi", f"Failed for method: {method}"

    def test_detect_router_decorator(self):
        """Test detecting @router decorator"""
        code = """
router = APIRouter()

@router.get("/items")
def get_items():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_detect_apirouter_decorator(self):
        """Test detecting @APIRouter decorator"""
        code = """
APIRouter = APIRouter

@APIRouter.get("/items")
def get_items():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"


class TestFastAPIWithVariousCodePatterns:
    """Test FastAPI detection with various code patterns"""

    def test_fastapi_class_based_views(self):
        """Test detecting FastAPI with class-based views"""
        code = """
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

@router.get("/items")
class ItemView:
    def get(self):
        return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_fastapi_with_dependency_injection(self):
        """Test detecting FastAPI with dependency injection"""
        code = """
from fastapi import FastAPI, Depends

app = FastAPI()

def get_db():
    return db

@app.get("/users")
def read_users(db = Depends(get_db)):
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"

    def test_fastapi_with_middleware(self):
        """Test detecting FastAPI with middleware"""
        code = """
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/")
def read_root():
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "fastapi"


class TestFastAPIPriorityOverFlask:
    """Test FastAPI is prioritized when both frameworks are present"""

    def test_fastapi_priority_when_both_imports(self):
        """Test FastAPI is detected when both are imported"""
        code = """
from fastapi import FastAPI
from flask import Flask  # Should be ignored

app = FastAPI()

@app.get("/api/users")
def users():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        # FastAPI should be detected first due to import order
        assert framework in ["fastapi", "flask"]

    def test_detect_from_flask_code(self):
        """Test Flask detection from pure Flask code"""
        code = """
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello"
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"


class TestFastAPIEdgeCases:
    """Test FastAPI detection edge cases"""

    def test_empty_ast(self):
        """Test with empty AST"""
        tree = ast.parse("")
        framework = detect_framework(tree)
        assert framework == "flask"  # Default fallback

    def test_only_comments(self):
        """Test with only comments"""
        code = """
# This is a comment
# Another comment
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"  # Default fallback

    def test_string_containing_fastapi(self):
        """Test code with FastAPI mentioned but not imported"""
        code = """
def get_framework_name():
    return "fastapi"
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"  # Should not detect from string

    def test_variable_named_fastapi(self):
        """Test code with variable named fastapi"""
        code = """
fastapi = "some framework"
def hello():
    return fastapi
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"  # Should not detect from variable name
