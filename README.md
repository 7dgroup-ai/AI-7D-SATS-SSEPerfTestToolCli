# 7DGroup SSE 流式输出性能测试工具

**Author: 7DGroup**

这是一个专业级的 SSE（Server-Sent Events）流式输出性能测试与压测工具，由 7DGroup 团队开发，专为 AI 大模型流式响应场景设计。该工具采用 Python3 开发，提供了完整的性能测试解决方案，能够全面评估流式 AI 服务的响应速度、吞吐量、稳定性和并发处理能力。

## 架构图
![](assets/2026-01-15-21-47-26.png)

**核心能力**：
- **流式性能测试**：精确测量 SSE 流式输出的关键性能指标，包括首 Token 时间（TTFT）、每 Token 输出时间（TPOT）、首字节时间（TTFB）、吞吐量（tokens/s）等，帮助开发者深入了解 AI 服务的响应特性。
- **高并发压测**：支持多线程并发测试，可模拟大量用户同时访问的场景，通过配置线程数、执行时长、Ramp-up 等参数，灵活控制压测强度和模式，全面评估系统在高负载下的表现。
- **参数化测试**：支持查询文本参数化和 API Key 参数化，可以从文件中批量读取测试数据，实现多样化的测试场景，特别适用于多租户、多模型、负载均衡等复杂场景的性能评估。
- **实时监控统计**：多线程测试时自动启用实时汇总统计功能，每秒输出系统级别的性能指标，包括活跃线程数、累计数据块数、平均响应时间、TPOT、Tokens/s、成功率等，让测试过程可视化、可监控。
- **专业报告生成**：自动生成美观的 HTML 性能测试报告，包含 12+ 个关键指标的趋势图表、系统级别性能指标分析、详细的统计表格（平均值、最小值、最大值、P90、P95、P99 百分位数），支持交互式图表缩放和拖拽，所有图表同步缩放，方便深入分析性能数据。
- **智能重试机制**：内置 HTTP 重试机制，自动处理网络异常和服务器错误（429、500、502、503、504 状态码），最多重试 3 次，采用指数退避策略，提高测试的可靠性和稳定性。
- **灵活执行模式**：支持单次执行和持续执行两种模式，可以指定测试执行时长，结合 Ramp-up 功能实现渐进式压测，模拟真实的用户访问模式，全面评估系统的性能表现和稳定性。
- **线程安全设计**：采用线程锁机制保证多线程环境下的数据安全，参数化提供器支持线程安全的循环读取，确保高并发场景下的数据一致性和测试准确性。

**应用场景**：
- AI 大模型服务的性能评估和优化
- 流式 API 的响应速度测试
- 系统容量规划和负载评估
- 多租户、多模型场景的性能对比
- 生产环境性能监控和基准测试
- CI/CD 流程中的自动化性能测试


## 功能特性

- ✅ 支持 SSE 
- ✅ 计算关键性能指标：
  - **TTFT** (Time To First Token): 首Token时间
  - **TPOT** (Time Per Output Token): 每Token输出时间
  - **TTFB** (Time To First Byte): 首字节时间
  - **吞吐量**: tokens/秒
- ✅ 统计信息：
  - 数据块数量
  - Token 数量
  - 完整回答长度
  - 对话ID和消息ID
- ✅ **HTML 性能报告**：
  - 自动生成美观的 HTML 报告（默认输出到 `report/` 目录，文件名带时间戳）
  - 包含 12+ 个关键指标的趋势图表（TTFT、TPOT、TTFB、吞吐量、响应时间、Token 数量、RPS、线程数等）
  - 系统级别性能指标趋势图（系统总吞吐量、系统平均响应时间、系统平均TPOT、总请求数）
  - 详细的统计表格（平均值、最小值、最大值、P90、P95、P99）
  - 交互式图表支持缩放和拖拽（所有图表同步缩放）
  - 7DGroup 品牌标识
- ✅ **实时汇总统计**：
  - 多线程测试时每秒自动输出实时汇总统计
  - 显示活跃线程数、数据块数、平均响应时间、TPOT、Tokens/s、成功率等
