# 从零编写 AI 大模型压测工具教程

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

### 核心功能

1. **流式响应处理**：处理 SSE（Server-Sent Events）格式的流式响应
2. **性能指标计算**：计算 TTFT、TPOT、吞吐量等关键指标
3. **并发测试**：支持多线程并发压测
4. **参数化支持**：支持从文件读取查询和 API Key
5. **实时统计**：每秒汇总所有线程的统计数据
6. **结果报告**：生成详细的测试报告

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
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              核心测试引擎                        │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ QueryProvider│  │ApiKeyProvider│            │
│  │ (查询提供器) │  │ (Key提供器)  │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────────────────────────────┐     │
│  │      SSETester (测试器)               │     │
│  │  - 发送请求                           │     │
│  │  - 处理流式响应                       │     │
│  │  - 计算性能指标                       │     │
│  └──────────────────────────────────────┘     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              并发控制层                          │
│  - 线程管理                                     │
│  - Ramp-up 控制                                 │
│  - Duration 控制                                │
│  - 共享统计信息                                 │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│              统计汇总层                          │
│  - 实时汇总线程                                  │
│  - 最终报告生成                                  │
└─────────────────────────────────────────────────┘
```

### 核心类设计

1. **QueryProvider**：线程安全的查询提供器
2. **ApiKeyProvider**：线程安全的 API Key 提供器
3. **SSETester**：核心测试器类
4. **run_test_thread**：线程执行函数
5. **aggregate_stats**：统计汇总函数

---

## 逐步实现

### 第一步：项目初始化

创建项目结构：

```bash
mkdir ai_loadtest_tool
cd ai_loadtest_tool
touch test_ai_streaming.py
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
class AITester:
    """AI 流式输出测试器基类"""
    
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

### 第三步：实现流式响应处理

#### 3.1 发送流式请求

```python
def test_streaming(self, query: str, verbose: bool = True) -> Dict:
    """测试流式输出"""
    
    # 构建请求 URL
    url = f"{self.base_url}/v1/chat-messages"
    
    # 构建请求体
    request_body = {
        "query": query,
        "response_mode": "streaming",
        # ... 其他参数
    }
    
    # 设置请求头
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    
    # 初始化统计变量
    stats = {
        "request_start_time": 0,
        "first_byte_time": 0,
        "first_token_time": 0,
        "chunk_count": 0,
        "token_count": 0,
        "full_answer": "",
        "error": None
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
        
        # 检查响应状态
        if response.status_code != 200:
            stats["error"] = f"HTTP {response.status_code}"
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
                
                # 更新统计
                stats["full_answer"] += answer_chunk
                stats["chunk_count"] += 1
                
        except json.JSONDecodeError:
            # 处理解析错误
            pass
```

**关键点**：
- `iter_lines(decode_unicode=True)`：逐行读取，自动解码 Unicode
- SSE 格式：`data: {...}` 前缀
- 实时处理：每收到一个数据块立即处理

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
    stats["ttfb"] = stats["first_byte_time"] - stats["request_start_time"]
    
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
    else:
        stats["tpot"] = 0
    
    # 4. 吞吐量 (Tokens/s)
    if stats["streaming_duration"] > 0 and stats["token_count"] > 0:
        stats["throughput"] = (stats["token_count"] / stats["streaming_duration"]) * 1000
    else:
        stats["throughput"] = 0
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
   - 反映模型的生成速度

4. **吞吐量 (Throughput)**
   - 每秒输出的 token 数量
   - 反映整体性能

### 第五步：实现线程安全的参数化提供器

#### 5.1 QueryProvider 实现

```python
class QueryProvider:
    """参数化查询提供器（线程安全）"""
    
    def __init__(self, param_file: Optional[str] = None, default_query: str = "你好"):
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
            except Exception as e:
                print(f"警告: 读取参数化文件失败: {e}")
                self.queries.append(default_query)
        else:
            self.queries.append(default_query)
    
    def get_next_query(self) -> str:
        """获取下一个查询（线程安全，循环轮询）"""
        with self.lock:  # 使用锁保证线程安全
            if not self.queries:
                return "你好"
            
            query = self.queries[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.queries)  # 循环
            return query
```

