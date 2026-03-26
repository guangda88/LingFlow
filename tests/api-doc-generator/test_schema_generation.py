"""Tests for schema/Pydantic model extraction"""

import ast
import pytest
import sys
from pathlib import Path

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / 'skills'
sys.path.insert(0, str(skills_dir / 'api-doc-generator'))

from implementation import (
    extract_schemas,
    SchemaInfo,
    _is_pydantic_model,
    _is_dataclass,
)


class TestPydanticModelExtraction:
    """Test extraction of Pydantic models"""

    def test_extract_simple_pydantic_model(self, pydantic_models_code):
        """Test extracting a simple Pydantic model"""
        tree = ast.parse(pydantic_models_code)
        schemas = extract_schemas(tree, pydantic_models_code)

        assert 'UserBase' in schemas
        assert 'UserCreate' in schemas
        assert 'User' in schemas

    def test_extract_model_properties(self, pydantic_models_code):
        """Test extracting model properties"""
        tree = ast.parse(pydantic_models_code)
        schemas = extract_schemas(tree, pydantic_models_code)

        user_base = schemas['UserBase']
        assert 'name' in user_base.properties
        assert 'email' in user_base.properties
        assert user_base.properties['name']['type'] == 'string'

    def test_extract_model_with_optional_fields(self, pydantic_models_code):
        """Test extracting model with optional fields"""
        tree = ast.parse(pydantic_models_code)
        schemas = extract_schemas(tree, pydantic_models_code)

        user_create = schemas['UserCreate']
        assert 'password' in user_create.properties
        # Password is required in UserCreate

    def test_extract_nested_models(self):
        """Test extracting models that inherit from each other"""
        code = '''
from pydantic import BaseModel

class BaseItem(BaseModel):
    id: int
    name: str

class Item(BaseItem):
    description: str
    price: float
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'BaseItem' in schemas
        assert 'Item' in schemas
        assert 'id' in schemas['BaseItem'].properties
        assert 'description' in schemas['Item'].properties

    def test_extract_model_with_field_descriptions(self):
        """Test extracting Field descriptions"""
        code = '''
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(..., description="User's name")
    email: str = Field(..., description="User's email")
    age: int = Field(None, description="User's age")
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'User' in schemas
        assert 'name' in schemas['User'].properties
        assert 'email' in schemas['User'].properties
        assert 'age' in schemas['User'].properties

    def test_extract_model_with_list_types(self):
        """Test extracting models with List types"""
        code = '''
from pydantic import BaseModel
from typing import List

class User(BaseModel):
    tags: List[str]
    scores: List[int]

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'User' in schemas
        assert 'tags' in schemas['User'].properties
        assert schemas['User'].properties['tags']['type'] == 'array'
        assert 'PaginatedResponse' in schemas

    def test_extract_model_with_config_class(self):
        """Test extracting model with Config class"""
        code = '''
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

    class Config:
        schema_extra = {"example": {"name": "Test"}}
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'User' in schemas
        # Config class doesn't affect basic schema extraction

    def test_extract_model_with_generic_model(self):
        """Test extracting GenericModel"""
        code = '''
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: list
    total: int
    page: int
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        # Should still extract the model
        assert 'PaginatedResponse' in schemas

    def test_extract_multiple_models(self):
        """Test extracting multiple models from one file"""
        code = '''
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

class Post(BaseModel):
    id: int
    title: str
    author_id: int

class Comment(BaseModel):
    id: int
    content: str
    post_id: int
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert len(schemas) == 3
        assert 'User' in schemas
        assert 'Post' in schemas
        assert 'Comment' in schemas


class TestDataclassExtraction:
    """Test extraction of dataclass models"""

    def test_extract_simple_dataclass(self, dataclass_models_code):
        """Test extracting a simple dataclass"""
        tree = ast.parse(dataclass_models_code)
        schemas = extract_schemas(tree, dataclass_models_code)

        assert 'User' in schemas
        assert 'Post' in schemas

    def test_extract_dataclass_properties(self, dataclass_models_code):
        """Test extracting dataclass properties"""
        tree = ast.parse(dataclass_models_code)
        schemas = extract_schemas(tree, dataclass_models_code)

        user = schemas['User']
        assert 'id' in user.properties
        assert 'name' in user.properties
        assert 'email' in user.properties
        assert 'age' in user.properties

    def test_extract_dataclass_with_default_values(self):
        """Test extracting dataclass with default values"""
        code = '''
from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    name: str
    email: Optional[str] = None
    age: int = 0
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        user = schemas['User']
        # Fields with defaults should not be in required
        assert 'id' in user.properties
        assert 'name' in user.properties

    def test_extract_nested_dataclass(self):
        """Test extracting nested dataclasses"""
        code = '''
from dataclasses import dataclass

@dataclass
class Address:
    street: str
    city: str

@dataclass
class User:
    id: int
    name: str
    address: Address
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'Address' in schemas
        assert 'User' in schemas
        assert 'address' in schemas['User'].properties