- ✅ **HTTP 重试机制**：
  - 自动重试失败的请求（429、500、502、503、504 状态码）
  - 最多重试 3 次，带指数退避策略

## 项目结构

```
AI-7D-SATS-SSEPerfTestToolCli/
├── src/sse_perf_tool/        # 源代码目录
│   ├── __init__.py           # 包初始化文件
│   ├── providers.py          # 参数提供器（查询和 API Key）
│   ├── tester.py             # SSE 测试器核心逻辑
│   ├── test_runner.py        # 测试运行器和统计汇总
│   └── report_generator.py    # HTML 报告生成器
├── docs/                   # 文档目录
│   ├── 指标计算方法.md     # 性能指标计算说明
│   ├── 请求体模板使用指南.md # 请求体模板使用说明
│   ├── CLAUDE.md          # Claude Code 助手指南
│   └── AGENTS.md         # AI Agent 开发指南
├── examples/               # 示例目录
│   ├── request_body_template_default.json   # 默认请求体模板
│   ├── request_body_template_example.json  # OpenAI 风格请求体模板
│   └── queries_example.txt  # 查询示例文件
├── assets/                 # 资源目录
│   ├── 2026-01-15-21-47-26.png # 架构图
│   └── 架构图.html            # 交互式架构图
├── .github/                # GitHub 相关配置
│   ├── workflows/          # GitHub Actions 工作流
│   └── ISSUE_TEMPLATE/     # Issue 模板
├── tests/                 # 测试目录（待添加）
├── openspec/              # OpenSpec 规范
├── .gitignore            # Git 忽略文件配置
├── LICENSE               # 许可证
├── README.md             # 项目说明文档
├── CONTRIBUTING.md       # 贡献指南
├── PROJECT_STRUCTURE.md  # 项目结构详细说明
├── requirements.txt      # Python 依赖列表
└── sse_perfTestTool.py  # 主入口文件
```

## 安装依赖

```bash
pip3 install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
# API Key 可以是 'app-xxx' 或 'Bearer app-xxx' 格式
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"

# 或者使用完整 Bearer token 格式
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "Bearer app-xxx"
```

### 测试不同的 API 接口

默认情况下，工具测试的是 `/v1/chat-messages` 接口。如果您想测试其他 API 接口，可以使用 `--api-path` 参数：

```bash
# 测试默认接口（/v1/chat-messages）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"

# 测试其他接口，例如 OpenAI 风格的接口
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --api-path "/v1/chat/completions"

# 测试自定义接口
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --api-path "/api/v1/stream"

# 测试其他路径的接口
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --api-path "/stream/chat"
```

**注意**：
- `--api-path` 参数指定的是 API 的路径部分，不需要包含协议、主机和端口
- 路径应该以 `/` 开头，例如：`/v1/chat-messages`、`/api/stream` 等
- 不同的 API 接口可能有不同的请求体格式，可以使用 `--request-body-file` 参数指定自定义请求体模板

### 自定义请求体格式

不同的 API 接口通常需要不同的请求体格式。工具支持通过 JSON 模板文件自定义请求体格式：

```bash
# 使用自定义请求体模板
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" \
  --api-path "/v1/chat/completions" \
  --request-body-file examples/request_body_template_example.json
```

**请求体模板文件格式**：

模板文件是一个 JSON 文件，支持以下变量替换：
- `{query}` - 替换为查询文本
- `{conversation_id}` - 替换为对话ID
- `{user}` - 替换为用户标识
- `{inputs.key}` - 替换为 inputs 字典中对应 key 的值（如果提供了 inputs）
- `{files}` - 替换为文件列表（如果提供了 files）

**示例模板文件**：

