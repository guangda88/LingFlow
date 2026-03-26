"""Fixtures and configuration for api-doc-generator tests"""

import ast
import pytest
import tempfile
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add skills directory to path for imports
skills_dir = Path(__file__).parent.parent.parent / 'skills'
sys.path.insert(0, str(skills_dir / 'api-doc-generator'))

from implementation import (
    RouteInfo,
    SchemaInfo,
    detect_framework,
    extract_routes,
    extract_schemas,
    generate_openapi_spec,
    scan_code,
)


# ============== Sample Code Fixtures ==============

@pytest.fixture
def fastapi_simple_code():
    """Simple FastAPI application code"""
    return '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    """Get all users"""
    return []

@app.post("/users/{user_id}")
async def update_user(user_id: int):
    """Update user by ID"""
    return {"id": user_id}
'''


@pytest.fixture
def fastapi_complex_code():
    """Complex FastAPI application with various features"""
    return '''
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()


class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: str


@app.get("/users", tags=["users"])
async def list_users(skip: int = 0, limit: int = 10):
    """
    List all users

    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return

    Returns:
        List of users
    """
    return []


@app.get("/users/{user_id}", responses={200: {"description": "User found"}})
async def get_user(user_id: int):
    """Get a specific user by ID"""
    return {"id": user_id}


@app.post("/users")
async def create_user(user: UserCreate):
    """Create a new user"""
    return {"id": 1}


@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserCreate):
    """Update an existing user"""
    return {"id": user_id}


@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user"""
    return {"deleted": True}
'''


@pytest.fixture
def flask_simple_code():
    """Simple Flask application code"""
    return '''
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/items", methods=["GET"])
def get_items():
    """Get all items"""
    return jsonify([])

@app.route("/items/<int:item_id>", methods=["GET", "PUT"])
def get_item(item_id):
    """Get single item"""
    return jsonify({"id": item_id})
'''


@pytest.fixture
def flask_complex_code():
    """Complex Flask application with various features"""
    return '''
from flask import Flask, Blueprint, request, jsonify

app = Flask(__name__)
bp = Blueprint('api', __name__, url_prefix='/api')


@app.route("/", methods=["GET"])
def index():
    """Home page"""
    return "Hello"


@bp.route("/users", methods=["GET", "POST"])
def users():
    """List or create users"""
    return jsonify([])


@bp.route("/users/<int:user_id>", methods=["GET", "PUT", "DELETE"])
def user_detail(user_id):
    """Get, update or delete user"""
    return jsonify({"id": user_id})


@bp.route("/posts/<slug:post_slug>", methods=["GET"])
def post_detail(post_slug):
    """Get post by slug"""
    return jsonify({"slug": post_slug})


@bp.route("/search", methods=["GET"])
def search():
    """Search with query parameters"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    return jsonify({"query": query, "page": page})
'''


@pytest.fixture
def pydantic_models_code():
    """Code with Pydantic models"""
    return '''
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int
'''


@pytest.fixture
def dataclass_models_code():
    """Code with dataclass models"""
    return '''
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class User:
    """User data model"""
    id: int
    name: str
    email: str
    age: Optional[int] = None


@dataclass
class Post:
    """Post data model"""
    id: int
    title: str
    content: str
    author: User
    tags: List[str]
