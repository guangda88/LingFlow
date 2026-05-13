# lingflow 代码审查规范

> 版本: v3.3.0
> 更新日期: 2026-03-23
> 适用范围: lingflow 所有代码和文档

---

## 概述

本文档定义了 lingflow 代码审查的全面维度清单，按从外到内、从浅到深分成 8 大维度，可直接当评审检查表使用。

**代码审查 = 规范 + 逻辑 + 可读 + 性能 + 安全 + 健壮 + 可测 + 架构**

---

## 8 大审查维度

### 1. 代码规范与风格

#### 检查项

- **命名规范**
  - [ ] 变量名见名知意，符合 Python PEP 8 规范
  - [ ] 函数名使用动词或动词短语，明确表达功能
  - [ ] 类名使用大驼峰命名法（PascalCase）
  - [ ] 文件名使用小写加下划线格式（snake_case）
  - [ ] 常量使用全大写加下划线（UPPER_CASE）

- **格式规范**
  - [ ] 缩进使用 4 个空格（统一使用空格，不使用 Tab）
  - [ ] 每行不超过 100 字符（推荐 88-100 字符）
  - [ ] 函数之间、类之间有适当的空行分隔
  - [ ] 括号内不留空格，逗号后留一个空格
  - [ ] 运算符两侧留空格（除了括号、逗号等）

- **注释规范**
  - [ ] 关键逻辑有注释说明"为什么"而不是"是什么"
  - [ ] 复杂算法有步骤说明和时间/空间复杂度分析
  - [ ] 业务规则有明确注释，特别是非直观的规则
  - [ ] 避免冗余注释（如注释代码本身）
  - [ ] 公共 API 有完整的 docstring（使用 Google 或 NumPy 风格）

- **魔法值处理**
  - [ ] 硬编码数字抽成常量或配置
  - [ ] 硬编码字符串抽成常量（特别是重复出现的）
  - [ ] 使用枚举（Enum）代替魔法数字
  - [ ] 配置项通过配置文件或环境变量管理

#### 参考标准

```python
# ✅ 良好示例
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
DEFAULT_PRIORITY = TaskPriority.NORMAL

def process_data(user_id: int, items: List[Item]) -> Result:
    """
    处理用户数据

    Args:
        user_id: 用户 ID
        items: 待处理的项目列表

    Returns:
        处理结果，包含成功和失败的数量

    Raises:
        ValidationError: 当数据验证失败时
    """
    if not items:
        return Result(success=0, failed=0)

    # 使用分批处理以提高性能
    batch_size = 100
    results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        results.append(_process_batch(user_id, batch))

    return _aggregate_results(results)
```

```python
# ❌ 不良示例
def process(d, x):
    # 处理数据
    if len(x) == 0:
        return None

    r = []
    for i in range(0, len(x), 100):  # 魔法数字 100
        b = x[i:i+100]
        r.append(p(d, b))  # 不清晰的函数名

    return sum(r)
```

---

### 2. 功能与业务逻辑

#### 检查项

- **需求覆盖**
  - [ ] 是否完全实现了需求文档中的所有功能点
  - [ ] 边界条件是否覆盖（空值、最大值、最小值）
  - [ ] 异常场景是否处理（网络中断、磁盘满、超时）
  - [ ] 兼容性是否考虑（不同 Python 版本、操作系统）

- **逻辑正确性**
  - [ ] 分支逻辑（if-else）覆盖所有情况
  - [ ] 循环条件正确，无死循环风险
  - [ ] 循环体内变量更新正确
  - [ ] 递归有明确的终止条件

- **异常处理**
  - [ ] 空值（None、空字符串、空列表）检查
  - [ ] 数组/列表越界检查
  - [ ] 非法参数验证和明确错误提示
  - [ ] 类型转换安全（使用 try-except 或 isinstance）

- **业务规则一致性**
  - [ ] 业务规则与产品需求文档（PRD）一致
  - [ ] 与设计文档（UML、流程图）一致
  - [ ] 与数据库模型一致（字段类型、约束）
  - [ ] 与 API 文档一致（请求/响应格式）

