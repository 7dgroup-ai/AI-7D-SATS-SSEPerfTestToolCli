## ADDED Requirements

### Requirement: Report Summary Cards Enhancement
报告 SHALL 在汇总卡片区域显示数据块数量（chunk_count）和平均响应时间指标。

#### Scenario: 汇总卡片显示完整指标
- **WHEN** 生成 HTML 报告
- **THEN** 汇总卡片区域 SHALL 包含以下指标：
  - 总请求数
  - 成功率
  - 成功请求数
  - 失败请求数
  - 数据块数量（总 chunk 数）
  - 平均响应时间
  - 平均 TTFT
  - 平均 TPOT
  - 平均吞吐量
  - 总 Token 数

### Requirement: Two-Column Chart Layout
趋势图 SHALL 以一行两列的网格布局显示，减少页面垂直空间占用。

#### Scenario: 图表两列布局
- **WHEN** 用户在桌面浏览器中查看报告
- **THEN** 趋势图 SHALL 以一行两列的方式排列
- **AND** 每个图表保持可读性和交互性

#### Scenario: 小屏幕响应式布局
- **WHEN** 用户在移动设备或窄屏幕中查看报告
- **THEN** 趋势图 SHALL 自动切换为单列布局

### Requirement: RPS Trend Chart
报告 SHALL 包含 RPS（每秒请求数）趋势图，显示测试过程中请求速率的变化。

#### Scenario: RPS 趋势图显示
- **WHEN** 生成 HTML 报告
- **THEN** 报告 SHALL 包含 RPS 趋势图
- **AND** 图表横坐标为时间（时:分:秒格式）
- **AND** 图表纵坐标为每秒请求数

### Requirement: Enhanced 7DGroup Logo
报告 SHALL 显示重新设计的 7DGroup LOGO，使用炫酷的渐变色和动画效果。

#### Scenario: 炫酷 LOGO 显示
- **WHEN** 用户查看报告头部
- **THEN** SHALL 显示带有渐变色的 7DGroup LOGO
- **AND** LOGO 可以包含动画效果（如微光、呼吸等）

### Requirement: Percentile Statistics in Detail Table
详细指标统计表 SHALL 显示每个指标的 P90、P95、P99 百分位数值。

#### Scenario: 百分位数统计显示
- **WHEN** 用户查看详细指标统计表
- **THEN** 表格 SHALL 包含以下列：指标名称、平均值、最小值、最大值、P90、P95、P99、单位
- **AND** 所有关键指标（TTFT、TPOT、TTFB、吞吐量、响应时间、RPS）都显示完整统计

### Requirement: Chart Zoom and Pan Interaction
所有趋势图 SHALL 支持通过鼠标拖拽选择时间范围进行放大，并提供重置功能。

#### Scenario: 拖拽放大功能
- **WHEN** 用户在图表上拖拽选择区域
- **THEN** 图表 SHALL 放大到选中的时间范围

#### Scenario: 重置缩放功能
- **WHEN** 用户双击图表或点击重置按钮
- **THEN** 图表 SHALL 恢复到初始显示范围
