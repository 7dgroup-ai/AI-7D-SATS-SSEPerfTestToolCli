# Contributing to AI-7D-SATS-SSEPerfTestToolCli

感谢您对 AI-7D-SATS-SSEPerfTestToolCli 项目的关注！我们欢迎任何形式的贡献。

## 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请：

1. 检查 [Issues](https://github.com/7dgroup-ai/AI-7D-SATS-SSEPerfTestToolCli/issues) 确认问题是否已被报告
2. 如果没有，创建一个新的 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤
   - 预期行为和实际行为
   - 环境信息（操作系统、Python 版本等）
   - 相关的日志或截图

### 提交代码

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码风格
- 添加适当的注释和文档字符串
- 确保代码通过测试
- 更新相关文档

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/7dgroup-ai/AI-7D-SATS-SSEPerfTestToolCli.git
cd AI-7D-SATS-SSEPerfTestToolCli

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
python sse_perfTestTool.py --help
```

## 许可证

通过贡献代码，您同意您的贡献将根据项目的许可证进行许可。