#### 参考标准

```python
# ✅ 良好示例
def calculate_discount(user: User, amount: float) -> float:
    """
    根据用户等级计算折扣

    业务规则：
    - VIP 用户享受 20% 折扣
    - 普通 1000 元以上享受 10% 折扣
    - 最低折扣金额为 0 元
    """
    if not user or not isinstance(amount, (int, float)):
        raise ValueError("Invalid user or amount")

    if amount <= 0:
        return 0.0

    if user.is_vip:
        return min(amount * 0.2, amount)

    if amount >= 1000:
        return min(amount * 0.1, amount)

    return 0.0
```

```python
# ❌ 不良示例
def discount(u, a):
    # 没有边界检查
    if u.level == 'vip':
        return a * 0.2
    elif a > 1000:  # 逻辑可能有问题
        return a * 0.1
    # 没有返回值，可能返回 None
```

---

### 3. 可读性与可维护性

#### 检查项

- **单一职责原则**
  - [ ] 函数只做一件事，功能单一
  - [ ] 函数长度不超过 50 行（推荐 20-30 行）
  - [ ] 类的职责明确，不过度复杂
  - [ ] 方法数量合理（单个类不超过 20 个方法）

- **代码结构**
  - [ ] 避免深层嵌套（超过 3 层嵌套需要重构）
  - [ ] 使用卫语句（guard clauses）减少嵌套
  - [ ] 避免复杂的条件表达式（拆分为多个变量）
  - [ ] 避免过长的参数列表（超过 4 个参数考虑使用对象）

- **代码复用**
  - [ ] 重复代码（Copy-Paste）抽离为公共函数
  - [ ] 相似逻辑使用策略模式或模板方法
  - [ ] 使用继承或组合复用代码
  - [ ] 工具函数放在独立的工具模块

- **模块组织**
  - [ ] 分层清晰（表现层、业务层、数据层）
  - [ ] 模块依赖单向（上层依赖下层，不循环依赖）
  - [ ] 模块大小合理（单个文件不超过 500 行）
  - [ ] 接口设计清晰，易于扩展

#### 参考标准

```python
# ✅ 良好示例
def process_user(user: User) -> ProcessResult:
    """处理用户信息（单一职责）"""
    if not _is_valid_user(user):
        return ProcessResult(success=False, error="Invalid user")

    enriched = _enrich_user_data(user)
    saved = _save_user(enriched)
    notified = _notify_user(saved)

    return ProcessResult(success=True, data=saved)


def _is_valid_user(user: User) -> bool:
    """验证用户数据"""
    return user and user.id and user.email


def _enrich_user_data(user: User) -> User:
    """丰富用户数据"""
    user.full_name = f"{user.first_name} {user.last_name}"
    user.age = calculate_age(user.birth_date)
    return user
```

```python
# ❌ 不良示例
def process(u):
    # 太多职责，嵌套太深
    if u:
        if u.id:
            if u.email:
                if validate_email(u.email):
                    if save_user(u):
                        if send_email(u):
                            if log_user(u):
                                return True
                            else:
                                return False
                        else:
                            return False
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
        return False
```

---

### 4. 性能与资源效率

#### 检查项

- **算法复杂度**
  - [ ] 时间复杂度合理，避免 O(n²) 或更高（除非必要）
  - [ ] 空间复杂度合理，避免过度内存消耗
  - [ ] 使用合适的数据结构（字典、集合查询 O(1)，列表查询 O(n)）
  - [ ] 避免在循环中进行重复计算

- **数据库操作**
  - [ ] 查询字段有索引（常用查询条件）
  - [ ] 避免慢查询（使用 EXPLAIN 分析）
  - [ ] 避免 N+1 问题（使用 JOIN 或批量查询）
  - [ ] 使用连接池，避免频繁创建连接

- **资源管理**
  - [ ] 文件、数据库连接、网络连接及时关闭（使用 with 语句）
  - [ ] 大对象及时释放（使用 del 或重置引用）
  - [ ] 避免内存泄漏（弱引用、循环引用检查）
  - [ ] 锁使用合理，避免死锁

