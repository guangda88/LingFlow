"""Integration tests for api-doc-generator skill"""

import json
import pytest
import sys
from pathlib import Path

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / 'skills'
sys.path.insert(0, str(skills_dir / 'api-doc-generator'))

from implementation import execute_skill, scan_code


class TestExecuteSkillIntegration:
    """Integration tests for execute_skill function"""

    def test_execute_skill_with_fastapi_file(self, temp_file):
        """Test executing skill with FastAPI file"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users(skip: int = 0, limit: int = 10):
    """Get all users"""
    return []

@app.post("/users")
async def create_user(name: str, email: str):
    """Create a new user"""
    return {"id": 1}
'''
        test_file = temp_file('fastapi_app.py', code)

        result = execute_skill({
            'input': str(test_file),
            'format': 'json'
        })

        assert result['success'] is True
        assert result['routes_count'] == 2
        assert 'openapi' in result
        assert result['format'] == 'json'

    def test_execute_skill_with_flask_file(self, temp_file):
        """Test executing skill with Flask file"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/items", methods=["GET", "POST"])
def items():
    return []

@app.route("/items/<int:item_id>", methods=["GET", "PUT", "DELETE"])
def item_detail(item_id):
    return {}
'''
        test_file = temp_file('flask_app.py', code)

        result = execute_skill({
            'input': str(test_file),
            'framework': 'flask'
        })

        assert result['success'] is True
        assert result['routes_count'] == 5  # GET, POST + GET, PUT, DELETE

    def test_execute_skill_with_directory(self, temp_fastapi_project):
        """Test executing skill with directory"""
        result = execute_skill({
            'input': str(temp_fastapi_project),
            'framework': 'fastapi'
        })

        assert result['success'] is True
        assert result['routes_count'] > 0

    def test_execute_skill_with_output_file(self, temp_file):
        """Test executing skill with output file"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
'''
        test_file = temp_file('app.py', code)
        output_file = test_file.parent / 'openapi.json'

        result = execute_skill({
            'input': str(test_file),
            'output': str(output_file),
            'format': 'json'
        })

        assert result['success'] is True
        assert 'output_file' in result
        assert output_file.exists()

        # Verify output content
        with open(output_file) as f:
            doc = json.load(f)
        assert doc['openapi'] == '3.0.0'

    def test_execute_skill_yaml_output(self, temp_file):
        """Test YAML output format"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test():
    return {}
'''
        test_file = temp_file('app.py', code)
        output_file = test_file.parent / 'openapi.yaml'

        result = execute_skill({
            'input': str(test_file),
            'output': str(output_file),
            'format': 'yaml'
        })

        assert result['success'] is True
        assert output_file.exists()

        content = output_file.read_text()
        assert 'openapi:' in content

    def test_execute_skill_with_custom_metadata(self, temp_file):
        """Test with custom title, version, and base URL"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index():
    return {}
'''
        test_file = temp_file('app.py', code)

        result = execute_skill({
            'input': str(test_file),
            'title': 'My Custom API',
            'version': '2.5.0',
            'base_url': 'https://api.example.com/v1'
        })

        assert result['success'] is True
        assert result['openapi']['info']['title'] == 'My Custom API'
        assert result['openapi']['info']['version'] == '2.5.0'
        assert result['openapi']['servers'][0]['url'] == 'https://api.example.com/v1'

    def test_execute_skill_auto_detection(self, temp_file):
        """Test automatic framework detection"""
        fastapi_code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def index():
    return {}
'''
        test_file = temp_file('auto.py', fastapi_code)

        result = execute_skill({
            'input': str(test_file),
            'framework': 'auto'
        })

        assert result['success'] is True

    def test_execute_skill_no_routes_error(self, temp_file):
        """Test error when no routes found"""
        code = '''
# Just a module with utility functions
def add(a, b):
    return a + b
'''
        test_file = temp_file('utils.py', code)

        result = execute_skill({
            'input': str(test_file)
        })

        assert result['success'] is False
        assert 'error' in result
        assert '未找到' in result['error']

    def test_execute_skill_missing_input(self):
        """Test error when input is not provided"""
        result = execute_skill({})

        assert result['success'] is False
        assert 'error' in result
        assert 'input' in result['error']

    def test_execute_skill_nonexistent_file(self):
        """Test error when file doesn't exist"""
        result = execute_skill({
            'input': '/nonexistent/file.py'
        })

        assert result['success'] is False
        assert 'error' in result


