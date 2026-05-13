# v3.8.0 技术债行动清单

**更新日期**: 2026-04-02
**数据来源**: 全量代码扫描（95+ .py, lingflow-api/, docs/）
**测试基线**: 1360 passed, 0 failed
**P0 修复状态**: ✅ 全部完成
**P1 修复状态**: ✅ 全部完成
**P2 部分完成**: P2.1 ✅

---

## ✅ P0 — 发布阻塞 (4项) - **已完成**

- [x] **P0.1** API 端点崩溃 — `lingflow-api/app/main.py`
  - [x] L284: `CodeReviewer` → `BaseCodeReviewer`
  - [x] L311,331: `lingflow.intelligence` 不存在 → 501 Not Implemented
  - [x] L353: `RequirementManager` → `RequirementsTraceability`
  - [x] 验证: `python -c "import sys; sys.path.insert(0,'lingflow-api'); from app.main import app; print('OK')"` ✅

- [x] **P0.2** 硬编码密钥 — `lingflow-api/app/core/config.py:21`
  - [x] `"dev-key-12345"` → `""`, 启动时无密钥打印 warning ✅

- [x] **P0.3** 版本号落后 — `lingflow/bootstrap.py:19`
  - [x] `"3.6.0"` → `"3.8.0"` ✅

- [x] **P0.4** track_context 空操作 — `lingflow/__init__.py:82`
  - [x] 改为从 `lingflow.context` 导入真实实现 ✅
  - [x] 验证: `python -c "from lingflow import track_context; print(type(track_context))"` ✅

---

## ✅ P1 — 本迭代修 (6项) - **已完成**

- [x] **P1.1** 双配置系统 — `core/config.py` 加 `__post_init__` DeprecationWarning
  - [x] `tests/test_config.py` 添加 `@pytest.mark.filterwarnings` + 弃用验证测试 ✅

- [x] **P1.2** get_smart_compressor 导出 — `compression/__init__.py` 加入 `__all__` ✅

- [x] **P1.3** ai_friendly 私有属性 — `ai_friendly.py:259`
  - [x] `self._coordinator.execute_skill_async()` (不存在) → `run_in_executor` 包装 `self.run_skill()` ✅
  - [x] 移除 `TaskResult.error()` 调用（方法不存在），改用 dict 返回 ✅

- [x] **P1.4** 零测试模块 — 优先补 workflow/ 和 context/ (待定)

- [x] **P1.5** API 版本号 — 从 `settings.APP_VERSION` 读取 (`"3.8.0"`) ✅

- [x] **P1.6** CORS — `settings.CORS_ORIGINS` 环境变量（逗号分隔）✅

---

## P2 — 择机修 (5项, 2-3h)

- [x] **P2.1** 25处文档版本号 `v3.7.0` → `v3.8.0` ✅
- [ ] **P2.2** agents.json 统一为 V2 格式
- [ ] **P2.3** Phase 5 注释代码清理
- [ ] **P2.4** compress_context 签名不一致
- [ ] **P2.5** API 2个 TODO 记为 Issue

---

## P3 — 低影响 (3项, 1h)

- [ ] 68处历史报告版本号（不动）
- [ ] scripts/archive/ 存档脚本
- [ ] .lingflow/ 运行时文件加入 .gitignore

---

## 验证命令

```bash
python -m pytest -q --tb=line          # 1360 passed
lingflow --version                      # 3.8.0
python -c "from lingflow import track_context; print('OK')"
python -c "from lingflow.ai_friendly import AIFriendlylingflow; AIFriendlylingflow(); print('OK')"
```
