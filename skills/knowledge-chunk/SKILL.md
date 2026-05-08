# knowledge-chunk 技能

## 技能概述

knowledge-chunk 负责将文本文件分块，输出结构化 chunks 供向量化使用。支持按字符数分块、句子边界对齐、重叠窗口。

## 功能特性

- **智能分块**: 按字符数分块，在句子边界对齐
- **重叠窗口**: 前后块之间有可控重叠
- **元数据保留**: 每个chunk保留源文件、偏移量信息

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| file_path | str | 必填 | 源文件路径 |
| chunk_size | int | 300 | 块大小（字符） |
| overlap | int | 50 | 重叠大小（字符） |
| encoding | str | utf-8 | 文件编码 |

## 输出

```json
{
  "chunks": [{"content": "...", "start": 0, "end": 300, "index": 0}],
  "file": "example.txt",
  "total_chunks": 42,
  "chunk_size": 300,
  "overlap": 50
}
```

## 相关技能

- `knowledge-import` - 上游扫描
- `knowledge-embed` - 下游向量化
