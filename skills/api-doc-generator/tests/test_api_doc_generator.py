"""api-doc-generator 技能测试"""

import unittest
import tempfile
import shutil
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from implementation import execute_skill, scan_code, generate_openapi_spec, RouteInfo


class TestAPIDocGenerator(unittest.TestCase):
    """测试 API 文档生成器"""

    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        shutil.rmtree(self.test_dir)

    def test_fastapi_route_detection(self):
        """测试 FastAPI 路由检测"""
        # 创建测试文件
        test_file = Path(self.test_dir) / "test_app.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/users")
async def get_users():
    """获取用户列表"""
    return []

@app.post("/users/{user_id}")
async def update_user(user_id: int):
    """更新用户信息"""
    return {"id": user_id}
''')

        routes, schemas = scan_code(str(test_file), 'fastapi')

        self.assertEqual(len(routes), 2)
        self.assertEqual(routes[0].path, '/users')
        self.assertEqual(routes[0].method, 'GET')
        self.assertEqual(routes[1].path, '/users/{user_id}')
        self.assertEqual(routes[1].method, 'POST')

    def test_flask_route_detection(self):
        """测试 Flask 路由检测"""
        test_file = Path(self.test_dir) / "flask_app.py"
        test_file.write_text('''
from flask import Flask

app = Flask(__name__)

@app.route("/items", methods=["GET"])
def get_items():
    """获取物品列表"""
    return []

@app.route("/items/<int:item_id>", methods=["GET", "PUT"])
def get_item(item_id):
    """获取单个物品"""
    return {"id": item_id}
''')

        routes, schemas = scan_code(str(test_file), 'flask')

        self.assertEqual(len(routes), 3)  # GET /items, GET /items/<id>, PUT /items/<id>

    def test_openapi_generation(self):
        """测试 OpenAPI 文档生成"""
        from implementation import RouteInfo

        routes = [
            RouteInfo(
                path='/api/users',
                method='GET',
                handler_name='get_users',
                summary='获取用户列表',
                description='返回所有用户的分页列表',
                tags=['users'],
                responses={'200': {'description': '成功'}}
            ),
            RouteInfo(
                path='/api/users/{user_id}',
                method='GET',
                handler_name='get_user',
                summary='获取单个用户',
                parameters=[
                    {'name': 'user_id', 'in': 'path', 'required': True, 'schema': {'type': 'integer'}}
                ],
                responses={'200': {'description': '成功'}}
            )
        ]

        doc = generate_openapi_spec(
            routes=routes,
            schemas={},
            title='Test API',
            version='1.0.0',
            base_url=''
        )

        self.assertEqual(doc['openapi'], '3.0.0')
        self.assertEqual(doc['info']['title'], 'Test API')
        self.assertIn('/api/users', doc['paths'])
        self.assertIn('get', doc['paths']['/api/users'])

    def test_pydantic_model_extraction(self):
        """测试 Pydantic 模型提取"""
        test_file = Path(self.test_dir) / "models.py"
        test_file.write_text('''
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    email: str
    age: int = None

class Config:
    schema_extra = {"example": {"name": "Test"}}
''')

        routes, schemas = scan_code(str(test_file), 'fastapi')

        self.assertIn('UserCreate', schemas)
        self.assertIn('name', schemas['UserCreate'].properties)
        self.assertIn('email', schemas['UserCreate'].properties)

    def test_execute_skill_basic(self):
        """测试基本技能执行"""
        test_file = Path(self.test_dir) / "basic.py"
        test_file.write_text('''
from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
def hello():
    """Hello World endpoint"""
    return {"message": "Hello"}
''')

        result = execute_skill({
            'input': str(test_file),
            'format': 'json'
        })

        self.assertTrue(result['success'])
        self.assertEqual(result['routes_count'], 1)
        self.assertIn('openapi', result)

    def test_yaml_output(self):
        """测试 YAML 输出"""
        test_file = Path(self.test_dir) / "yaml_test.py"
        test_file.write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/test")
def test():
    return {}
''')

        output_file = Path(self.test_dir) / "output.yaml"

        result = execute_skill({
            'input': str(test_file),
            'output': str(output_file),
            'format': 'yaml'
        })

        self.assertTrue(result['success'])
        self.assertTrue(output_file.exists())

    def test_framework_auto_detection(self):
        """测试框架自动检测"""
        # FastAPI 检测
        fastapi_file = Path(self.test_dir) / "fastapi_detect.py"
        fastapi_file.write_text('''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def index():
    return {}
''')

        routes, _ = scan_code(str(fastapi_file), 'auto')
        self.assertGreater(len(routes), 0)

        # Flask 检测
        flask_file = Path(self.test_dir) / "flask_detect.py"
        flask_file.write_text('''
from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return {}
''')

        routes, _ = scan_code(str(flask_file), 'auto')
        self.assertGreater(len(routes), 0)


if __name__ == '__main__':
    unittest.main()
