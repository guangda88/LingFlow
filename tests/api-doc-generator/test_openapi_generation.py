"""Tests for OpenAPI document generation"""

import pytest
import sys
from pathlib import Path

# Add skills directory to path
skills_dir = Path(__file__).parent.parent.parent / 'skills'
sys.path.insert(0, str(skills_dir / 'api-doc-generator'))

from implementation import (
    generate_openapi_spec,
    RouteInfo,
    SchemaInfo,
)


class TestOpenAPIBasicStructure:
    """Test basic OpenAPI document structure"""

    def test_generate_minimal_document(self):
        """Test generating minimal OpenAPI document"""
        doc = generate_openapi_spec(
            routes=[],
            schemas={},
            title='Test API',
            version='1.0.0',
            base_url=''
        )

        assert doc['openapi'] == '3.0.0'
        assert doc['info']['title'] == 'Test API'
        assert doc['info']['version'] == '1.0.0'
        assert 'description' in doc['info']
        assert doc['paths'] == {}
        assert doc['components']['schemas'] == {}

    def test_openapi_version(self):
        """Test that OpenAPI version is always 3.0.0"""
        doc = generate_openapi_spec(
            routes=[],
            schemas={},
            title='Any API',
            version='2.0.0',
            base_url=''
        )

        assert doc['openapi'] == '3.0.0'

    def test_info_section(self):
        """Test info section generation"""
        doc = generate_openapi_spec(
            routes=[],
            schemas={},
            title='My Awesome API',
            version='2.1.0',
            base_url=''
        )

        assert doc['info']['title'] == 'My Awesome API'
        assert doc['info']['version'] == '2.1.0'
        assert 'Auto-generated' in doc['info']['description']

    def test_servers_section(self):
        """Test servers section with base URL"""
        doc = generate_openapi_spec(
            routes=[],
            schemas={},
            title='API',
            version='1.0.0',
            base_url='http://localhost:8000'
        )

        assert 'servers' in doc
        assert len(doc['servers']) == 1
        assert doc['servers'][0]['url'] == 'http://localhost:8000'

    def test_no_servers_without_base_url(self):
        """Test that servers section is omitted without base URL"""
        doc = generate_openapi_spec(
            routes=[],
            schemas={},
            title='API',
            version='1.0.0',
            base_url=''
        )

        assert 'servers' not in doc


