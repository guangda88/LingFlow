# GitHub Release 创建指南 - v3.8.0

**状态**: 准备就绪，待创建

---

## 🔗 创建步骤

### 方法 1: 网页界面（推荐）

1. **访问 Releases 页面**
   ```
   https://github.com/guangda88/LingFlow/releases/new
   ```

2. **填写 Release 信息**

   **Tag**:
   - 选择: `v3.8.0`
   - 标题会自动填充

   **Title**:
   ```
   🎉 v3.8.0 - AI 生态平台
   ```

   **Description**:
   使用 `RELEASE_v3.8.0.md` 的内容，或复制以下内容：

   ```markdown
   # 🎉 LingFlow v3.8.0 生态版发布

   **发布日期**: 2026-04-02
   **版本**: v3.8.0
   **状态**: ✅ 生产就绪

   ---

   ## 🎯 重大更新

   LingFlow 从本地工具升级为**AI 生态平台**，现在支持 **4 种使用方式**！

   ### 🚀 新增使用方式

   #### 1️⃣ GitHub Actions
   CI/CD 集成，质量门禁自动化。

   ```yaml
   - uses: guangda88/LingFlow/actions/quality-gate@v3.8.0
     with:
       command: review
       path: ./src
   ```

   #### 2️⃣ REST API
   跨语言云端 API，支持任何技术栈。

   ```bash
   docker run -p 8000:8000 guangda88/lingflow-api:latest
   ```

   #### 3️⃣ 技能市场
   社区贡献技能市场，轻量级架构。

   ```bash
   lingflow skill search fastapi
   lingflow skill install fastapi-validator
   ```

   **索引仓库**: https://github.com/lingflow/skills-index

   #### 4️⃣ MCP Server v1.3.0
   21 个工具，8 个功能域，灵系命名（国学雅正）。

   ---

   ## 📦 安装

   ```bash
   pip install lingflow-core==3.8.0
   ```

   ---

   ## 📚 文档

   - [README](https://github.com/guangda88/LingFlow) - 使用指南
   - [架构演进](https://github.com/guangda88/LingFlow/docs/architecture/)
   - [技术债报告](https://github.com/guangda88/LingFlow/TECHNICAL_DEBT_ACTION_ITEMS.md)

   ---

   **"众智混元，万法灵通"**

   *LingFlow v3.8.0 - 从本地工具到 AI 生态平台*
   ```

3. **勾选选项**
   - ✅ Set as the latest release
   - ✅ Set as a pre-release (❌ 不勾选)

4. **发布**
   - 点击 "Publish release" 按钮

---

### 方法 2: GitHub CLI（如已安装）

```bash
# 安装 GitHub CLI
# Ubuntu/Debian: sudo apt install gh
# macOS: brew install gh

# 登录
gh auth login

# 创建 Release
gh release create v3.8.0 \
  --title "🎉 v3.8.0 - AI生态平台" \
  --notes-file RELEASE_v3.8.0.md \
  --repo guangda88/LingFlow
```

---

## ✅ 验证

### 检查 Release

1. 访问: https://github.com/guangda88/LingFlow/releases
2. 确认 `v3.8.0` 显示为最新版本
3. 检查 Assets 是否包含源码包

### 验证 PyPI

```bash
pip install lingflow-core==3.8.0
lingflow --version  # 应该输出 3.8.0
```

---

## 📊 发布统计

| 平台 | 状态 | 链接 |
|------|------|------|
| Git Tag | ✅ 已推送 | https://github.com/guangda88/LingFlow/releases/tag/v3.8.0 |
| PyPI | ✅ 已发布 | https://pypi.org/project/lingflow-core/ |
| Docker Hub | ⏳ 待推送 | 需要登录 |
| GitHub Release | ⏳ 待创建 | 需要手动操作 |

---

**预计时间**: 5-10 分钟
