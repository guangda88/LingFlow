# ima-batch-embed

## 描述
IMA 知识库批量嵌入生成。从 `ima_knowledge` 表读取未嵌入记录，批量调用嵌入服务，写入 `doc_embeddings_staging` 表。

## 参数

| 参数 | 类型 | 必选 | 默认值 | 说明 |
|------|------|------|--------|------|
| batch_size | int | 否 | 100 | 每批嵌入数量（嵌入服务上限） |
| limit | int | 否 | 0 | 总处理限制，0=全部 |
| category | string | 否 | "" | 按category过滤（中医/气功/儒家/太极） |
| dry_run | bool | 否 | false | 仅统计不写入 |
| resume | bool | 否 | true | 跳过已有staging记录 |

## 输出
```json
{
  "total_records": 101707,
  "already_staged": 0,
  "pending": 101707,
  "processed": 100,
  "embedded": 98,
  "failed": 2,
  "elapsed_seconds": 1.5
}
```

## 依赖
- PostgreSQL: zhineng_kb (port 5436)
- 嵌入服务: http://localhost:8001/embed_batch
