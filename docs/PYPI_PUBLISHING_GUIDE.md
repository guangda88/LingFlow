# lingflow PyPI 发布指南

## 📦 当前状态

**发布流程**:
- 更新 `pyproject.toml` 版本号
- 更新 `lingflow/__init__.py` 版本号
- 更新 `VERSION` 文件
- 本地构建测试
- 发布到 PyPI

**生成的包**:
```
dist/lingflow_core-{version}-py3-none-any.whl
dist/lingflow_core-{version}.tar.gz
```

## 🚀 发布步骤

### 1. 注册 PyPI 账号（如果还没有）

访问 https://pypi.org/account/register/ 注册账号

### 2. 启用双因素认证（2FA）

PyPI 现在要求所有发布者启用 2FA：
- 登录 PyPI
- 进入 Account Settings → Two-factor authentication
- 配置 2FA（推荐使用认证器应用）

### 3. 创建 API Token

1. 访问 https://pypi.org/manage/account/token/
2. 创建新的 API Token
3. 范围选择：Entire account（用于第一次发布）
4. 保存 Token（只显示一次！）

### 4. 配置认证

**方法 A: 使用 --token 参数（推荐）**
```bash
# 不需要保存 token 到文件
twine upload dist/* --token __your_token_here__
```

**方法 B: 使用 ~/.pypirc**
```bash
# 创建 ~/.pypirc 文件
cat > ~/.pypirc << EOF
[pypi]
username = __token__
password = <your-token-here>
EOF

chmod 600 ~/.pypirc
```

### 5. 测试发布到 TestPyPI（强烈推荐）

```bash
# 1. 注册 TestPyPI 账号（独立于正式 PyPI）
# 访问 https://test.pypi.org/account/register/

# 2. 创建 TestPyPI token
# 访问 https://test.pypi.org/manage/account/token/

# 3. 发布到 TestPyPI
twine upload --repository testpypi dist/* --token __test_token__

# 4. 从 TestPyPI 安装测试
pip install --index-url https://test.pypi.org/simple/ lingflow-core
```

### 6. 正式发布到 PyPI

```bash
# 确保在项目根目录
cd /home/ai/lingflow

# 发布
twine upload dist/* --token __your_pypi_token__
```

### 7. 验证发布

```bash
# 等待 1-2 分钟让索引更新
# 然后测试安装
pip install lingflow-core

# 验证版本
python -c "import lingflow; print(lingflow.__version__)"
# 应该输出: 当前版本号
```

## 📋 发布检查清单

- [ ] `pyproject.toml` 版本已更新
- [ ] `lingflow/__init__.py` 版本已更新
- [ ] `VERSION` 文件已更新
- [ ] README.md 描述准确
- [ ] LICENSE 文件存在（MIT）
- [ ] 包构建成功: `python -m build`
- [ ] 包验证通过: `twine check dist/*`
- [ ] TestPyPI 测试成功
- [ ] PyPI 账号已启用 2FA
- [ ] API Token 已创建

## 🎯 发布后验证

1. **访问项目页面**:
   https://pypi.org/project/lingflow-core/

2. **测试安装**:
   ```bash
   # 创建新虚拟环境测试
   python -m venv /tmp/test_env
   source /tmp/test_env/bin/activate
   pip install lingflow-core
   python -c "import lingflow; print(lingflow.__version__)"
   ```

3. **测试 CLI**:
   ```bash
   lingflow --help
   lingflow list-skills
   ```

## 🔐 安全注意事项

1. **永远不要提交 API Token 到 git**
2. **使用 ~/.pypirc 时设置正确权限**: `chmod 600 ~/.pypirc`
3. **在 TestPyPI 先测试**，避免正式 PyPI 发布错误
4. **包名不能修改**，一旦发布不能删除（只能 yank）

## 📚 用户安装指南

发布成功后，用户可以：

**基础安装**:
```bash
pip install lingflow-core
```

**完整功能（包含情报系统）**:
```bash
pip install lingflow-core[full]
```

**仅开发工具**:
```bash
pip install lingflow-core[dev]
```

**仅情报系统**:
```bash
pip install lingflow-core[intelligence]
```

## 🔄 版本更新流程

下次发布新版本时：

1. **更新版本号**:
   - `pyproject.toml`: `version = "x.y.z"`
   - `lingflow/__init__.py`: `__version__ = "x.y.z"`
   - `VERSION`: `x.y.z`

2. **更新 CHANGELOG.md**

3. **构建新版本**:
   ```bash
   rm -rf dist build
   python -m build
   ```

4. **发布**:
   ```bash
   twine upload dist/*
   ```

## 📞 发布问题排查

### 问题 1: 403 Forbidden
- 检查 API Token 是否正确
- 确认 Token 有发布权限

### 问题 2: 包名已存在
- 在 https://pypi.org/search/ 检查包名
- 如果包名被占用，需要更改 setup.py 中的 name

### 问题 3: 文件过大
- PyPI 单文件限制 60MB
- 当前包大小 388K，没有问题

### 问题 4: 版本已存在
- 不能发布相同版本号
- 需要更新版本号

---

## 🎉 准备就绪！

当前所有配置已完成，您可以：

1. **立即发布**：如果已有 PyPI Token，直接运行发布命令
2. **测试发布**：先发布到 TestPyPI 测试流程
3. **自定义配置**：根据需要调整 setup.py 中的信息

**准备好发布了吗？** 只需运行：
```bash
cd /home/ai/lingflow
twine upload dist/* --token __your_token_here__
```

祝发布顺利！ 🚀
