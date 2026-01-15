## ADDED Requirements

### Requirement: Report Directory Auto-Creation
当生成 HTML 报告时，系统 SHALL 自动创建 `report/` 目录（如果该目录不存在）。

#### Scenario: report 目录不存在时自动创建
- **WHEN** 用户运行测试且未指定 `--html-report` 参数
- **AND** 项目根目录下不存在 `report/` 目录
- **THEN** 系统 SHALL 自动创建 `report/` 目录
- **AND** 将报告文件生成到该目录中

#### Scenario: report 目录已存在
- **WHEN** 用户运行测试且未指定 `--html-report` 参数
- **AND** 项目根目录下已存在 `report/` 目录
- **THEN** 系统 SHALL 直接将报告文件生成到该目录中

### Requirement: Default Report Output Path
系统 SHALL 将默认报告输出路径设置为 `report/` 目录下，文件名格式保持为 `report_[model_name]_[timestamp].html` 或 `report_[timestamp].html`。

#### Scenario: 默认报告路径
- **WHEN** 用户运行测试且未指定 `--html-report` 参数
- **THEN** 报告文件 SHALL 生成到 `report/` 目录下
- **AND** 文件名包含时间戳（格式：YYYYMMDD_HHMMSS）

#### Scenario: 使用模型名称的报告命名
- **WHEN** 用户运行测试且指定了 `--model-name` 参数
- **AND** 未指定 `--html-report` 参数
- **THEN** 报告文件 SHALL 命名为 `report_[safe_model_name]_[timestamp].html`
- **AND** 输出到 `report/` 目录

### Requirement: Custom Report Path Override
当用户通过 `--html-report` 参数指定自定义路径时，系统 SHALL 使用用户指定的路径，而非默认的 `report/` 目录。

#### Scenario: 用户指定自定义报告路径
- **WHEN** 用户运行测试且指定 `--html-report /custom/path/report.html`
- **THEN** 报告文件 SHALL 生成到用户指定的路径
- **AND** 不使用默认的 `report/` 目录

#### Scenario: 用户指定自定义目录中的报告
- **WHEN** 用户运行测试且指定 `--html-report output/my_report.html`
- **THEN** 报告文件 SHALL 生成到 `output/my_report.html`
