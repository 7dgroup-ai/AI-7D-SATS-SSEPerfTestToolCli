# SSE 流式输出性能测试工具

这是一个用于测试 SSE（Server-Sent Events）流式输出的 Python3 脚本，实现了与 `chatmessagestest.jmx` JMeter 脚本相同的功能。

## 功能特性

- ✅ 支持 SSE 
- ✅ 实时输出流式内容
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
  - 自动生成美观的 HTML 报告
  - 包含关键指标的趋势图表（TTFT、TPOT、TTFB、吞吐量等）
  - 详细的统计表格
  - 7DGroup 品牌标识

## 安装依赖

```bash
pip3 install -r requirements.txt
```

## 使用方法

### 基本用法

```bash
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"
```

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
- 示例文件：`queries_example.txt`

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
# 基本测试并生成报告
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --html-report report.html

# 多线程测试并生成报告
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --html-report report.html

# 持续测试并生成报告
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --duration 60 --html-report report.html
```

**HTML 报告特性**：
- 📊 包含 6 个关键指标的趋势图表（TTFT、TPOT、TTFB、吞吐量、响应时间、Token 数量）
- 📈 使用 Chart.js 绘制的交互式图表
- 📋 详细的统计表格（平均值、最小值、最大值）
- 🎨 现代化的 UI 设计，包含 7DGroup 品牌标识
- 📱 响应式设计，支持不同屏幕尺寸

报告文件可以在浏览器中直接打开查看。

## 参数说明

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `--host` | 服务器主机地址 | localhost | 否 |
| `--port` | 服务器端口 | 80 | 否 |
| `--api-key` | API 密钥（Bearer token） | - | **是** |
| `--query` | 查询文本 | "你是谁" | 否 |
| `--conversation-id` | 对话ID | "" | 否 |
| `--user` | 用户标识 | "gaolou" | 否 |
| `--timeout` | 请求超时时间（秒） | 60 | 否 |
| `--threads` | 并发线程数 | 1 | 否 |
| `--param-file` | 参数化文件路径（每行一个查询） | None | 否 |
| `--api-key-file` | API Key 参数化文件路径（每行一个 API Key） | None | 否 |
| `--ramp-up` | 压测线程递增时间（秒） | 0 | 否 |
| `--duration` / `--execution-time` | 测试执行时间长度（秒），>0 表示在指定时间窗口内循环发送请求，0 表示只执行一次 | 0 | 否 |
| `--html-report` | 生成 HTML 报告文件路径 | None | 否 |
| `--quiet` | 静默模式 | False | 否 |

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

开始多线程测试，线程数: 3
============================================================

[线程1] 开始发送流式请求...
[线程1] URL: http://localhost:80/v1/chat-messages
[线程1] Query: 你是谁
============================================================
[线程2] 开始发送流式请求...
[线程2] URL: http://localhost:80/v1/chat-messages
[线程2] Query: 介绍一下你自己
============================================================
[线程3] 开始发送流式请求...
[线程3] URL: http://localhost:80/v1/chat-messages
[线程3] Query: 什么是人工智能
============================================================

[线程1] 响应代码: 200
[线程1] 开始接收流式响应...
------------------------------------------------------------
[线程1] [关键指标] 首Token时间(TTFT): 250.15 ms

----------------------------------------------------------------------------------------------------
[线程1]         数据块      平均响应时间(ms)        TPOT(ms/token)            Tokens/s
----------------------------------------------------------------------------------------------------
[线程1]           105                 27.82                 12.48                 80.46
...

============================================================
           多线程测试完成 - 汇总统计
============================================================
总线程数: 3
成功: 3
失败: 0
总数据块数: 75
总Token数: 135
总响应时间: 4487.34 ms
平均响应时间: 1495.78 ms
============================================================
```

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

## 与 JMeter 脚本的对应关系

| JMeter 功能 | Python 实现 |
|------------|-------------|
| JSR223Sampler | `test_streaming()` 方法 |
| SSE 流式处理 | `response.iter_lines()` |
| TTFB 计算 | `first_byte_time - request_start_time` |
| TTFT 计算 | `first_token_time - request_start_time` |
| TPOT 计算 | `(last_token_time - first_token_time) / (token_count - 1)` |
| 实时输出 | `print(answer_chunk, end="", flush=True)` |

## 注意事项

1. **Token 估算**: 脚本使用简单的算法估算 token 数量（中文字符数 + 英文单词数）。对于精确的 token 计数，建议使用实际的 tokenizer。

2. **网络超时**: 默认超时时间为 60 秒，可以通过 `--timeout` 参数调整。

3. **错误处理**: 如果请求失败，脚本会返回错误信息并退出码为 1。

4. **多线程测试**: 
   - 使用 `--threads` 参数可以指定并发线程数
   - 每个线程会独立执行测试，输出会带有线程ID标识（如 `[线程1]`）
   - 多线程测试完成后会显示汇总统计信息
   - 建议根据服务器性能合理设置线程数，避免过载

5. **参数化文件**:
   - 参数化文件必须是UTF-8编码的文本文件
   - 每行一个查询文本，空行会被自动跳过
   - 当使用参数化文件时，每个线程会循环使用文件中的查询
   - 如果参数化文件不存在或读取失败，会使用默认查询或 `--query` 参数指定的查询
   - 示例文件：`queries_example.txt`

6. **线程安全**: 参数化查询提供器使用线程锁保证线程安全，多个线程可以安全地并发读取查询。

## 故障排查

如果在执行脚本后，监控界面中没有看到新数据，请参考 [故障排查指南](TROUBLESHOOTING.md)。

**常见问题**：
- 监控数据可能有 1-5 分钟的延迟
- 确认 API Key 属于当前查看的应用
- 检查监控界面的时间范围设置
- 确认响应代码为 200（请求成功）

## 许可证

本脚本遵循与原项目相同的许可证。
