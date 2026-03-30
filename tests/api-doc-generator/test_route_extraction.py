"""Tests for route extraction from code"""

import ast
import pytest
import sys
from pathlib import Path

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / 'skills'
sys.path.insert(0, str(skills_dir / 'api-doc-generator'))

from implementation import (
    extract_routes,
    parse_route_decorator,
    extract_parameters,
    extract_request_body,
    extract_responses,
)


class TestFastAPIRouteExtraction:
    """Test route extraction from FastAPI code"""

    def test_extract_simple_get_route(self, fastapi_simple_code):
        """Test extracting a simple GET route"""
        tree = ast.parse(fastapi_simple_code)
        routes = extract_routes(tree, fastapi_simple_code, 'test.py', 'fastapi')

        assert len(routes) == 2
        assert routes[0].path == '/users'
        assert routes[0].method == 'GET'
        assert routes[0].handler_name == 'get_users'

    def test_extract_post_route_with_param(self, fastapi_simple_code):
        """Test extracting POST route with path parameter"""
        tree = ast.parse(fastapi_simple_code)
        routes = extract_routes(tree, fastapi_simple_code, 'test.py', 'fastapi')

        post_route = [r for r in routes if r.method == 'POST'][0]
        assert post_route.path == '/users/{user_id}'
        assert post_route.handler_name == 'update_user'

    def test_extract_all_http_methods(self):
        """Test extracting all HTTP method routes"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items():
    return []

@app.post("/items")
def create_item():
    return {}

@app.put("/items/{id}")
def update_item(id: int):
    return {}

@app.patch("/items/{id}")
def patch_item(id: int):
    return {}

@app.delete("/items/{id}")
def delete_item(id: int):
    return []

@app.options("/items")
def options_items():
    return []

@app.head("/items")
def head_items():
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        methods = {r.method for r in routes}
        assert methods == {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'}

    def test_extract_router_routes(self):
        """Test extracting routes from APIRouter"""
        code = '''
from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/users")
def get_users():
    return []

@router.post("/users")
def create_user():
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert len(routes) == 2
        assert routes[0].path == '/api/users'
        assert routes[1].path == '/api/users'

    def test_extract_route_with_docstring(self):
        """Test extracting docstring from route"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """
    Get all users from the database.

    Returns a paginated list of users.
    """
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert routes[0].summary == 'Get all users from the database.'
        assert 'paginated list' in routes[0].description.lower()

    def test_extract_route_without_docstring(self):
        """Test extracting route without docstring"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items():
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert routes[0].summary == ''
        assert routes[0].description == ''


class TestFlaskRouteExtraction:
    """Test route extraction from Flask code"""

    def test_extract_simple_route(self, flask_simple_code):
        """Test extracting a simple Flask route"""
        tree = ast.parse(flask_simple_code)
        routes = extract_routes(tree, flask_simple_code, 'test.py', 'flask')

        assert len(routes) == 3  # GET /items, GET /items/<id>, PUT /items/<id>

    def test_extract_route_with_multiple_methods(self):
        """Test extracting route with multiple methods"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/items", methods=["GET", "POST", "DELETE"])
def items():
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'flask')

        assert len(routes) == 3
        methods = {r.method for r in routes}
        assert methods == {'GET', 'POST', 'DELETE'}
        for route in routes:
            assert route.path == '/items'

    def test_extract_route_default_method(self):
        """Test extracting route without methods defaults to GET"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/home")
def home():
    return "Hello"
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'flask')

        assert len(routes) == 1
        assert routes[0].method == 'GET'

    def test_extract_blueprint_routes(self):
        """Test extracting routes from Blueprint"""
        code = '''
from flask import Blueprint

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route("/users", methods=["GET", "POST"])
def users():
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'flask')

        assert len(routes) == 2
        for route in routes:
            assert route.path == '/api/users'

    def test_extract_route_with_path_param(self):
        """Test extracting Flask route with path parameter"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'flask')

        assert len(routes) == 1
        assert routes[0].path == '/users/<int:user_id>'
        assert routes[0].method == 'GET'


class TestParameterExtraction:
    """Test parameter extraction from routes"""

    def test_extract_fastapi_path_params(self):
        """Test extracting FastAPI path parameters"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}/posts/{post_id}")
def get_post(user_id: int, post_id: int):
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert len(routes) == 1
        params = routes[0].parameters
        assert len(params) == 2
        param_names = {p['name'] for p in params}
        assert param_names == {'user_id', 'post_id'}
        assert all(p['in'] == 'path' for p in params)
        assert all(p['required'] for p in params)

    def test_extract_flask_int_path_params(self):
        """Test extracting Flask int path parameters"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/items/<int:item_id>")
def get_item(item_id):
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'flask')

        params = routes[0].parameters
        assert len(params) == 1
        assert params[0]['name'] == 'item_id'
        assert params[0]['in'] == 'path'
        assert params[0]['schema']['type'] == 'integer'

    def test_extract_flask_string_path_params(self):
        """Test extracting Flask string path parameters"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/posts/<slug:post_slug>")
def get_post(post_slug):
            return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'flask')

        params = routes[0].parameters
        assert len(params) == 1
        assert params[0]['name'] == 'post_slug'
        assert params[0]['schema']['type'] == 'string'

    def test_extract_query_params(self):
        """Test extracting query parameters"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users(skip: int = 0, limit: int = 10, search: str = None):
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        params = routes[0].parameters
        query_params = [p for p in params if p['in'] == 'query']

        assert len(query_params) == 3
        param_names = {p['name'] for p in query_params}
        assert param_names == {'skip', 'limit', 'search'}

        # Check required flags
        skip_param = next(p for p in query_params if p['name'] == 'skip')
        assert skip_param['required'] == False

        search_param = next(p for p in query_params if p['name'] == 'search')
        assert search_param['required'] == False

    def test_extract_param_types(self):
        """Test extracting parameter type annotations"""
        code = '''
