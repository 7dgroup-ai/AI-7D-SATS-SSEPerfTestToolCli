<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SSE Performance Testing Tool - A Python CLI tool for load testing SSE (Server-Sent Events) streaming endpoints. Generates HTML reports with performance metrics visualization.

## Common Commands

```bash
# Install dependencies
pip3 install requests

# Basic test (single request)
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"

# Multi-threaded test with duration
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5 --duration 60

# With parameter file (queries cycle through file)
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --param-file queries.txt --threads 3

# With ramp-up (gradual thread start)
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --ramp-up 10 --duration 60

# Custom HTML report output
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --html-report report.html --model-name "gpt-4"

# Quiet mode (minimal output)
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --quiet
```

## Architecture

```
sse_perfTestTool.py    # Entry point: CLI argument parsing, thread orchestration
    ├── src/sse_perf_tool/providers.py       # QueryProvider, ApiKeyProvider (thread-safe cycling)
    ├── src/sse_perf_tool/tester.py          # SSETester class: HTTP/SSE handling, metrics calculation
    ├── src/sse_perf_tool/test_runner.py     # run_test_thread(), aggregate_stats() for real-time stats
    └── src/sse_perf_tool/report_generator.py # HTML report generation with Chart.js visualizations
```

### Key Components

**SSETester** (`src/sse_perf_tool/tester.py`):
- Handles SSE streaming via `requests.Session` with retry logic
- Calculates per-request metrics: TTFT, TPOT, TTFB, throughput
- Token estimation: Chinese characters count as 1, English words count as 1

**Test Runner** (`src/sse_perf_tool/test_runner.py`):
- `run_test_thread()`: Worker thread loop with duration/stop_event control
- `aggregate_stats()`: Background thread collecting stats every second into `shared_stats["time_series"]`

**Report Generator** (`src/sse_perf_tool/report_generator.py`):
- Groups results by thread_id for weighted average calculations
- Generates request-level and system-level time series charts

### Data Flow

1. Main thread creates `shared_stats` dict with lock, spawns test threads
2. Each test thread calls `tester.test_streaming()`, updates `shared_stats["thread_stats"]` in real-time
3. Aggregator thread polls every second, computes system-level metrics
4. After completion, `generate_html_report()` produces final report

## Key Metrics

- **TTFT** (Time To First Token): `first_token_time - request_start_time`
- **TPOT** (Time Per Output Token): `(last_token_time - first_token_time) / (token_count - 1)`
- **TTFB** (Time To First Byte): `first_byte_time - request_start_time`
- **Throughput**: `token_count / streaming_duration * 1000` (tokens/s)

System-level metrics use weighted averages across threads by request count.

## API Endpoint

Target: `POST http://{host}:{port}/v1/chat-messages`

Request body follows chat API format with `response_mode: "streaming"`.