1. **OpenAI 风格的接口** (`examples/request_body_template_example.json`):
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "user",
      "content": "{query}"
    }
  ],
  "stream": true,
  "temperature": 0.7,
  "user": "{user}"
}
```

2. **默认格式** (`examples/request_body_template_default.json`):
```json
{
  "inputs": {
    "query": "{query}"
  },
  "query": "{query}",
  "response_mode": "streaming",
  "conversation_id": "{conversation_id}",
  "user": "{user}",
  "files": []
}
```

**使用说明**：
- 如果不指定 `--request-body-file`，工具将使用默认的请求体格式（适用于 `/v1/chat-messages`）
- 如果指定了模板文件但加载失败，工具会回退到默认格式并显示警告
- 模板文件必须是有效的 JSON 格式
- 变量替换是递归的，支持嵌套的 JSON 结构

### 自定义查询

```bash
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --query "你好，请介绍一下你自己"
```

### 完整参数示例

```bash
python3 sse_perfTestTool.py \
  --host localhost \
  --port 80 \
  --api-key "app-1FOPPwMZseqz8rXLjs3G4Knu" \
  --query "你是谁" \
  --conversation-id "" \
  --user "gaolou" \
  --timeout 60
```

### 多线程测试

```bash
# 使用2个线程并发测试
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 2


python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-1FOPPwMZseqz8rXLjs3G4Knu" --threads 2



# 使用5个线程并发测试
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5
```

### 使用参数化文件

参数化文件是一个文本文件，每行一个查询文本。脚本会循环使用文件中的查询。

```bash
# 创建参数化文件 queries.txt，每行一个查询
echo -e "你是谁\n介绍一下你自己\n什么是人工智能" > queries.txt

# 使用参数化文件进行测试
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --param-file queries.txt

# 多线程 + 参数化文件（每个线程会循环使用文件中的查询）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --param-file queries.txt --threads 3
```

**参数化文件格式**：
- 每行一个查询文本
- 空行会被自动跳过
- 支持UTF-8编码的中文和英文
- 示例文件：`examples/queries_example.txt`

### 使用 API Key 参数化文件

支持从文件中读取多个 API Key，每个线程会循环使用文件中的 API Key。这对于测试不同 API Key 的性能或负载均衡场景很有用。

```bash
# 创建 API Key 文件 apiKeys.txt，每行一个 API Key
echo -e "app-key1\napp-key2\nBearer app-key3" > apiKeys.txt

# 使用 API Key 参数化文件进行测试
python3 sse_perfTestTool.py --host localhost --port 80 --api-key-file apiKeys.txt --threads 5

# 如果 API Key 文件读取失败，会回退到 --api-key 参数指定的默认 Key
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-default" --api-key-file apiKeys.txt
```

**API Key 文件格式**：
- 每行一个 API Key（可以是 `app-xxx` 或 `Bearer app-xxx` 格式）
- 空行会被自动跳过
- 支持UTF-8编码

### 静默模式（仅输出结果统计）

```bash
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --quiet
```

### 指定执行时间长度

默认情况下，每个线程执行一次请求后就会退出。使用 `--duration` 或 `--execution-time` 参数可以指定测试的执行时间长度，在指定时间内持续循环发送请求。

```bash
# 持续运行60秒（每个线程在60秒内循环发送请求）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --duration 60

# 使用 --execution-time 别名（等同于 --duration）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --execution-time 120

# 持续运行5分钟（300秒）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --duration 300

# 结合 ramp-up 使用（10个线程，10秒内逐步启动，然后持续运行60秒）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --ramp-up 10 --duration 60
```

**执行模式说明**：
- **单次执行模式**（`--duration 0` 或未指定）：每个线程执行一次请求后退出
- **持续执行模式**（`--duration > 0`）：在指定时间长度内，每个线程循环发送请求，直到时间到达

### 生成 HTML 性能报告

```bash
# 基本测试并生成报告（指定文件路径）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --html-report report.html

# 多线程测试并生成报告（指定文件路径）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --html-report report.html

# 持续测试并生成报告（指定文件路径）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --duration 60 --html-report report.html

# 不指定 --html-report，自动生成到 report/ 目录（文件名带时间戳）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5
# 报告会自动保存为: report/report_20260105_123456.html

