# knowledge-import 技能

## 技能概述

knowledge-import 负责从灵知知识库扫描并验证源文件（txt/pdf/docx），输出文件清单和元数据，供下游 knowledge-chunk / knowledge-embed 消费。

## 功能特性

- **多格式扫描**: 支持 txt / pdf / docx 格式
- **去重检测**: 与已处理文件对比，跳过重复导入
- **元数据提取**: 文件名、大小、格式、编码检测
- **批量扫描**: 按目录递归扫描

## 使用场景

- 导入168教材到灵知系统
- 批量扫描知识库源文件
- 增量导入（仅处理新增文件）

## 触发条件

- `import knowledge`
- `scan textbooks`
- `knowledge import`
- `导入教材`

## 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| source_dir | str | 必填 | 源文件目录 |
| formats | list | ["txt"] | 要扫描的文件格式 |
| processed_dir | str | None | 已处理文件目录（用于去重） |
| recursive | bool | True | 是否递归扫描子目录 |

## 输出

```json
{
  "files": [{"path": "...", "name": "...", "size": 1234, "format": "txt", "encoding": "utf-8"}],
  "total": 10,
  "skipped": 3,
  "new": 7
}
```

## 相关技能

- `knowledge-chunk` - 文本分块
- `knowledge-embed` - 向量化
- `workflow-executor` - 编排完整导入流水线