- **并发场景**
  - [ ] 避免不必要的阻塞（同步 I/O 考虑异步）
  - [ ] 避免频繁的全量遍历（使用缓存）
  - [ ] 使用线程池、进程池优化并发
  - [ ] 注意线程安全（共享资源加锁）

#### 参考标准

```python
# ✅ 良好示例
def find_duplicates(items: List[Item]) -> Set[Item]:
    """
    查找重复项（使用集合优化时间复杂度）

    时间复杂度: O(n)
    空间复杂度: O(n)
    """
    seen = set()
    duplicates = set()

    for item in items:
        if item.id in seen:
            duplicates.add(item)
        else:
            seen.add(item.id)

    return duplicates


async def fetch_user_data(user_ids: List[int]) -> Dict[int, User]:
    """批量获取用户数据（使用异步和连接池）"""
    async with get_db_connection() as conn:
        # 使用 IN 查询避免 N+1 问题
        query = "SELECT * FROM users WHERE id IN %s"
        results = await conn.execute(query, (tuple(user_ids),))
        return {row.id: row for row in results}
```

```python
# ❌ 不良示例
def find_duplicates(items):
    """低效实现（嵌套循环 O(n²)）"""
    duplicates = []

    for i, item1 in enumerate(items):
        for j, item2 in enumerate(items):
            if i != j and item1.id == item2.id:
                if item1 not in duplicates:  # 列表查询 O(n)
                    duplicates.append(item1)

    return duplicates


def fetch_user_data(user_ids):
    """低效实现（N+1 问题）"""
    results = {}
    for user_id in user_ids:
        conn = create_connection()  # 没有使用连接池
        user = conn.execute(f"SELECT * FROM users WHERE id = {user_id}")
        conn.close()
        results[user_id] = user
    return results
```

---

### 5. 安全合规

#### 检查项

- **输入校验**
  - [ ] 所有外部输入（用户输入、API 参数、文件）严格校验
  - [ ] 使用白名单而非黑名单（允许已知安全值）
  - [ ] 过滤特殊字符（SQL、HTML、Shell 命令注入字符）
  - [ ] 参数类型、长度、范围验证

- **防注入攻击**
  - [ ] SQL 查询使用参数化查询（不拼接字符串）
  - [ ] NoSQL 查询使用安全的查询构造器
  - [ ] 命令执行使用参数化方式（subprocess.run 不使用 shell=True）
  - [ ] 模板引擎使用自动转义

- **Web 安全**
  - [ ] XSS 防护（输出时转义 HTML 特殊字符）
  - [ ] CSRF 防护（使用 token 验证）
  - [ ] 权限校验（每个操作检查用户权限）
  - [ ] 会话管理（超时、安全 Cookie）

- **敏感信息保护**
  - [ ] 密码、密钥不硬编码（使用环境变量或配置文件）
  - [ ] 日志中不输出敏感信息（密码、Token、身份证号）
  - [ ] 使用加密存储（密码使用 bcrypt 或 Argon2）
  - [ ] 传输使用 HTTPS

- **合规要求**
  - [ ] 符合 GDPR/个人信息保护法（数据最小化、用户同意）
  - [ ] 符合行业安全标准（OWASP Top 10）
  - [ ] 数据保留和删除策略
  - [ ] 安全审计日志

#### 参考标准

```python
# ✅ 良好示例
import os
from werkzeug.security import generate_password_hash

# 从环境变量读取密钥
API_KEY = os.environ.get('API_KEY')
DB_PASSWORD = os.environ.get('DB_PASSWORD')


def validate_input(user_input: str) -> str:
    """严格的输入验证"""
    if not isinstance(user_input, str):
        raise ValueError("Input must be string")

    # 限制长度
    if len(user_input) > 1000:
        raise ValueError("Input too long")

    # 只允许字母数字和基本标点
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,!?:-')
    if not all(c in allowed_chars for c in user_input):
        raise ValueError("Invalid characters")

    return user_input.strip()


def query_user(user_id: int) -> Optional[User]:
    """安全的数据库查询（参数化查询）"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID")

    with get_db_connection() as conn:
        # 使用参数化查询，不拼接字符串
        result = conn.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return result.fetchone()


def log_event(event: Event):
    """安全的日志记录（过滤敏感信息）"""
    safe_event = {
        'type': event.type,
        'user_id': event.user_id,  # 只记录 ID，不记录敏感信息
        'timestamp': event.timestamp,
        # 不记录: password, token, credit_card 等
    }
    logger.info(f"Event: {safe_event}")
```

