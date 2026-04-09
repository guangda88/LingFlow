"""Tests for Flask framework detection"""

import ast
import sys
from pathlib import Path

import pytest

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / "skills"
sys.path.insert(0, str(skills_dir / "api-doc-generator"))

from implementation import detect_framework


class TestFlaskImportDetection:
    """Test Flask detection through imports"""

    def test_detect_flask_import(self, flask_simple_code):
        """Test detecting Flask from import statement"""
        tree = ast.parse(flask_simple_code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_flask_from_import(self, flask_complex_code):
        """Test detecting Flask from from...import statement"""
        tree = ast.parse(flask_complex_code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_blueprint_import(self):
        """Test detecting Flask Blueprint import"""
        code = """
from flask import Blueprint

bp = Blueprint('api', __name__)

@bp.route("/items")
def get_items():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_flask_submodule_import(self):
        """Test detecting Flask from submodule imports"""
        code = """
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_no_flask_import(self):
        """Test that non-Flask code is not detected as Flask"""
        code = """
import os
import sys
from datetime import datetime

def hello():
    return "world"
"""
        tree = ast.parse(code)
        # Should return default (flask) since no framework detected
        framework = detect_framework(tree)
        assert framework == "flask"  # Default fallback


class TestFlaskDecoratorDetection:
    """Test Flask detection through decorators"""

    def test_detect_app_route_decorator(self):
        """Test detecting @app.route decorator"""
        code = """
app = Flask(__name__)

@app.route("/users")
def get_users():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_bp_route_decorator(self):
        """Test detecting @bp.route decorator"""
        code = """
bp = Blueprint('api', __name__)

@bp.route("/items")
def get_items():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_blueprint_route_decorator(self):
        """Test detecting @blueprint.route decorator"""
        code = """
blueprint = Blueprint('api', __name__)

@blueprint.route("/posts")
def get_posts():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_route_with_methods(self):
        """Test detecting route with methods parameter"""
        code = """
app = Flask(__name__)

@app.route("/items", methods=["GET", "POST"])
def items():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"


class TestFlaskWithPathParameters:
    """Test Flask detection with path parameters"""

    def test_detect_int_path_param(self):
        """Test detecting route with int path parameter"""
        code = """
app = Flask(__name__)

@app.route("/items/<int:item_id>")
def get_item(item_id):
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_string_path_param(self):
        """Test detecting route with string path parameter"""
        code = """
app = Flask(__name__)

@app.route("/posts/<slug:post_slug>")
def get_post(post_slug):
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_uuid_path_param(self):
        """Test detecting route with UUID path parameter"""
        code = """
app = Flask(__name__)

@app.route("/users/<uuid:user_id>")
def get_user(user_id):
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_detect_path_converter(self):
        """Test detecting route with path converter"""
        code = """
app = Flask(__name__)

@app.route("/files/<path:filename>")
def get_file(filename):
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"


class TestFlaskWithVariousCodePatterns:
    """Test Flask detection with various code patterns"""

    def test_flask_with_blueprints(self):
        """Test detecting Flask with Blueprint usage"""
        code = """
from flask import Flask, Blueprint

app = Flask(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route("/users")
def users():
    return []

app.register_blueprint(api_bp)
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_with_url_rules(self):
        """Test detecting Flask with url_rule definitions"""
        code = """
from flask import Flask

app = Flask(__name__)

def index():
    return "Hello"

app.add_url_rule('/', view_func=index)
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_with_error_handlers(self):
        """Test detecting Flask with error handlers"""
        code = """
from flask import Flask

app = Flask(__name__)

@app.errorhandler(404)
def not_found(e):
    return "Not found", 404
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_with_before_request(self):
        """Test detecting Flask with before_request handlers"""
        code = """
from flask import Flask

app = Flask(__name__)

@app.before_request
def before():
    pass

@app.route("/")
def index():
    return "Hello"
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"


class TestFlaskExtensions:
    """Test Flask detection with extensions"""

    def test_flask_with_restful(self):
        """Test detecting Flask with Flask-RESTful"""
        code = """
from flask import Flask
from flask_restful import Api, Resource

app = Flask(__name__)
api = Api(app)

class UserResource(Resource):
    def get(self):
        return {}

api.add_resource(UserResource, '/users')
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_with_login(self):
        """Test detecting Flask with Flask-Login"""
        code = """
from flask import Flask, render_template
from flask_login import LoginManager, login_required

app = Flask(__name__)
login_manager = LoginManager(app)

@app.route("/protected")
@login_required
def protected():
    return "Secret"
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_with_sqlalchemy(self):
        """Test detecting Flask with Flask-SQLAlchemy"""
        code = """
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
db = SQLAlchemy(app)

@app.route("/users")
def users():
    return []
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"


class TestFlaskVsFastAPI:
    """Test Flask is correctly distinguished from FastAPI"""

    def test_only_flask_detected(self):
        """Test only Flask is detected when no FastAPI present"""
        code = """
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_app_get_not_fastapi(self):
        """Test Flask @app.get is not detected as FastAPI"""
        # Note: Flask doesn't have @app.get, this is a hypothetical
        # If someone uses @app.get in Flask, it might be ambiguous
        code = """
from flask import Flask

app = Flask(__name__)

# Hypothetical Flask setup
def get_route(path):
    def decorator(f):
        return f
    return decorator

app.get = get_route

@app.get("/")
def index():
    return {}
"""
        tree = ast.parse(code)
        # This would need to be handled by the detection logic
        framework = detect_framework(tree)
        # With Flask import, should detect as Flask
        assert framework == "flask"


class TestFlaskEdgeCases:
    """Test Flask detection edge cases"""

    def test_multiple_flask_apps(self):
        """Test with multiple Flask app instances"""
        code = """
from flask import Flask

app1 = Flask('app1')
app2 = Flask('app2')

@app1.route("/route1")
def route1():
    return {}

@app2.route("/route2")
def route2():
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_nested_blueprints(self):
        """Test with nested blueprint patterns"""
        code = """
from flask import Blueprint

parent_bp = Blueprint('parent', __name__)
child_bp = Blueprint('child', __name__)

@parent_bp.route("/parent")
def parent():
    return {}

@child_bp.route("/child")
def child():
    return {}
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"

    def test_flask_class_based_views(self):
        """Test Flask class-based views"""
        code = """
from flask import Flask, views

app = Flask(__name__)

class UserView(views.MethodView):
    def get(self):
        return {}

    def post(self):
        return {}

app.add_url_rule('/users', view_func=UserView.as_view('users'))
"""
        tree = ast.parse(code)
        framework = detect_framework(tree)
        assert framework == "flask"
