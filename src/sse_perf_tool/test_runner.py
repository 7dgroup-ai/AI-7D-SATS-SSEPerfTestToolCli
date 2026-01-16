#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试运行模块
包含测试线程函数和统计汇总函数

Author: 7DGroup
"""

import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any

from .tester import SSETester
from .providers import QueryProvider, ApiKeyProvider


def run_test_thread(tester: SSETester, query_provider: QueryProvider,
                    thread_id: int, conversation_id: str, user: str,
                    verbose: bool, results_list: List[Dict], results_lock: threading.Lock,
                    shared_stats: Optional[Dict[str, Any]] = None,
                    stop_event: Optional[threading.Event] = None,
                    end_time_ms: Optional[float] = None,
                    api_key_provider: Optional[ApiKeyProvider] = None):
    """
    运行测试的线程函数
    
    Args:
        tester: 测试器实例
        query_provider: 查询提供器
        thread_id: 线程ID
        conversation_id: 对话ID
        user: 用户标识
        verbose: 是否输出详细信息
        results_list: 结果列表（线程安全）
        results_lock: 结果锁
        shared_stats: 共享统计信息
        stop_event: 停止事件
        end_time_ms: 结束时间（毫秒）
        api_key_provider: API Key 提供器
    """
    # 如果需要汇总，预先记录线程开始时间
    if shared_stats is not None:
        with shared_stats["lock"]:
            shared_stats["thread_stats"][thread_id] = {
                "start_time": time.time() * 1000,
                "chunks": 0,
                "tokens": 0,
                "last_update": time.time() * 1000
            }

    def time_remaining_ok() -> bool:
        if stop_event and stop_event.is_set():
            return False
        if end_time_ms is not None:
            return time.time() * 1000 < end_time_ms
        return True

    while time_remaining_ok():
        api_key = api_key_provider.get_next_key() if api_key_provider else tester.api_key
        if not api_key:
            break
        result = tester.test_streaming(
            query=query_provider.get_next_query(),
            conversation_id=conversation_id,
            user=user,
            verbose=verbose,
            thread_id=thread_id,
            shared_stats=shared_stats,
            api_key_override=api_key
        )
        # 添加线程ID和查询信息
        result["thread_id"] = thread_id
        # 线程安全地添加结果
        with results_lock:
            results_list.append(result)
        # 统计成功/失败，并记录每个线程的请求指标（用于按线程计算）
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
                        "chunk_count": result.get("chunk_count", 0)  # 添加数据块数
                    })
                else:
                    shared_stats["fail"] += 1
        # 如果只跑一次（无持续时间且无外部停止），跑完退出
        if end_time_ms is None and stop_event is None:
            break

    # 线程结束时更新最后一次时间
    if shared_stats is not None:
        with shared_stats["lock"]:
            ts = shared_stats["thread_stats"].get(thread_id)
            if ts:
                ts["last_update"] = time.time() * 1000


def aggregate_stats(shared_stats: Dict[str, Any], stop_event: threading.Event, verbose: bool = True):
    """
    每秒汇总所有线程的实时统计信息
    
    Args:
        shared_stats: 共享统计信息字典
        stop_event: 停止事件
        verbose: 是否输出详细信息
    """
    printed_header = False
    header_line = "-" * 180
    while not stop_event.wait(1):
        if not verbose:
            continue
        with shared_stats["lock"]:
            thread_stats = list(shared_stats["thread_stats"].values())
            if not thread_stats:
                continue
            active_threads = len(shared_stats["thread_stats"])
            total_threads = shared_stats.get("total_threads", active_threads)
            total_reqs = shared_stats.get("requests", 0)
            total_success = shared_stats.get("success", 0)
            earliest_start = min(s.get("start_time", shared_stats.get("start_time", time.time() * 1000)) for s in thread_stats)
            latest_update = max(s.get("last_update", earliest_start) for s in thread_stats)
            # 计算所有线程的累计数据块数和token数（从thread_stats获取实时统计）
            total_chunks = sum(s.get("chunks", 0) for s in thread_stats)
            total_tokens = sum(s.get("tokens", 0) for s in thread_stats)
            # 获取每个线程的请求数据（用于按线程计算指标）
            thread_requests = shared_stats.get("thread_requests", {})
        
        elapsed_ms = max(latest_update - earliest_start, 1)
        
        # 实时汇总计算：使用已完成的请求数据，按线程计算后再汇总
        # 1. 从 thread_requests 获取每个线程已完成的请求数据
        thread_metrics = {}
        total_completed_chunks = 0  # 从已完成的请求中获取数据块数
        for thread_id, requests in thread_requests.items():
            if requests:  # 只使用已完成的请求
                # 从已完成的请求中获取chunk_count（每个请求的数据块数）
                thread_chunks = sum(r.get("chunk_count", 0) for r in requests)
                total_completed_chunks += thread_chunks
                thread_metrics[thread_id] = {
                    "avg_response_time": sum(r.get("total_response_time", 0) for r in requests) / len(requests),
                    "avg_tpot": sum(r.get("tpot", 0) for r in requests) / len(requests),
                    "total_tokens": sum(r.get("token_count", 0) for r in requests),
                    "total_chunks": thread_chunks,
                    "request_count": len(requests)
                }
        
        # 2. 汇总所有线程的指标（加权平均）
        if thread_metrics:
            total_request_count = sum(m.get("request_count", 0) for m in thread_metrics.values())
            total_completed_tokens = sum(m.get("total_tokens", 0) for m in thread_metrics.values())
            
            if total_request_count > 0:
                # 使用已完成的请求计算平均值
                avg_response_time = sum(m.get("avg_response_time", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
                tpot = sum(m.get("avg_tpot", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
                # 计算吞吐量：已完成的tokens / 已用时间
                tokens_per_second = (total_completed_tokens * 1000) / elapsed_ms if elapsed_ms > 0 else 0
            else:
                avg_response_time = 0
                tpot = 0
                tokens_per_second = 0
        else:
            # 如果没有已完成的请求，使用实时统计（从thread_stats获取）
            # 注意：这些是实时统计，反映当前正在进行的请求的累计数据
            # 如果 total_chunks 或 total_tokens 为0，说明可能还没有收到数据块
            if total_chunks > 0:
                avg_response_time = elapsed_ms / total_chunks
            else:
                avg_response_time = 0
            if total_tokens > 1:
                tpot = elapsed_ms / (total_tokens - 1)
            else:
                tpot = 0
            tokens_per_second = (total_tokens * 1000) / elapsed_ms if elapsed_ms > 0 else 0
        
        # 数据块数：优先使用已完成的请求的数据块数，如果没有则使用实时统计（从thread_stats获取）
        # total_chunks 是从 thread_stats 中实时获取的，反映所有线程累计接收的数据块数（包括正在进行的请求）
        # 注意：total_chunks 是累积的，不会在请求完成后重置
        # 如果 total_completed_chunks 为0，说明可能还没有已完成的请求，使用实时统计的 total_chunks
        display_chunks = total_completed_chunks if total_completed_chunks > 0 else total_chunks
        
        # 如果 total_chunks 也是0，可能是：
        # 1. 请求还没开始接收数据块
        # 2. thread_stats 没有被正确更新（检查 thread_id 是否正确传递）
        
        success_rate = (total_success / total_reqs * 100) if total_reqs > 0 else 0.0
        now_str = datetime.now().strftime("%H:%M:%S")
        if not printed_header:
            print("\n" + header_line)
            print(f"{'时间':<10} {'线程数(活跃/总)':<18} {'数据块':>12} {'平均响应时间(ms)':>22} {'TPOT(ms/token)':>22} {'Tokens/s':>22} {'成功率(%)':>14}")
            print(header_line)
            printed_header = True
        print(f"{now_str:<10} {f'{active_threads}/{total_threads}':<18} {display_chunks:>12} {avg_response_time:>22.2f} {tpot:>22.2f} {tokens_per_second:>22.2f} {success_rate:>14.2f}")
        
        # 记录时间序列数据用于报告
        if "time_series" not in shared_stats:
            shared_stats["time_series"] = []
        shared_stats["time_series"].append({
            "timestamp": latest_update,
            "time_str": now_str,
            "active_threads": active_threads,
            "total_threads": total_threads,
            "total_chunks": display_chunks,  # 使用显示的数据块数（可能是已完成的或实时的）
            "total_tokens": total_tokens,
            "avg_response_time": avg_response_time,
            "tpot": tpot,
            "tokens_per_second": tokens_per_second,
            "success_rate": success_rate,
            "total_requests": total_reqs,
            "success_requests": total_success
        })