class TestRequiredFieldDetection:
    """Test detection of required fields"""

    def test_pydantic_required_fields(self):
        """Test detecting required fields in Pydantic models"""
        code = '''
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    required_field: str
    optional_field: Optional[str] = None
    another_required: int
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        user = schemas['User']
        # Required fields detection based on default values
        assert 'required_field' in user.properties

    def test_dataclass_required_fields(self):
        """Test detecting required fields in dataclasses"""
        code = '''
from dataclasses import dataclass

@dataclass
class Item:
    required: str
    with_default: str = "default"
    optional: int = None
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        item = schemas['Item']
        assert 'required' in item.properties
        assert 'with_default' in item.properties


class TestTypeAnnotationExtraction:
    """Test extraction of type annotations"""

    def test_extract_simple_types(self):
        """Test extracting simple type annotations"""
        code = '''
from pydantic import BaseModel

class Item(BaseModel):
    str_field: str
    int_field: int
    float_field: float
    bool_field: bool
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        item = schemas['Item']
        assert item.properties['str_field']['type'] == 'string'
        assert item.properties['int_field']['type'] == 'integer'
        assert item.properties['float_field']['type'] == 'number'
        assert item.properties['bool_field']['type'] == 'boolean'

    def test_extract_optional_types(self):
        """Test extracting Optional type annotations"""
        code = '''
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    name: Optional[str]
    age: Optional[int]
    email: str
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        user = schemas['User']
        assert user.properties['name']['type'] == 'string'
        assert user.properties['age']['type'] == 'integer'

    def test_extract_list_types(self):
        """Test extracting List type annotations"""
        code = '''
from pydantic import BaseModel
from typing import List

class Item(BaseModel):
    tags: List[str]
    numbers: List[int]
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        item = schemas['Item']
        assert item.properties['tags']['type'] == 'array'
        assert item.properties['numbers']['type'] == 'array'

    def test_extract_dict_types(self):
        """Test extracting dict type annotations"""
        code = '''
from pydantic import BaseModel

class Item(BaseModel):
    metadata: dict
    settings: dict
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        item = schemas['Item']
        assert item.properties['metadata']['type'] == 'object'
        assert item.properties['settings']['type'] == 'object'


class TestIsPydanticModel:
    """Test _is_pydantic_model helper function"""

    def test_detect_basemodel_inheritance(self):
        """Test detecting BaseModel inheritance"""
        code = '''
from pydantic import BaseModel

class User(BaseModel):
    name: str
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_pydantic_model(class_node, code) is True

    def test_detect_generic_model_inheritance(self):
        """Test detecting GenericModel inheritance"""
        code = '''
from pydantic import GenericModel

class Paginated(GenericModel):
    items: list
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_pydantic_model(class_node, code) is True

    def test_detect_config_class(self):
        """Test detecting Config class as indicator"""
        code = '''
class User:
    name: str

    class Config:
        orm_mode = True
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_pydantic_model(class_node, code) is True

    def test_reject_non_pydantic_class(self):
        """Test rejecting non-Pydantic class"""
        code = '''
class User:
    name: str

    def greet(self):
        return f"Hello {self.name}"
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_pydantic_model(class_node, code) is False


class TestIsDataclass:
    """Test _is_dataclass helper function"""

    def test_detect_dataclass_decorator(self):
        """Test detecting @dataclass decorator"""
        code = '''
from dataclasses import dataclass

@dataclass
class User:
    name: str
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_dataclass(class_node) is True

    def test_reject_regular_class(self):
        """Test rejecting regular class"""
        code = '''
class User:
    name: str
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_dataclass(class_node) is False

    def test_detect_dataclass_with_parentheses(self):
        """Test detecting @dataclass() with parentheses"""
        code = '''
from dataclasses import dataclass

@dataclass()
class Item:
    id: int
'''
        tree = ast.parse(code)
        class_node = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)][0]
        assert _is_dataclass(class_node) is True


class TestComplexSchemaScenarios:
    """Test schema extraction in complex scenarios"""

    def test_mixed_pydantic_and_dataclass(self):
        """Test extracting both Pydantic and dataclass models"""
        code = '''
from pydantic import BaseModel
from dataclasses import dataclass

class PydanticUser(BaseModel):
    id: int
    name: str

@dataclass
class DataclassUser:
    id: int
    name: str
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'PydanticUser' in schemas
        assert 'DataclassUser' in schemas

    def test_models_in_class_methods(self):
        """Test extracting models from nested class definitions"""
        code = '''
from pydantic import BaseModel

class Factory:
    class User(BaseModel):
        id: int
        name: str

    class Item(BaseModel):
        id: int
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        # Should extract models from nested classes too
        assert 'User' in schemas
        assert 'Item' in schemas

    def test_empty_model(self):
        """Test extracting empty model"""
        code = '''
from pydantic import BaseModel

class Empty(BaseModel):
    pass
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        assert 'Empty' in schemas
        assert len(schemas['Empty'].properties) == 0

    def test_model_with_annotations_only(self):
        """Test extracting model with only annotations"""
        code = '''
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str
    email: str
'''
        tree = ast.parse(code)
        schemas = extract_schemas(tree, code)

        user = schemas['User']
        assert len(user.properties) == 3
        assert set(user.properties.keys()) == {'id', 'name', 'email'}
