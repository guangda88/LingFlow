# Content Production Pipeline (内容生产流水线)

从灵知知识库检索内容 → 组织为结构化文章元数据 → 交付灵扬发布的流水线技能。

## 功能特性

- **智能检索**: 按主题从灵知搜索API获取相关文档片段
- **内容组织**: 将检索结果结构化为文章元数据(title, tags, summary, content_body)
- **多平台适配**: 按目标平台格式化输出
- **批量生产**: 支持一次查询生成多篇文章

## 触发条件

- `content production`
- `produce articles`
- `内容生产`
- `publish pipeline`

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| source_query | str | 必填 | 检索查询主题 |
| target_platform | str | "wechat" | 目标发布平台 (wechat/zhihu/weibo/github) |
| max_articles | int | 3 | 最多生成文章数 |
| top_k | int | 20 | 每次检索返回的文档片段数 |
| search_api_url | str | http://127.0.0.1:8000/api/v1/search/hybrid | 灵知搜索API地址 |
| use_query_expansion | bool | True | 启用查询扩展 |
| domains | list | [] | 限定领域过滤 (如 ["古籍", "气功"]) |

## 输出

```json
{
  "success": true,
  "articles": [
    {
      "title": "文章标题",
      "tags": ["tag1", "tag2"],
      "summary": "文章摘要，100字以内",
      "target_platform": "wechat",
      "content_body": "# Markdown格式的文章正文\n\n...",
      "source_doc_ids": [12345, 12346],
      "word_count": 1500
    }
  ],
  "total_articles": 1,
  "source_chunks_used": 5,
  "elapsed_seconds": 12.3
}
```

## 依赖

- 灵知搜索API (`/api/v1/search/hybrid`) — 内容检索
- 灵扬发布接口 — 文章交付发布