class TestScanCodeIntegration:
    """Integration tests for scan_code function"""

    def test_scan_with_pydantic_models(self, temp_file):
        """Test scanning code with Pydantic models"""
        code = '''
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

class UserResponse(BaseModel):
    id: int
    name: str

@app.post("/users")
def create_user(user: UserCreate) -> UserResponse:
    return user
'''
        test_file = temp_file('models.py', code)

        routes, schemas = scan_code(str(test_file), 'fastapi')

        assert len(routes) == 1
        assert 'UserCreate' in schemas
        assert 'UserResponse' in schemas

    def test_scan_with_dataclass_models(self, temp_file):
        """Test scanning code with dataclass models"""
        code = '''
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str
'''
        test_file = temp_file('dataclass.py', code)

        routes, schemas = scan_code(str(test_file), 'fastapi')

        assert 'User' in schemas
        assert schemas['User'].type == 'object'

    def test_scan_complex_fastapi_app(self, temp_file):
        """Test scanning a complex FastAPI application"""
        code = '''
from fastapi import FastAPI, APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="Blog API")

router = APIRouter(prefix="/api/v1")

class PostCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str
    tags: List[str] = []

class PostResponse(BaseModel):
    id: int
    title: str
    content: str

@router.get("/posts", tags=["posts"])
async def list_posts(skip: int = 0, limit: int = 10):
    """List all blog posts"""
    return []

@router.get("/posts/{post_id}", tags=["posts"])
async def get_post(post_id: int):
    """Get a specific post"""
    return {}

@router.post("/posts", tags=["posts"])
async def create_post(post: PostCreate):
    """Create a new post"""
    return {"id": 1}

@router.put("/posts/{post_id}", tags=["posts"])
async def update_post(post_id: int, post: PostCreate):
    """Update an existing post"""
    return {}

@router.delete("/posts/{post_id}", tags=["posts"])
async def delete_post(post_id: int):
    """Delete a post"""
    return {}

app.include_router(router)
'''
        test_file = temp_file('blog_api.py', code)

        routes, schemas = scan_code(str(test_file), 'fastapi')

        # Should extract all routes
        assert len(routes) >= 5
        assert schemas['PostCreate'].type == 'object'
        assert schemas['PostResponse'].type == 'object'

    def test_scan_flask_with_blueprints(self, temp_file):
        """Test scanning Flask app with blueprints"""
        code = '''
from flask import Flask, Blueprint

app = Flask(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/users", methods=["GET", "POST"])
def users():
    return []

@api_bp.route("/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
def user_detail(user_id):
    return {}

@api_bp.route("/posts/<slug:post_slug>", methods=["GET"])
def post_detail(post_slug):
    return {}
'''
        test_file = temp_file('blueprints.py', code)

        routes, schemas = scan_code(str(test_file), 'flask')

        # Should extract all routes
        assert len(routes) >= 5  # GET/POST users, GET/PUT/DELETE user_id, GET post_slug

    def test_scan_with_syntax_error(self, temp_file):
        """Test handling syntax errors gracefully"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users"  # Missing closing paren
def get_users():
    return []
'''
        test_file = temp_file('syntax_error.py', code)

        # Should not raise exception, just skip the file
        routes, schemas = scan_code(str(test_file), 'fastapi')

        # May have 0 routes due to syntax error
        assert isinstance(routes, list)
        assert isinstance(schemas, dict)


class TestCompleteWorkflow:
    """Test complete workflows"""

    def test_fastapi_to_openapi_workflow(self, temp_file):
        """Test complete workflow: FastAPI code -> OpenAPI document"""
        code = '''
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users", tags=["users"], responses={200: {"description": "Success"}})
async def list_users(skip: int = 0, limit: int = 10):
    """List all users with pagination"""
    return []

@app.get("/users/{user_id}", tags=["users"])
async def get_user(user_id: int):
    """Get a user by ID"""
    return {}

@app.post("/users", tags=["users"])
async def create_user(user: User):
    """Create a new user"""
    return user

@app.put("/users/{user_id}", tags=["users"])
async def update_user(user_id: int, user: User):
    """Update a user"""
    return user

@app.delete("/users/{user_id}", tags=["users"])
async def delete_user(user_id: int):
    """Delete a user"""
    return {}
'''
        test_file = temp_file('users_api.py', code)

        result = execute_skill({
            'input': str(test_file),
            'title': 'Users Management API',
            'version': '1.0.0',
            'base_url': 'https://api.example.com'
        })

        assert result['success'] is True
        assert result['routes_count'] == 5
        assert result['schemas_count'] == 1

        doc = result['openapi']

        # Verify document structure
        assert doc['openapi'] == '3.0.0'
        assert doc['info']['title'] == 'Users Management API'
        assert doc['servers'][0]['url'] == 'https://api.example.com'

        # Verify paths
        assert '/users' in doc['paths']
        assert '/users/{user_id}' in doc['paths']

        # Verify methods
        users_path = doc['paths']['/users']
        assert 'get' in users_path
        assert 'post' in users_path

        # Verify tags
        assert users_path['get']['tags'] == ['users']

        # Verify parameters
        get_params = users_path['get']['parameters']
        param_names = {p['name'] for p in get_params}
        assert 'skip' in param_names
        assert 'limit' in param_names

        # Verify schema
        assert 'User' in doc['components']['schemas']
        user_schema = doc['components']['schemas']['User']
        assert 'id' in user_schema['properties']
        assert 'name' in user_schema['properties']
        assert 'email' in user_schema['properties']

    def test_flask_to_openapi_workflow(self, temp_file):
        """Test complete workflow: Flask code -> OpenAPI document"""
        code = '''
from flask import Flask, Blueprint

app = Flask(__name__)
api = Blueprint('api', __name__, url_prefix='/api')

@api.route("/products", methods=["GET"])
def list_products():
    """List all products"""
    pass

@api.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    """Get a product"""
    pass

@api.route("/products", methods=["POST"])
def create_product():
    """Create a product"""
    pass

@api.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    """Update a product"""
    pass

@api.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Delete a product"""
    pass
'''
        test_file = temp_file('products_api.py', code)

        result = execute_skill({
            'input': str(test_file),
            'framework': 'flask',
            'title': 'Products API'
        })

        assert result['success'] is True
        assert result['routes_count'] == 5

        doc = result['openapi']

        # Verify paths
        assert '/api/products' in doc['paths']
        assert '/api/products/<int:product_id>' in doc['paths']

        # Verify all HTTP methods
        products_path = doc['paths']['/api/products']
        assert 'get' in products_path
        assert 'post' in products_path

    def test_mixed_project_structure(self, temp_fastapi_project):
        """Test scanning a mixed project structure"""
        result = execute_skill({
            'input': str(temp_fastapi_project),
            'framework': 'fastapi',
            'title': 'Project API'
        })

        assert result['success'] is True
        assert result['routes_count'] > 0

        doc = result['openapi']
        assert len(doc['paths']) > 0
