# 🟠 灵通 (LingFlow) — 安全策略

> 风险等级: **HIGH** | 角色: 工作流引擎 — 提供技能、工作流、需求、测试、监控、文件操作

## 概述

| 项目 | 值 |
|------|------|
| Agent ID | `LingFlow` |
| 角色 | 工作流引擎 — 提供技能、工作流、需求、测试、监控、文件操作 |
| 风险等级 | HIGH |
| 工具 | 26 个 MCP 工具（技能执行、代码审查、工作流编排、需求管理、测试运行） |

## 攻击面

- MCP 工具 run_skill / run_workflow 可执行任意工作流
- review_code 接受用户代码输入
- download_file 可从外部下载文件
- multiedit 可批量修改文件
- run_tests 执行测试代码

## 安全规则

1. 工作流执行前验证 YAML 定义完整性
2. download_file 仅允许 HTTPS 源
3. review_code 输出不得泄露环境变量或密钥
4. run_skill/run_workflow 需记录审计日志
5. 文件操作工具不得写入其他 agent 的项目目录

## 凭证文件

- 无直接凭证文件（通过环境变量或灵通+代理）

## 灵族安全基线引用

本文件遵循 `~/.lingflow-plus/docs/security_baseline_v1.py` 定义的 9 类安全基线：

| ID | 类别 | 关键规则 |
|----|------|----------|
| SEC-ID-001 | 身份安全 | AGENTS.md + CRUSH.md 锚定，HMAC-SHA256 跨 agent 签名 |
| SEC-CMD-001 | 命令执行 | 白名单制，非黑名单制 |
| SEC-CRED-001 | 凭证管理 | chmod 600，环境变量加载 |
| SEC-AUTH-001 | 网络鉴权 | API Key + CORS 限制 |
| SEC-MCP-001 | MCP 工具安全 | LOW→CRITICAL 风险分级 |
| SEC-CFG-001 | 配置隔离 | 爆炸半径控制 |
| SEC-EXEC-001 | 执行惯性 | 硬中断 + 重启循环检测 |
| SEC-DATA-001 | 数据完整性 | 验证数据必须实际经过验证 |
| SEC-MON-001 | 监控 & 响应 | 审计日志 + 异常检测 |

完整基线文档：`/data/lingfamily/LingFlow_plus/docs/security_baseline_v1.py`
安全巡检脚本：`/data/lingfamily/LingFlow_plus/docs/security_patrol.py`


## OWASP LLM Top 10 映射

| # | 风险 | 本 agent 相关性 |
|---|------|----------------|
| LLM01 | 提示注入 | 所有工具接受外部输入，需验证和消毒 |
| LLM02 | 敏感信息泄露 | 工具输出不得包含凭证、密钥、内部路径 |
| LLM03 | 供应链漏洞 | 依赖项需定期审计，锁定版本 |
| LLM04 | 数据与模型投毒 | 输入数据需标注来源，训练数据需验证 |
| LLM05 | 不当输出处理 | 输出需验证，不直接执行未经确认的操作 |
| LLM06 | 过度授权 | ⚠️ 工具权限需定期审计，确保不越界 |
| LLM07 | 系统提示泄露 | 系统提示不得包含敏感信息 |
| LLM08 | 向量/嵌入弱点 | 如使用向量搜索，需验证嵌入来源 |
| LLM09 | 错误信息 | 输出需标注可信度，幻觉内容需标记 |
| LLM10 | 无限消费 | 资源密集操作需设上限和速率限制 |


---

*生成时间: 2026-04-12 | 由灵通+ (LingFlow+) 自动生成*
*下次审查: 2026-07-12 或重大变更时*
