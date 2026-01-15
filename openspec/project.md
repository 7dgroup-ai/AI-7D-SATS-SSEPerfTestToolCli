# Project Context

## Purpose
AI-7D-SATS-SSEPerfTestToolCli 是一个用于测试 SSE（Server-Sent Events）流式输出性能的 Python CLI 工具。主要目标是：
- 对 AI 大模型的流式输出进行性能压测
- 测量关键性能指标（TTFT、TPOT、TTFB、吞吐量等）
- 生成详细的 HTML 性能报告
- 支持多线程并发测试和渐进式负载增加（ramp-up）

## Tech Stack
- **Python 3.9+**: 主要编程语言
- **urllib3**: HTTP 客户端库，用于 SSE 连接
- **threading**: 多线程并发测试
- **Chart.js**: HTML 报告中的图表渲染（通过 CDN）
- **JSON**: 数据序列化和解析

## Project Conventions

### Code Style
- 使用 Python 3.9+ 语法
- 文件编码：UTF-8（`# -*- coding: utf-8 -*-`）
- 函数和类使用 docstring 文档字符串
- 变量命名：snake_case
- 类命名：PascalCase
- 常量：UPPER_CASE
- 注释使用中文，便于团队理解

### Architecture Patterns
- **模块化设计**：
  - `sse_perfTestTool.py`: 主入口，参数解析和线程管理
  - `tester.py`: SSE 测试核心逻辑（`SSETester` 类）
  - `test_runner.py`: 测试线程运行和统计汇总
  - `report_generator.py`: HTML 报告生成
  - `providers.py`: 查询和 API Key 提供器
- **线程安全**：使用 `threading.Lock` 保护共享数据（`shared_stats`）
- **事件驱动**：使用 `threading.Event` 控制测试停止
- **数据聚合**：按线程分组计算指标，然后加权平均汇总

### Testing Strategy
- 性能测试工具本身，主要关注功能正确性
- 关键指标计算需要验证准确性
- HTML 报告生成需要验证数据完整性

### Git Workflow
- 主分支：`main` 或 `master`
- 功能开发：创建功能分支
- 提交信息：使用中文描述变更内容

## Domain Context

### 性能指标术语
- **TTFT (Time To First Token)**: 从请求发送到收到第一个 token 的时间（毫秒）
- **TPOT (Time Per Output Token)**: 每个输出 token 的平均时间（毫秒/token）
- **TTFB (Time To First Byte)**: 从请求发送到收到第一个字节的时间（毫秒）
- **吞吐量 (Throughput)**: 每秒生成的 token 数（tokens/s）
- **响应时间 (Response Time)**: 完整请求的总时间（毫秒）

### 测试模式
- **单次执行模式**: 每个线程执行一次请求后退出
- **持续时间模式**: 在指定时间内持续发送请求
- **渐进式负载 (Ramp-up)**: 逐步增加并发线程数

### 数据流
1. 主线程创建测试线程和统计汇总线程
2. 测试线程循环发送 SSE 请求，实时更新 `shared_stats`
3. 统计汇总线程每秒读取 `shared_stats` 并输出实时统计
4. 测试结束后，生成 HTML 报告

## Important Constraints
- 必须支持 Python 3.9+
- SSE 连接需要保持长连接，注意超时处理
- 多线程环境下需要确保线程安全
- 报告文件名需要包含模型名和时间戳，避免覆盖
- 指标计算必须按线程分组后再汇总，确保准确性

## External Dependencies
- **SSE API**: 测试目标 API（SSE 流式输出）
- **Chart.js CDN**: HTML 报告中的图表库（无需本地安装）