class TestPathGeneration:
    """Test path generation from routes"""

    def test_single_route_path(self):
        """Test generating path for single route"""
        routes = [
            RouteInfo(
                path='/users',
                method='GET',
                handler_name='get_users'
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        assert '/users' in doc['paths']
        assert 'get' in doc['paths']['/users']

    def test_multiple_routes_same_path(self):
        """Test generating multiple methods for same path"""
        routes = [
            RouteInfo(path='/users', method='GET', handler_name='get_users'),
            RouteInfo(path='/users', method='POST', handler_name='create_user'),
            RouteInfo(path='/users', method='DELETE', handler_name='delete_users'),
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        assert 'get' in doc['paths']['/users']
        assert 'post' in doc['paths']['/users']
        assert 'delete' in doc['paths']['/users']

    def test_multiple_different_paths(self):
        """Test generating multiple different paths"""
        routes = [
            RouteInfo(path='/users', method='GET', handler_name='get_users'),
            RouteInfo(path='/posts', method='GET', handler_name='get_posts'),
            RouteInfo(path='/comments', method='GET', handler_name='get_comments'),
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        assert len(doc['paths']) == 3
        assert '/users' in doc['paths']
        assert '/posts' in doc['paths']
        assert '/comments' in doc['paths']

    def test_path_parameters(self):
        """Test paths with parameters"""
        routes = [
            RouteInfo(
                path='/users/{user_id}',
                method='GET',
                handler_name='get_user',
                parameters=[
                    {'name': 'user_id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
                ]
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        assert '/users/{user_id}' in doc['paths']
        assert 'parameters' in doc['paths']['/users/{user_id}']['get']
        assert doc['paths']['/users/{user_id}']['get']['parameters'][0]['name'] == 'user_id'


class TestOperationGeneration:
    """Test operation (method) generation details"""

    def test_operation_summary(self, route_info_get):
        """Test operation summary"""
        doc = generate_openapi_spec([route_info_get], {}, 'API', '1.0.0', '')

        operation = doc['paths']['/api/users']['get']
        assert operation['summary'] == 'List all users'

    def test_operation_summary_fallback(self):
        """Test operation summary falls back to handler name"""
        routes = [
            RouteInfo(
                path='/items',
                method='GET',
                handler_name='get_items'
                # No summary
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/items']['get']
        assert operation['summary'] == 'get_items'

    def test_operation_id(self):
        """Test operationId is set to handler name"""
        routes = [
            RouteInfo(
                path='/users',
                method='GET',
                handler_name='list_all_users',
                summary='List users'
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/users']['get']
        assert operation['operationId'] == 'list_all_users'

    def test_operation_description(self, route_info_get):
        """Test operation description"""
        doc = generate_openapi_spec([route_info_get], {}, 'API', '1.0.0', '')

        operation = doc['paths']['/api/users']['get']
        assert operation['description'] == 'Returns paginated list of users'

    def test_operation_tags(self, route_info_get):
        """Test operation tags"""
        doc = generate_openapi_spec([route_info_get], {}, 'API', '1.0.0', '')

        operation = doc['paths']['/api/users']['get']
        assert operation['tags'] == ['users']

    def test_operation_parameters(self, route_info_get):
        """Test operation parameters"""
        doc = generate_openapi_spec([route_info_get], {}, 'API', '1.0.0', '')

        operation = doc['paths']['/api/users']['get']
        assert 'parameters' in operation
        assert len(operation['parameters']) == 2
        assert operation['parameters'][0]['name'] == 'skip'

    def test_operation_request_body(self, route_info_post):
        """Test operation request body"""
        doc = generate_openapi_spec([route_info_post], {}, 'API', '1.0.0', '')

        operation = doc['paths']['/api/users']['post']
        assert 'requestBody' in operation
        assert 'content' in operation['requestBody']
        assert 'application/json' in operation['requestBody']['content']

    def test_operation_deprecated(self, route_info_deprecated):
        """Test deprecated operation"""
        doc = generate_openapi_spec([route_info_deprecated], {}, 'API', '1.0.0', '')

        operation = doc['paths']['/api/legacy']['get']
        assert operation['deprecated'] is True

    def test_operation_not_deprecated_by_default(self):
        """Test operations are not deprecated by default"""
        routes = [
            RouteInfo(
                path='/active',
                method='GET',
                handler_name='active_endpoint',
                deprecated=False
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/active']['get']
        assert 'deprecated' not in operation


class TestResponseGeneration:
    """Test response generation"""

    def test_default_response(self):
        """Test default 200 response"""
        routes = [
            RouteInfo(
                path='/test',
                method='GET',
                handler_name='test',
                responses={}
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/test']['get']
        assert '200' in operation['responses']

    def test_custom_responses(self):
        """Test custom response codes"""
        routes = [
            RouteInfo(
                path='/users/{user_id}',
                method='GET',
                handler_name='get_user',
                responses={
                    '200': {'description': 'User found'},
                    '404': {'description': 'User not found'},
                    '500': {'description': 'Server error'}
                }
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/users/{user_id}']['get']
        assert '200' in operation['responses']
        assert '404' in operation['responses']
        assert '500' in operation['responses']
        assert operation['responses']['404']['description'] == 'User not found'

    def test_response_with_content(self):
        """Test response with content type"""
        routes = [
            RouteInfo(
                path='/users',
                method='GET',
                handler_name='get_users',
                responses={
                    '200': {
                        'description': 'Success',
                        'content': {
                            'application/json': {
                                'schema': {'type': 'array'}
                            }
                        }
                    }
                }
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/users']['get']
        assert 'content' in operation['responses']['200']
        assert operation['responses']['200']['content']['application/json']['schema']['type'] == 'array'


class TestSchemaGeneration:
    """Test components/schemas generation"""

    def test_empty_schemas(self):
        """Test document with no schemas"""
        doc = generate_openapi_spec([], {}, 'API', '1.0.0', '')

        assert doc['components']['schemas'] == {}

    def test_single_schema(self, schema_user):
        """Test document with single schema"""
        doc = generate_openapi_spec([], {'User': schema_user}, 'API', '1.0.0', '')

        assert 'User' in doc['components']['schemas']
        assert doc['components']['schemas']['User']['type'] == 'object'

    def test_schema_properties(self, schema_user):
        """Test schema properties"""
        doc = generate_openapi_spec([], {'User': schema_user}, 'API', '1.0.0', '')

        user_schema = doc['components']['schemas']['User']
        assert 'properties' in user_schema
        assert 'id' in user_schema['properties']
        assert 'name' in user_schema['properties']
        assert 'email' in user_schema['properties']

    def test_schema_required_fields(self, schema_user):
        """Test schema required fields"""
        doc = generate_openapi_spec([], {'User': schema_user}, 'API', '1.0.0', '')

        user_schema = doc['components']['schemas']['User']
        assert 'required' in user_schema
        assert set(user_schema['required']) == {'id', 'name', 'email'}

    def test_schema_description(self, schema_user):
        """Test schema description"""
        doc = generate_openapi_spec([], {'User': schema_user}, 'API', '1.0.0', '')

        user_schema = doc['components']['schemas']['User']
        assert user_schema['description'] == 'User model'

    def test_multiple_schemas(self):
        """Test document with multiple schemas"""
        schemas = {
            'User': SchemaInfo(
                name='User',
                type='object',
                properties={'id': {'type': 'integer'}, 'name': {'type': 'string'}}
            ),
            'Post': SchemaInfo(
                name='Post',
                type='object',
                properties={'id': {'type': 'integer'}, 'title': {'type': 'string'}}
            ),
        }

        doc = generate_openapi_spec([], schemas, 'API', '1.0.0', '')

        assert len(doc['components']['schemas']) == 2
        assert 'User' in doc['components']['schemas']
        assert 'Post' in doc['components']['schemas']


class TestCompleteOpenAPIGeneration:
    """Test complete OpenAPI document generation"""

    def test_full_document_with_routes_and_schemas(self, route_info_get, route_info_post, schema_user):
        """Test generating document with routes and schemas"""
        routes = [route_info_get, route_info_post]
        schemas = {'User': schema_user}

        doc = generate_openapi_spec(routes, schemas, 'User API', '1.0.0', 'http://api.example.com')

        # Verify structure
        assert doc['openapi'] == '3.0.0'
        assert doc['info']['title'] == 'User API'
        assert doc['servers'][0]['url'] == 'http://api.example.com'

        # Verify paths
        assert '/api/users' in doc['paths']
        assert 'get' in doc['paths']['/api/users']
        assert 'post' in doc['paths']['/api/users']

        # Verify schemas
        assert 'User' in doc['components']['schemas']

    def test_realistic_api_document(self):
        """Test generating realistic API document"""
        routes = [
            RouteInfo(
                path='/api/users',
                method='GET',
                handler_name='list_users',
                summary='List all users',
                tags=['users'],
                parameters=[
                    {'name': 'page', 'in': 'query', 'required': False, 'schema': {'type': 'integer'}},
                    {'name': 'limit', 'in': 'query', 'required': False, 'schema': {'type': 'integer'}}
                ],
                responses={'200': {'description': 'Success'}}
            ),
            RouteInfo(
                path='/api/users/{user_id}',
                method='GET',
                handler_name='get_user',
                summary='Get user by ID',
                tags=['users'],
                parameters=[
                    {'name': 'user_id', 'in': 'path', 'required': True, 'schema': {'type': 'string'}}
                ],
                responses={'200': {'description': 'Success'}, '404': {'description': 'Not found'}}
            ),
            RouteInfo(
                path='/api/users',
                method='POST',
                handler_name='create_user',
                summary='Create new user',
                tags=['users'],
                request_body={
                    'content': {
                        'application/json': {
                            'schema': {'$ref': '#/components/schemas/UserCreate'}
                        }
                    }
                },
                responses={'201': {'description': 'Created'}, '400': {'description': 'Bad request'}}
            ),
        ]

        schemas = {
            'UserCreate': SchemaInfo(
                name='UserCreate',
                type='object',
                properties={
                    'name': {'type': 'string'},
                    'email': {'type': 'string'}
                },
                required=['name', 'email']
            )
        }

        doc = generate_openapi_spec(routes, schemas, 'User Management API', '1.0.0', 'http://localhost:8000/api')

        # Verify all paths are present
        assert '/api/users' in doc['paths']
        assert '/api/users/{user_id}' in doc['paths']

        # Verify methods on /api/users
        assert 'get' in doc['paths']['/api/users']
        assert 'post' in doc['paths']['/api/users']

        # Verify parameters on GET /api/users
        get_params = doc['paths']['/api/users']['get']['parameters']
        assert len(get_params) == 2

        # Verify request body on POST /api/users
        post_body = doc['paths']['/api/users']['post']['requestBody']
        assert 'UserCreate' in post_body['content']['application/json']['schema']['$ref']

        # Verify schemas
        assert 'UserCreate' in doc['components']['schemas']
        assert 'name' in doc['components']['schemas']['UserCreate']['properties']


class TestEdgeCases:
    """Test edge cases in OpenAPI generation"""

    def test_empty_route_list(self):
        """Test with empty route list"""
        doc = generate_openapi_spec([], {}, 'API', '1.0.0', '')

        assert doc['paths'] == {}

    def test_route_with_empty_tags(self):
        """Test route with empty tags list"""
        routes = [
            RouteInfo(
                path='/test',
                method='GET',
                handler_name='test',
                tags=[]
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        # Tags should still be present but empty
        operation = doc['paths']['/test']['get']
        assert operation.get('tags') == []

    def test_route_with_no_parameters(self):
        """Test route with no parameters"""
        routes = [
            RouteInfo(
                path='/test',
                method='GET',
                handler_name='test',
                parameters=[]
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/test']['get']
        assert 'parameters' not in operation or len(operation.get('parameters', [])) == 0

    def test_special_characters_in_summary(self):
        """Test handling special characters in summary"""
        routes = [
            RouteInfo(
                path='/test',
                method='GET',
                handler_name='test',
                summary='Test with "quotes" and \'apostrophes\''
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        assert '"' in doc['paths']['/test']['get']['summary']

    def test_unicode_in_description(self):
        """Test handling Unicode in descriptions"""
        routes = [
            RouteInfo(
                path='/test',
                method='GET',
                handler_name='test',
                description='Description with émojis 🎉 and 中文'
            )
        ]

        doc = generate_openapi_spec(routes, {}, 'API', '1.0.0', '')

        operation = doc['paths']['/test']['get']
        assert '🎉' in operation['description']
        assert '中文' in operation['description']
