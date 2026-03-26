"""database-schema-designer 技能实现 - 从业务需求设计数据库表结构

异常处理:
    - DatabaseSchemaError: 数据库设计相关错误
    - ValueError: 无效的数据库类型或配置
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# 导入自定义异常
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from exceptions import DatabaseSchemaError

# 导入 Pydantic 验证模型
try:
    from pydantic import ValidationError as PydanticValidationError
    from .validation import DatabaseSchemaParams
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============== 数据类型定义 ==============
class DatabaseType(Enum):
    """支持的数据库类型"""
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    MSSQL = "mssql"
    ORACLE = "oracle"


class RelationType(Enum):
    """实体关系类型"""
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"  # 添加 N:1 关系
    MANY_TO_MANY = "N:M"
    NONE = ""


# ============== 数据类型映射 ==============
DATA_TYPE_MAPPING = {
    DatabaseType.MYSQL: {
        'string': 'VARCHAR(255)',
        'text': 'TEXT',
        'integer': 'INT',
        'bigint': 'BIGINT',
        'decimal': 'DECIMAL(10,2)',
        'boolean': 'TINYINT(1)',
        'date': 'DATE',
        'datetime': 'DATETIME',
        'timestamp': 'TIMESTAMP',
        'json': 'JSON',
        'uuid': 'CHAR(36)',
        'email': 'VARCHAR(255)',
        'url': 'VARCHAR(500)',
    },
    DatabaseType.POSTGRESQL: {
        'string': 'VARCHAR(255)',
        'text': 'TEXT',
        'integer': 'INTEGER',
        'bigint': 'BIGINT',
        'decimal': 'DECIMAL(10,2)',
        'boolean': 'BOOLEAN',
        'date': 'DATE',
        'datetime': 'TIMESTAMP',
        'timestamp': 'TIMESTAMP',
        'json': 'JSONB',
        'uuid': 'UUID',
        'email': 'VARCHAR(255)',
        'url': 'VARCHAR(500)',
    },
    DatabaseType.SQLITE: {
        'string': 'TEXT',
        'text': 'TEXT',
        'integer': 'INTEGER',
        'bigint': 'INTEGER',
        'decimal': 'REAL',
        'boolean': 'INTEGER',
        'date': 'TEXT',
        'datetime': 'TEXT',
        'timestamp': 'TEXT',
        'json': 'TEXT',
        'uuid': 'TEXT',
        'email': 'TEXT',
        'url': 'TEXT',
    }
}


# ============== 数据模型 ==============
@dataclass
class Column:
    """列定义"""
    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key: Optional[str] = None  # 引用的表
    foreign_key_column: Optional[str] = None  # 引用的列
    unique: bool = False
    default: Optional[Any] = None
    auto_increment: bool = False
    comment: str = ""

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'data_type': self.data_type,
            'nullable': self.nullable,
            'primary_key': self.primary_key,
            'foreign_key': self.foreign_key,
            'foreign_key_column': self.foreign_key_column,
            'unique': self.unique,
            'default': self.default,
            'auto_increment': self.auto_increment,
            'comment': self.comment
        }


@dataclass
class Table:
    """表定义"""
    name: str
    columns: List[Column] = field(default_factory=list)
    comment: str = ""
    indexes: List[Dict] = field(default_factory=list)

    def add_column(self, column: Column):
        self.columns.append(column)

    def add_index(self, index_name: str, columns: List[str], unique: bool = False):
        self.indexes.append({
            'name': index_name,
            'columns': columns,
            'unique': unique
        })

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'columns': [col.to_dict() for col in self.columns],
            'comment': self.comment,
            'indexes': self.indexes
        }


@dataclass
class Entity:
    """业务实体"""
    name: str
    description: str = ""
    attributes: List[Dict] = field(default_factory=list)
    relations: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'attributes': self.attributes,
            'relations': self.relations
        }


@dataclass
class SchemaDesign:
    """数据库设计"""
    name: str
    entities: List[Entity] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    database_type: DatabaseType = DatabaseType.MYSQL
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'entities': [e.to_dict() for e in self.entities],
            'tables': [t.to_dict() for t in self.tables],
            'database_type': self.database_type.value,
            'created_at': self.created_at
        }


# ============== 核心功能函数 ==============

def design_schema(params: Dict) -> Dict:
    """从业务需求设计数据库架构

    Args:
        params: 设计参数，包含:
            - requirement: 业务需求描述文本
            - database_type: 数据库类型 (默认 mysql)
            - naming_convention: 命名约定 (snake_case, camelCase, PascalCase)
            - include_timestamps: 是否包含时间戳字段 (默认 True)
            - include_soft_delete: 是否包含软删除 (默认 False)

    Returns:
        设计结果字典

    Raises:
        DatabaseSchemaError: 数据库设计过程中的错误
        ValueError: 无效的数据库类型
    """
    requirement = params.get('requirement', '')
    database_type_str = params.get('database_type', 'mysql')
    naming_convention = params.get('naming_convention', 'snake_case')
    include_timestamps = params.get('include_timestamps', True)
    include_soft_delete = params.get('include_soft_delete', False)

    if not requirement:
        return {"error": "请提供业务需求描述 (requirement 参数)"}

    # 解析数据库类型
    try:
        database_type = DatabaseType(database_type_str.lower())
    except ValueError as e:
        raise ValueError(f'不支持的数据库类型: {database_type_str}. 支持的类型: {[t.value for t in DatabaseType]}')

    # 创建设计
    design = SchemaDesign(
        name=extract_project_name(requirement),
        database_type=database_type
    )

    # 从需求中识别实体
    entities = extract_entities(requirement, naming_convention)
    design.entities = entities

    # 分析实体关系
    relations = analyze_relations(requirement, entities)
    for entity, rels in zip(entities, relations):
        entity.relations = rels

    # 生成表结构
    design.tables = generate_tables(
        entities,
        relations,
        database_type,
        include_timestamps,
        include_soft_delete,
        naming_convention
    )

    # 生成ER图
    er_diagram = generate_er_diagram(design)

    # 生成DDL
    ddl = generate_ddl(design)

    return {
        'design': design.to_dict(),
        'er_diagram': er_diagram,
        'ddl': ddl,
        'summary': generate_design_summary(design)
    }


def extract_project_name(requirement: str) -> str:
    """从需求中提取项目名称"""
    lines = requirement.strip().split('\n')
    first_line = lines[0] if lines else requirement[:50]

    # 尝试提取标题
    if ':' in first_line:
        return first_line.split(':')[0].strip()
    if '==' in first_line:
        return first_line.replace('=', '').strip()

    return "未命名项目"


def extract_entities(requirement: str, naming_convention: str) -> List[Entity]:
    """从需求文本中识别实体

    基于NLP模式识别:
    1. 名词短语识别
    2. 常见实体关键词
    3. 属性关联分析
    """
    entities = []
    lines = requirement.split('\n')

    # 常见实体关键词模式
    entity_patterns = [
        r'(用户|User|用户信息)',
        r'(订单|Order|订单信息)',
        r'(产品|Product|商品)',
        r'(分类|Category|类别)',
        r'(评论|Comment|评价)',
        r'(文章|Article|帖子)',
        r'(标签|Tag)',
        r'(角色|Role|权限)',
        r'(部门|Department)',
        r'(员工|Employee|Staff)',
        r'(客户|Customer)',
        r'(供应商|Supplier)',
        r'(库存|Inventory|Stock)',
        r'(购物车|Cart)',
        r'(支付|Payment)',
        r'(物流|Shipping|Delivery)',
        r'(地址|Address)',
        r'(消息|Message|通知)',
        r'(文件|File|附件)',
        r'(设置|Setting|配置)',
    ]

    # 主键命名映射
    primary_key_names = {
        'User': 'user_id',
        'users': 'user_id',
        '用户': 'user_id',
        'Order': 'order_id',
        'orders': 'order_id',
        '订单': 'order_id',
        'Product': 'product_id',
        'products': 'product_id',
        '产品': 'product_id',
        '商品': 'product_id',
    }

    # 实体属性模板
    attribute_templates = {
        'user': [
            {'name': 'username', 'type': 'string', 'nullable': False},
            {'name': 'email', 'type': 'email', 'nullable': False, 'unique': True},
            {'name': 'password_hash', 'type': 'string', 'nullable': False},
            {'name': 'nickname', 'type': 'string'},
            {'name': 'avatar', 'type': 'string'},
            {'name': 'status', 'type': 'integer', 'default': 1},
        ],
        'order': [
            {'name': 'order_no', 'type': 'string', 'nullable': False, 'unique': True},
            {'name': 'amount', 'type': 'decimal', 'nullable': False},
            {'name': 'status', 'type': 'integer', 'default': 0},
            {'name': 'payment_status', 'type': 'integer', 'default': 0},
        ],
        'product': [
            {'name': 'name', 'type': 'string', 'nullable': False},
            {'name': 'description', 'type': 'text'},
            {'name': 'price', 'type': 'decimal', 'nullable': False},
            {'name': 'stock', 'type': 'integer', 'default': 0},
            {'name': 'status', 'type': 'integer', 'default': 1},
        ],
        'category': [
            {'name': 'name', 'type': 'string', 'nullable': False},
            {'name': 'parent_id', 'type': 'integer'},
            {'name': 'sort_order', 'type': 'integer', 'default': 0},
        ],
        'comment': [
            {'name': 'content', 'type': 'text', 'nullable': False},
            {'name': 'rating', 'type': 'integer'},
        ],
        'article': [
            {'name': 'title', 'type': 'string', 'nullable': False},
            {'name': 'content', 'type': 'text', 'nullable': False},
            {'name': 'views', 'type': 'integer', 'default': 0},
        ],
    }

    # 从需求中提取实体
    found_entities = set()
    for pattern in entity_patterns:
        matches = re.finditer(pattern, requirement, re.IGNORECASE)
        for match in matches:
            entity_name = match.group(1)
            # 标准化实体名
            normalized = normalize_entity_name(entity_name, naming_convention)
            found_entities.add(normalized)

    # 如果没有找到实体，尝试从行中提取
    if not found_entities:
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # 尝试识别名词
                words = re.findall(r'\b[A-Z][a-z]+\b|\b[\u4e00-\u9fa5]{2,}\b', line)
                for word in words:
                    if len(word) >= 2:
                        found_entities.add(word)

    # 创建实体对象
    for entity_name in sorted(found_entities):
        # 获取英文名称
        english_name = chinese_to_english(entity_name)
        key = english_name.lower()

        entity = Entity(
            name=apply_naming_convention(entity_name, naming_convention, 'table'),
            description=f"{entity_name}实体"
        )

        # 添加模板属性
        if key in attribute_templates:
            for attr in attribute_templates[key]:
                entity.attributes.append(attr)

        entities.append(entity)

    return entities


def normalize_entity_name(name: str, naming_convention: str) -> str:
    """标准化实体名称"""
    # 移除常见的后缀
    name = re.sub(r'(信息|数据)$', '', name)
    return name


def chinese_to_english(chinese: str) -> str:
    """中文转英文映射"""
    mapping = {
        '用户': 'User',
        '订单': 'Order',
        '产品': 'Product',
        '商品': 'Product',
        '分类': 'Category',
        '评论': 'Comment',
        '文章': 'Article',
        '标签': 'Tag',
        '角色': 'Role',
        '部门': 'Department',
        '员工': 'Employee',
        '客户': 'Customer',
        '供应商': 'Supplier',
        '库存': 'Inventory',
        '购物车': 'Cart',
        '支付': 'Payment',
        '物流': 'Shipping',
        '地址': 'Address',
        '消息': 'Message',
        '文件': 'File',
        '设置': 'Setting',
    }
    return mapping.get(chinese, chinese)


def apply_naming_convention(name: str, convention: str, context: str = 'column') -> str:
    """应用命名约定"""
    if convention == 'snake_case':
        # 转换为 snake_case
        name = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_')
        return name
    elif convention == 'camelCase':
        # 转换为 camelCase
        components = name.lower().split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    elif convention == 'PascalCase':
        # 转换为 PascalCase
        return ''.join(x.capitalize() for x in name.lower().split('_'))
    return name


def analyze_relations(requirement: str, entities: List[Entity]) -> List[List[Dict]]:
    """分析实体之间的关系

    识别模式:
    - "一个用户有多个订单" -> 1:N
    - "订单属于用户" -> N:1
    - "文章和标签多对多" -> N:M
    """
    all_relations = []

    # 关系关键词模式
    relation_patterns = [
        (r'(用户).*?(多个|many).*(订单|order)', 'User', 'Order', RelationType.ONE_TO_MANY),
        (r'(订单).*?(属于|belong).*(用户|user)', 'Order', 'User', RelationType.MANY_TO_ONE),
        (r'(产品).*(分类|category)', 'Product', 'Category', RelationType.MANY_TO_ONE),
        (r'(文章).*(标签|tag)', 'Article', 'Tag', RelationType.MANY_TO_MANY),
        (r'(评论).*(文章|article)', 'Comment', 'Article', RelationType.MANY_TO_ONE),
        (r'(评论).*(用户|user)', 'Comment', 'User', RelationType.MANY_TO_ONE),
    ]

    for entity in entities:
        entity_relations = []

        # 从需求文本中查找关系
        entity_name_lower = entity.name.lower()

        # 尝试匹配已知模式
        for pattern, from_entity, to_entity, rel_type in relation_patterns:
            if re.search(pattern, requirement, re.IGNORECASE):
                # 查找目标实体
                target_entity = None
                for e in entities:
                    if from_entity.lower() in e.name.lower():
                        source = e
                    if to_entity.lower() in e.name.lower():
                        target_entity = e

                if target_entity and target_entity.name != entity.name:
                    entity_relations.append({
                        'related_entity': target_entity.name,
                        'type': rel_type.value,
                        'description': f"{entity.name} 与 {target_entity.name} 的关系"
                    })

        all_relations.append(entity_relations)

    return all_relations


def generate_tables(
    entities: List[Entity],
    relations: List[List[Dict]],
    database_type: DatabaseType,
    include_timestamps: bool,
    include_soft_delete: bool,
    naming_convention: str
) -> List[Table]:
    """生成表结构"""
    tables = []

    # 类型映射
    type_map = DATA_TYPE_MAPPING.get(database_type, DATA_TYPE_MAPPING[DatabaseType.MYSQL])

    for entity, entity_relations in zip(entities, relations):
        table = Table(
            name=apply_naming_convention(entity.name, naming_convention, 'table'),
            comment=entity.description
        )

        # 添加主键
        pk_name = f"{apply_naming_convention(entity.name, naming_convention, 'column')}_id"
        if entity.name.lower() in ['user', 'users', '用户']:
            pk_name = 'id'

        table.add_column(Column(
            name=pk_name,
            data_type='BIGINT' if database_type == DatabaseType.MYSQL else 'BIGINT',
            nullable=False,
            primary_key=True,
            auto_increment=True,
            comment='主键ID'
        ))

        # 添加实体属性列
        for attr in entity.attributes:
            col_type = type_map.get(attr.get('type', 'string'), 'VARCHAR(255)')
            column = Column(
                name=apply_naming_convention(attr['name'], naming_convention),
                data_type=col_type,
                nullable=attr.get('nullable', True),
                unique=attr.get('unique', False),
                default=attr.get('default'),
                comment=attr.get('name', '')
            )
            table.add_column(column)

        # 添加外键列
        for rel in entity_relations:
            if rel['type'] in ['1:N', 'N:1']:
                fk_name = f"{rel['related_entity']}_id"
                fk_name = apply_naming_convention(fk_name, naming_convention)
                table.add_column(Column(
                    name=fk_name,
                    data_type='BIGINT',
                    nullable=True,
                    foreign_key=rel['related_entity'],
                    foreign_key_column='id',
                    comment=f'关联{rel["related_entity"]}表'
                ))

        # 添加时间戳字段
        if include_timestamps:
            timestamp_type = type_map.get('timestamp', 'TIMESTAMP')
            table.add_column(Column(
                name='created_at',
                data_type=timestamp_type,
                nullable=False,
                default='CURRENT_TIMESTAMP',
                comment='创建时间'
            ))
            table.add_column(Column(
                name='updated_at',
                data_type=timestamp_type,
                nullable=False,
                default='CURRENT_TIMESTAMP',
                comment='更新时间'
            ))

        # 添加软删除字段
        if include_soft_delete:
            table.add_column(Column(
                name='deleted_at',
                data_type=timestamp_type,
                nullable=True,
                comment='删除时间'
            ))

        # 添加索引
        if entity_relations:
            for rel in entity_relations:
                if rel['type'] in ['1:N', 'N:1']:
                    fk_name = f"{rel['related_entity']}_id"
                    fk_name = apply_naming_convention(fk_name, naming_convention)
                    table.add_index(
                        f"idx_{fk_name}",
                        [fk_name],
                        unique=False
                    )

        tables.append(table)

    # 为多对多关系创建关联表
    for entity, entity_relations in zip(entities, relations):
        for rel in entity_relations:
            if rel['type'] == 'N:M':
                # 创建关联表
                junction_table_name = f"{entity.name}_{rel['related_entity']}"
                junction_table_name = apply_naming_convention(junction_table_name, naming_convention, 'table')

                # 检查是否已创建
                if not any(t.name == junction_table_name for t in tables):
                    junction_table = Table(
                        name=junction_table_name,
                        comment=f"{entity.name}与{rel['related_entity']}关联表"
                    )

                    # 添加外键
                    entity_fk = f"{entity.name}_id"
                    related_fk = f"{rel['related_entity']}_id"

                    entity_fk = apply_naming_convention(entity_fk, naming_convention)
                    related_fk = apply_naming_convention(related_fk, naming_convention)

                    junction_table.add_column(Column(
                        name=entity_fk,
                        data_type='BIGINT',
                        nullable=False,
                        foreign_key=entity.name,
                        foreign_key_column='id'
                    ))
                    junction_table.add_column(Column(
                        name=related_fk,
                        data_type='BIGINT',
                        nullable=False,
                        foreign_key=rel['related_entity'],
                        foreign_key_column='id'
                    ))

                    # 添加联合唯一索引
                    junction_table.add_index(
                        f"uidx_{entity_fk}_{related_fk}",
                        [entity_fk, related_fk],
                        unique=True
                    )

                    tables.append(junction_table)

    return tables


def generate_er_diagram(design: SchemaDesign) -> str:
    """生成ER图 (Mermaid格式)"""
    lines = ["erDiagram"]

    # 生成实体定义
    for table in design.tables:
        lines.append(f"    {table.name} {{")

        for col in table.columns:
            # 标记主键和外键
            type_str = col.data_type
            if col.primary_key:
                type_str = f"PK {type_str}"
            elif col.foreign_key:
                type_str = f"FK {type_str}"

            # 标记可空
            nullable = "" if col.nullable else " NOT NULL"

            lines.append(f"        {col.name} {type_str}{nullable}")

        lines.append("    }")

    # 生成关系
    for table in design.tables:
        for col in table.columns:
            if col.foreign_key:
                # 1:N 关系
                lines.append(f"    {col.foreign_key} ||--o{{ {table.name} : \"拥有\"")

    return "\n".join(lines)


def generate_ddl(design: SchemaDesign) -> str:
    """生成DDL SQL语句"""
    database_type = design.database_type
    lines = []

    # 数据库特定设置
    if database_type == DatabaseType.MYSQL:
        lines.append("-- MySQL DDL")
        lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    elif database_type == DatabaseType.POSTGRESQL:
        lines.append("-- PostgreSQL DDL")
    elif database_type == DatabaseType.SQLITE:
        lines.append("-- SQLite DDL")

    lines.append("")

    # 生成建表语句
    for table in design.tables:
        lines.append(f"-- {table.comment}")
        lines.append(f"CREATE TABLE {table.name} (")

        column_defs = []
        primary_keys = []

        for col in table.columns:
            col_def = f"    {col.name} {col.data_type}"

            # 约束
            if not col.nullable and not col.primary_key:
                col_def += " NOT NULL"

            if col.auto_increment and database_type == DatabaseType.MYSQL:
                col_def += " AUTO_INCREMENT"

            if col.unique and not col.primary_key:
                col_def += " UNIQUE"

            if col.default is not None:
                if isinstance(col.default, str) and col.default.upper() != 'CURRENT_TIMESTAMP':
                    col_def += f" DEFAULT '{col.default}'"
                else:
                    col_def += f" DEFAULT {col.default}"

            column_defs.append(col_def)

            if col.primary_key:
                primary_keys.append(col.name)

        # 添加主键约束
        if primary_keys:
            column_defs.append(f"    PRIMARY KEY ({', '.join(primary_keys)})")

        # 添加外键约束
        for col in table.columns:
            if col.foreign_key:
                fk_col = col.foreign_key_column or 'id'
                if database_type == DatabaseType.MYSQL:
                    column_defs.append(
                        f"    FOREIGN KEY ({col.name}) REFERENCES {col.foreign_key}({fk_col})"
                    )
                elif database_type == DatabaseType.POSTGRESQL:
                    column_defs.append(
                        f"    FOREIGN KEY ({col.name}) REFERENCES {col.foreign_key}({fk_col})"
                    )

        lines.append(",\n".join(column_defs))
        lines.append(");")
        lines.append("")

        # 生成索引
        for idx in table.indexes:
            unique = "UNIQUE " if idx.get('unique') else ""
            lines.append(
                f"CREATE {unique}INDEX {idx['name']} ON {table.name} ({', '.join(idx['columns'])});"
            )

        lines.append("")

    if database_type == DatabaseType.MYSQL:
        lines.append("SET FOREIGN_KEY_CHECKS = 1;")

    return "\n".join(lines)


def generate_design_summary(design: SchemaDesign) -> Dict:
    """生成设计摘要"""
    return {
        'project_name': design.name,
        'database_type': design.database_type.value,
        'entities_count': len(design.entities),
        'tables_count': len(design.tables),
        'entities': [e.name for e in design.entities],
        'tables': [t.name for t in design.tables],
        'relations': count_relations(design),
    }


def count_relations(design: SchemaDesign) -> Dict[str, int]:
    """统计关系数量"""
    counts = {'1:1': 0, '1:N': 0, 'N:M': 0}

    for entity in design.entities:
        for rel in entity.relations:
            rel_type = rel.get('type', '')
            if rel_type in counts:
                counts[rel_type] += 1

    return counts


def execute_skill(params: Dict) -> Dict:
    """执行技能入口

    Args:
        params: 技能参数

    Returns:
        执行结果

    Raises:
        DatabaseSchemaError: 数据库设计过程中的错误
    """
    # 使用 Pydantic 验证输入参数
    if PYDANTIC_AVAILABLE:
        try:
            validated = DatabaseSchemaParams(**params)
            # 转换为字典用于后续处理
            params = validated.dict(exclude_unset=True)
        except PydanticValidationError as e:
            return {
                'success': False,
                'error': '输入参数验证失败',
                'validation_errors': e.errors()
            }

    try:
        return design_schema(params)
    except ValueError as e:
        logger.error(f"数据库设计参数错误: {e}")
        return {
            'success': False,
            'error': f'参数错误: {str(e)}'
        }
    except DatabaseSchemaError as e:
        logger.error(f"数据库设计错误: {e}")
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"数据库设计时出现未预期错误: {e}")
        return {
            'success': False,
            'error': f'设计失败: {str(e)}'
        }
