# 项目结构说明

```
AI-7D-SATS-SSEPerfTestToolCli/
├── .github/                    # GitHub 相关配置
│   ├── workflows/             # GitHub Actions 工作流
│   │   └── ci.yml            # CI 配置
│   └── ISSUE_TEMPLATE/       # Issue 模板
│       ├── bug_report.md     # Bug 报告模板
│       └── feature_request.md # 功能请求模板
├── src/                       # 源代码目录
│   └── sse_perf_tool/        # 主包
│       ├── __init__.py       # 包初始化文件
│       ├── providers.py      # 参数提供器（查询和 API Key）
│       ├── tester.py         # SSE 测试器核心逻辑
│       ├── test_runner.py    # 测试运行器和统计汇总
│       └── report_generator.py # HTML 报告生成器
├── tests/                     # 测试目录（待添加）
├── docs/                      # 文档目录
│   ├── 指标计算方法.md       # 性能指标计算说明
│   ├── 请求体模板使用指南.md # 请求体模板使用说明
│   ├── CLAUDE.md            # Claude Code 助手指南
│   └── AGENTS.md           # AI Agent 开发指南
├── examples/                  # 示例目录
│   ├── request_body_template_default.json   # 默认请求体模板
│   └── request_body_template_example.json  # OpenAI 风格请求体模板
├── assets/                    # 资源目录
│   ├── 2026-01-15-21-47-26.png # 架构图
│   └── 架构图.html            # 交互式架构图
├── openspec/                  # OpenSpec 规范（保留）
│   ├── AGENTS.md             # Agent 规范
│   ├── project.md            # 项目规范
│   └── changes/              # 变更记录
├── .gitignore                # Git 忽略文件配置
├── LICENSE                   # 许可证
├── README.md                 # 项目说明文档
├── CONTRIBUTING.md           # 贡献指南
├── PROJECT_STRUCTURE.md       # 项目结构说明
├── requirements.txt          # Python 依赖列表
└── sse_perfTestTool.py       # 主入口文件
```

## 目录说明

### src/sse_perf_tool/
包含所有核心源代码模块：
- `providers.py`: 提供查询和 API Key 的参数化支持
- `tester.py`: SSE 流式测试的核心实现
- `test_runner.py`: 多线程测试运行和统计汇总
- `report_generator.py`: HTML 性能报告生成

### docs/
项目相关文档：
- `指标计算方法.md`: 详细说明 TTFT、TPOT、TTFB 等指标的计算方法
- `请求体模板使用指南.md`: 如何使用自定义请求体模板

### examples/
示例文件和模板：
- JSON 请求体模板示例
- 可用于快速开始测试

### assets/
静态资源文件：
- 架构图
- 其他图片资源

### .github/
GitHub 相关配置：
- CI/CD 工作流
- Issue 和 PR 模板

## 开发指南

### 添加新功能
1. 在 `src/sse_perf_tool/` 中添加或修改模块
2. 更新相关文档
3. 添加示例（如需要）

### 运行测试
```bash
python sse_perfTestTool.py --help
```

### 安装依赖
```bash
pip install -r requirements.txt
```
