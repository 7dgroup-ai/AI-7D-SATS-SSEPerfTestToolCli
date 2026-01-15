# Tasks: add-report-directory

## 1. Implementation
- [x] 1.1 修改 `report_generator.py`：在生成报告前检查并创建 `report/` 目录
- [x] 1.2 修改 `report_generator.py`：更新默认输出路径为 `report/` 目录下
- [x] 1.3 修改 `sse_perfTestTool.py`：更新默认报告路径逻辑

## 2. Validation
- [x] 2.1 测试默认情况下报告生成到 `report/` 目录
- [x] 2.2 测试 `report/` 目录不存在时自动创建
- [x] 2.3 测试 `--html-report` 自定义路径仍然正常工作
