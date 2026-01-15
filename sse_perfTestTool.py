#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSE 流式输出性能测试脚本
计算关键指标：TTFT (Time To First Token) 和 TPOT (Time Per Output Token)

主入口文件 - 负责参数解析和测试流程控制
"""

import sys
import argparse
import threading
import time

# 导入各个模块
from providers import QueryProvider, ApiKeyProvider
from tester import SSETester
from test_runner import run_test_thread, aggregate_stats
from report_generator import generate_html_report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="SSE 流式输出性能测试工具（支持多线程和参数化）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本测试（只输入 token）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"
  
  # 基本测试（完整 Bearer token）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "Bearer app-xxx"
  
  # 自定义查询
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --query "你好"
  
  # 多线程测试（2个线程）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 2
  
  # 使用参数化文件
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --param-file queries.txt --threads 3
  
  # 指定执行时间长度（持续运行60秒）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --duration 60
  
  # 使用 --execution-time 别名（等同于 --duration）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --execution-time 120
  
  # 静默模式（不输出详细信息）
  python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --quiet
        """
    )
    
    parser.add_argument("--host", type=str, default="localhost",
                       help="服务器主机地址 (默认: localhost)")
    parser.add_argument("--port", type=int, default=80,
                       help="服务器端口 (默认: 80)")
    parser.add_argument("--api-key", type=str, required=False, default="",
                       help="API 密钥 (可以是 'app-xxx' 或 'Bearer app-xxx' 格式)")
    parser.add_argument("--query", type=str, default="你是谁",
                       help="查询文本 (默认: 你是谁，当使用参数化文件时此参数无效)")
    parser.add_argument("--conversation-id", type=str, default="",
                       help="对话ID (默认: 空)")
    parser.add_argument("--user", type=str, default="gaolou",
                       help="用户标识 (默认: gaolou)")
    parser.add_argument("--timeout", type=int, default=60,
                       help="请求超时时间（秒） (默认: 60)")
    parser.add_argument("--threads", type=int, default=1,
                       help="并发线程数 (默认: 1)")
    parser.add_argument("--param-file", type=str, default=None,
                       help="参数化文件路径，每行一个查询文本，会循环使用")
    parser.add_argument("--api-key-file", type=str, default=None,
                       help="API Key 参数化文件路径，每行一个 API Key，会循环使用")
    parser.add_argument("--ramp-up", type=int, default=0,
                       help="压测线程递增时间（秒），例如10个线程配10秒表示每秒启动1个线程")
    parser.add_argument("--duration", "--execution-time", type=int, default=0, dest="duration",
                       help="测试执行时间长度（秒），>0 表示在指定时间窗口内循环发送请求，0 表示只执行一次")
    parser.add_argument("--quiet", action="store_true",
                       help="静默模式，不输出详细信息")
    parser.add_argument("--html-report", type=str, default=None,
                       help="生成 HTML 报告文件路径（例如: report.html）。如果不指定，默认输出到 report/ 目录，文件名自动带时间戳")
    parser.add_argument("--model-name", type=str, default=None,
                       help="模型名称（可选），如果提供会包含在报告文件名中")
    
    args = parser.parse_args()
    
    # 创建查询提供器
    query_provider = QueryProvider(
        param_file=args.param_file,
        default_query=args.query
    )

    # 创建 API Key 提供器
    api_key_provider = None
    if args.api_key_file:
        api_key_provider = ApiKeyProvider(args.api_key_file, args.api_key)
    else:
        if not args.api_key:
            print("错误: 需要提供 --api-key 或 --api-key-file")
            sys.exit(1)
    
    # 如果使用参数化文件，显示加载的查询数量
    if args.param_file and not args.quiet:
        print(f"已加载参数化文件: {args.param_file}")
        print(f"查询数量: {len(query_provider.queries)}")
        print()
    
    # 创建测试器
    tester = SSETester(
        host=args.host,
        port=args.port,
        api_key=args.api_key,
        timeout=args.timeout
    )
    
    # 是否开启汇总线程（单线程也开启，避免单线程输出）
    enable_agg = True
    per_thread_verbose = False  # 关闭线程内输出，统一看汇总
    
    results_list = []
    results_lock = threading.Lock()
    threads = []
    shared_stats = {
        "lock": threading.Lock(),
        "thread_stats": {},
        "start_time": time.time() * 1000,
        "total_threads": max(1, args.threads),
        "requests": 0,
        "success": 0,
        "fail": 0
    }
    stop_event = threading.Event()
    duration_ms = args.duration * 1000 if args.duration > 0 else None
    end_time_ms = shared_stats["start_time"] + duration_ms if duration_ms else None
    if enable_agg:
        agg_thread = threading.Thread(target=aggregate_stats, args=(shared_stats, stop_event, not args.quiet), daemon=True)
        agg_thread.start()
    else:
        agg_thread = None
    
    thread_count = max(1, args.threads)
    if not args.quiet:
        print(f"开始测试，线程数: {thread_count}")
        if args.duration > 0:
            duration_str = f"{args.duration}秒"
            if args.duration >= 60:
                minutes = args.duration // 60
                seconds = args.duration % 60
                if seconds > 0:
                    duration_str = f"{minutes}分{seconds}秒"
                else:
                    duration_str = f"{minutes}分钟"
            print(f"执行时间长度: {duration_str}")
        else:
            print("执行模式: 单次执行（每个线程执行一次后退出）")
        print("=" * 60)
        print()
    
    # 创建并启动线程
    for i in range(thread_count):
        # ramp-up 控制启动间隔
        if args.ramp_up > 0 and i > 0:
            ramp_step = args.ramp_up / thread_count
            time.sleep(ramp_step)
        thread = threading.Thread(
            target=run_test_thread,
            args=(tester, query_provider, i + 1, args.conversation_id,
                  args.user, per_thread_verbose, results_list, results_lock, shared_stats, stop_event, end_time_ms, api_key_provider)
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
    else:
        timer_thread = None

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 停止汇总线程
    if agg_thread:
        stop_event.set()
        agg_thread.join(timeout=2)
    if timer_thread:
        timer_thread.join(timeout=1)
    
    # 汇总统计信息
    if not args.quiet:
        print("\n" + "=" * 60)
        print("           测试完成 - 汇总统计")
        print("=" * 60)
        
        total_chunks = sum(r.get("chunk_count", 0) for r in results_list)
        total_tokens = sum(r.get("token_count", 0) for r in results_list)
        total_time = sum(r.get("total_response_time", 0) for r in results_list)
        successful = sum(1 for r in results_list if not r.get("error"))
        failed = len(results_list) - successful
        
        print(f"配置线程数: {thread_count}")
        print(f"请求次数: {len(results_list)}")
        # 计算实际执行时间
        if results_list:
            actual_start_time = min((r.get("request_start_time", 0) for r in results_list), default=0)
            actual_end_time = max((r.get("request_end_time", 0) for r in results_list), default=0)
            actual_duration = (actual_end_time - actual_start_time) / 1000.0  # 转换为秒
            if args.duration > 0:
                print(f"配置执行时间: {args.duration} 秒")
            print(f"实际执行时间: {actual_duration:.2f} 秒")
        elif args.duration > 0:
            print(f"配置执行时间: {args.duration} 秒")
        print(f"成功: {successful}")
        print(f"失败: {failed}")
        total_reqs = len(results_list)
        success_rate = (successful / total_reqs * 100) if total_reqs > 0 else 0.0
        print(f"成功率: {success_rate:.2f} %")
        print(f"总数据块数: {total_chunks}")
        print(f"总Token数: {total_tokens}")
        print(f"总响应时间: {total_time:.2f} ms")
        
        if successful > 0:
            avg_time = total_time / successful
            print(f"平均响应时间: {avg_time:.2f} ms")
            # 汇总 TTFT 与 TTFB（成功请求）
            total_ttfb = sum(r.get("ttfb", 0) for r in results_list if not r.get("error"))
            total_ttft = sum(r.get("ttft", 0) for r in results_list if not r.get("error"))
            avg_ttfb = total_ttfb / successful
            avg_ttft = total_ttft / successful
            print(f"平均TTFB: {avg_ttfb:.2f} ms")
            print(f"平均TTFT: {avg_ttft:.2f} ms")
        
        print("=" * 60)
        print()
    
    # 生成 HTML 报告
    # 如果指定了 --html-report，使用指定路径；否则使用默认值（会自动输出到 report/ 目录）
    report_file = args.html_report if args.html_report else "test_report.html"
    generate_html_report(
        results_list=results_list,
        shared_stats=shared_stats,
        output_file=report_file,
        host=args.host,
        port=args.port,
        thread_count=thread_count,
        duration=args.duration,
        model_name=args.model_name
    )
    
    # 检查是否有错误
    has_error = any(r.get("error") for r in results_list)
    sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()