'''


# ============== RouteInfo Fixtures ==============

@pytest.fixture
def route_info_get():
    """GET route info"""
    return RouteInfo(
        path='/api/users',
        method='GET',
        handler_name='list_users',
        summary='List all users',
        description='Returns paginated list of users',
        tags=['users'],
        parameters=[
            {'name': 'skip', 'in': 'query', 'required': False, 'schema': {'type': 'integer'}},
            {'name': 'limit', 'in': 'query', 'required': False, 'schema': {'type': 'integer'}}
        ],
        responses={'200': {'description': 'Success'}}
    )


@pytest.fixture
def route_info_post():
    """POST route info"""
    return RouteInfo(
        path='/api/users',
        method='POST',
        handler_name='create_user',
        summary='Create a new user',
        description='Creates a user with the provided data',
        tags=['users'],
        request_body={
            'content': {
                'application/json': {
                    'schema': {'$ref': '#/components/schemas/UserCreate'}
                }
            },
            'required': True
        },
        responses={'201': {'description': 'User created'}, '400': {'description': 'Bad request'}}
    )


@pytest.fixture
def route_info_with_path_param():
    """Route with path parameter"""
    return RouteInfo(
        path='/api/users/{user_id}',
        method='GET',
        handler_name='get_user',
        summary='Get user by ID',
        parameters=[
            {'name': 'user_id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
        ],
        responses={'200': {'description': 'Success'}, '404': {'description': 'Not found'}}
    )


@pytest.fixture
def route_info_deprecated():
    """Deprecated route"""
    return RouteInfo(
        path='/api/legacy',
        method='GET',
        handler_name='legacy_endpoint',
        deprecated=True,
        responses={'200': {'description': 'Success'}}
    )


# ============== SchemaInfo Fixtures ==============

@pytest.fixture
def schema_user():
    """User schema"""
    return SchemaInfo(
        name='User',
        type='object',
        properties={
            'id': {'type': 'integer'},
            'name': {'type': 'string'},
            'email': {'type': 'string'}
        },
        required=['id', 'name', 'email'],
        description='User model'
    )


@pytest.fixture
def schema_user_create():
    """UserCreate schema"""
    return SchemaInfo(
        name='UserCreate',
        type='object',
        properties={
            'name': {'type': 'string'},
            'email': {'type': 'string'},
            'age': {'type': 'integer'}
        },
        required=['name', 'email'],
        description='User creation model'
    )


@pytest.fixture
def schema_with_enum():
    """Schema with enum values"""
    return SchemaInfo(
        name='Status',
        type='string',
        enum=['active', 'inactive', 'pending'],
        description='User status'
    )


# ============== OpenAPI Document Fixtures ==============

@pytest.fixture
def openapi_minimal():
    """Minimal OpenAPI document"""
    return {
        'openapi': '3.0.0',
        'info': {
            'title': 'API Documentation',
            'version': '1.0.0',
            'description': 'Auto-generated API documentation'
        },
        'paths': {},
        'components': {
            'schemas': {}
        }
    }


@pytest.fixture
def openapi_with_routes():
    """OpenAPI document with routes"""
    return {
        'openapi': '3.0.0',
        'info': {
            'title': 'Test API',
            'version': '1.0.0',
            'description': 'Auto-generated API documentation'
        },
        'paths': {
            '/api/users': {
                'get': {
                    'summary': 'List users',
                    'operationId': 'list_users',
                    'responses': {'200': {'description': 'Success'}},
                    'tags': ['users']
                }
            },
            '/api/users/{user_id}': {
                'get': {
                    'summary': 'Get user',
                    'operationId': 'get_user',
                    'parameters': [
                        {'name': 'user_id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
                    ],
                    'responses': {'200': {'description': 'Success'}}
                }
            }
        },
        'components': {
            'schemas': {
                'User': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'name': {'type': 'string'}
                    },
                    'required': ['id', 'name']
                }
            }
        }
    }


# ============== File and Directory Fixtures ==============

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with content"""
    def _create_file(filename: str, content: str) -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path
    return _create_file


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory"""
    def _create_dir(dirname: str) -> Path:
        dir_path = tmp_path / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path
    return _create_dir


@pytest.fixture
def temp_fastapi_project(tmp_path):
    """Create a temporary FastAPI project structure"""
    project_dir = tmp_path / 'fastapi_project'
    project_dir.mkdir()

    # Create main app
    (project_dir / 'main.py').write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
''')

    # Create models
    (project_dir / 'models.py').write_text('''
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float
''')

    # Create routes
    routes_dir = project_dir / 'routes'
    routes_dir.mkdir()
    (routes_dir / 'users.py').write_text('''
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
def get_users():
    return []
''')

    return project_dir


@pytest.fixture
def temp_flask_project(tmp_path):
    """Create a temporary Flask project structure"""
    project_dir = tmp_path / 'flask_project'
    project_dir.mkdir()

    # Create app
    (project_dir / 'app.py').write_text('''
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "Hello"
''')

    # Create views
    views_dir = project_dir / 'views'
    views_dir.mkdir()
    (views_dir / 'users.py').write_text('''
from flask import Blueprint

bp = Blueprint('users', __name__)

@bp.route("/users")
def list_users():
    return []
''')

    return project_dir


# ============== AST Tree Fixtures ==============

@pytest.fixture
def fastapi_ast(fastapi_simple_code):
    """AST of FastAPI code"""
    return ast.parse(fastapi_simple_code)


@pytest.fixture
def flask_ast(flask_simple_code):
    """AST of Flask code"""
    return ast.parse(flask_simple_code)


@pytest.fixture
def pydantic_ast(pydantic_models_code):
    """AST of Pydantic models"""
    return ast.parse(pydantic_models_code)


# ============== Parameter Fixtures ==============

@pytest.fixture
def skill_params_basic():
    """Basic skill execution parameters"""
    return {
        'input': '/path/to/app.py',
        'format': 'yaml',
        'framework': 'auto',
        'title': 'My API',
        'version': '1.0.0',
        'base_url': 'http://localhost:8000'
    }


@pytest.fixture
def skill_params_json():
    """Skill parameters for JSON output"""
    return {
        'input': '/path/to/app.py',
        'output': '/path/to/api.json',
        'format': 'json',
        'framework': 'fastapi'
    }


@pytest.fixture
def skill_params_with_output():
    """Skill parameters with output file"""
    return {
        'input': '/path/to/app.py',
        'output': '/path/to/openapi.yaml',
        'format': 'yaml'
    }


# ============== Error Scenario Fixtures ==============

@pytest.fixture
def code_syntax_error():
    """Code with syntax error"""
    return '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users"
def get_users():  # Missing closing parenthesis
    return []
'''


@pytest.fixture
def code_no_routes():
    """Code with no routes"""
    return '''
"""Utility functions"""

def add(a, b):
    return a + b

def multiply(x, y):
    return x * y
'''


@pytest.fixture
def code_mixed_frameworks():
    """Code mixing imports from multiple frameworks"""
    return '''
from fastapi import FastAPI
from flask import Flask

app = FastAPI()

@app.get("/api/users")
def users():
    return []
'''