```python
# ❌ 不良示例
API_KEY = "sk-proj-abc123xyz..."  # 硬编码密钥 ❌


def query_user(user_id):
    """不安全的数据库查询（SQL 注入风险）"""
    query = f"SELECT * FROM users WHERE id = {user_id}"  # 拼接字符串 ❌
    result = conn.execute(query)
    return result


def log_event(event):
    """不安全的日志记录（泄露敏感信息）"""
    logger.info(f"Event: {event}")  # 可能泄露密码、Token ❌
```

---

### 6. 健壮性与异常处理

#### 检查项

- **异常捕获**
  - [ ] 捕获具体的异常类型（不使用裸 except:）
  - [ ] 不吞异常（至少记录日志）
  - [ ] 不抛出通用异常（使用业务异常）
  - [ ] 异常信息清晰，包含上下文

- **错误处理**
  - [ ] 错误码/错误信息清晰，便于定位问题
  - [ ] 向用户返回友好的错误提示（不暴露内部实现）
  - [ ] 向开发者返回详细的错误堆栈（日志或调试模式）

- **空值安全**
  - [ ] 空指针检查（Python 中为 None）
  - [ ] 空集合处理（使用 get() 或 default）
  - [ ] 类型转换安全（使用 try-except）
  - [ ] 可选链式调用（使用 and / or 或 ?.）

- **容错机制**
  - [ ] 降级策略（服务不可用时返回缓存或默认值）
  - [ ] 重试机制（指数退避，限制重试次数）
  - [ ] 熔断机制（错误率达到阈值时停止调用）
  - [ ] 超时控制（避免无限等待）

#### 参考标准

```python
# ✅ 良好示例
class PaymentError(Exception):
    """支付异常"""
    pass


def process_payment(user_id: int, amount: float) -> PaymentResult:
    """
    处理支付（完善的异常处理）

    Raises:
        UserNotFoundError: 用户不存在
        PaymentError: 支付失败
    """
    try:
        user = get_user(user_id)
        if not user:
            raise UserNotFoundError(f"User {user_id} not found")

        # 带重试和超时的支付调用
        result = retry_on_failure(
            lambda: payment_gateway.charge(user.payment_method, amount),
            max_retries=3,
            timeout=30
        )

        return PaymentResult(success=True, transaction_id=result.id)

    except UserNotFoundError as e:
        logger.error(f"Payment failed: {e}")
        raise  # 向上传播业务异常

    except payment_gateway.TimeoutError as e:
        logger.error(f"Payment timeout: {e}")
        # 降级：标记为待处理
        return PaymentResult(success=False, status="pending", error="Payment timeout")

    except Exception as e:
        logger.exception(f"Unexpected payment error: {e}")
        raise PaymentError(f"Payment processing failed: {e}") from e
```

```python
# ❌ 不良示例
def process_payment(user_id, amount):
    """不完善的异常处理"""
    try:
        user = get_user(user_id)
        # 没有检查 user 是否为 None

        result = payment_gateway.charge(user.payment_method, amount)
        return result

    except:  # 捕获所有异常 ❌
        pass  # 吞异常 ❌

    # 没有返回值，可能返回 None ❌
```

---

### 7. 可测试性与测试覆盖

#### 检查项

- **可测试性**
  - [ ] 函数/方法可独立测试（无隐藏依赖）
  - [ ] 依赖可注入（方便 Mock）
  - [ ] 无硬编码依赖（文件路径、数据库连接）
  - [ ] 避免全局状态

