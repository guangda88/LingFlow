# Pull Request

## 变更类型
- [ ] 新功能 (feature)
- [ ] Bug修复 (bugfix)
- [ ] 重构 (refactor)
- [ ] 文档 (docs)
- [ ] 安全修复 (security)
- [ ] 紧急修复 (hotfix) — 须24h内补审查

## 变更摘要
<!-- 1-2句话描述核心变更 -->

## 审计合规检查（必填）

### Layer 1: 单文件审计
- [ ] 每个修改文件已逐行审查
- [ ] 边界条件已处理（None/空值/0）
- [ ] 错误处理完整
- [ ] 代码风格符合项目规范（black + isort + flake8 clean）

### Layer 2: 交叉文件验证
- [ ] import路径正确，目标模块实际存在
- [ ] 数据流类型匹配（producer → consumer）
- [ ] 公共接口变更不影响现有调用方

### Layer 3: Cross-review
- [ ] 已通过灵通或灵克独立审查
- [ ] 审查结果已在LingMessage中记录

### 测试
- [ ] 本地测试全绿: `pytest`
- [ ] 新功能有对应测试
- [ ] CI检查通过

## 关联
Closes #
