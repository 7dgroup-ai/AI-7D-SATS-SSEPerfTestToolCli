#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSE 测试器模块
包含 SSETester 类，用于执行 SSE 流式输出测试

Author: 7DGroup
"""

import json
import time
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class SSETester:
    """SSE 流式输出测试器"""
    
    def __init__(self, host: str = "localhost", port: int = 80, 
                 api_key: str = "", timeout: int = 60):
        """
        初始化测试器
        
        Args:
            host: 服务器主机地址
            port: 服务器端口
            api_key: API 密钥（Bearer token）
            timeout: 请求超时时间（秒）
        """
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
    
    def test_streaming(self, query: str = "你是谁", inputs: Optional[Dict] = None,
                      conversation_id: str = "", user: str = "gaolou",
                      files: Optional[List[Dict]] = None, 
                      verbose: bool = True, thread_id: Optional[int] = None,
                      shared_stats: Optional[Dict[str, Any]] = None,
                      api_key_override: Optional[str] = None) -> Dict:
        """
        测试 SSE 流式输出
        
        Args:
            query: 查询文本
            inputs: 输入参数字典
            conversation_id: 对话ID
            user: 用户标识
            files: 文件列表
            verbose: 是否输出详细信息
            thread_id: 线程ID
            shared_stats: 共享统计信息字典
            api_key_override: 覆盖的 API key
            
        Returns:
            包含测试结果的字典
        """
        # 构建请求 URL
        url = f"{self.base_url}/v1/chat-messages"
        
        # 构建请求体
        if inputs is None:
            inputs = {"query": query}
        
        if files is None:
            files = [
                {
                    "type": "image",
                    "transfer_method": "remote_url",
                    "url": "https://example.com/logo.png"
                }
            ]
        
        request_body = {
            "inputs": inputs,
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user,
            "files": files
        }
        
        # 选择 API key
        use_api_key = api_key_override if api_key_override else self.api_key
        # 设置请求头
        # 智能处理 API key：如果已经包含 "Bearer " 前缀，就不再添加
        auth_token = use_api_key if use_api_key.startswith("Bearer ") else f"Bearer {use_api_key}"
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        # 初始化统计变量
        stats = {
            "thread_id": thread_id,
            "request_start_time": 0,
            "connect_start_time": 0,
            "connect_end_time": 0,
            "first_byte_time": 0,
            "first_token_time": 0,  # TTFT
            "last_byte_time": 0,
            "request_end_time": 0,
            "chunk_count": 0,
            "token_count": 0,
            "full_answer": "",
            "conversation_id": "",
            "message_id": "",
            "response_code": 0,
            "error": None,
            "token_times": []  # 记录每个 token 的时间戳
        }
        
        try:
            # 记录请求开始时间
            stats["request_start_time"] = time.time() * 1000  # 转换为毫秒
            stats["connect_start_time"] = stats["request_start_time"]
            
            # 线程ID前缀
            thread_prefix = f"[线程{thread_id}] " if thread_id else ""
            
            if verbose:
                print("=" * 60)
                print(f"{thread_prefix}开始发送流式请求...")
                print(f"{thread_prefix}URL: {url}")
                print(f"{thread_prefix}Query: {query}")
                print("=" * 60)
            
            # 发送 POST 请求，启用流式响应
            response = self.session.post(
                url,
                json=request_body,
                headers=headers,
                stream=True,
                timeout=self.timeout
            )
            
            # 记录连接完成时间
            stats["connect_end_time"] = time.time() * 1000
            stats["response_code"] = response.status_code
            
            if verbose:
                print(f"{thread_prefix}响应代码: {response.status_code}")
                print(f"{thread_prefix}用户标识: {user}")
                print(f"{thread_prefix}开始接收流式响应...")
                print("-" * 60)
            
            # 检查响应状态
            if response.status_code < 200 or response.status_code >= 300:
                error_text = response.text
                stats["error"] = f"HTTP {response.status_code}: {error_text}"
                if verbose:
                    print(f"错误: {stats['error']}")
                return stats
            
            # 读取流式响应
            first_byte_received = False
            first_token_received = False
            table_header_printed = False  # 标记表头是否已打印
            
            for line in response.iter_lines(decode_unicode=True):
                if line is None:
                    continue
                
                # 记录首字节时间（第一次读取到数据）
                if not first_byte_received:
                    stats["first_byte_time"] = time.time() * 1000
                    first_byte_received = True
                    if verbose:
                        ttfb = stats["first_byte_time"] - stats["request_start_time"]
                        print(f"[时间统计] 首字节时间(TTFB): {ttfb:.2f} ms")
                
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
                        
                        # 提取对话ID和消息ID
                        if "conversation_id" in json_data:
                            stats["conversation_id"] = json_data["conversation_id"]
                        
                        if "message_id" in json_data:
                            stats["message_id"] = json_data["message_id"]
                        
                        # 处理流式文本数据
                        if "answer" in json_data:
                            answer_chunk = json_data["answer"]
                            
                            # 记录第一个 token 的时间（TTFT）
                            if not first_token_received:
                                stats["first_token_time"] = time.time() * 1000
                                first_token_received = True
                                ttft = stats["first_token_time"] - stats["request_start_time"]
                                if verbose:
                                    print(f"\n{thread_prefix}[关键指标] 首Token时间(TTFT): {ttft:.2f} ms")
                                    # 打印表头（使用固定宽度确保对齐）
                                    print("\n" + "-" * 100)
                                    # 使用固定宽度格式化，确保列对齐（统一使用右对齐）
                                    # 数据块: 12字符, 平均响应时间: 22字符, TPOT: 22字符, Tokens/s: 22字符
                                    header = f"{'数据块':>12}  {'平均响应时间(ms)':>22}  {'TPOT(ms/token)':>22}  {'Tokens/s':>22}"
                                    if thread_id:
                                        header = f"{thread_prefix}{header}"
                                    print(header)
                                    print("-" * 100)
                                    table_header_printed = True
                            
                            # 计算 token 数量（简单估算：中文字符算1个token，英文单词算1个token）
                            chunk_tokens = self._estimate_tokens(answer_chunk)
                            stats["token_count"] += chunk_tokens
                            
                            # 记录每个 token 的时间戳（用于计算 TPOT）
                            current_time = time.time() * 1000
                            for _ in range(chunk_tokens):
                                stats["token_times"].append(current_time)
                            
                            stats["full_answer"] += answer_chunk
                            stats["chunk_count"] += 1
                            
                            # 计算并输出实时统计信息（表格形式）
                            if verbose and first_token_received:
                                # 计算从第一个token到现在的总时间（毫秒）
                                elapsed_time_ms = current_time - stats["first_token_time"]
                                elapsed_time_s = elapsed_time_ms / 1000.0
                                
                                # 平均响应时间 = 总时间 / 数据块数
                                avg_response_time = elapsed_time_ms / stats["chunk_count"] if stats["chunk_count"] > 0 else 0
                                
                                # 计算 TPOT (Time Per Output Token)
                                # TPOT = (当前时间 - 第一个token时间) / (当前token数量 - 1)
                                if stats["token_count"] > 1:
                                    tpot = elapsed_time_ms / (stats["token_count"] - 1)
                                else:
                                    tpot = 0.0
                                
                                # Tokens/s = 总token数 / 总时间（秒）
                                tokens_per_second = stats["token_count"] / elapsed_time_s if elapsed_time_s > 0 else 0
                                
                                # 以表格行形式输出实时统计信息（使用与表头相同的固定宽度格式）
                                row = f"{stats['chunk_count']:>12}  {avg_response_time:>22.2f}  {tpot:>22.2f}  {tokens_per_second:>22.2f}"
                                if thread_id:
                                    row = f"{thread_prefix}{row}"
                                print(row)
                            
                            # 将实时统计写入共享汇总（用于全局汇总线程）
                            # 注意：thread_id 可能是 0，所以使用 thread_id is not None 而不是直接判断 thread_id
                            if shared_stats is not None and thread_id is not None:
                                with shared_stats["lock"]:
                                    prev = shared_stats["thread_stats"].get(thread_id, {})
                                    shared_stats["thread_stats"][thread_id] = {
                                        "start_time": prev.get("start_time", shared_stats.get("start_time", stats["request_start_time"])),
                                        "chunks": prev.get("chunks", 0) + 1,
                                        "tokens": prev.get("tokens", 0) + chunk_tokens,
                                        "last_update": current_time
                                    }
                            
                            # 不再输出数据块的具体内容，只保留统计信息表格
                    
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，记录原始数据
                        if data.strip() and verbose:
                            print(f"[原始数据] {data}")
            
            # 记录请求结束时间
            stats["request_end_time"] = time.time() * 1000
            
            if verbose:
                # 如果表头已打印，打印表格底部边框
                if table_header_printed:
                    print("-" * 100)
                print("\n" + "=" * 60)
            
            # 计算时间统计
            self._calculate_metrics(stats)
            
            # 输出最终结果
            if verbose:
                self._print_results(stats)
            
            return stats
        
        except requests.exceptions.RequestException as e:
            stats["error"] = str(e)
            stats["request_end_time"] = time.time() * 1000
            thread_prefix = f"[线程{thread_id}] " if thread_id else ""
            if verbose:
                print(f"\n{thread_prefix}错误: {stats['error']}")
            return stats
    
    def _estimate_tokens(self, text: str) -> int:
        """
        估算文本的 token 数量
        简单估算：中文字符算1个token，英文单词算1个token
        
        Args:
            text: 文本内容
            
        Returns:
            估算的 token 数量
        """
        # 简单估算：中文字符数 + 英文单词数
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len([w for w in text.split() if w.isalpha()])
        # 如果文本很短，至少算1个token
        return max(1, chinese_chars + english_words)
    
    def _calculate_metrics(self, stats: Dict):
        """
        计算关键指标
        
        Args:
            stats: 统计信息字典
        """
        # 计算基本时间指标
        stats["connect_time"] = stats["connect_end_time"] - stats["connect_start_time"]
        stats["ttfb"] = stats["first_byte_time"] - stats["request_start_time"] if stats["first_byte_time"] > 0 else 0
        stats["total_response_time"] = stats["request_end_time"] - stats["request_start_time"]
        
        # 计算 TTFT (Time To First Token)
        if stats["first_token_time"] > 0:
            stats["ttft"] = stats["first_token_time"] - stats["request_start_time"]
        else:
            stats["ttft"] = 0
        
        # 计算 TPOT (Time Per Output Token)
        # TPOT = (最后一个token时间 - 第一个token时间) / (token数量 - 1)
        if stats["token_count"] > 1 and len(stats["token_times"]) > 1:
            first_token_time = stats["token_times"][0]
            last_token_time = stats["token_times"][-1]
            total_token_time = last_token_time - first_token_time
            stats["tpot"] = total_token_time / (stats["token_count"] - 1) if stats["token_count"] > 1 else 0
        elif stats["token_count"] == 1:
            # 只有一个token，TPOT 为 0
            stats["tpot"] = 0
        else:
            stats["tpot"] = 0
        
        # 计算流式传输时长
        if stats["first_byte_time"] > 0:
            stats["streaming_duration"] = stats["last_byte_time"] - stats["first_byte_time"]
        else:
            stats["streaming_duration"] = 0
        
        # 计算吞吐量（tokens/秒）
        if stats["streaming_duration"] > 0 and stats["token_count"] > 0:
            stats["throughput"] = (stats["token_count"] / stats["streaming_duration"]) * 1000  # tokens/秒
        else:
            stats["throughput"] = 0
    
    def _print_results(self, stats: Dict):
        """
        打印测试结果
        
        Args:
            stats: 统计信息字典
        """
        thread_id = stats.get("thread_id")
        thread_prefix = f"[线程{thread_id}] " if thread_id else ""
        
        print("=" * 60)
        title = "           流式响应接收完成 - 统计信息"
        if thread_id:
            title = f"{thread_prefix}{title}"
        print(title)
        print("=" * 60)
        print(f"对话ID: {stats['conversation_id']}")
        print(f"消息ID: {stats['message_id']}")
        if stats.get('thread_id'):
            print(f"线程ID: {stats['thread_id']}")
        if stats.get('query'):
            print(f"查询文本: {stats['query']}")
        print(f"总数据块数: {stats['chunk_count']}")
        print(f"Token数量: {stats['token_count']}")
        print(f"完整回答长度: {len(stats['full_answer'])} 字符")
        print("-" * 60)
        print("[时间统计]")
        print(f"  连接时间: {stats['connect_time']:.2f} ms")
        print(f"  首字节时间(TTFB): {stats['ttfb']:.2f} ms")
        print(f"  流式传输时长: {stats['streaming_duration']:.2f} ms")
        print(f"  总响应时间: {stats['total_response_time']:.2f} ms")
        print("-" * 60)
        print("[关键指标]")
        print(f"  首Token时间(TTFT): {stats['ttft']:.2f} ms")
        print(f"  每Token时间(TPOT): {stats['tpot']:.2f} ms/token")
        print(f"  吞吐量: {stats['throughput']:.2f} tokens/秒")
        print("=" * 60)
        print()
        
        # 如果有错误，打印错误信息
        if stats["error"]:
            print(f"[错误] {stats['error']}")
            print()