- **测试覆盖**
  - [ ] 核心逻辑有单元测试
  - [ ] 边界条件有测试用例
  - [ ] 异常场景有测试用例
  - [ ] 测试覆盖率 ≥ 80%

- **测试质量**
  - [ ] 测试代码质量同业务代码（可读、可维护）
  - [ ] 测试命名清晰（test_功能_场景_预期）
  - [ ] 使用断言（Assert）验证结果（不是纸面测试）
  - [ ] 测试独立（不依赖执行顺序）

- **Mock 和 Stub**
  - [ ] 使用 Mock 隔离外部依赖（数据库、网络、文件）
  - [ ] Mock 行为符合真实场景
  - [ ] 验证 Mock 是否被正确调用
  - [ ] 清理 Mock 状态

#### 参考标准

```python
# ✅ 良好示例（可测试代码）
class UserService:
    """用户服务（依赖注入，易于测试）"""

    def __init__(self, db: Database, email_client: EmailClient):
        self.db = db
        self.email_client = email_client

    def register_user(self, email: str, password: str) -> User:
        """注册用户（单一职责，易于测试）"""
        if not self._is_valid_email(email):
            raise ValidationError("Invalid email")

        if self.db.user_exists(email):
            raise ValidationError("User already exists")

        hashed_password = self._hash_password(password)
        user = self.db.create_user(email, hashed_password)

        self.email_client.send_welcome_email(user.email)

        return user

    def _is_valid_email(self, email: str) -> bool:
        """验证邮箱格式（可独立测试）"""
        return '@' in email and '.' in email

    def _hash_password(self, password: str) -> str:
        """哈希密码（可独立测试）"""
        return generate_password_hash(password)
```

```python
# ✅ 良好示例（测试代码）
import pytest
from unittest.mock import Mock, patch

class TestUserService:
    """用户服务测试"""

    def test_register_user_success(self):
        """测试成功注册用户"""
        # 准备 Mock
        mock_db = Mock()
        mock_email_client = Mock()

        # 设置 Mock 行为
        mock_db.user_exists.return_value = False
        mock_db.create_user.return_value = User(id=1, email="test@example.com")

        # 创建服务
        service = UserService(mock_db, mock_email_client)

        # 执行测试
        result = service.register_user("test@example.com", "password123")

        # 验证结果
        assert result.id == 1
        assert result.email == "test@example.com"

        # 验证 Mock 调用
        mock_db.user_exists.assert_called_once_with("test@example.com")
        mock_db.create_user.assert_called_once()
        mock_email_client.send_welcome_email.assert_called_once_with("test@example.com")

    def test_register_user_duplicate_email(self):
        """测试重复邮箱"""
        mock_db = Mock()
        mock_db.user_exists.return_value = True  # 用户已存在

        service = UserService(mock_db, Mock())

        # 执行测试并验证抛出异常
        with pytest.raises(ValidationError, match="User already exists"):
            service.register_user("test@example.com", "password123")

    def test_is_valid_email_valid(self):
        """测试有效邮箱"""
        service = UserService(Mock(), Mock())
        assert service._is_valid_email("test@example.com") is True

    def test_is_valid_email_invalid(self):
        """测试无效邮箱"""
        service = UserService(Mock(), Mock())
        assert service._is_valid_email("invalid") is False
```

```python
# ❌ 不良示例（不易测试）
class UserService:
    def register_user(self, email, password):
        # 硬编码依赖，无法 Mock
        db = Database()  # ❌

        # 全局状态，测试间有依赖
        global current_user  # ❌

        # 文件路径硬编码，不易测试
        with open("/path/to/config.json") as f:  # ❌
            config = json.load(f)

        # 不使用断言，只是打印结果（纸面测试）❌
        print(f"Registered: {email}")
```

```python
# ❌ 不良示例（测试代码）
def test_register_user():
    service = UserService()

    # 没有断言，只是调用函数（纸面测试）❌
    try:
        service.register_user("test@example.com", "password123")
        print("✓ Test passed")
    except:
        print("✗ Test failed")

    # 测试依赖于全局状态 ❌
    global test_counter
    test_counter += 1
```

