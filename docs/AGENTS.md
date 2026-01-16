# AGENTS.md - AI Agent Development Guidelines

## Project Overview

This is a Python-based SSE (Server-Sent Events) performance testing tool that measures streaming response metrics including TTFT, TPOT, TTFB, and throughput. The tool supports multi-threaded testing, parameterized queries, and generates HTML reports with interactive charts.

## Commands

### Running Tests
```bash
# No test framework is currently configured
# To run main tool:
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx"

# Basic test with query
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --query "你好，请介绍一下你自己"

# Multi-threaded test
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 5

# Test with parameterized file
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --param-file queries.txt

# Duration-based test
python3 sse_perfTestTool.py --host localhost --port 80 --api-key "app-xxx" --threads 10 --duration 60
```

### Dependencies Management
```bash
# Install dependencies (if requirements.txt exists)
pip3 install -r requirements.txt

# Current dependencies appear to be:
# - requests (for HTTP calls)
# - Standard library only
```

### Code Quality
```bash
# No linting/formatting tools configured
# Consider adding:
pip install black isort flake8 mypy

# Run formatters (if configured):
black *.py
isort *.py

# Run linters (if configured):
flake8 *.py
mypy *.py
```

## Code Style Guidelines

### Python Version & Encoding
- **Target**: Python 3.7+
- **Encoding**: UTF-8 (required for Chinese content)
- **Shebang**: `#!/usr/bin/env python3` for executable scripts
- **File Header**: Include UTF-8 encoding comment and module docstring

### Import Organization
```python
# Standard library imports first
import sys
import argparse
import threading
import time

# Third-party imports second
import requests
import json

# Local imports last
from providers import QueryProvider, ApiKeyProvider
from tester import SSETester
```

### Code Structure & Patterns

#### Class Design
- Use clear, descriptive class names (e.g., `SSETester`, `QueryProvider`)
- Include comprehensive docstrings with Args/Returns documentation
- Use type hints consistently for all method signatures

#### Method Design
- Private methods use underscore prefix: `_calculate_metrics()`, `_print_results()`
- Public methods have clear verb-noun naming: `test_streaming()`, `get_next_query()`
- Return structured data (dicts) rather than multiple values

#### Error Handling
```python
try:
    # Operation
    result = some_operation()
except requests.exceptions.RequestException as e:
    # Handle specific exceptions
    error_msg = str(e)
    stats["error"] = error_msg
    return stats
except Exception as e:
    # Catch-all with context
    print(f"Unexpected error: {e}")
    raise
```

### Thread Safety Patterns
- Use `threading.Lock()` for shared state access
- Wrap critical sections in `with lock:` blocks
- Use `threading.Event()` for coordination between threads

#### Example Pattern:
```python
class ThreadSafeProvider:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = []
    
    def get_next(self):
        with self.lock:
            # Critical section
            item = self.data[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.data)
            return item
```

### Data Structures
- Use `deque` for thread-safe circular buffers
- Use `Dict[str, Any]` for flexible result structures
- Prefer structured dicts over tuples for return values

### Performance Considerations
- Use `response.iter_lines()` for streaming responses
- Calculate time metrics in milliseconds using `time.time() * 1000`
- Use generator patterns for large data processing

### Logging & Output
- Use Chinese comments where appropriate (this is a Chinese-language tool)
- Include thread IDs in multi-threaded output: `[线程1]`
- Use consistent formatting for metrics display
- Provide both detailed and quiet output modes

### Configuration & Args
- Use `argparse` for CLI interface
- Provide sensible defaults for all parameters
- Support both short and long parameter names
- Include comprehensive help text with examples

### File Naming Conventions
- Main entry point: `sse_perfTestTool.py`
- Core classes: `src/sse_perf_tool/tester.py`, `src/sse_perf_tool/providers.py`, `src/sse_perf_tool/test_runner.py`
- Utilities: `src/sse_perf_tool/report_generator.py`
- Use snake_case for all Python files

### Constants & Magic Numbers
- Define timeouts as parameters with defaults (e.g., 60 seconds)
- Use descriptive variable names instead of magic numbers
- Document measurement units (ms, tokens/s, etc.)

### Documentation Standards
- Include module docstrings explaining purpose
- Document complex algorithms with inline comments
- Explain metric calculations (especially TTFT/TPOT formulas)
- Provide usage examples in docstrings

### Testing Considerations
While no test framework is currently set up, consider:
- Unit tests for metric calculations
- Integration tests for SSE streams
- Performance benchmarks
- Mock server responses for isolated testing

## Key Metrics Implementation

### Core Metrics
- **TTFT**: Time to First Token (`first_token_time - request_start_time`)
- **TPOT**: Time Per Output Token (`(last_token_time - first_token_time) / (token_count - 1)`)
- **TTFB**: Time to First Byte (`first_byte_time - request_start_time`)
- **Throughput**: Tokens per second (`token_count / streaming_duration * 1000`)

### Metric Calculations
All time measurements should be in milliseconds for consistency.
Use `time.time() * 1000` for high-precision timestamps.

## Development Notes

- This tool focuses on Chinese language AI model testing
- Multi-threading requires careful synchronization
- HTML reports use Chart.js for visualization
- Error handling should be robust for network scenarios
- Consider rate limiting and backpressure handling

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