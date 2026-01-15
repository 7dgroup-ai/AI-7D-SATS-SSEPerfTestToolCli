# 从零编写 AI 大模型压测工具教程 v1.0

本教程将带你从零开始，逐步构建一个功能完整的 AI 大模型流式输出性能测试工具。我们将以 SSE 流式输出测试脚本为例，详细讲解每个步骤和关键技术点。

## 目录

1. [项目概述](#项目概述)
2. [技术栈选择](#技术栈选择)
3. [架构设计](#架构设计)
4. [逐步实现](#逐步实现)
5. [关键技术详解](#关键技术详解)
6. [测试与优化](#测试与优化)
7. [扩展功能](#扩展功能)
8. [最佳实践](#最佳实践)

---

## 项目概述

### 目标

构建一个 AI 大模型流式输出性能测试工具，能够：

- 测试流式 API 的性能
- 计算关键性能指标（TTFT、TPOT、TTFB 等）
- 支持多线程并发测试
- 支持参数化测试
- 提供实时统计和汇总报告
- 生成可视化 HTML 报告

### 核心功能

1. **流式响应处理**：处理 SSE（Server-Sent Events）格式的流式响应
2. **性能指标计算**：计算 TTFT、TPOT、吞吐量等关键指标
3. **并发测试**：支持多线程并发压测
4. **参数化支持**：支持从文件读取查询和 API Key
5. **实时统计**：每秒汇总所有线程的统计数据
6. **结果报告**：生成详细的 HTML 可视化测试报告

---

## 技术栈选择

### Python 3.x

选择 Python 的原因：
- 丰富的 HTTP 库（requests）
- 强大的并发支持（threading）
- 简洁的语法，易于维护
- 丰富的第三方库生态

### 核心依赖

```python
import json          # JSON 数据处理
import time          # 时间戳和延时
import sys           # 系统相关
import argparse      # 命令行参数解析
import threading     # 多线程支持
from datetime import datetime  # 时间格式化
from typing import Dict, List, Optional, Any  # 类型提示
from collections import deque  # 双端队列（用于循环）
import requests      # HTTP 请求库
from requests.adapters import HTTPAdapter  # 请求适配器
from urllib3.util.retry import Retry  # 重试策略
```

### 依赖安装

创建 `requirements.txt`：

```txt
requests>=2.28.0
urllib3>=1.26.0
```

安装命令：

```bash
pip3 install -r requirements.txt
```

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────┐
│              命令行接口层                        │
│         (argparse 参数解析)                      │
│         sse_perfTestTool.py                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              核心测试引擎                        │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ QueryProvider│  │ApiKeyProvider│            │
│  │ (查询提供器) │  │ (Key提供器)  │            │
│  │ providers.py │  │ providers.py │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────────────────────────────┐     │
│  │     SSETester (测试器)                │     │
│  │  - 发送请求                           │     │
│  │  - 处理流式响应                       │     │
│  │  - 计算性能指标                       │     │
│  │  tester.py                            │     │
│  └──────────────────────────────────────┘     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              并发控制层                          │
│  - 线程管理                                     │
│  - Ramp-up 控制                                 │
│  - Duration 控制                                │
│  - 共享统计信息                                 │
│  test_runner.py                                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              报告生成层                          │
│  - HTML 可视化报告                              │
│  - Chart.js 趋势图                              │
│  - 百分位统计                                   │
│  report_generator.py                            │
└─────────────────────────────────────────────────┘
```

### 核心类设计

1. **QueryProvider**：线程安全的查询提供器（providers.py）
2. **ApiKeyProvider**：线程安全的 API Key 提供器（providers.py）
3. **SSETester**：核心测试器类（tester.py）
4. **run_test_thread**：线程执行函数（test_runner.py）
5. **aggregate_stats**：统计汇总函数（test_runner.py）
6. **generate_html_report**：HTML 报告生成函数（report_generator.py）

---

## 逐步实现

### 第一步：项目初始化

创建项目结构：

```bash
mkdir sse_perf_test_tool
cd sse_perf_test_tool
touch sse_perfTestTool.py    # 主入口
touch providers.py           # 参数提供器
touch tester.py              # 测试器
touch test_runner.py         # 测试运行器
touch report_generator.py    # 报告生成器
touch requirements.txt
touch README.md
```

编写 `requirements.txt`：

```txt
requests>=2.28.0
urllib3>=1.26.0
```

### 第二步：基础框架搭建

#### 2.1 导入必要的库

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 大模型流式输出性能测试工具
"""

import json
import time
import sys
import argparse
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import deque
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
```

#### 2.2 创建基础测试器类

```python
class SSETester:
    """SSE 流式输出测试器"""

    def __init__(self, host: str = "localhost", port: int = 80,
                 api_key: str = "", timeout: int = 60):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"

        # 创建带重试机制的 session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
```

**关键点**：
- 使用 `requests.Session()` 复用连接，提高性能
- 配置重试策略，自动处理临时错误
- 支持 HTTP 和 HTTPS
- 默认端口为 80（与实际代码一致）

### 第三步：实现流式响应处理

#### 3.1 发送流式请求

```python
def test_streaming(self, query: str = "你是谁", inputs: Optional[Dict] = None,
                  conversation_id: str = "", user: str = "gaolou",
                  files: Optional[List[Dict]] = None,
                  verbose: bool = True, thread_id: Optional[int] = None,
                  shared_stats: Optional[Dict[str, Any]] = None,
                  api_key_override: Optional[str] = None) -> Dict:
    """测试 SSE 流式输出"""

    # 构建请求 URL
    url = f"{self.base_url}/v1/chat-messages"

    # 构建请求体
    request_body = {
        "inputs": inputs if inputs else {"query": query},
        "query": query,
        "response_mode": "streaming",
        "conversation_id": conversation_id,
        "user": user,
        "files": files if files else []
    }

    # 智能处理 API key：如果已经包含 "Bearer " 前缀，就不再添加
    use_api_key = api_key_override if api_key_override else self.api_key
    auth_token = use_api_key if use_api_key.startswith("Bearer ") else f"Bearer {use_api_key}"

    # 设置请求头
    headers = {
        "Authorization": auth_token,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    # 初始化统计变量
    stats = {
        "thread_id": thread_id,
        "request_start_time": 0,
        "first_byte_time": 0,
        "first_token_time": 0,
        "last_byte_time": 0,
        "request_end_time": 0,
        "chunk_count": 0,
        "token_count": 0,
        "full_answer": "",
        "error": None,
        "token_times": []  # 记录每个 token 的时间戳
    }

    try:
        # 记录请求开始时间
        stats["request_start_time"] = time.time() * 1000

        # 发送 POST 请求，启用流式响应
        response = self.session.post(
            url,
            json=request_body,
            headers=headers,
            stream=True,  # 关键：启用流式响应
            timeout=self.timeout
        )

        # 检查响应状态（支持 2xx 状态码）
        if response.status_code < 200 or response.status_code >= 300:
            error_text = response.text
            stats["error"] = f"HTTP {response.status_code}: {error_text}"
            return stats

        # 处理流式响应
        # ...

    except Exception as e:
        stats["error"] = str(e)
        return stats
```

**关键点**：
- `stream=True`：启用流式响应，不会一次性加载所有内容
- 使用毫秒级时间戳，提高精度
- 智能处理 API Key 的 Bearer 前缀
- 支持 2xx 范围内的所有成功状态码
- 完善的错误处理

#### 3.2 解析 SSE 格式响应

```python
# 读取流式响应
first_byte_received = False
first_token_received = False

for line in response.iter_lines(decode_unicode=True):
    if line is None:
        continue

    # 记录首字节时间
    if not first_byte_received:
        stats["first_byte_time"] = time.time() * 1000
        first_byte_received = True

    # 更新最后字节时间
    stats["last_byte_time"] = time.time() * 1000

    # 处理 Server-Sent Events (SSE) 格式
    if line.startswith("data: "):
        data = line[6:]  # 去掉 "data: " 前缀

        # 跳过空数据或结束标记
        if not data.strip() or data.strip() == "[DONE]":
            continue

        try:
            # 解析 JSON 数据
            json_data = json.loads(data)

            # 提取流式文本数据
            if "answer" in json_data:
                answer_chunk = json_data["answer"]

                # 记录第一个 token 的时间（TTFT）
                if not first_token_received:
                    stats["first_token_time"] = time.time() * 1000
                    first_token_received = True

                # 计算 token 数量
                chunk_tokens = self._estimate_tokens(answer_chunk)
                stats["token_count"] += chunk_tokens

                # 记录每个 token 的时间戳（用于计算 TPOT）
                current_time = time.time() * 1000
                for _ in range(chunk_tokens):
                    stats["token_times"].append(current_time)

                # 更新统计
                stats["full_answer"] += answer_chunk
                stats["chunk_count"] += 1

                # 将实时统计写入共享汇总
                if shared_stats is not None and thread_id is not None:
                    with shared_stats["lock"]:
                        prev = shared_stats["thread_stats"].get(thread_id, {})
                        shared_stats["thread_stats"][thread_id] = {
                            "start_time": prev.get("start_time", stats["request_start_time"]),
                            "chunks": prev.get("chunks", 0) + 1,
                            "tokens": prev.get("tokens", 0) + chunk_tokens,
                            "last_update": current_time
                        }

        except json.JSONDecodeError:
            # 处理解析错误
            pass
```

**关键点**：
- `iter_lines(decode_unicode=True)`：逐行读取，自动解码 Unicode
- SSE 格式：`data: {...}` 前缀
- 实时处理：每收到一个数据块立即处理
- 实时更新共享统计信息

### 第四步：实现性能指标计算

#### 4.1 Token 数量估算

```python
def _estimate_tokens(self, text: str) -> int:
    """
    估算文本的 token 数量
    简单估算：中文字符算1个token，英文单词算1个token
    """
    # 中文字符数
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

    # 英文单词数
    english_words = len([w for w in text.split() if w.isalpha()])

    # 至少算1个token
    return max(1, chinese_chars + english_words)
```

**说明**：
- 这是简化估算，实际项目中可以使用 tiktoken 等库
- 对于精确测试，建议使用实际的 tokenizer

#### 4.2 计算关键指标

```python
def _calculate_metrics(self, stats: Dict):
    """计算关键性能指标"""

    # 1. TTFB (Time To First Byte)
    stats["ttfb"] = stats["first_byte_time"] - stats["request_start_time"] if stats["first_byte_time"] > 0 else 0

    # 2. TTFT (Time To First Token)
    if stats["first_token_time"] > 0:
        stats["ttft"] = stats["first_token_time"] - stats["request_start_time"]
    else:
        stats["ttft"] = 0

    # 3. TPOT (Time Per Output Token)
    # 需要记录每个 token 的时间戳
    if stats["token_count"] > 1 and len(stats["token_times"]) > 1:
        first_token_time = stats["token_times"][0]
        last_token_time = stats["token_times"][-1]
        total_token_time = last_token_time - first_token_time
        stats["tpot"] = total_token_time / (stats["token_count"] - 1)
    elif stats["token_count"] == 1:
        # 只有一个 token，TPOT 为 0
        stats["tpot"] = 0
    else:
        stats["tpot"] = 0

    # 4. 流式传输时长
    if stats["first_byte_time"] > 0:
        stats["streaming_duration"] = stats["last_byte_time"] - stats["first_byte_time"]
    else:
        stats["streaming_duration"] = 0

    # 5. 吞吐量 (Tokens/s)
    if stats["streaming_duration"] > 0 and stats["token_count"] > 0:
        stats["throughput"] = (stats["token_count"] / stats["streaming_duration"]) * 1000  # tokens/秒
    else:
        stats["throughput"] = 0

    # 6. 总响应时间
    stats["total_response_time"] = stats["request_end_time"] - stats["request_start_time"]
```

**关键指标说明**：

1. **TTFB (Time To First Byte)**
   - 从请求开始到收到第一个字节的时间
   - 反映网络延迟和服务器初始响应速度

2. **TTFT (Time To First Token)**
   - 从请求开始到收到第一个有效 token 的时间
   - AI 模型性能的关键指标

3. **TPOT (Time Per Output Token)**
   - 每个输出 token 的平均时间
   - 计算公式：`(最后token时间 - 第一个token时间) / (token数量 - 1)`
   - 只有1个token时，TPOT为0（无间隔可计算）

4. **吞吐量 (Throughput)**
   - 每秒输出的 token 数量
   - 反映整体性能

### 第五步：实现线程安全的参数化提供器

#### 5.1 QueryProvider 实现

```python
class QueryProvider:
    """参数化查询提供器（线程安全）"""

    def __init__(self, param_file: Optional[str] = None, default_query: str = "你是谁"):
        """
        初始化查询提供器

        Args:
            param_file: 参数化文件路径，每行一个查询
            default_query: 默认查询文本（默认为"你是谁"）
        """
        self.lock = threading.Lock()  # 线程锁
        self.queries = deque()        # 使用双端队列
        self.current_index = 0

        # 从文件读取查询
        if param_file:
            try:
                with open(param_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        query = line.strip()
                        if query:  # 跳过空行
                            self.queries.append(query)
            except FileNotFoundError:
                print(f"警告: 参数化文件 '{param_file}' 不存在，使用默认查询")
                self.queries.append(default_query)
            except Exception as e:
                print(f"警告: 读取参数化文件失败: {e}，使用默认查询")
                self.queries.append(default_query)
        else:
            self.queries.append(default_query)

        if not self.queries:
            self.queries.append(default_query)

    def get_next_query(self) -> str:
        """获取下一个查询（线程安全，循环轮询）"""
        with self.lock:  # 使用锁保证线程安全
            if not self.queries:
                return "你是谁"

            query = self.queries[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.queries)  # 循环
            return query
```

**关键点**：
- `threading.Lock()`：保证多线程安全
- `deque`：高效的双端队列
- 循环轮询：使用取模运算实现循环
- 默认查询为 "你是谁"（与实际代码一致）

#### 5.2 ApiKeyProvider 实现

```python
class ApiKeyProvider:
    """API Key 提供器（线程安全，循环使用）"""

    def __init__(self, key_file: Optional[str] = None, default_key: str = ""):
        self.lock = threading.Lock()
        self.keys = deque()
        self.current_index = 0

        if key_file:
            try:
                with open(key_file, "r", encoding="utf-8") as f:
                    for line in f:
                        k = line.strip()
                        if k:
                            self.keys.append(k)
            except Exception as e:
                print(f"警告: 读取 API Key 文件失败 ({e})，回退到默认 key")
                if default_key:
                    self.keys.append(default_key)

        if not self.keys and default_key:
            self.keys.append(default_key)

    def get_next_key(self) -> str:
        """获取下一个 API Key（线程安全）"""
        with self.lock:
            if not self.keys:
                return ""
            key = self.keys[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.keys)
            return key
```

### 第六步：实现多线程并发测试

#### 6.1 线程执行函数

```python
def run_test_thread(tester: SSETester, query_provider: QueryProvider,
                    thread_id: int, conversation_id: str, user: str,
                    verbose: bool, results_list: List[Dict], results_lock: threading.Lock,
                    shared_stats: Optional[Dict[str, Any]] = None,
                    stop_event: Optional[threading.Event] = None,
                    end_time_ms: Optional[float] = None,
                    api_key_provider: Optional[ApiKeyProvider] = None):
    """运行测试的线程函数"""

    # 初始化线程统计
    if shared_stats is not None:
        with shared_stats["lock"]:
            shared_stats["thread_stats"][thread_id] = {
                "start_time": time.time() * 1000,
                "chunks": 0,
                "tokens": 0,
                "last_update": time.time() * 1000
            }

    # 循环执行测试（如果设置了 duration）
    def time_remaining_ok() -> bool:
        if stop_event and stop_event.is_set():
            return False
        if end_time_ms is not None:
            return time.time() * 1000 < end_time_ms
        return True

    while time_remaining_ok():
        # 获取 API Key（支持循环使用）
        api_key = api_key_provider.get_next_key() if api_key_provider else tester.api_key
        if not api_key:
            break

        # 执行测试
        result = tester.test_streaming(
            query=query_provider.get_next_query(),
            conversation_id=conversation_id,
            user=user,
            verbose=verbose,
            thread_id=thread_id,
            shared_stats=shared_stats,
            api_key_override=api_key
        )

        # 保存结果
        result["thread_id"] = thread_id
        with results_lock:
            results_list.append(result)

        # 更新共享统计
        if shared_stats is not None:
            with shared_stats["lock"]:
                shared_stats["requests"] += 1
                if not result.get("error"):
                    shared_stats["success"] += 1
                    # 记录每个线程的请求指标，用于按线程计算
                    if "thread_requests" not in shared_stats:
                        shared_stats["thread_requests"] = {}
                    if thread_id not in shared_stats["thread_requests"]:
                        shared_stats["thread_requests"][thread_id] = []
                    shared_stats["thread_requests"][thread_id].append({
                        "ttft": result.get("ttft", 0),
                        "tpot": result.get("tpot", 0),
                        "ttfb": result.get("ttfb", 0),
                        "throughput": result.get("throughput", 0),
                        "total_response_time": result.get("total_response_time", 0),
                        "token_count": result.get("token_count", 0),
                        "chunk_count": result.get("chunk_count", 0)
                    })
                else:
                    shared_stats["fail"] += 1

        # 如果只跑一次，退出循环
        if end_time_ms is None and stop_event is None:
            break
```

**关键点**：
- 使用 `threading.Event` 控制线程停止
- 使用 `threading.Lock` 保护共享数据
- 支持循环执行（duration 模式）
- 支持 API Key 循环使用
- 记录每个线程的请求指标用于加权平均计算

#### 6.2 主函数中的线程管理

```python
def main():
    parser = argparse.ArgumentParser(
        description="SSE 流式输出性能测试工具（支持多线程和参数化）"
    )
    parser.add_argument("--host", type=str, default="localhost",
                       help="服务器主机地址")
    parser.add_argument("--port", type=int, default=80,
                       help="服务器端口（默认: 80）")
    parser.add_argument("--api-key", type=str, default="",
                       help="API 密钥 (可以是 'app-xxx' 或 'Bearer app-xxx' 格式)")
    parser.add_argument("--threads", type=int, default=1,
                       help="并发线程数")
    parser.add_argument("--ramp-up", type=int, default=0,
                       help="线程递增时间（秒）")
    parser.add_argument("--duration", "--execution-time", type=int, default=0, dest="duration",
                       help="测试持续时间（秒），>0 表示循环发送，0 表示只执行一次")
    parser.add_argument("--param-file", type=str, default=None,
                       help="参数化文件路径")
    parser.add_argument("--api-key-file", type=str, default=None,
                       help="API Key 参数化文件路径")
    parser.add_argument("--quiet", action="store_true",
                       help="静默模式")
    parser.add_argument("--html-report", type=str, default=None,
                       help="HTML 报告文件路径")
    parser.add_argument("--model-name", type=str, default=None,
                       help="模型名称（可选）")
    # ... 其他参数

    args = parser.parse_args()

    # 创建测试器
    tester = SSETester(host=args.host, port=args.port, api_key=args.api_key)

    # 创建查询提供器
    query_provider = QueryProvider(param_file=args.param_file, default_query=args.query)

    # 创建 API Key 提供器
    api_key_provider = None
    if args.api_key_file:
        api_key_provider = ApiKeyProvider(args.api_key_file, args.api_key)

    # 初始化共享统计
    shared_stats = {
        "lock": threading.Lock(),
        "thread_stats": {},
        "start_time": time.time() * 1000,
        "total_threads": args.threads,
        "requests": 0,
        "success": 0,
        "fail": 0
    }

    # 创建停止事件和持续时间控制
    stop_event = threading.Event()
    duration_ms = args.duration * 1000 if args.duration > 0 else None
    end_time_ms = shared_stats["start_time"] + duration_ms if duration_ms else None

    # 启动汇总线程
    results_list = []
    results_lock = threading.Lock()

    agg_thread = threading.Thread(
        target=aggregate_stats,
        args=(shared_stats, stop_event, not args.quiet),
        daemon=True
    )
    agg_thread.start()

    # 创建并启动测试线程
    threads = []
    for i in range(args.threads):
        # Ramp-up 控制：逐步启动线程
        if args.ramp_up > 0 and i > 0:
            ramp_step = args.ramp_up / args.threads
            time.sleep(ramp_step)

        thread = threading.Thread(
            target=run_test_thread,
            args=(tester, query_provider, i + 1, args.conversation_id,
                  args.user, False, results_list, results_lock,
                  shared_stats, stop_event, end_time_ms, api_key_provider)
        )
        threads.append(thread)
        thread.start()

    # 持续时间控制：到达时间后触发停止
    if duration_ms:
        def timer_stop():
            time.sleep(args.duration)
            stop_event.set()
        timer_thread = threading.Thread(target=timer_stop, daemon=True)
        timer_thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 停止汇总线程
    stop_event.set()
    agg_thread.join(timeout=2)

    # 生成 HTML 报告
    generate_html_report(
        results_list=results_list,
        shared_stats=shared_stats,
        output_file=args.html_report or "test_report.html",
        host=args.host,
        port=args.port,
        thread_count=args.threads,
        duration=args.duration,
        model_name=args.model_name
    )
```

**关键点**：
- Ramp-up：通过 `time.sleep()` 控制线程启动间隔
- Duration：使用独立的定时线程控制测试时长
- 线程同步：使用 `join()` 等待所有线程完成
- 支持 `--execution-time` 作为 `--duration` 的别名

### 第七步：实现实时统计汇总

#### 7.1 汇总统计函数

```python
def aggregate_stats(shared_stats: Dict[str, Any], stop_event: threading.Event,
                   verbose: bool = True):
    """每秒汇总所有线程的实时统计信息"""

    printed_header = False
    header_line = "-" * 180

    while not stop_event.wait(1):  # 每秒执行一次
        if not verbose:
            continue

        with shared_stats["lock"]:
            thread_stats = list(shared_stats["thread_stats"].values())
            if not thread_stats:
                continue

            # 计算汇总数据
            active_threads = len(shared_stats["thread_stats"])
            total_threads = shared_stats.get("total_threads", active_threads)
            total_reqs = shared_stats.get("requests", 0)
            total_success = shared_stats.get("success", 0)

            # 计算时间范围
            earliest_start = min(s.get("start_time", 0) for s in thread_stats)
            latest_update = max(s.get("last_update", 0) for s in thread_stats)

            # 从实时统计获取数据
            total_chunks = sum(s.get("chunks", 0) for s in thread_stats)
            total_tokens = sum(s.get("tokens", 0) for s in thread_stats)

            # 获取每个线程的请求数据
            thread_requests = shared_stats.get("thread_requests", {})

        elapsed_ms = max(latest_update - earliest_start, 1)

        # 使用已完成的请求数据，按线程计算后再汇总（加权平均）
        thread_metrics = {}
        total_completed_chunks = 0

        for thread_id, requests in thread_requests.items():
            if requests:
                thread_chunks = sum(r.get("chunk_count", 0) for r in requests)
                total_completed_chunks += thread_chunks
                thread_metrics[thread_id] = {
                    "avg_response_time": sum(r.get("total_response_time", 0) for r in requests) / len(requests),
                    "avg_tpot": sum(r.get("tpot", 0) for r in requests) / len(requests),
                    "total_tokens": sum(r.get("token_count", 0) for r in requests),
                    "request_count": len(requests)
                }

        # 汇总所有线程的指标（加权平均）
        if thread_metrics:
            total_request_count = sum(m.get("request_count", 0) for m in thread_metrics.values())
            total_completed_tokens = sum(m.get("total_tokens", 0) for m in thread_metrics.values())

            if total_request_count > 0:
                avg_response_time = sum(m.get("avg_response_time", 0) * m.get("request_count", 0)
                                       for m in thread_metrics.values()) / total_request_count
                tpot = sum(m.get("avg_tpot", 0) * m.get("request_count", 0)
                          for m in thread_metrics.values()) / total_request_count
                tokens_per_second = (total_completed_tokens * 1000) / elapsed_ms if elapsed_ms > 0 else 0
            else:
                avg_response_time = 0
                tpot = 0
                tokens_per_second = 0
        else:
            # 如果没有已完成的请求，使用实时统计
            if total_chunks > 0:
                avg_response_time = elapsed_ms / total_chunks
            else:
                avg_response_time = 0

            # TPOT 备用计算：只有1个或0个token时返回0
            if total_tokens > 1:
                tpot = elapsed_ms / (total_tokens - 1)
            else:
                tpot = 0

            tokens_per_second = (total_tokens * 1000) / elapsed_ms if elapsed_ms > 0 else 0

        display_chunks = total_completed_chunks if total_completed_chunks > 0 else total_chunks
        success_rate = (total_success / total_reqs * 100) if total_reqs > 0 else 0.0

        now_str = datetime.now().strftime("%H:%M:%S")
        if not printed_header:
            print("\n" + header_line)
            print(f"{'时间':<10} {'线程数(活跃/总)':<18} {'数据块':>12} "
                  f"{'平均响应时间(ms)':>22} {'TPOT(ms/token)':>22} "
                  f"{'Tokens/s':>22} {'成功率(%)':>14}")
            print(header_line)
            printed_header = True

        print(f"{now_str:<10} {f'{active_threads}/{total_threads}':<18} "
              f"{display_chunks:>12} {avg_response_time:>22.2f} "
              f"{tpot:>22.2f} {tokens_per_second:>22.2f} {success_rate:>14.2f}")

        # 记录时间序列数据用于报告
        if "time_series" not in shared_stats:
            shared_stats["time_series"] = []
        shared_stats["time_series"].append({
            "timestamp": latest_update,
            "time_str": now_str,
            "active_threads": active_threads,
            "total_threads": total_threads,
            "total_chunks": display_chunks,
            "total_tokens": total_tokens,
            "avg_response_time": avg_response_time,
            "tpot": tpot,
            "tokens_per_second": tokens_per_second,
            "success_rate": success_rate,
            "total_requests": total_reqs,
            "success_requests": total_success
        })
```

**关键点**：
- `stop_event.wait(1)`：每秒唤醒一次，检查停止标志
- 线程安全：使用锁保护共享数据访问
- 实时计算：每次循环重新计算所有指标
- 加权平均：按线程请求数进行加权，确保准确性
- TPOT 备用公式：只有1个token时返回0（无间隔可计算）
- 记录时间序列数据用于生成 HTML 报告

### 第八步：实现命令行接口

#### 8.1 使用 argparse 解析参数

```python
def main():
    parser = argparse.ArgumentParser(
        description="SSE 流式输出性能测试工具（支持多线程和参数化）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本测试（只输入 token）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"

  # 基本测试（完整 Bearer token）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "Bearer app-xxx"

  # 多线程测试
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5

  # 使用参数化文件
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --param-file queries.txt

  # 持续压测
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --ramp-up 10 --duration 60

  # 使用 --execution-time 别名（等同于 --duration）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --execution-time 120
        """
    )

    # 基础参数
    parser.add_argument("--host", type=str, default="localhost",
                       help="服务器主机地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=80,
                       help="服务器端口 (默认: 80)")
    parser.add_argument("--api-key", type=str, default="",
                       help="API 密钥 (可以是 'app-xxx' 或 'Bearer app-xxx' 格式)")
    parser.add_argument("--query", type=str, default="你是谁",
                       help="查询文本 (默认: 你是谁)")

    # 测试参数
    parser.add_argument("--threads", type=int, default=1,
                       help="并发线程数 (默认: 1)")
    parser.add_argument("--ramp-up", type=int, default=0,
                       help="线程递增时间（秒）")
    parser.add_argument("--duration", "--execution-time", type=int, default=0, dest="duration",
                       help="测试持续时间（秒），>0 表示循环发送，0 表示只执行一次")

    # 参数化
    parser.add_argument("--param-file", type=str, default=None,
                       help="参数化文件路径")
    parser.add_argument("--api-key-file", type=str, default=None,
                       help="API Key 参数化文件路径")

    # 报告
    parser.add_argument("--html-report", type=str, default=None,
                       help="HTML 报告文件路径（默认输出到 report/ 目录）")
    parser.add_argument("--model-name", type=str, default=None,
                       help="模型名称（可选，包含在报告文件名中）")

    # 其他
    parser.add_argument("--quiet", action="store_true",
                       help="静默模式")
    parser.add_argument("--timeout", type=int, default=60,
                       help="请求超时时间（秒）")

    args = parser.parse_args()

    # 执行测试
    # ...
```

**关键点**：
- `argparse`：Python 标准库，功能强大
- `action="store_true"`：布尔标志参数
- `formatter_class=RawDescriptionHelpFormatter`：保留帮助文本格式
- 支持 `--execution-time` 作为 `--duration` 的别名

---

## 关键技术详解

### 1. 流式响应处理

#### SSE (Server-Sent Events) 格式

SSE 是一种服务器推送技术，格式如下：

```
data: {"answer": "你好"}

data: {"answer": "，我是"}

data: {"answer": "AI助手"}

data: [DONE]
```

**处理要点**：
- 每行以 `data: ` 开头
- 空行是分隔符
- `[DONE]` 表示结束

#### 逐行读取

```python
for line in response.iter_lines(decode_unicode=True):
    if line.startswith("data: "):
        data = line[6:]  # 去掉前缀
        json_data = json.loads(data)  # 解析 JSON
```

**关键**：
- `iter_lines()`：逐行迭代，不一次性加载
- `decode_unicode=True`：自动解码 Unicode

### 2. 线程安全设计

#### 使用锁保护共享数据

```python
class QueryProvider:
    def __init__(self):
        self.lock = threading.Lock()  # 创建锁
        self.queries = deque()
        self.current_index = 0

    def get_next_query(self):
        with self.lock:  # 获取锁
            # 临界区代码
            query = self.queries[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.queries)
            return query
        # 自动释放锁
```

**关键点**：
- `with self.lock`：自动获取和释放锁
- 临界区尽可能小，减少锁竞争

#### 共享统计信息

```python
shared_stats = {
    "lock": threading.Lock(),
    "thread_stats": {},      # 每个线程的实时统计
    "thread_requests": {},   # 每个线程的已完成请求（用于加权平均）
    "requests": 0,           # 总请求数
    "success": 0,            # 成功数
    "fail": 0               # 失败数
}

# 更新统计
with shared_stats["lock"]:
    shared_stats["requests"] += 1
    if success:
        shared_stats["success"] += 1
```

### 3. 时间戳管理

#### 使用毫秒级时间戳

```python
# 获取当前时间（毫秒）
current_time = time.time() * 1000

# 计算时间差
elapsed_ms = end_time - start_time
```

**原因**：
- 毫秒级精度足够，且计算简单
- 避免浮点数精度问题

#### 记录关键时间点

```python
stats = {
    "request_start_time": time.time() * 1000,  # 请求开始
    "first_byte_time": 0,                      # 首字节
    "first_token_time": 0,                     # 首Token
    "last_byte_time": 0,                       # 最后字节
    "request_end_time": 0                      # 请求结束
}
```

### 4. Token 计数策略

#### 简单估算方法

```python
def _estimate_tokens(self, text: str) -> int:
    # 中文字符数
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')

    # 英文单词数
    english_words = len([w for w in text.split() if w.isalpha()])

    return max(1, chinese_chars + english_words)
```

#### 精确计数方法（可选）

```python
# 使用 tiktoken（需要安装：pip install tiktoken）
import tiktoken

def _estimate_tokens(self, text: str, model: str = "gpt-3.5-turbo") -> int:
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
```

### 5. 错误处理策略

#### 分层错误处理

```python
try:
    # 发送请求
    response = self.session.post(url, json=request_body, stream=True)

    # 检查 HTTP 状态码（支持 2xx 范围）
    if response.status_code < 200 or response.status_code >= 300:
        error_text = response.text
        stats["error"] = f"HTTP {response.status_code}: {error_text}"
        return stats

    # 处理响应
    for line in response.iter_lines():
        try:
            # 解析 JSON
            json_data = json.loads(data)
        except json.JSONDecodeError as e:
            # JSON 解析错误，记录但继续
            if verbose:
                print(f"JSON解析错误: {e}")
            continue

except requests.exceptions.RequestException as e:
    # 网络错误
    stats["error"] = str(e)
    return stats
except Exception as e:
    # 其他未知错误
    stats["error"] = f"未知错误: {e}"
    return stats
```

### 6. 性能优化技巧

#### 连接复用

```python
# 使用 Session 复用连接
self.session = requests.Session()
# 所有请求使用同一个 session，自动复用 TCP 连接
```

#### 流式读取

```python
# 使用 stream=True，不一次性加载响应
response = requests.post(url, stream=True)
for line in response.iter_lines():
    # 逐行处理，内存占用小
```

---

## 测试与优化

### 单元测试

创建 `test_providers.py`：

```python
import unittest
from providers import QueryProvider, ApiKeyProvider

class TestProviders(unittest.TestCase):
    def test_query_provider(self):
        provider = QueryProvider(default_query="test")
        self.assertEqual(provider.get_next_query(), "test")

    def test_api_key_provider(self):
        provider = ApiKeyProvider(default_key="test-key")
        self.assertEqual(provider.get_next_key(), "test-key")

if __name__ == "__main__":
    unittest.main()
```

### 性能测试

```bash
# 测试单线程性能
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 1 --duration 10

# 测试多线程性能
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --duration 30

# 测试高并发
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 50 --ramp-up 20 --duration 60
```

### 调试技巧

#### 1. 启用详细输出

移除 `--quiet` 参数，或在测试函数中启用 verbose 模式。

#### 2. 使用日志模块

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"收到数据块: {chunk}")
logger.error(f"请求失败: {error}")
```

---

## 扩展功能

### 1. HTML 可视化报告

本工具使用 `report_generator.py` 生成包含以下功能的 HTML 报告：

- **汇总卡片**：显示总请求数、成功率、平均响应时间等
- **趋势图**：使用 Chart.js 绘制 TTFT、TPOT、吞吐量等趋势
- **同步缩放**：所有图表支持拖拽缩放，且自动同步
- **百分位统计**：P90、P95、P99 等百分位数据
- **响应式布局**：支持不同屏幕尺寸

### 2. 结果导出（CSV/JSON）

```python
import csv
import json

def export_results_csv(results_list: List[Dict], filename: str):
    """导出结果为 CSV"""
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'thread_id', 'query', 'chunk_count', 'token_count',
            'ttft', 'tpot', 'throughput', 'success'
        ])
        writer.writeheader()
        for result in results_list:
            writer.writerow(result)

def export_results_json(results_list: List[Dict], filename: str):
    """导出结果为 JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results_list, f, ensure_ascii=False, indent=2)
```

---

## 最佳实践

### 1. 代码组织

```
sse_perf_test_tool/
├── sse_perfTestTool.py    # 主入口文件
├── providers.py           # 参数化提供器
├── tester.py              # SSE 测试器
├── test_runner.py         # 测试运行器
├── report_generator.py    # HTML 报告生成器
├── requirements.txt       # 依赖
├── README.md             # 文档
└── report/               # 报告输出目录
```

### 2. 配置管理

```python
# config.py
import os

class Config:
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 80
    DEFAULT_TIMEOUT = 60
    DEFAULT_THREADS = 1
    DEFAULT_QUERY = "你是谁"

    # 可以从环境变量读取
    API_KEY = os.getenv("API_KEY", "")
```

### 3. 日志管理

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("测试开始")
```

### 4. 异常处理

```python
# 使用装饰器统一处理异常
def handle_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"{func.__name__} 失败: {e}", exc_info=True)
            return None
    return wrapper

@handle_exceptions
def test_streaming(self, query: str):
    # 测试逻辑
    pass
```

---

## 完整示例代码结构

### 最小可用版本（MVP）

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 大模型流式输出性能测试工具 - 最小版本
"""

import json
import time
import requests
import argparse

class SimpleSSETester:
    def __init__(self, host: str, port: int, api_key: str):
        self.url = f"http://{host}:{port}/v1/chat-messages"
        self.api_key = api_key

    def test(self, query: str = "你是谁"):
        """执行单次测试"""
        stats = {
            "start_time": time.time() * 1000,
            "first_token_time": 0,
            "chunk_count": 0,
            "token_count": 0
        }

        # 智能处理 API key
        auth_token = self.api_key if self.api_key.startswith("Bearer ") else f"Bearer {self.api_key}"

        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }

        body = {
            "query": query,
            "response_mode": "streaming"
        }

        try:
            response = requests.post(self.url, json=body, headers=headers, stream=True)

            # 检查 2xx 状态码
            if response.status_code < 200 or response.status_code >= 300:
                print(f"错误: HTTP {response.status_code}")
                return stats

            first_token = True
            for line in response.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    data = line[6:]
                    if data.strip() and data.strip() != "[DONE]":
                        try:
                            json_data = json.loads(data)
                            if "answer" in json_data:
                                if first_token:
                                    stats["first_token_time"] = time.time() * 1000
                                    first_token = False
                                stats["chunk_count"] += 1
                                stats["token_count"] += len(json_data["answer"])
                        except:
                            pass

            stats["end_time"] = time.time() * 1000
            stats["ttft"] = stats["first_token_time"] - stats["start_time"]
            stats["total_time"] = stats["end_time"] - stats["start_time"]

            return stats

        except Exception as e:
            print(f"错误: {e}")
            return stats

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--query", default="你是谁")

    args = parser.parse_args()

    tester = SimpleSSETester(args.host, args.port, args.api_key)
    result = tester.test(args.query)

    print(f"TTFT: {result['ttft']:.2f} ms")
    print(f"总时间: {result['total_time']:.2f} ms")
    print(f"数据块数: {result['chunk_count']}")
    print(f"Token数: {result['token_count']}")

if __name__ == "__main__":
    main()
```

这个最小版本包含：
- 基本的流式请求
- 简单的统计
- 命令行接口
- 智能 API Key 处理
- 正确的 HTTP 状态码检查

可以在此基础上逐步添加功能。

---

## 总结

### 开发流程

1. **需求分析** → 确定要测试的指标和功能
2. **架构设计** → 设计类结构和数据流
3. **逐步实现** → 从简单到复杂，逐步添加功能
4. **测试验证** → 单元测试和集成测试
5. **优化改进** → 性能优化和功能扩展

### 关键要点

1. **流式处理**：使用 `stream=True` 和 `iter_lines()`
2. **线程安全**：使用锁保护共享数据
3. **时间管理**：使用毫秒级时间戳
4. **错误处理**：完善的异常处理机制
5. **可扩展性**：模块化设计，易于扩展
6. **智能处理**：API Key 的 Bearer 前缀自动识别
7. **加权平均**：多线程统计使用按线程加权平均

### 项目文件结构

```
sse_perf_test_tool/
├── sse_perfTestTool.py    # 主入口：参数解析、流程控制
├── providers.py           # QueryProvider, ApiKeyProvider
├── tester.py              # SSETester：HTTP/SSE 处理、指标计算
├── test_runner.py         # run_test_thread(), aggregate_stats()
├── report_generator.py    # HTML 报告生成（Chart.js 可视化）
├── requirements.txt       # 依赖
└── report/               # 报告输出目录（自动创建）
```

### 下一步

- 添加更多性能指标
- 支持更多 API 格式
- 实现结果可视化增强
- 添加分布式测试支持
- 集成到 CI/CD 流程

---

## 参考资源

- [requests 文档](https://requests.readthedocs.io/)
- [Python threading 文档](https://docs.python.org/3/library/threading.html)
- [SSE 规范](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Chart.js 文档](https://www.chartjs.org/docs/)
- [性能测试最佳实践](https://k6.io/docs/test-types/load-testing/)

---

## 版本历史

- **v1.0** (2026-01-07)：与实际代码实现同步，修正所有差异
  - 修正默认查询为 "你是谁"
  - 修正默认端口为 80
  - 修正类名为 SSETester
  - 添加智能 API Key 处理说明
  - 修正 HTTP 状态码检查逻辑
  - 修正 TPOT 备用公式
  - 添加项目完整文件结构说明
  - 添加 --execution-time 参数说明
  - 添加 HTML 报告生成功能说明
  - 添加加权平均计算说明

---

**祝你开发顺利！**