---

### 8. 架构与设计合理性

#### 检查项

- **架构约束**
  - [ ] 符合分层架构（表现层、业务层、数据层）
  - [ ] 符合领域驱动设计（DDD）原则（如果适用）
  - [ ] 符合微服务架构（如果适用）
  - [ ] 服务边界清晰，职责明确

- **依赖关系**
  - [ ] 依赖关系清晰，单向依赖（不循环依赖）
  - [ ] 高层模块不依赖低层模块（依赖倒置原则）
  - [ ] 接口抽象稳定（面向接口编程）
  - [ ] 使用依赖注入（DI）或控制反转（IoC）

- **可扩展性**
  - [ ] 遵循开闭原则（对扩展开放，对修改封闭）
  - [ ] 使用策略模式、模板方法模式等设计模式
  - [ ] 不硬编码业务流程（使用配置或规则引擎）
  - [ ] 插件化设计（如果适用）

- **技术债务**
  - [ ] 没有明显的技术债埋坑
  - [ ] 临时代码标记为 TODO 并跟踪
  - [ ] 遗留代码有重构计划
  - [ ] 兼容历史代码（版本兼容性）

- **可观测性**
  - [ ] 日志记录完整（关键操作、错误、性能）
  - [ ] 监控指标（响应时间、错误率、吞吐量）
  - [ ] 告警机制（异常情况及时通知）
  - [ ] 分布式追踪（如果适用）

#### 参考标准

```python
# ✅ 良好示例（清晰的架构设计）

# 接口层（presentation）
class UserController:
    """用户控制器（接口层）"""

    def __init__(self, user_service: IUserService):
        self.user_service = user_service  # 依赖注入

    def register(self, request: RegisterRequest) -> Response:
        """注册接口"""
        try:
            user = self.user_service.register_user(
                request.email,
                request.password
            )
            return Response.success(user.to_dict())
        except ValidationError as e:
            return Response.error(400, str(e))
        except Exception as e:
            logger.exception("Register failed")
            return Response.error(500, "Internal error")


# 业务层（domain/service）
class IUserService(ABC):
    """用户服务接口（抽象）"""

    @abstractmethod
    def register_user(self, email: str, password: str) -> User:
        pass


class UserService(IUserService):
    """用户服务实现（业务层）"""

    def __init__(self, user_repository: IUserRepository, email_client: IEmailClient):
        self.user_repository = user_repository  # 依赖倒置
        self.email_client = email_client

    def register_user(self, email: str, password: str) -> User:
        """注册用户（业务逻辑）"""
        self._validate_email(email)
        self._validate_password(password)

        hashed = self._hash_password(password)
        user = self.user_repository.create(email, hashed)

        self.email_client.send_welcome(user.email)

        return user


# 数据层（infrastructure/repository）
class IUserRepository(ABC):
    """用户仓储接口（抽象）"""

    @abstractmethod
    def create(self, email: str, password: str) -> User:
        pass


class UserRepository(IUserRepository):
    """用户仓储实现（数据层）"""

    def __init__(self, db: Database):
        self.db = db

    def create(self, email: str, password: str) -> User:
        """创建用户（数据访问）"""
        cursor = self.db.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s) RETURNING *",
            (email, password)
        )
        return User.from_row(cursor.fetchone())
```

```python
# ❌ 不良示例（混乱的架构）

class UserController:
    """控制器包含了所有层的逻辑（违反分层架构）"""

    def register(self, email, password):
        # 业务逻辑混杂在控制器中
        if '@' not in email:
            return {"error": "Invalid email"}

        # 数据访问直接在控制器中
        db = Database()  # 硬编码依赖 ❌
        if db.execute(f"SELECT * FROM users WHERE email = '{email}'").fetchone():  # SQL 注入 ❌
            return {"error": "User exists"}

        # 密码处理逻辑混杂
        hashed = hash(password)  # 不安全 ❌
        db.execute(f"INSERT INTO users (email, password) VALUES ('{email}', '{hashed}')")

        # 邮件发送逻辑混杂
        send_email(email, "Welcome!")  # 硬编码依赖 ❌

        return {"success": True}


# 循环依赖 ❌
# module_a.py
from module_b import ClassB

class ClassA:
    def __init__(self):
        self.b = ClassB()


# module_b.py
from module_a import ClassA

class ClassB:
    def __init__(self):
        self.a = ClassA()  # 循环依赖 ❌
```