# 指定模型名称（会包含在报告文件名中）
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --model-name "gpt-4" --threads 5
# 报告会自动保存为: report/report_gpt-4_20260105_123456.html
```

**HTML 报告特性**：
- 📊 包含 12+ 个关键指标的趋势图表：
  - 请求级别指标：TTFT、TPOT、TTFB、吞吐量、响应时间、Token 数量
  - 系统级别指标：RPS（每秒请求数）、活跃线程数、系统总吞吐量、系统平均响应时间、系统平均TPOT、总请求数
- 📈 使用 Chart.js 绘制的交互式图表，支持：
  - 拖拽选择区域放大（所有图表同步缩放）
  - 双击任意图表恢复原始视图
  - 鼠标悬停显示详细数值
- 📋 详细的统计表格（平均值、最小值、最大值、P90、P95、P99）
- 🎨 现代化的 UI 设计，包含 7DGroup 品牌标识
- 📱 响应式设计，支持不同屏幕尺寸
- 🔄 自动生成到 `report/` 目录（如果未指定路径），文件名包含时间戳和模型名称

**报告文件位置**：
- 如果指定 `--html-report`，报告保存到指定路径
- 如果未指定，报告自动保存到 `report/` 目录，文件名格式：`report_[模型名_]YYYYMMDD_HHMMSS.html`
- 报告文件可以在浏览器中直接打开查看

## 参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `--host` | 服务器主机地址 | localhost | 否 |
| `--port` | 服务器端口 | 80 | 否 |
| `--api-key` | API 密钥（支持 `app-xxx` 或 `Bearer app-xxx` 格式） | - | **是**（如果未使用 `--api-key-file`） |
| `--api-path` | API 路径（接口路径） | "/v1/chat-messages" | 否 |
| `--request-body-file` | 请求体模板文件路径（JSON 格式），支持变量替换 | None | 否 |
| `--query` | 查询文本 | "你是谁" | 否 |
| `--conversation-id` | 对话ID | "" | 否 |
| `--user` | 用户标识 | "gaolou" | 否 |
| `--timeout` | 请求超时时间（秒） | 60 | 否 |
| `--threads` | 并发线程数 | 1 | 否 |
| `--param-file` | 参数化文件路径（每行一个查询） | None | 否 |
| `--api-key-file` | API Key 参数化文件路径（每行一个 API Key） | None | 否 |
| `--ramp-up` | 压测线程递增时间（秒） | 0 | 否 |
| `--duration` / `--execution-time` | 测试执行时间长度（秒），>0 表示在指定时间窗口内循环发送请求，0 表示只执行一次 | 0 | 否 |
| `--html-report` | 生成 HTML 报告文件路径。如果不指定，默认输出到 `report/` 目录，文件名自动带时间戳 | None | 否 |
| `--model-name` | 模型名称（可选），如果提供会包含在报告文件名中 | None | 否 |
| `--quiet` | 静默模式，不输出详细信息和实时汇总统计 | False | 否 |

## 输出示例

### 单线程测试输出

```
============================================================
开始发送流式请求...
URL: http://localhost:80/v1/chat-messages
Query: 你是谁
============================================================
响应代码: 200
开始接收流式响应...
------------------------------------------------------------
[时间统计] 首字节时间(TTFB): 245.32 ms
[关键指标] 首Token时间(TTFT): 250.15 ms

----------------------------------------------------------------------------------------------------
        数据块      平均响应时间(ms)        TPOT(ms/token)            Tokens/s
----------------------------------------------------------------------------------------------------
           105                 27.82                 12.48                 80.46
           106                 27.56                 12.33                 81.46
...
----------------------------------------------------------------------------------------------------
============================================================
           流式响应接收完成 - 统计信息
============================================================
对话ID: abc123-def456-ghi789
消息ID: msg-123456
总数据块数: 25
Token数量: 45
完整回答长度: 120 字符
------------------------------------------------------------
[时间统计]
  连接时间: 5.23 ms
  首字节时间(TTFB): 245.32 ms
  流式传输时长: 1250.45 ms
  总响应时间: 1495.78 ms
