# knowledge-embed 技能

## 技能概述

knowledge-embed 负责将文本chunks通过embedding服务生成向量，并存入灵知PostgreSQL数据库。

## 功能特性

- **批量向量化**: 批量调用embedding服务
- **数据库写入**: 写入灵知 doc_chunks 表
- **进度追踪**: 跟踪已处理/失败数量

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chunks | list | 必填 | 待向量化的chunks列表 |
| doc_title | str | 必填 | 文档标题 |
| embedding_url | str | http://localhost:8001 | Embedding服务地址 |
| db_url | str | postgresql://... | 数据库连接字符串 |
| batch_size | int | 16 | 每批向量化的chunk数 |

## 输出

```json
{
  "embedded": 42,
  "failed": 0,
  "doc_title": "智能气功功法学",
  "batch_count": 3
}
```

## 相关技能

- `knowledge-chunk` - 上游分块
- `knowledge-import` - 最上游扫描