---

## 使用指南

### 作为代码审查检查表

1. **Pull Request 审查**
   - 在审查 PR 时，逐项检查 8 个维度
   - 记录发现的问题，标注优先级（P0/P1/P2）
   - 提供具体的改进建议

2. **团队代码规范**
   - 将此文档作为团队代码规范的一部分
   - 新员工入职培训材料
   - 定期 Code Review 会议参考

3. **自动化检查**
   - 使用 linter（flake8、pylint）检查维度 1
   - 使用 security linter（bandit）检查维度 5
   - 使用 coverage.py 检查维度 7
   - 使用 sonarqube 综合检查所有维度

### 权重建议

根据项目特点，可以为不同维度设置权重：

- **安全敏感项目**: 安全合规 > 架构设计 > 健壮性
- **性能关键项目**: 性能效率 > 架构设计 > 可读性
- **快速迭代项目**: 可测试性 > 可读性 > 代码规范
- **长期维护项目**: 架构设计 > 可读性 > 代码规范

### 常见问题

**Q: 是否每次审查都要检查所有维度？**

A: 不一定。可以根据项目阶段和改动范围调整：
- 小改动：重点检查维度 1、2、3
- 大改动：重点检查维度 4、6、8
- 安全相关：重点检查维度 5、6
- 性能相关：重点检查维度 4、5、8

**Q: 如何平衡代码质量和开发速度？**

A: 使用分层标准：
- P0（阻塞）: 必须修复（安全、严重 bug）
- P1（重要）: 建议修复（性能、可读性）
- P2（优化）: 可以延后（代码风格、文档）

**Q: 如何处理遗留代码？**

A:
- 修改遗留代码时，先修复当前文件的问题
- 技术债记录到 TODO 列表或项目看板
- 规划专门的重构时间（如每个 Sprint 20%）
- 渐进式重构，不要一次性重写

---

## 工具推荐

### 代码质量工具

- **flake8**: Python 代码规范检查（维度 1）
- **pylint**: 代码质量和错误检测（维度 1、3）
- **black**: 代码格式化（维度 1）
- **isort**: import 排序（维度 1）

### 安全工具

- **bandit**: Python 安全漏洞检测（维度 5）
- **safety**: 依赖安全检查（维度 5）
- **semgrep**: 多语言安全规则检测（维度 5）

### 测试工具

- **pytest**: 测试框架（维度 7）
- **coverage.py**: 测试覆盖率（维度 7）
- **pytest-cov**: pytest 覆盖率插件（维度 7）
- **unittest.mock**: Mock 框架（维度 7）

### 性能工具

- **cProfile**: Python 性能分析（维度 4）
- **memory_profiler**: 内存分析（维度 4）
- **py-spy**: 实时性能分析（维度 4）

### 综合工具

- **pre-commit**: Git hooks 管理工具
- **sonarqube**: 综合代码质量分析平台
- **tox**: 测试环境管理

---

## 参考资料

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [The Pragmatic Programmer by Andrew Hunt and David Thomas](https://www.amazon.com/Pragmatic-Programmer-Journey-Mastery/dp/020161622X)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [12-Factor App](https://12factor.net/)
- [Domain-Driven Design by Eric Evans](https://www.amazon.com/Domain-Driven-Design-Tackling-Complexity-Software/dp/0321125215)

---

## 版本历史

- **v1.0.0** (2026-03-22): 初始版本，定义 8 大审查维度

---

**文档维护者**: lingflow 开发团队
**反馈渠道**: 通过 GitHub Issues 提交建议
**最后更新**: 2026-03-22