------------------------------------------------------------
[关键指标]
  首Token时间(TTFT): 250.15 ms
  每Token时间(TPOT): 28.45 ms/token
  吞吐量: 35.15 tokens/秒
============================================================
```

### 多线程测试输出

```
已加载参数化文件: queries.txt
查询数量: 10

开始测试，线程数: 3
执行模式: 单次执行（每个线程执行一次后退出）
============================================================

--------------------------------------------------------------------------------------------------------------------------------------------
时间       线程数(活跃/总)    数据块  平均响应时间(ms)    TPOT(ms/token)            Tokens/s        成功率(%)
--------------------------------------------------------------------------------------------------------------------------------------------
10:30:15   3/3               15      1250.50             28.45                     35.15           100.00
10:30:16   3/3               30      1250.50             28.45                     35.15           100.00
10:30:17   3/3               45      1250.50             28.45                     35.15           100.00
...

============================================================
           测试完成 - 汇总统计
============================================================
配置线程数: 3
请求次数: 3
实际执行时间: 2.50 秒
成功: 3
失败: 0
成功率: 100.00 %
总数据块数: 75
总Token数: 135
总响应时间: 4487.34 ms
平均响应时间: 1495.78 ms
平均TTFB: 245.32 ms
平均TTFT: 250.15 ms
============================================================

✓ HTML 报告已生成: /path/to/report/report_20260105_103017.html
```

**实时汇总统计说明**：
- 多线程测试时，每秒自动输出一次实时汇总统计
- 显示当前时间、活跃线程数、累计数据块数、平均响应时间、TPOT、Tokens/s、成功率等
- 使用 `--quiet` 参数可以关闭实时汇总统计输出

## 关键指标说明

### TTFT (Time To First Token)
从请求开始到收到第一个包含 answer 的 token 的时间。这是衡量响应速度的重要指标。

### TPOT (Time Per Output Token)
每个输出 token 的平均时间，计算公式：
```
TPOT = (最后一个token时间 - 第一个token时间) / (token数量 - 1)
单位：毫秒/token (ms/token)
```

**说明**：使用 `(token数量 - 1)` 是因为计算的是 token 之间的间隔数。例如，如果有 3 个 token，那么有 2 个间隔。

### Tokens/s (Tokens per second)
每秒输出的 token 数量，计算公式：
```
Tokens/s = token数量 / (总时间 / 1000)
        = (token数量 * 1000) / 总时间(毫秒)
