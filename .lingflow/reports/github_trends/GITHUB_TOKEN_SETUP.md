# GitHub Token 设置指南

> **目的**: 提高GitHub API限额，避免403错误
> **限额提升**: 60次/小时 → 5000次/小时

---

## 📝 方法1：生成GitHub Personal Access Token（推荐）

### 步骤1：生成Token

1. **访问GitHub设置页面**
   - 登录GitHub
   - 访问：https://github.com/settings/tokens
   - 或：Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **生成新Token**
   - 点击 "Generate new token" → "Generate new token (classic)"

3. **配置Token**
   ```
   Note: LingFlow Trend Collector

   Expiration: 选择过期时间（建议90天或更长）

   Scopes（权限范围）:
   ☑️ public_repo（必选）：访问公共仓库
   ☑️ read:org（可选）：读取组织信息
   ☑️ user:email（可选）：访问用户邮箱
   ```

4. **生成并保存**
   - 点击 "Generate token"
   - ⚠️ **重要**：立即复制Token（只显示一次！）
   - 看起来类似：`ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## 🔧 方法2：设置环境变量（推荐）

### 临时设置（当前会话）

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

验证：
```bash
echo $GITHUB_TOKEN
```

### 永久设置（推荐）

**编辑 ~/.bashrc 或 ~/.zshrc**：

```bash
# 添加到文件末尾
export GITHUB_TOKEN="ghp_your_token_here"
```

**重新加载配置**：
```bash
source ~/.bashrc  # Bash
# 或
source ~/.zshrc   # Zsh
```

---

## 💻 方法3：直接在脚本中配置

### 创建配置文件

```bash
# 创建配置文件
touch /home/ai/.github_token
chmod 600 /home/ai/.github_token  # 设置权限为仅所有者可读写
```

**编辑文件**：
```bash
echo "ghp_your_token_here" > /home/ai/.github_token
```

### 修改采集脚本使用Token

`scripts/github_trend_collector.py` 会自动读取环境变量 `GITHUB_TOKEN`，无需修改代码。

如果要测试Token是否生效：

```python
import os
from pathlib import Path

# 方法1：从环境变量（推荐）
token = os.getenv('GITHUB_TOKEN', '')

# 方法2：从文件
token_file = Path.home() / '.github_token'
if token_file.exists():
    token = token_file.read_text().strip()

print(f"Token: {token[:10]}..." if token else "未设置Token")
```

---

## ✅ 验证Token是否生效

### 测试脚本

```bash
# 测试Token是否生效
python3 << 'EOF'
import os

token = os.getenv('GITHUB_TOKEN', '')
if token:
    print(f"✅ Token已设置: {token[:10]}...")
    print(f"   Token长度: {len(token)} 字符")
else:
    print("❌ Token未设置")

# 测试GitHub API
import requests
headers = {}
if token:
    headers['Authorization'] = f'token {token}'

response = requests.get(
    'https://api.github.com/rate_limit',
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"\n📊 API限额信息:")
    print(f"   核心API: {data['resources']['core']}")
else:
    print(f"❌ API请求失败: {response.status_code}")
EOF
```

### 预期输出（成功）

```
✅ Token已设置: ghp_xxxxxxx...
   Token长度: 40 字符

📊 API限额信息:
   核心API: {'limit': 5000, 'remaining': 4999, 'reset': 1712345678}
```

### 预期输出（未设置）

```
❌ Token未设置

📊 API限额信息:
   核心API: {'limit': 60, 'remaining': 58, 'reset': 1712345678}
```

---

## 🚀 快速设置（推荐流程）

### 一键设置

```bash
# 1. 设置环境变量（临时）
export GITHUB_TOKEN="ghp_your_actual_token_here"

# 2. 验证
python3 /home/ai/LingFlow/scripts/github_trend_collector.py

# 3. 如果有效，添加到 ~/.bashrc 永久保存
echo 'export GITHUB_TOKEN="ghp_your_actual_token_here"' >> ~/.bashrc
source ~/.bashrc
```

---

## 🔒 安全建议

### ⚠️ 重要安全提示

1. **不要泄露Token**
   - 不要提交到Git仓库
   - 不要在公开地方分享
   - 定期更换Token

2. **设置合适的过期时间**
   - 建议：90天
   - 过期后需重新生成

3. **最小权限原则**
   - 只勾选必要的Scopes
   - 对于公共仓库采集，只需 `public_repo`

4. **文件权限**
   - 如果使用文件存储：`chmod 600 ~/.github_token`
   - 确保只有所有者可读写

### Git忽略配置

在项目根目录的 `.gitignore` 中添加：

```gitignore
# GitHub Token
.github_token
.env
.github_token.*
```

---

## 📊 配置前后对比

| 指标 | 无Token | 有Token |
|------|---------|---------|
| API限额 | 60次/小时 | 5000次/小时 |
| 请求间隔 | 需要（避免超限） | 无需担心 |
| 403错误 | 频繁 | 罕见 |
| 采集关键词 | 5-7个 | 20+个 |
| 采集深度 | 表面 | 深入 |

---

## 🛠️ 故障排除

### 问题1：Token无效

**症状**：
```
401 Unauthorized
```

**解决**：
1. 检查Token是否复制完整
2. 检查Token是否过期
3. 重新生成Token

### 问题2：仍然403错误

**症状**：
```
403 Forbidden
API rate limit exceeded
```

**解决**：
1. 检查Token是否正确设置
2. 验证Token是否生效
3. 添加请求延迟：
   ```python
   import time
   time.sleep(1)  # 每次请求延迟1秒
   ```

### 问题3：环境变量未生效

**症状**：
```bash
echo $GITHUB_TOKEN
# 输出为空
```

**解决**：
```bash
# 检查Shell类型
echo $SHELL

# Bash用户
echo 'export GITHUB_TOKEN="ghp_xxx"' >> ~/.bashrc
source ~/.bashrc

# Zsh用户
echo 'export GITHUB_TOKEN="ghp_xxx"' >> ~/.zshrc
source ~/.zshrc
```

---

## 📝 配置模板

### 复制粘贴版

```bash
# ===== 步骤1：设置环境变量 =====
export GITHUB_TOKEN="替换为你的实际Token"

# ===== 步骤2：验证 =====
echo "Token: ${GITHUB_TOKEN:0:10}..."

# ===== 步骤3：测试采集 =====
python3 /home/ai/LingFlow/scripts/github_trend_collector.py

# ===== 步骤4：如果成功，永久保存 =====
echo 'export GITHUB_TOKEN="替换为你的实际Token"' >> ~/.bashrc
source ~/.bashrc

# ===== 步骤5：验证永久设置 =====
echo $GITHUB_TOKEN
```

---

## 🎯 推荐配置

**最佳实践**：
1. ✅ 使用环境变量（推荐）
2. ✅ 设置90天过期
3. ✅ 仅授予 `public_repo` 权限
4. ✅ 定期更换Token
5. ✅ 添加到 `.gitignore`

**不推荐**：
- ❌ 硬编码在脚本中
- ❌ 提交到版本控制
- ❌ 分享给他人
- ❌ 设置无限期过期

---

**设置完成后，运行采集脚本验证效果！**

```bash
python3 /home/ai/LingFlow/scripts/github_trend_collector.py
```

预期：API限额从60提升到5000，403错误消失。
