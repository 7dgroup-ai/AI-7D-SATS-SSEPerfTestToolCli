# Change: 将生成的报告输出到 report 目录

## Why
当前工具生成的 HTML 报告文件直接输出到项目根目录，导致根目录下报告文件堆积，影响项目结构整洁性。将报告文件统一存放到 `report/` 目录可以更好地组织输出文件。

## What Changes
- 修改默认报告输出路径为 `report/` 目录
- 如果 `report/` 目录不存在，自动创建该目录
- 保持 `--html-report` 参数的自定义路径功能不变（用户显式指定路径时使用用户路径）

## Impact
- Affected specs: report-generation（新建）
- Affected code:
  - `report_generator.py`: 修改 `generate_html_report` 函数中的默认输出路径逻辑
  - `sse_perfTestTool.py`: 修改默认报告路径的传递逻辑