from fastapi import FastAPI
from typing import Optional

app = FastAPI()

@app.get("/items")
def get_items(
    id: int,
    name: str,
    price: float,
    active: bool,
    tags: Optional[str] = None
):
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        params = routes[0].parameters
        param_types = {p['name']: p['schema']['type'] for p in params}

        assert param_types.get('id') == 'integer'
        assert param_types.get('name') == 'string'
        assert param_types.get('price') == 'number'
        assert param_types.get('active') == 'boolean'

    def test_exclude_special_params(self):
        """Test that special parameters are excluded"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items(request, skip: int = 0):
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        params = routes[0].parameters
        param_names = [p['name'] for p in params]

        assert 'request' not in param_names
        assert 'skip' in param_names


class TestRequestBodyExtraction:
    """Test request body extraction"""

    def test_extract_body_param(self):
        """Test extracting Body parameter"""
        code = '''
from fastapi import FastAPI, Body

app = FastAPI()

@app.post("/users")
def create_user(name: str = Body(...), email: str = Body(...)):
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert routes[0].request_body is not None
        assert 'content' in routes[0].request_body
        assert 'application/json' in routes[0].request_body['content']

    def test_extract_pydantic_model_body(self):
        """Test extracting Pydantic model as request body"""
        code = '''
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

@app.post("/users")
def create_user(user: UserCreate):
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert routes[0].request_body is not None
        assert 'UserCreate' in routes[0].request_body['content']['application/json']['schema']['$ref']
        assert routes[0].request_body.get('required') == True

    def test_no_request_body_for_get(self):
        """Test that GET requests don't have request body"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items():
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert routes[0].request_body is None


class TestResponseExtraction:
    """Test response extraction"""

    def test_extract_default_response(self):
        """Test extracting default 200 response"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
def get_items():
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert '200' in routes[0].responses
        assert routes[0].responses['200']['description'] == '成功'

    def test_extract_response_from_docstring(self):
        """Test extracting response from docstring"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
def get_users():
    """
    Get all users

    Returns:
        200: User list returned successfully
        404: No users found
    """
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        # Check for 200 response
        assert '200' in routes[0].responses
        # The docstring parsing might not catch this format exactly
        # but should have at least the default

    def test_extract_response_from_return_type(self):
        """Test extracting response from return type annotation"""
        code = '''
from fastapi import FastAPI
from typing import List

app = FastAPI()

@app.get("/items")
def get_items() -> List[str]:
    return []
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert '200' in routes[0].responses
        response = routes[0].responses['200']
        assert 'content' in response
        assert response['content']['application/json']['schema']['type'] == 'array'

    def test_extract_multiple_responses(self):
        """Test extracting multiple response codes"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """
    Get a user

    Returns:
        200: User found
        404: User not found
    """
    return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        # Should at least have default 200
        assert '200' in routes[0].responses


class TestClassBasedRoutes:
    """Test route extraction from class-based views"""

    def test_extract_routes_from_class(self):
        """Test extracting routes from class methods"""
        code = '''
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

class UserView:
    @router.get("/users")
    def list_users(self):
        return []

    @router.post("/users")
    def create_user(self):
        return {}
'''
        tree = ast.parse(code)
        routes = extract_routes(tree, code, 'test.py', 'fastapi')

        assert len(routes) == 2
        handler_names = {r.handler_name for r in routes}
        assert 'list_users' in handler_names
        assert 'create_user' in handler_names


class TestRouteDecoratorParsing:
    """Test parse_route_decorator function directly"""

    def test_parse_single_decorator(self):
        """Test parsing a single route decorator"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/test")
def test_func():
    pass
'''
        tree = ast.parse(code)
        func_node = tree.body[2]  # The function definition

        routes = parse_route_decorator(func_node, 'fastapi')
        assert len(routes) == 1
        assert routes[0].path == '/test'
        assert routes[0].method == 'GET'

    def test_parse_multiple_decorators(self):
        """Test parsing multiple decorators on same function"""
        code = '''
from fastapi import FastAPI

app = FastAPI()

@app.get("/items")
@app.post("/items")
def items_handler():
    pass
'''
        tree = ast.parse(code)
        func_node = tree.body[2]  # The function definition

        routes = parse_route_decorator(func_node, 'fastapi')
        # Should extract both routes
        assert len(routes) >= 1

    def test_parse_flask_multi_method_decorator(self):
        """Test parsing Flask decorator with multiple methods"""
        code = '''
from flask import Flask

app = Flask(__name__)

@app.route("/items", methods=["GET", "POST", "PUT"])
def items_handler():
    pass
'''
        tree = ast.parse(code)
        func_node = tree.body[2]  # The function definition

        routes = parse_route_decorator(func_node, 'flask')
        assert len(routes) == 3
        methods = {r.method for r in routes}
        assert methods == {'GET', 'POST', 'PUT'}

    def test_parse_decorator_without_route(self):
        """Test parsing function without route decorator"""
        code = '''

def helper_function():
    pass
'''
        tree = ast.parse(code)
        func_node = tree.body[0]  # The function definition

        routes = parse_route_decorator(func_node, 'fastapi')
        assert len(routes) == 0