**关键点**：
- `threading.Lock()`：保证多线程安全
- `deque`：高效的双端队列
- 循环轮询：使用取模运算实现循环

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
                print(f"警告: 读取 API Key 文件失败: {e}")
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
def run_test_thread(tester: AITester, query_provider: QueryProvider,
                    thread_id: int, results_list: List[Dict], 
                    results_lock: threading.Lock,
                    shared_stats: Optional[Dict[str, Any]] = None,
                    stop_event: Optional[threading.Event] = None,
                    end_time_ms: Optional[float] = None):
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
        # 获取查询
        query = query_provider.get_next_query()
        
        # 执行测试
        result = tester.test_streaming(
            query=query,
            verbose=False,  # 多线程时关闭详细输出
            thread_id=thread_id,
            shared_stats=shared_stats
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

#### 6.2 主函数中的线程管理

```python
def main():
    parser = argparse.ArgumentParser(description="AI 流式输出性能测试工具")
    parser.add_argument("--threads", type=int, default=1, help="并发线程数")
    parser.add_argument("--ramp-up", type=int, default=0, help="线程递增时间（秒）")
    parser.add_argument("--duration", type=int, default=0, help="测试持续时间（秒）")
    # ... 其他参数
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = AITester(host=args.host, port=args.port, api_key=args.api_key)
    
    # 创建查询提供器
    query_provider = QueryProvider(param_file=args.param_file)
    
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
    
    # 创建并启动测试线程
    threads = []
    for i in range(args.threads):
        # Ramp-up 控制：逐步启动线程
        if args.ramp_up > 0 and i > 0:
            ramp_step = args.ramp_up / args.threads
            time.sleep(ramp_step)
        
        thread = threading.Thread(
            target=run_test_thread,
            args=(tester, query_provider, i + 1, results_list, 
                  results_lock, shared_stats, stop_event, end_time_ms)
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
    
    # 输出最终统计
    print_final_stats(results_list, args.threads, args.duration)
```

**关键点**：
- Ramp-up：通过 `time.sleep()` 控制线程启动间隔
- Duration：使用独立的定时线程控制测试时长
- 线程同步：使用 `join()` 等待所有线程完成

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
            
            # 计算总数据
            total_chunks = sum(s.get("chunks", 0) for s in thread_stats)
            total_tokens = sum(s.get("tokens", 0) for s in thread_stats)
        
        # 计算指标
        elapsed_ms = max(latest_update - earliest_start, 1)
        avg_response_time = elapsed_ms / max(total_chunks, 1)
        tpot = elapsed_ms / max(total_tokens - 1, 1)
        tokens_per_second = (total_tokens * 1000) / elapsed_ms
        success_rate = (total_success / total_reqs * 100) if total_reqs > 0 else 0.0
        
        # 输出表格
        now_str = datetime.now().strftime("%H:%M:%S")
        if not printed_header:
            print("\n" + header_line)
            print(f"{'时间':<10} {'线程数(活跃/总)':<18} {'数据块':>12} "
                  f"{'平均响应时间(ms)':>22} {'TPOT(ms/token)':>22} "
                  f"{'Tokens/s':>22} {'成功率(%)':>14}")
            print(header_line)
            printed_header = True
        
        print(f"{now_str:<10} {f'{active_threads}/{total_threads}':<18} "
              f"{total_chunks:>12} {avg_response_time:>22.2f} "
              f"{tpot:>22.2f} {tokens_per_second:>22.2f} {success_rate:>14.2f}")
```

**关键点**：
- `stop_event.wait(1)`：每秒唤醒一次，检查停止标志
- 线程安全：使用锁保护共享数据访问
- 实时计算：每次循环重新计算所有指标

#### 7.2 在主函数中启动汇总线程

```python
# 启动汇总线程
if enable_agg:
    agg_thread = threading.Thread(
        target=aggregate_stats, 
        args=(shared_stats, stop_event, not args.quiet), 
        daemon=True  # 守护线程，主程序退出时自动结束
    )
    agg_thread.start()
```

### 第八步：实现命令行接口

#### 8.1 使用 argparse 解析参数

```python
def main():
    parser = argparse.ArgumentParser(
        description="AI 流式输出性能测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本测试
  python3 test_ai_streaming.py --host localhost --port 8080
  
  # 多线程测试
  python3 test_ai_streaming.py --host localhost --port 8080 --threads 5
  
  # 持续压测
  python3 test_ai_streaming.py --host localhost --port 8080 --threads 10 --ramp-up 10 --duration 60
        """
    )
    
    # 基础参数
    parser.add_argument("--host", type=str, default="localhost",
                       help="服务器主机地址")
    parser.add_argument("--port", type=int, default=8080,
                       help="服务器端口")
    parser.add_argument("--api-key", type=str, default="",
                       help="API 密钥")
    
    # 测试参数
    parser.add_argument("--threads", type=int, default=1,
                       help="并发线程数")
    parser.add_argument("--ramp-up", type=int, default=0,
                       help="线程递增时间（秒）")
    parser.add_argument("--duration", type=int, default=0,
                       help="测试持续时间（秒）")
    
    # 参数化
    parser.add_argument("--param-file", type=str, default=None,
                       help="参数化文件路径")
    parser.add_argument("--api-key-file", type=str, default=None,
                       help="API Key 参数化文件路径")
    
    # 其他
    parser.add_argument("--quiet", action="store_true",
                       help="静默模式")
    
    args = parser.parse_args()
    
    # 执行测试
    # ...
```

**关键点**：
- `argparse`：Python 标准库，功能强大
- `action="store_true"`：布尔标志参数
- `formatter_class=RawDescriptionHelpFormatter`：保留帮助文本格式

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
    "thread_stats": {},  # 每个线程的统计
    "requests": 0,        # 总请求数
    "success": 0,         # 成功数
    "fail": 0            # 失败数
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
    "last_byte_time": 0,                      # 最后字节
    "request_end_time": 0                     # 请求结束
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
    
    # 检查 HTTP 状态码
    if response.status_code != 200:
        stats["error"] = f"HTTP {response.status_code}"
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

#### 异步处理（高级）

```python
# 使用 asyncio 和 aiohttp（需要额外实现）
import asyncio
import aiohttp

async def test_streaming_async(session, url, data):
    async with session.post(url, json=data) as response:
        async for line in response.content:
            # 处理流式数据
            pass
```

---

## 测试与优化

### 单元测试

创建 `test_ai_tester.py`：

```python
import unittest
from test_ai_streaming import AITester, QueryProvider

class TestAITester(unittest.TestCase):
    def test_query_provider(self):
        provider = QueryProvider(default_query="test")
        self.assertEqual(provider.get_next_query(), "test")
    
    def test_token_estimation(self):
        tester = AITester()
        tokens = tester._estimate_tokens("你好 world")
        self.assertGreater(tokens, 0)

if __name__ == "__main__":
    unittest.main()
```

### 性能测试

```bash
# 测试单线程性能
python3 test_ai_streaming.py --threads 1 --duration 10

# 测试多线程性能
python3 test_ai_streaming.py --threads 10 --duration 30

# 测试高并发
python3 test_ai_streaming.py --threads 50 --ramp-up 20 --duration 60
```

### 调试技巧

#### 1. 启用详细输出

```python
# 在测试函数中添加调试输出
if verbose:
    print(f"[调试] 收到数据: {data[:100]}")
    print(f"[调试] 解析结果: {json_data}")
```

#### 2. 记录原始响应

```python
raw_lines = []
for line in response.iter_lines():
    if len(raw_lines) < 5:  # 只记录前5行
        raw_lines.append(line)
    
# 如果没有收到数据，输出原始响应
if chunk_count == 0:
    print("原始响应:")
    for line in raw_lines:
        print(f"  {line}")
```

#### 3. 使用日志模块

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug(f"收到数据块: {chunk}")
logger.error(f"请求失败: {error}")
```

---

## 扩展功能

### 1. 结果导出（CSV/JSON）

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

### 2. 实时图表（使用 matplotlib）

```python
import matplotlib.pyplot as plt
from collections import deque

class RealTimePlotter:
    def __init__(self):
        self.times = deque(maxlen=100)
        self.throughputs = deque(maxlen=100)
        plt.ion()  # 交互模式
    
    def update(self, throughput: float):
        self.times.append(time.time())
        self.throughputs.append(throughput)
        
        plt.clf()
        plt.plot(list(self.times), list(self.throughputs))
        plt.ylabel('Tokens/s')
        plt.xlabel('Time')
        plt.draw()
        plt.pause(0.01)
```

### 3. 分布式测试（使用多进程）

```python
from multiprocessing import Process, Queue

def run_test_process(queue: Queue, config: Dict):
    """在独立进程中运行测试"""
    tester = AITester(**config)
    results = tester.test_streaming(config['query'])
    queue.put(results)

# 主进程
processes = []
for i in range(num_processes):
    p = Process(target=run_test_process, args=(queue, config))
    p.start()
    processes.append(p)
```

### 4. 结果分析报告

```python
def generate_report(results_list: List[Dict]) -> str:
    """生成 HTML 报告"""
    html = """
    <html>
    <head><title>性能测试报告</title></head>
    <body>
        <h1>性能测试报告</h1>
        <table>
            <tr>
                <th>指标</th><th>平均值</th><th>最小值</th><th>最大值</th>
            </tr>
    """
    
    # 计算统计数据
    ttfts = [r['ttft'] for r in results_list if r.get('ttft')]
    avg_ttft = sum(ttfts) / len(ttfts) if ttfts else 0
    
    html += f"""
            <tr>
                <td>TTFT</td>
                <td>{avg_ttft:.2f} ms</td>
                <td>{min(ttfts):.2f} ms</td>
                <td>{max(ttfts):.2f} ms</td>
            </tr>
    """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    return html
```

---

## 最佳实践

### 1. 代码组织

```
ai_loadtest_tool/
├── test_ai_streaming.py    # 主测试脚本
├── providers.py            # 参数化提供器
├── metrics.py              # 指标计算
├── utils.py                # 工具函数
├── requirements.txt        # 依赖
├── README.md              # 文档
└── tests/                 # 测试文件
    └── test_providers.py
```

### 2. 配置管理

```python
# config.py
class Config:
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = 8080
    DEFAULT_TIMEOUT = 60
    DEFAULT_THREADS = 1
    
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

### 5. 性能监控

```python
import psutil
import time

def monitor_resources(duration: int):
    """监控系统资源使用"""
    start_time = time.time()
    cpu_samples = []
    memory_samples = []
    
    while time.time() - start_time < duration:
        cpu_samples.append(psutil.cpu_percent())
        memory_samples.append(psutil.virtual_memory().percent)
        time.sleep(1)
    
    print(f"平均 CPU 使用率: {sum(cpu_samples)/len(cpu_samples):.2f}%")
    print(f"平均内存使用率: {sum(memory_samples)/len(memory_samples):.2f}%")
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

class SimpleAITester:
    def __init__(self, host: str, port: int, api_key: str):
        self.url = f"http://{host}:{port}/v1/chat-messages"
        self.api_key = api_key
    
    def test(self, query: str):
        """执行单次测试"""
        stats = {
            "start_time": time.time() * 1000,
            "first_token_time": 0,
            "chunk_count": 0,
            "token_count": 0
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        body = {
            "query": query,
            "response_mode": "streaming"
        }
        
        try:
            response = requests.post(self.url, json=body, headers=headers, stream=True)
            
            if response.status_code != 200:
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
    parser.add_argument("--query", default="你好")
    
    args = parser.parse_args()
    
    tester = SimpleAITester(args.host, args.port, args.api_key)
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

### 下一步

- 添加更多性能指标
- 支持更多 API 格式
- 实现结果可视化
- 添加分布式测试支持
- 集成到 CI/CD 流程

---

## 参考资源

- [requests 文档](https://requests.readthedocs.io/)
- [Python threading 文档](https://docs.python.org/3/library/threading.html)
- [SSE 规范](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [性能测试最佳实践](https://k6.io/docs/test-types/load-testing/)

---

**祝你开发顺利！** 🚀
