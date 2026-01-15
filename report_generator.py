#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 报告生成模块
包含生成 HTML 性能测试报告的函数
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


def calculate_percentile(values: List[float], percentile: float) -> float:
    """计算百分位数"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = (len(sorted_values) - 1) * percentile / 100
    lower = int(index)
    upper = lower + 1
    if upper >= len(sorted_values):
        return sorted_values[-1]
    weight = index - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def generate_html_report(results_list: List[Dict], shared_stats: Optional[Dict[str, Any]] = None,
                        output_file: str = "test_report.html", host: str = "", port: int = 0,
                        thread_count: int = 1, duration: int = 0, model_name: Optional[str] = None):
    """
    生成 HTML 性能测试报告

    Args:
        results_list: 测试结果列表
        shared_stats: 共享统计信息（包含时间序列数据）
        output_file: 输出文件路径（如果使用默认值，会自动添加模型名和时间戳）
        host: 服务器主机
        port: 服务器端口
        thread_count: 线程数
        duration: 测试持续时间（秒）
        model_name: 模型名称（可选，如果提供会包含在文件名中）
    """
    # 如果使用默认文件名，自动生成带时间戳的文件名，并输出到 report/ 目录
    if output_file == "test_report.html" or os.path.basename(output_file) == "test_report.html":
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 默认使用 report/ 目录
        dir_path = "report"

        # 确保 report 目录存在
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        # 构建文件名
        if model_name:
            # 清理模型名，移除不适合作为文件名的字符
            safe_model_name = "".join(c for c in model_name if c.isalnum() or c in ('-', '_')).strip()
            if safe_model_name:
                filename = f"report_{safe_model_name}_{timestamp}.html"
            else:
                filename = f"report_{timestamp}.html"
        else:
            filename = f"report_{timestamp}.html"

        # 组合目录路径和文件名
        output_file = os.path.join(dir_path, filename)
    # 计算汇总统计
    successful_results = [r for r in results_list if not r.get("error")]
    failed_results = [r for r in results_list if r.get("error")]

    total_requests = len(results_list)
    successful = len(successful_results)
    failed = len(failed_results)
    success_rate = (successful / total_requests * 100) if total_requests > 0 else 0.0

    total_tokens = sum(r.get("token_count", 0) for r in results_list)
    total_chunks = sum(r.get("chunk_count", 0) for r in results_list)
    total_time = sum(r.get("total_response_time", 0) for r in results_list)

    # 按线程分组计算指标，然后再汇总（正确的计算方式）
    # 1. 按线程ID分组
    thread_results: Dict[int, List[Dict]] = {}
    for r in results_list:
        thread_id = r.get("thread_id", 0)
        if thread_id not in thread_results:
            thread_results[thread_id] = []
        thread_results[thread_id].append(r)

    # 2. 计算每个线程的平均指标
    thread_metrics: Dict[int, Dict[str, float]] = {}
    for thread_id, thread_reqs in thread_results.items():
        thread_successful = [r for r in thread_reqs if not r.get("error")]
        if thread_successful:
            thread_metrics[thread_id] = {
                "avg_ttft": sum(r.get("ttft", 0) for r in thread_successful) / len(thread_successful),
                "avg_tpot": sum(r.get("tpot", 0) for r in thread_successful) / len(thread_successful),
                "avg_ttfb": sum(r.get("ttfb", 0) for r in thread_successful) / len(thread_successful),
                "avg_throughput": sum(r.get("throughput", 0) for r in thread_successful) / len(thread_successful),
                "avg_response_time": sum(r.get("total_response_time", 0) for r in thread_successful) / len(thread_successful),
                "request_count": len(thread_successful)
            }
        else:
            thread_metrics[thread_id] = {
                "avg_ttft": 0,
                "avg_tpot": 0,
                "avg_ttfb": 0,
                "avg_throughput": 0,
                "avg_response_time": 0,
                "request_count": 0
            }

    # 3. 汇总所有线程的指标（加权平均，权重为每个线程的请求数）
    total_request_count = sum(m.get("request_count", 0) for m in thread_metrics.values())
    if total_request_count > 0:
        avg_time = sum(m.get("avg_response_time", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
        avg_ttfb = sum(m.get("avg_ttfb", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
        avg_ttft = sum(m.get("avg_ttft", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
        avg_tpot = sum(m.get("avg_tpot", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
        avg_throughput = sum(m.get("avg_throughput", 0) * m.get("request_count", 0) for m in thread_metrics.values()) / total_request_count
    else:
        avg_time = 0
        avg_ttfb = 0
        avg_ttft = 0
        avg_tpot = 0
        avg_throughput = 0

    # 计算百分位数统计
    ttft_values = [r.get("ttft", 0) for r in successful_results]
    tpot_values = [r.get("tpot", 0) for r in successful_results]
    ttfb_values = [r.get("ttfb", 0) for r in successful_results]
    throughput_values = [r.get("throughput", 0) for r in successful_results]
    response_time_values = [r.get("total_response_time", 0) for r in successful_results]

    # TTFT 百分位数
    ttft_min = min(ttft_values, default=0)
    ttft_max = max(ttft_values, default=0)
    ttft_p90 = calculate_percentile(ttft_values, 90)
    ttft_p95 = calculate_percentile(ttft_values, 95)
    ttft_p99 = calculate_percentile(ttft_values, 99)

    # TPOT 百分位数
    tpot_min = min(tpot_values, default=0)
    tpot_max = max(tpot_values, default=0)
    tpot_p90 = calculate_percentile(tpot_values, 90)
    tpot_p95 = calculate_percentile(tpot_values, 95)
    tpot_p99 = calculate_percentile(tpot_values, 99)

    # TTFB 百分位数
    ttfb_min = min(ttfb_values, default=0)
    ttfb_max = max(ttfb_values, default=0)
    ttfb_p90 = calculate_percentile(ttfb_values, 90)
    ttfb_p95 = calculate_percentile(ttfb_values, 95)
    ttfb_p99 = calculate_percentile(ttfb_values, 99)

    # 吞吐量百分位数
    throughput_min = min(throughput_values, default=0)
    throughput_max = max(throughput_values, default=0)
    throughput_p90 = calculate_percentile(throughput_values, 90)
    throughput_p95 = calculate_percentile(throughput_values, 95)
    throughput_p99 = calculate_percentile(throughput_values, 99)

    # 响应时间百分位数
    response_time_min = min(response_time_values, default=0)
    response_time_max = max(response_time_values, default=0)
    response_time_p90 = calculate_percentile(response_time_values, 90)
    response_time_p95 = calculate_percentile(response_time_values, 95)
    response_time_p99 = calculate_percentile(response_time_values, 99)

    # 准备每个请求的时间序列数据
    request_timeline = []
    # 计算时间基准：使用第一个请求的开始时间，但如果shared_stats中有更早的时间，使用更早的时间
    start_time = float(min((r.get("request_start_time", 0) for r in results_list), default=0))
    if shared_stats and "time_series" in shared_stats and shared_stats["time_series"]:
        # 检查time_series中是否有更早的时间戳
        time_series = shared_stats["time_series"]
        if time_series:
            earliest_ts = min((ts.get("timestamp", start_time) for ts in time_series if isinstance(ts.get("timestamp"), (int, float))), default=start_time)
            if isinstance(earliest_ts, (int, float)):
                start_time = min(start_time, float(earliest_ts))

    for r in sorted(results_list, key=lambda x: x.get("request_start_time", 0)):
        if not r.get("error"):
            # 使用真实的时间戳（毫秒）
            real_timestamp = r.get("request_start_time", 0)
            request_timeline.append({
                "time": real_timestamp,  # 真实时间戳（毫秒）
                "ttft": r.get("ttft", 0),
                "tpot": r.get("tpot", 0),
                "ttfb": r.get("ttfb", 0),
                "throughput": r.get("throughput", 0),
                "token_count": r.get("token_count", 0),
                "response_time": r.get("total_response_time", 0)
            })

    # 7DGroup LOGO (炫酷的渐变动画 SVG)
    logo_base64 = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjIwIiBoZWlnaHQ9IjcwIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxkZWZzPjxsaW5lYXJHcmFkaWVudCBpZD0iZ3JhZDEiIHgxPSIwJSIgeTE9IjAlIiB4Mj0iMTAwJSIgeTI9IjEwMCUiPjxzdG9wIG9mZnNldD0iMCUiIHN0eWxlPSJzdG9wLWNvbG9yOiNmZjZiNmI7c3RvcC1vcGFjaXR5OjEiPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9InN0b3AtY29sb3IiIHZhbHVlcz0iI2ZmNmI2YjsjNjY3ZWVhOyNmMDkzZmI7I2ZmNmI2YiIgZHVyPSI0cyIgcmVwZWF0Q291bnQ9ImluZGVmaW5pdGUiLz48L3N0b3A+PHN0b3Agb2Zmc2V0PSI1MCUiIHN0eWxlPSJzdG9wLWNvbG9yOiM2NjdlZWE7c3RvcC1vcGFjaXR5OjEiPjxhbmltYXRlIGF0dHJpYnV0ZU5hbWU9InN0b3AtY29sb3IiIHZhbHVlcz0iIzY2N2VlYTsjZjA5M2ZiOyNmZjZiNmI7IzY2N2VlYSIgZHVyPSI0cyIgcmVwZWF0Q291bnQ9ImluZGVmaW5pdGUiLz48L3N0b3A+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojZjA5M2ZiO3N0b3Atb3BhY2l0eToxIj48YW5pbWF0ZSBhdHRyaWJ1dGVOYW1lPSJzdG9wLWNvbG9yIiB2YWx1ZXM9IiNmMDkzZmI7I2ZmNmI2YjsjNjY3ZWVhOyNmMDkzZmIiIGR1cj0iNHMiIHJlcGVhdENvdW50PSJpbmRlZmluaXRlIi8+PC9zdG9wPjwvbGluZWFyR3JhZGllbnQ+PGZpbHRlciBpZD0iZ2xvdyI+PGZlR2F1c3NpYW5CbHVyIHN0ZERldmlhdGlvbj0iMiIgcmVzdWx0PSJjb2xvcmVkQmx1ciIvPjxmZU1lcmdlPjxmZU1lcmdlTm9kZSBpbj0iY29sb3JlZEJsdXIiLz48ZmVNZXJnZU5vZGUgaW49IlNvdXJjZUdyYXBoaWMiLz48L2ZlTWVyZ2U+PC9maWx0ZXI+PC9kZWZzPjxyZWN0IHdpZHRoPSIyMjAiIGhlaWdodD0iNzAiIHJ4PSIxMiIgZmlsbD0idXJsKCNncmFkMSkiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IidJbnRlcicsICdTZWdvZSBVSScsIHNhbnMtc2VyaWYiIGZvbnQtc2l6ZT0iMjgiIGZvbnQtd2VpZ2h0PSI4MDAiIGZpbGw9IiNmZmYiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuMzVlbSIgZmlsdGVyPSJ1cmwoI2dsb3cpIj48dHNwYW4gZmlsbD0iI2ZmZiI+NzwvdHNwYW4+PHRzcGFuIGZpbGw9IiNmZmUxMDAiPkQ8L3RzcGFuPjx0c3BhbiBmaWxsPSIjZmZmIj5Hcm91cDwvdHNwYW4+PC90ZXh0Pjwvc3ZnPg=="

    # 序列化 JSON 数据用于 JavaScript（确保正确处理空数据）
    if not request_timeline:
        # 如果没有数据，创建一个空数组
        request_timeline = [{"time": 0, "ttft": 0, "tpot": 0, "ttfb": 0, "throughput": 0, "token_count": 0, "response_time": 0}]

    request_timeline_json = json.dumps(request_timeline, ensure_ascii=False)

    # 准备系统级别的时间序列数据（从 shared_stats 的 time_series 中提取）
    # 重要：统一使用 start_time 作为时间基准，确保与其他指标图表的时间轴对齐
    # time_series 包含系统级别的指标：总吞吐量、平均响应时间等，这些会随线程数变化
    thread_timeline = []
    system_timeline = []  # 系统级别的指标时间序列
    rps_timeline = []  # RPS 时间序列

    if shared_stats and "time_series" in shared_stats and shared_stats["time_series"]:
        time_series = shared_stats["time_series"]
        if time_series:
            # 统一使用 start_time 作为基准，确保时间轴对齐
            prev_requests = 0
            for ts in time_series:
                timestamp_val = ts.get("timestamp", 0)
                # 确保是数字类型
                if isinstance(timestamp_val, (int, float)):
                    timestamp: float = float(timestamp_val)  # type: ignore
                else:
                    continue  # 跳过无效的时间戳
                # 使用真实时间戳（毫秒）
                real_timestamp: float = timestamp  # type: ignore
                # 线程数数据
                thread_timeline.append({
                    "time": real_timestamp,  # 真实时间戳（毫秒）
                    "active_threads": ts.get("active_threads", 0),
                    "total_threads": ts.get("total_threads", thread_count)
                })
                # 系统级别的指标数据（这些会随线程数变化）
                current_requests = ts.get("total_requests", 0)
                rps = current_requests - prev_requests  # 每秒请求数
                prev_requests = current_requests

                system_timeline.append({
                    "time": real_timestamp,  # 真实时间戳（毫秒）
                    "system_throughput": ts.get("tokens_per_second", 0),  # 系统总吞吐量（tokens/s）
                    "system_avg_response_time": ts.get("avg_response_time", 0),  # 系统平均响应时间（ms）
                    "system_tpot": ts.get("tpot", 0),  # 系统平均TPOT（ms/token）
                    "total_requests": current_requests,  # 总请求数
                    "total_tokens": ts.get("total_tokens", 0),  # 总token数
                    "success_rate": ts.get("success_rate", 0),  # 成功率（%）
                    "rps": rps  # 每秒请求数
                })
                rps_timeline.append({
                    "time": real_timestamp,
                    "rps": max(0, rps)  # 确保 RPS 非负
                })
    else:
        # 如果没有 time_series 数据，尝试从 results_list 中推断
        # 按时间分组统计每个时间点的活跃线程数
        if results_list:
            # 创建一个时间窗口，统计每个时间点的活跃线程数
            time_windows: Dict[int, set] = {}
            time_to_timestamp: Dict[int, float] = {}  # 记录每个时间窗口对应的真实时间戳
            rps_windows: Dict[int, int] = {}  # 记录每秒的请求数
            for r in results_list:
                req_start = r.get("request_start_time", 0)
                req_end = r.get("request_end_time", req_start)
                thread_id = r.get("thread_id", 0)
                # 将时间转换为秒（相对于开始时间）用于分组
                start_sec = int((req_start - start_time) / 1000.0)
                end_sec = int((req_end - start_time) / 1000.0)
                # 在时间窗口中标记线程活跃
                for t in range(start_sec, end_sec + 1):
                    if t not in time_windows:
                        time_windows[t] = set()
                        time_to_timestamp[t] = start_time + t * 1000  # 计算真实时间戳
                    time_windows[t].add(thread_id)
                # 统计 RPS（请求开始时间所在的秒）
                if start_sec not in rps_windows:
                    rps_windows[start_sec] = 0
                rps_windows[start_sec] += 1
            # 转换为时间序列
            if time_windows:
                for t in sorted(time_windows.keys()):
                    thread_timeline.append({
                        "time": time_to_timestamp.get(t, start_time + t * 1000),  # 真实时间戳（毫秒）
                        "active_threads": len(time_windows[t]),
                        "total_threads": thread_count
                    })
                    rps_timeline.append({
                        "time": time_to_timestamp.get(t, start_time + t * 1000),
                        "rps": rps_windows.get(t, 0)
                    })

    # 如果没有线程时间序列数据，创建一个默认值
    if not thread_timeline:
        current_timestamp = start_time if start_time > 0 else datetime.now().timestamp() * 1000
        thread_timeline = [{"time": current_timestamp, "active_threads": thread_count, "total_threads": thread_count}]

    # 如果没有 RPS 时间序列数据，创建一个默认值
    if not rps_timeline:
        current_timestamp = start_time if start_time > 0 else datetime.now().timestamp() * 1000
        rps_timeline = [{"time": current_timestamp, "rps": 0}]

    # 计算平均 RPS
    if rps_timeline and len(rps_timeline) > 1:
        avg_rps = sum(r.get("rps", 0) for r in rps_timeline) / len(rps_timeline)
    elif duration > 0:
        avg_rps = total_requests / duration
    else:
        avg_rps = total_requests

    # RPS 百分位数
    rps_values = [r.get("rps", 0) for r in rps_timeline]
    rps_min = min(rps_values, default=0)
    rps_max = max(rps_values, default=0)
    rps_p90 = calculate_percentile(rps_values, 90)
    rps_p95 = calculate_percentile(rps_values, 95)
    rps_p99 = calculate_percentile(rps_values, 99)

    # 如果没有系统级别的时间序列数据，尝试从 results_list 生成时间序列
    if not system_timeline:
        # 从 results_list 按时间窗口生成系统级别的指标时间序列
        if results_list:
            successful_results_temp = [r for r in results_list if not r.get("error")]
            if successful_results_temp:
                # 按时间窗口（每秒）分组计算系统指标
                system_time_windows: Dict[int, List[Dict]] = {}
                system_time_to_timestamp: Dict[int, float] = {}  # 记录每个时间窗口对应的真实时间戳
                for r in successful_results_temp:
                    req_start = r.get("request_start_time", 0)
                    relative_time_sec = int((req_start - start_time) / 1000.0)
                    if relative_time_sec < 0:
                        relative_time_sec = 0
                    if relative_time_sec not in system_time_windows:
                        system_time_windows[relative_time_sec] = []
                        system_time_to_timestamp[relative_time_sec] = start_time + relative_time_sec * 1000
                    system_time_windows[relative_time_sec].append(r)

                # 为每个时间窗口计算系统指标
                cumulative_requests = 0
                for t in sorted(system_time_windows.keys()):
                    window_results = system_time_windows[t]
                    if window_results:
                        window_tokens = sum(r.get("token_count", 0) for r in window_results)
                        window_time = sum(r.get("total_response_time", 0) for r in window_results)
                        window_avg_time = window_time / len(window_results) if window_results else 0
                        window_avg_tpot = sum(r.get("tpot", 0) for r in window_results) / len(window_results) if window_results else 0
                        # 计算该时间窗口的吞吐量（假设窗口为1秒）
                        window_throughput = window_tokens  # tokens/s（1秒内的tokens数）
                        window_rps = len(window_results)  # 该秒内的请求数
                        cumulative_requests += window_rps

                        system_timeline.append({
                            "time": system_time_to_timestamp.get(t, start_time + t * 1000),  # 真实时间戳（毫秒）
                            "system_throughput": window_throughput,
                            "system_avg_response_time": window_avg_time,
                            "system_tpot": window_avg_tpot,
                            "total_requests": cumulative_requests,
                            "total_tokens": window_tokens,
                            "success_rate": 100.0,  # 窗口内都是成功请求
                            "rps": window_rps
                        })

                # 如果没有生成任何时间窗口数据，创建一个汇总数据点
                if not system_timeline:
                    total_tokens_temp = sum(r.get("token_count", 0) for r in results_list)
                    total_time_temp = sum(r.get("total_response_time", 0) for r in results_list)
                    avg_time_temp = total_time_temp / len(successful_results_temp) if successful_results_temp else 0
                    actual_start_time = min((r.get("request_start_time", 0) for r in results_list), default=0)
                    actual_end_time = max((r.get("request_end_time", 0) for r in results_list), default=0)
                    total_duration = (actual_end_time - actual_start_time) / 1000.0
                    system_throughput = (total_tokens_temp / total_duration) if total_duration > 0 else 0
                    system_timeline = [{
                        "time": actual_start_time,  # 真实时间戳（毫秒）
                        "system_throughput": system_throughput,
                        "system_avg_response_time": avg_time_temp,
                        "system_tpot": sum(r.get("tpot", 0) for r in successful_results_temp) / len(successful_results_temp) if successful_results_temp else 0,
                        "total_requests": len(results_list),
                        "total_tokens": total_tokens_temp,
                        "success_rate": (len(successful_results_temp) / len(results_list) * 100) if results_list else 0,
                        "rps": len(results_list) / total_duration if total_duration > 0 else 0
                    }]
            else:
                current_ts = start_time if start_time > 0 else datetime.now().timestamp() * 1000
                system_timeline = [{"time": current_ts, "system_throughput": 0, "system_avg_response_time": 0, "system_tpot": 0, "total_requests": 0, "total_tokens": 0, "success_rate": 0, "rps": 0}]
        else:
            current_ts = start_time if start_time > 0 else datetime.now().timestamp() * 1000
            system_timeline = [{"time": current_ts, "system_throughput": 0, "system_avg_response_time": 0, "system_tpot": 0, "total_requests": 0, "total_tokens": 0, "success_rate": 0, "rps": 0}]

    thread_timeline_json = json.dumps(thread_timeline, ensure_ascii=False)
    system_timeline_json = json.dumps(system_timeline, ensure_ascii=False)
    rps_timeline_json = json.dumps(rps_timeline, ensure_ascii=False)

    # 生成 HTML（全新炫酷设计）
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SSE 性能测试报告 | 7DGroup</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.1/dist/chartjs-plugin-zoom.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        @keyframes slideInRight {{
            from {{
                opacity: 0;
                transform: translateX(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        @keyframes pulse {{
            0%, 100% {{
                transform: scale(1);
            }}
            50% {{
                transform: scale(1.05);
            }}
        }}
        @keyframes shimmer {{
            0% {{
                background-position: -1000px 0;
            }}
            100% {{
                background-position: 1000px 0;
            }}
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            min-height: 100vh;
            padding: 20px;
            color: #1a1a1a;
        }}
        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.1);
            overflow: hidden;
            backdrop-filter: blur(10px);
            animation: fadeInUp 0.8s ease-out;
        }}
        .header {{
            background: linear-gradient(135deg, #1F6CFB 0%, #4A90E2 50%, #667eea 100%);
            color: white;
            padding: 50px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
        }}
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 4s ease-in-out infinite;
        }}
        .header-content {{
            flex: 1;
            z-index: 1;
            animation: slideInRight 0.8s ease-out;
        }}
        .header h1 {{
            font-size: 42px;
            font-weight: 800;
            margin-bottom: 15px;
            text-shadow: 0 4px 20px rgba(0,0,0,0.2);
            letter-spacing: -0.5px;
        }}
        .header .meta {{
            font-size: 15px;
            opacity: 0.95;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .header .meta div {{
            background: rgba(255,255,255,0.15);
            padding: 8px 16px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
        }}
        .logo {{
            width: 220px;
            height: 70px;
            margin-left: 30px;
            z-index: 1;
            animation: slideInRight 1s ease-out;
        }}
        .logo img {{
            width: 100%;
            height: 100%;
            object-fit: contain;
            filter: drop-shadow(0 4px 10px rgba(0,0,0,0.2));
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 20px;
            padding: 40px;
            background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
        }}
        @media (max-width: 1200px) {{
            .summary {{
                grid-template-columns: repeat(3, 1fr);
            }}
        }}
        @media (max-width: 768px) {{
            .summary {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        .summary-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04);
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.6s ease-out backwards;
        }}
        .summary-card:nth-child(1) {{ animation-delay: 0.05s; }}
        .summary-card:nth-child(2) {{ animation-delay: 0.1s; }}
        .summary-card:nth-child(3) {{ animation-delay: 0.15s; }}
        .summary-card:nth-child(4) {{ animation-delay: 0.2s; }}
        .summary-card:nth-child(5) {{ animation-delay: 0.25s; }}
        .summary-card:nth-child(6) {{ animation-delay: 0.3s; }}
        .summary-card:nth-child(7) {{ animation-delay: 0.35s; }}
        .summary-card:nth-child(8) {{ animation-delay: 0.4s; }}
        .summary-card:nth-child(9) {{ animation-delay: 0.45s; }}
        .summary-card:nth-child(10) {{ animation-delay: 0.5s; }}
        .summary-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            transition: left 0.5s;
        }}
        .summary-card:hover {{
            transform: translateY(-8px) scale(1.02);
            box-shadow: 0 16px 40px rgba(0,0,0,0.12), 0 0 0 1px rgba(31,108,251,0.2);
        }}
        .summary-card:hover::before {{
            left: 100%;
        }}
        .summary-card h3 {{
            color: #64748b;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #1F6CFB 0%, #667eea 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }}
        .summary-card .unit {{
            font-size: 14px;
            color: #94a3b8;
            margin-left: 4px;
            font-weight: 500;
        }}
        .summary-card.success .value {{
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .summary-card.error .value {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .charts-section {{
            padding: 40px;
            background: #ffffff;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }}
        .section-header h2 {{
            margin-bottom: 0;
        }}
        .reset-zoom-global {{
            background: linear-gradient(135deg, #1F6CFB 0%, #667eea 100%);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(31, 108, 251, 0.3);
        }}
        .reset-zoom-global:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(31, 108, 251, 0.4);
        }}
        .charts-section h2 {{
            color: #1a1a1a;
            margin-bottom: 32px;
            font-size: 32px;
            font-weight: 700;
            position: relative;
            padding-bottom: 16px;
            letter-spacing: -0.5px;
        }}
        .charts-section h2::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 80px;
            height: 4px;
            background: linear-gradient(90deg, #1F6CFB 0%, #667eea 100%);
            border-radius: 2px;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
        }}
        @media (max-width: 1200px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        .chart-container {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 24px;
            border-radius: 20px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
            transition: all 0.3s ease;
            animation: fadeInUp 0.6s ease-out backwards;
        }}
        .chart-container:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.1), 0 0 0 1px rgba(31,108,251,0.15);
        }}
        .chart-container h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #1a1a1a;
            margin-bottom: 16px;
            letter-spacing: -0.3px;
        }}
        .chart-wrapper {{
            position: relative;
            height: 300px;
        }}
        .zoom-hint {{
            text-align: center;
            color: #94a3b8;
            font-size: 11px;
            margin-top: 8px;
        }}
        .metrics-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 20px;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06);
            font-size: 14px;
        }}
        .metrics-table th,
        .metrics-table td {{
            padding: 14px 16px;
            text-align: center;
            border-bottom: 1px solid #e2e8f0;
        }}
        .metrics-table th {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e2e8f0 100%);
            font-weight: 700;
            color: #1a1a1a;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metrics-table td:first-child {{
            text-align: left;
            font-weight: 600;
        }}
        .metrics-table tbody tr {{
            transition: all 0.2s ease;
        }}
        .metrics-table tbody tr:hover {{
            background: linear-gradient(90deg, rgba(31,108,251,0.05) 0%, transparent 100%);
        }}
        .metrics-table tbody tr:last-child td {{
            border-bottom: none;
        }}
        .success {{
            color: #10b981;
            font-weight: 600;
        }}
        .error {{
            color: #ef4444;
            font-weight: 600;
        }}
        .footer {{
            text-align: center;
            padding: 30px;
            color: #64748b;
            background: linear-gradient(135deg, #f8f9fa 0%, #e2e8f0 100%);
            font-size: 13px;
            font-weight: 500;
        }}
        .loading {{
            display: none;
            text-align: center;
            padding: 40px;
        }}
        .loading-spinner {{
            width: 50px;
            height: 50px;
            border: 4px solid #e2e8f0;
            border-top: 4px solid #1F6CFB;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>SSE 性能测试报告</h1>
                <div class="meta">
                    <div>测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
                    <div>服务器: {host}:{port}</div>
                    <div>线程数: {thread_count} | 持续时间: {duration}秒</div>
                </div>
            </div>
            <div class="logo">
                <img src="{logo_base64}" alt="7DGroup Logo">
            </div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>总请求数</h3>
                <div class="value">{total_requests}</div>
            </div>
            <div class="summary-card success">
                <h3>成功率</h3>
                <div class="value">{success_rate:.2f}<span class="unit">%</span></div>
            </div>
            <div class="summary-card success">
                <h3>成功请求</h3>
                <div class="value">{successful}</div>
            </div>
            <div class="summary-card error">
                <h3>失败请求</h3>
                <div class="value">{failed}</div>
            </div>
            <div class="summary-card">
                <h3>总数据块</h3>
                <div class="value">{total_chunks}</div>
            </div>
            <div class="summary-card">
                <h3>平均响应时间</h3>
                <div class="value">{avg_time:.0f}<span class="unit">ms</span></div>
            </div>
            <div class="summary-card">
                <h3>平均 TTFT</h3>
                <div class="value">{avg_ttft:.2f}<span class="unit">ms</span></div>
            </div>
            <div class="summary-card">
                <h3>平均 TPOT</h3>
                <div class="value">{avg_tpot:.2f}<span class="unit">ms/token</span></div>
            </div>
            <div class="summary-card">
                <h3>平均吞吐量</h3>
                <div class="value">{avg_throughput:.2f}<span class="unit">tokens/s</span></div>
            </div>
            <div class="summary-card">
                <h3>总 Token 数</h3>
                <div class="value">{total_tokens}</div>
            </div>
        </div>

        <div class="charts-section">
            <div class="section-header">
                <h2>性能指标趋势图</h2>
                <button class="reset-zoom-global" onclick="resetAllZoom()">重置所有缩放</button>
            </div>
            <p style="color: #64748b; margin-bottom: 24px; font-size: 13px;">
                提示：可拖拽选择区域放大（所有图表同步缩放），双击任意图表恢复原始视图
            </p>

            <div class="charts-grid">
                <div class="chart-container">
                    <h3>TTFT (Time To First Token) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="ttftChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>TPOT (Time Per Output Token) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="tpotChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>TTFB (Time To First Byte) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="ttfbChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>吞吐量 (Tokens/s) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="throughputChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>响应时间趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="responseTimeChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>Token 数量趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="tokenCountChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>RPS (每秒请求数) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="rpsChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>活跃线程数趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="threadCountChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-section">
            <div class="section-header">
                <h2>系统级别性能指标趋势图</h2>
                <button class="reset-zoom-global" onclick="resetAllZoom()">重置所有缩放</button>
            </div>
            <p style="color: #64748b; margin-bottom: 24px; font-size: 13px;">
                以下图表显示系统整体性能随线程数变化的趋势，与上方图表同步缩放
            </p>

            <div class="charts-grid">
                <div class="chart-container">
                    <h3>系统总吞吐量 (Tokens/s) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="systemThroughputChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>系统平均响应时间 (ms) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="systemResponseTimeChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>系统平均 TPOT (ms/token) 趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="systemTpotChart"></canvas>
                    </div>
                </div>

                <div class="chart-container">
                    <h3>总请求数趋势</h3>
                    <div class="chart-wrapper">
                        <canvas id="totalRequestsChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <div class="charts-section">
            <h2>详细指标统计表</h2>
            <table class="metrics-table">
                <thead>
                    <tr>
                        <th>指标</th>
                        <th>平均值</th>
                        <th>最小值</th>
                        <th>最大值</th>
                        <th>P90</th>
                        <th>P95</th>
                        <th>P99</th>
                        <th>单位</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>TTFT (首Token时间)</td>
                        <td>{avg_ttft:.2f}</td>
                        <td>{ttft_min:.2f}</td>
                        <td>{ttft_max:.2f}</td>
                        <td>{ttft_p90:.2f}</td>
                        <td>{ttft_p95:.2f}</td>
                        <td>{ttft_p99:.2f}</td>
                        <td>ms</td>
                    </tr>
                    <tr>
                        <td>TPOT (每Token时间)</td>
                        <td>{avg_tpot:.2f}</td>
                        <td>{tpot_min:.2f}</td>
                        <td>{tpot_max:.2f}</td>
                        <td>{tpot_p90:.2f}</td>
                        <td>{tpot_p95:.2f}</td>
                        <td>{tpot_p99:.2f}</td>
                        <td>ms/token</td>
                    </tr>
                    <tr>
                        <td>TTFB (首字节时间)</td>
                        <td>{avg_ttfb:.2f}</td>
                        <td>{ttfb_min:.2f}</td>
                        <td>{ttfb_max:.2f}</td>
                        <td>{ttfb_p90:.2f}</td>
                        <td>{ttfb_p95:.2f}</td>
                        <td>{ttfb_p99:.2f}</td>
                        <td>ms</td>
                    </tr>
                    <tr>
                        <td>吞吐量</td>
                        <td>{avg_throughput:.2f}</td>
                        <td>{throughput_min:.2f}</td>
                        <td>{throughput_max:.2f}</td>
                        <td>{throughput_p90:.2f}</td>
                        <td>{throughput_p95:.2f}</td>
                        <td>{throughput_p99:.2f}</td>
                        <td>tokens/s</td>
                    </tr>
                    <tr>
                        <td>响应时间</td>
                        <td>{avg_time:.2f}</td>
                        <td>{response_time_min:.2f}</td>
                        <td>{response_time_max:.2f}</td>
                        <td>{response_time_p90:.2f}</td>
                        <td>{response_time_p95:.2f}</td>
                        <td>{response_time_p99:.2f}</td>
                        <td>ms</td>
                    </tr>
                    <tr>
                        <td>RPS (每秒请求数)</td>
                        <td>{avg_rps:.2f}</td>
                        <td>{rps_min:.2f}</td>
                        <td>{rps_max:.2f}</td>
                        <td>{rps_p90:.2f}</td>
                        <td>{rps_p95:.2f}</td>
                        <td>{rps_p99:.2f}</td>
                        <td>req/s</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 7DGroup Performance Testing Tool</p>
        </div>
    </div>

    <script>
        // 存储所有图表实例，用于同步缩放
        const chartInstances = {{}};
        let isSyncing = false;  // 防止循环触发

        // 重置所有图表缩放
        function resetAllZoom() {{
            isSyncing = true;
            Object.values(chartInstances).forEach(chart => {{
                if (chart) {{
                    chart.resetZoom();
                }}
            }});
            setTimeout(() => {{ isSyncing = false; }}, 100);
        }}

        // 获取图表的时间数据源
        function getChartTimeData(chartId) {{
            if (chartId.includes('system') || chartId === 'totalRequestsChart') {{
                return systemTimeline;
            }} else if (chartId === 'threadCountChart') {{
                return threadTimeline;
            }} else if (chartId === 'rpsChart') {{
                return rpsTimeline;
            }} else {{
                return requestTimeline;
            }}
        }}

        // 根据时间戳找到最近的索引
        function findClosestIndex(timeData, targetTime) {{
            if (!timeData || timeData.length === 0) return 0;
            let closestIdx = 0;
            let closestDiff = Math.abs(timeData[0].time - targetTime);
            for (let i = 1; i < timeData.length; i++) {{
                const diff = Math.abs(timeData[i].time - targetTime);
                if (diff < closestDiff) {{
                    closestDiff = diff;
                    closestIdx = i;
                }}
            }}
            return closestIdx;
        }}

        // 同步所有图表的缩放范围（基于时间）
        function syncZoom(sourceChart) {{
            if (isSyncing) return;
            isSyncing = true;

            const sourceXScale = sourceChart.scales.x;
            if (!sourceXScale) {{
                isSyncing = false;
                return;
            }}

            // 获取源图表的缩放范围索引
            const minIndex = Math.round(sourceXScale.min);
            const maxIndex = Math.round(sourceXScale.max);

            // 找到源图表对应的时间数据
            const sourceChartId = Object.keys(chartInstances).find(id => chartInstances[id] === sourceChart);
            const sourceTimeData = getChartTimeData(sourceChartId);

            if (!sourceTimeData || sourceTimeData.length === 0) {{
                isSyncing = false;
                return;
            }}

            // 获取缩放范围对应的时间值
            const minTime = sourceTimeData[Math.max(0, Math.min(minIndex, sourceTimeData.length - 1))].time;
            const maxTime = sourceTimeData[Math.max(0, Math.min(maxIndex, sourceTimeData.length - 1))].time;

            Object.entries(chartInstances).forEach(([id, chart]) => {{
                if (chart && chart !== sourceChart) {{
                    try {{
                        // 获取目标图表的时间数据
                        const targetTimeData = getChartTimeData(id);
                        // 根据时间找到对应的索引
                        const targetMinIdx = findClosestIndex(targetTimeData, minTime);
                        const targetMaxIdx = findClosestIndex(targetTimeData, maxTime);
                        // 使用 zoomScale 方法同步缩放
                        chart.zoomScale('x', {{min: targetMinIdx, max: targetMaxIdx}}, 'none');
                    }} catch (e) {{
                        console.warn('同步缩放失败:', id, e);
                    }}
                }}
            }});

            setTimeout(() => {{ isSyncing = false; }}, 50);
        }}

        // 等待 DOM 和 Chart.js 加载完成
        document.addEventListener('DOMContentLoaded', function() {{
            // 准备数据
            const requestTimeline = {request_timeline_json};
            const threadTimeline = {thread_timeline_json};
            const systemTimeline = {system_timeline_json};
            const rpsTimeline = {rps_timeline_json};

            // 检查数据有效性
            if (!requestTimeline || requestTimeline.length === 0) {{
                console.warn('没有可用的时间序列数据');
            }}

            if (!threadTimeline || threadTimeline.length === 0) {{
                console.warn('没有可用的线程数时间序列数据');
            }}

            if (!systemTimeline || systemTimeline.length === 0) {{
                console.warn('没有可用的系统级别时间序列数据');
            }}

            // 时间格式化函数：将毫秒时间戳转换为 HH:MM:SS 格式
            function formatTimestamp(timestamp) {{
                const date = new Date(timestamp);
                const hours = date.getHours().toString().padStart(2, '0');
                const minutes = date.getMinutes().toString().padStart(2, '0');
                const seconds = date.getSeconds().toString().padStart(2, '0');
                return hours + ':' + minutes + ':' + seconds;
            }}

            // 通用图表配置（带缩放功能）
            const chartOptions = {{
                responsive: true,
                maintainAspectRatio: false,
                animation: {{
                    duration: 800,
                    easing: 'easeInOutQuart'
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top',
                        labels: {{
                            usePointStyle: true,
                            padding: 15,
                            font: {{
                                size: 12,
                                weight: '600',
                                family: "'Inter', sans-serif"
                            }},
                            color: '#1a1a1a'
                        }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 10,
                        titleFont: {{
                            size: 13,
                            weight: '600'
                        }},
                        bodyFont: {{
                            size: 12
                        }},
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        cornerRadius: 6,
                        displayColors: true
                    }},
                    zoom: {{
                        pan: {{
                            enabled: true,
                            mode: 'x',
                            onPanComplete: function({{chart}}) {{
                                syncZoom(chart);
                            }}
                        }},
                        zoom: {{
                            wheel: {{
                                enabled: false
                            }},
                            pinch: {{
                                enabled: true
                            }},
                            drag: {{
                                enabled: true,
                                backgroundColor: 'rgba(31, 108, 251, 0.1)',
                                borderColor: 'rgba(31, 108, 251, 0.8)',
                                borderWidth: 1
                            }},
                            mode: 'x',
                            onZoomComplete: function({{chart}}) {{
                                syncZoom(chart);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        display: true,
                        grid: {{
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        }},
                        ticks: {{
                            color: '#64748b',
                            font: {{
                                size: 11,
                                weight: '500'
                            }},
                            maxRotation: 45,
                            minRotation: 0
                        }},
                        title: {{
                            display: true,
                            text: '时间 (时:分:秒)',
                            color: '#1a1a1a',
                            font: {{
                                size: 12,
                                weight: '600'
                            }},
                            padding: {{ top: 8, bottom: 0 }}
                        }}
                    }},
                    y: {{
                        display: true,
                        beginAtZero: true,
                        grid: {{
                            color: 'rgba(0, 0, 0, 0.05)',
                            drawBorder: false
                        }},
                        ticks: {{
                            color: '#64748b',
                            font: {{
                                size: 11,
                                weight: '500'
                            }}
                        }},
                        title: {{
                            display: true,
                            text: '',
                            color: '#1a1a1a',
                            font: {{
                                size: 12,
                                weight: '600'
                            }},
                            padding: {{ top: 0, bottom: 8 }}
                        }}
                    }}
                }}
            }};

            // 创建图表的辅助函数（支持自定义 Y 轴标题）
            function createChart(canvasId, label, dataKey, color, bgColor, yAxisTitle, dataSource) {{
                const ctx = document.getElementById(canvasId);
                if (!ctx) {{
                    console.error('找不到 canvas 元素:', canvasId);
                    return;
                }}

                const timeline = dataSource || requestTimeline;
                // 使用真实时间格式化
                const labels = timeline.map(r => formatTimestamp(r.time));
                const data = timeline.map(r => parseFloat(r[dataKey]) || 0);

                // 深拷贝图表配置并设置 Y 轴标题
                const options = JSON.parse(JSON.stringify(chartOptions));
                if (yAxisTitle) {{
                    options.scales.y.title.text = yAxisTitle;
                }}

                const chart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [{{
                            label: label,
                            data: data,
                            borderColor: color,
                            backgroundColor: bgColor,
                            borderWidth: 2,
                            pointRadius: 3,
                            pointHoverRadius: 5,
                            pointBackgroundColor: color,
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 1,
                            tension: 0.4,
                            fill: true,
                            cubicInterpolationMode: 'monotone'
                        }}]
                    }},
                    options: options
                }});

                // 存储图表实例
                chartInstances[canvasId] = chart;

                // 双击重置所有图表缩放
                ctx.ondblclick = function() {{
                    resetAllZoom();
                }};
            }}

            // 创建所有图表（带中文 Y 轴标题）
            if (requestTimeline && requestTimeline.length > 0) {{
                createChart('ttftChart', 'TTFT (ms)', 'ttft', 'rgba(75, 192, 192, 1)', 'rgba(75, 192, 192, 0.15)', 'TTFT (毫秒)');
                createChart('tpotChart', 'TPOT (ms/token)', 'tpot', 'rgba(255, 99, 132, 1)', 'rgba(255, 99, 132, 0.15)', 'TPOT (毫秒/token)');
                createChart('ttfbChart', 'TTFB (ms)', 'ttfb', 'rgba(54, 162, 235, 1)', 'rgba(54, 162, 235, 0.15)', 'TTFB (毫秒)');
                createChart('throughputChart', '吞吐量 (tokens/s)', 'throughput', 'rgba(153, 102, 255, 1)', 'rgba(153, 102, 255, 0.15)', '吞吐量 (tokens/秒)');
                createChart('responseTimeChart', '响应时间 (ms)', 'response_time', 'rgba(255, 159, 64, 1)', 'rgba(255, 159, 64, 0.15)', '响应时间 (毫秒)');
                createChart('tokenCountChart', 'Token 数量', 'token_count', 'rgba(201, 203, 207, 1)', 'rgba(201, 203, 207, 0.15)', 'Token 数量');
            }}

            // 创建 RPS 图表
            if (rpsTimeline && rpsTimeline.length > 0) {{
                createChart('rpsChart', 'RPS (req/s)', 'rps', 'rgba(236, 72, 153, 1)', 'rgba(236, 72, 153, 0.15)', 'RPS (请求/秒)', rpsTimeline);
            }}

            // 创建线程数图表（显示活跃线程数和总线程数）
            if (threadTimeline && threadTimeline.length > 0) {{
                const ctx = document.getElementById('threadCountChart');
                if (ctx) {{
                    // 使用真实时间格式化
                    const labels = threadTimeline.map(t => formatTimestamp(t.time));
                    const activeThreads = threadTimeline.map(t => parseFloat(t.active_threads) || 0);
                    const totalThreads = threadTimeline.map(t => parseFloat(t.total_threads) || 0);

                    // 线程数图表的特殊配置（深拷贝）
                    const threadChartOptions = JSON.parse(JSON.stringify(chartOptions));
                    threadChartOptions.scales.y.ticks.stepSize = 1;
                    threadChartOptions.scales.y.ticks.precision = 0;
                    threadChartOptions.scales.y.title.text = '线程数';

                    const chart = new Chart(ctx, {{
                        type: 'line',
                        data: {{
                            labels: labels,
                            datasets: [{{
                                label: '活跃线程数',
                                data: activeThreads,
                                borderColor: 'rgba(34, 197, 94, 1)',
                                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                                borderWidth: 2,
                                pointRadius: 3,
                                pointHoverRadius: 5,
                                pointBackgroundColor: 'rgba(34, 197, 94, 1)',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 1,
                                tension: 0.4,
                                fill: true,
                                cubicInterpolationMode: 'monotone'
                            }}, {{
                                label: '总线程数',
                                data: totalThreads,
                                borderColor: 'rgba(239, 68, 68, 1)',
                                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                                borderWidth: 2,
                                pointRadius: 3,
                                pointHoverRadius: 5,
                                pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 1,
                                tension: 0.4,
                                fill: true,
                                cubicInterpolationMode: 'monotone',
                                borderDash: [5, 5]
                            }}]
                        }},
                        options: threadChartOptions
                    }});

                    chartInstances['threadCountChart'] = chart;
                    ctx.ondblclick = function() {{ resetAllZoom(); }};
                }}
            }}

            // 创建系统级别的指标图表（这些会随线程数变化）
            if (systemTimeline && systemTimeline.length > 0) {{
                // 使用真实时间格式化
                const sysLabels = systemTimeline.map(t => formatTimestamp(t.time));

                // 创建系统总吞吐量图表
                const throughputCtx = document.getElementById('systemThroughputChart');
                if (throughputCtx) {{
                    const throughput = systemTimeline.map(t => parseFloat(t.system_throughput) || 0);
                    const sysThruOptions = JSON.parse(JSON.stringify(chartOptions));
                    sysThruOptions.scales.y.title.text = '系统总吞吐量 (tokens/秒)';

                    const chart = new Chart(throughputCtx, {{
                        type: 'line',
                        data: {{
                            labels: sysLabels,
                            datasets: [{{
                                label: '系统总吞吐量 (tokens/s)',
                                data: throughput,
                                borderColor: 'rgba(34, 197, 94, 1)',
                                backgroundColor: 'rgba(34, 197, 94, 0.15)',
                                borderWidth: 2,
                                pointRadius: 3,
                                pointHoverRadius: 5,
                                pointBackgroundColor: 'rgba(34, 197, 94, 1)',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 1,
                                tension: 0.4,
                                fill: true,
                                cubicInterpolationMode: 'monotone'
                            }}]
                        }},
                        options: sysThruOptions
                    }});

                    chartInstances['systemThroughputChart'] = chart;
                    throughputCtx.ondblclick = function() {{ resetAllZoom(); }};
                }}

                // 创建系统平均响应时间图表
                const responseTimeCtx = document.getElementById('systemResponseTimeChart');
                if (responseTimeCtx) {{
                    const responseTime = systemTimeline.map(t => parseFloat(t.system_avg_response_time) || 0);
                    const sysRespOptions = JSON.parse(JSON.stringify(chartOptions));
                    sysRespOptions.scales.y.title.text = '系统平均响应时间 (毫秒)';

                    const chart = new Chart(responseTimeCtx, {{
                        type: 'line',
                        data: {{
                            labels: sysLabels,
                            datasets: [{{
                                label: '系统平均响应时间 (ms)',
                                data: responseTime,
                                borderColor: 'rgba(239, 68, 68, 1)',
                                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                                borderWidth: 2,
                                pointRadius: 3,
                                pointHoverRadius: 5,
                                pointBackgroundColor: 'rgba(239, 68, 68, 1)',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 1,
                                tension: 0.4,
                                fill: true,
                                cubicInterpolationMode: 'monotone'
                            }}]
                        }},
                        options: sysRespOptions
                    }});

                    chartInstances['systemResponseTimeChart'] = chart;
                    responseTimeCtx.ondblclick = function() {{ resetAllZoom(); }};
                }}

                // 创建系统平均TPOT图表
                const tpotCtx = document.getElementById('systemTpotChart');
                if (tpotCtx) {{
                    const tpot = systemTimeline.map(t => parseFloat(t.system_tpot) || 0);
                    const sysTpotOptions = JSON.parse(JSON.stringify(chartOptions));
                    sysTpotOptions.scales.y.title.text = 'TPOT (毫秒/token)';

                    const chart = new Chart(tpotCtx, {{
                        type: 'line',
                        data: {{
                            labels: sysLabels,
                            datasets: [{{
                                label: '系统平均 TPOT (ms/token)',
                                data: tpot,
                                borderColor: 'rgba(255, 159, 64, 1)',
                                backgroundColor: 'rgba(255, 159, 64, 0.15)',
                                borderWidth: 2,
                                pointRadius: 3,
                                pointHoverRadius: 5,
                                pointBackgroundColor: 'rgba(255, 159, 64, 1)',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 1,
                                tension: 0.4,
                                fill: true,
                                cubicInterpolationMode: 'monotone'
                            }}]
                        }},
                        options: sysTpotOptions
                    }});

                    chartInstances['systemTpotChart'] = chart;
                    tpotCtx.ondblclick = function() {{ resetAllZoom(); }};
                }}

                // 创建总请求数图表
                const requestsCtx = document.getElementById('totalRequestsChart');
                if (requestsCtx) {{
                    const requests = systemTimeline.map(t => parseFloat(t.total_requests) || 0);
                    const sysReqOptions = JSON.parse(JSON.stringify(chartOptions));
                    sysReqOptions.scales.y.title.text = '请求数';

                    const chart = new Chart(requestsCtx, {{
                        type: 'line',
                        data: {{
                            labels: sysLabels,
                            datasets: [{{
                                label: '累计请求数',
                                data: requests,
                                borderColor: 'rgba(153, 102, 255, 1)',
                                backgroundColor: 'rgba(153, 102, 255, 0.15)',
                                borderWidth: 2,
                                pointRadius: 3,
                                pointHoverRadius: 5,
                                pointBackgroundColor: 'rgba(153, 102, 255, 1)',
                                pointBorderColor: '#ffffff',
                                pointBorderWidth: 1,
                                tension: 0.4,
                                fill: true,
                                cubicInterpolationMode: 'monotone'
                            }}]
                        }},
                        options: sysReqOptions
                    }});

                    chartInstances['totalRequestsChart'] = chart;
                    requestsCtx.ondblclick = function() {{ resetAllZoom(); }};
                }}
            }}
        }});
    </script>
</body>
</html>"""

    # 写入文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"\n✓ HTML 报告已生成: {os.path.abspath(output_file)}")
    except Exception as e:
        print(f"\n✗ 生成 HTML 报告失败: {e}")