单位：tokens/秒
```

### TPOT 与 Tokens/s 的关系

TPOT 和 Tokens/s 是**倒数关系**，但需要考虑单位转换（毫秒 ↔ 秒）：

当 `token数量` 较大时，`token数量 - 1 ≈ token数量`，因此：

```
TPOT × Tokens/s ≈ 1000
```

即：
```
Tokens/s ≈ 1000 / TPOT
TPOT ≈ 1000 / Tokens/s
```

**示例**：
- 如果 TPOT = 12.5 ms/token
- 那么 Tokens/s ≈ 1000 / 12.5 = 80 tokens/s

**细微差别**：
- TPOT 使用 `(token数量 - 1)` 计算间隔时间
- Tokens/s 使用 `token数量` 计算总吞吐量
- 在 token 数量较大时，这个差别可以忽略；在 token 数量较少时会有一些差异

### 吞吐量 (Throughput)
每秒输出的 token 数量（与 Tokens/s 相同），计算公式：
```
吞吐量 = token数量 / 流式传输时长 * 1000
单位：tokens/秒
```

## 注意事项

1. **Token 估算**: 脚本使用简单的算法估算 token 数量（中文字符数 + 英文单词数）。对于精确的 token 计数，建议使用实际的 tokenizer。

2. **网络超时**: 默认超时时间为 60 秒，可以通过 `--timeout` 参数调整。

3. **错误处理**: 
   - 如果请求失败，脚本会返回错误信息并退出码为 1
   - 对于 429（限流）、500、502、503、504 状态码，会自动重试（最多 3 次，带指数退避）

4. **多线程测试**: 
   - 使用 `--threads` 参数可以指定并发线程数
   - 多线程测试时会自动启用实时汇总统计（每秒输出一次）
   - 多线程测试完成后会显示汇总统计信息
   - 建议根据服务器性能合理设置线程数，避免过载

5. **参数化文件**:
   - 参数化文件必须是UTF-8编码的文本文件
   - 每行一个查询文本，空行会被自动跳过
   - 当使用参数化文件时，每个线程会循环使用文件中的查询
   - 如果参数化文件不存在或读取失败，会使用默认查询或 `--query` 参数指定的查询
   - 示例文件：`examples/queries_example.txt`

6. **API Key 参数化**:
   - API Key 文件格式：每行一个 API Key（支持 `app-xxx` 或 `Bearer app-xxx` 格式）
   - 每个线程会循环使用文件中的 API Key
   - 如果 API Key 文件读取失败，会回退到 `--api-key` 参数指定的默认 Key
   - 适用于测试不同 API Key 的性能或负载均衡场景

7. **线程安全**: 参数化查询提供器和 API Key 提供器都使用线程锁保证线程安全，多个线程可以安全地并发读取。

8. **HTML 报告**:
   - 如果不指定 `--html-report`，报告会自动生成到 `report/` 目录
   - 报告文件名包含时间戳，格式：`report_[模型名_]YYYYMMDD_HHMMSS.html`
   - 如果 `report/` 目录不存在，会自动创建
   - 报告包含交互式图表，支持缩放和拖拽（所有图表同步缩放）

9. **测试不同的 API 接口**:
   - 使用 `--api-path` 参数可以指定不同的 API 接口路径
   - 默认接口是 `/v1/chat-messages`，适用于大多数 AI 对话接口
   - 使用 `--request-body-file` 参数可以指定自定义的请求体模板文件
   - 请求体模板支持变量替换：`{query}`, `{conversation_id}`, `{user}`, `{inputs.key}`, `{files}`
   - 如果不指定请求体模板，工具将使用默认的请求体格式（适用于 `/v1/chat-messages`）
   - 项目提供了示例模板文件：`examples/request_body_template_example.json`（OpenAI 风格）和 `examples/request_body_template_default.json`（默认格式）
   - 如果您的 API 响应格式不同（例如 JSON 字段名不同），可能需要修改 `src/sse_perf_tool/tester.py` 中的响应解析逻辑（查找 `answer` 字段的部分）


**常见问题**：
- 监控数据可能有 1-5 分钟的延迟
- 确认 API Key 属于当前查看的应用
- 检查监控界面的时间范围设置
- 确认响应代码为 200（请求成功）

## 项目信息

- **作者**: 7DGroup
- **版本**: 1.0
- **Python 版本**: 3.7+
- **依赖**: requests, urllib3
- **Git 仓库**: 本项目已初始化为 Git 仓库，可以使用 Git 进行版本控制

## 许可证

本项目采用 [GNU 通用公共许可证第 3 版（GPL v3）](https://www.gnu.org/licenses/gpl-3.0.html) 进行许可。

### 许可证说明

本项目是自由软件：您可以根据自由软件基金会发布的 GNU 通用公共许可证第 3 版或（根据您的选择）任何更高版本的条款重新分发和/或修改它。

本程序是希望它有用，但**没有任何保证**；甚至没有适销性或特定用途适用性的隐含保证。有关更多详细信息，请参阅 GNU 通用公共许可证。

您应该已经收到 GNU 通用公共许可证的副本。如果没有，请参阅 <https://www.gnu.org/licenses/>。

### 版权信息

**Copyright (C) 2026  7DGroup**

本项目采用 GPL v3 许可证，这意味着：
- ✅ 您可以自由使用、修改和分发本软件
- ✅ 您可以用于商业和非商业目的
- ✅ 如果您修改了代码，必须同样使用 GPL v3 许可证发布修改后的代码
- ✅ 您必须保留原始的版权声明和许可证信息

更多关于 GPL v3 的信息，请访问：<https://www.gnu.org/licenses/gpl-3.0.html>
