# CLAUDE.md

本文件为 Claude Code 提供项目上下文。在目标机器上，Claude Code 读取此文件后应能完整理解并复现项目。

## 项目概述

这是一个「图片到代码」多模型协作流水线：

```
输入图片 → 千问 VL 图像理解 → DeepSeek 深度推理 → Claude Code 代码生成
```

- **千问 3.5-VL (qwen-vl-max)**: 通过 DashScope API 分析图片，输出详细的文字描述（UI元素、布局、文字、颜色等）
- **DeepSeek (deepseek-reasoner)**: 接收图像描述 + 用户需求，输出完整技术方案（架构、技术选型、文件结构）
- **Claude Code**: 根据 DeepSeek 的技术方案生成实际代码文件

项目还包含一个 MCP 服务器，让 Claude Code 可以直接调用千问 VL 分析图片。

## 文件结构

```
ai-pipeline/
├── config.json         # API 密钥和模型配置（需要用户填写密钥）
├── qwen_vision.py      # 千问 VL 图像理解模块（含自动压缩）
├── orchestrator.py     # 完整流水线编排器
├── mcp_server.py       # MCP 服务器（JSON-RPC 2.0 over stdio）
├── test_api.py         # API 连通性测试脚本
├── image-to-code.bat   # Windows 批处理快捷方式
└── requirements.txt    # Python 依赖
```

## 配置步骤（在新机器上执行）

### 1. 安装依赖
```bash
python -m pip install requests pillow
```

### 2. 填写 API 密钥
编辑 `config.json`，填入你的 DashScope 和 DeepSeek API 密钥：

```json
{
  "qwen": {
    "api_url": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "api_key": "<你的 DashScope API Key>",
    "model": "qwen-vl-max"
  },
  "deepseek": {
    "api_url": "https://api.deepseek.com/v1/chat/completions",
    "api_key": "<你的 DeepSeek API Key>",
    "model": "deepseek-reasoner"
  }
}
```

### 3. 测试 API 连通性
```bash
# 准备一张测试截图，然后运行：
python test_api.py
```

### 4. 运行完整流水线
```bash
python orchestrator.py <图片路径> "需求描述"
# 例如：
python orchestrator.py design.png "根据这个设计稿生成 React 组件"
# 仅生成方案不生成代码：
python orchestrator.py screenshot.png --no-code
```

### 5. 配置 MCP 服务器（可选）
将 `.mcp.json` 中的内容合并到用户目录下的 `.mcp.json`（`C:\Users\<用户名>\.mcp.json`），并修改 `args` 中的路径为实际项目路径。重启 Claude Code 后即可使用 `analyze_image` 工具。

## 关键技术细节

### 图片压缩策略 (qwen_vision.py)
- 超过 150KB 自动压缩
- RGBA/P 模式 → RGB + 白色背景
- 最大边长 1920px，LANCZOS 缩放
- 输出 JPEG quality 75

### 模型名称注意
- 正确的千问 VL 模型名: `qwen-vl-max`、`qwen-vl-plus`
- **不要使用** `qwen3.5-vl-plus`（不存在，会返回 404）

### Windows 编码修复
orchestrator.py 顶部有 GBK 编码修复：
```python
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
```

### MCP 协议
- 基于 JSON-RPC 2.0，通过 stdio 通信
- 支持方法: `initialize`、`tools/list`、`tools/call`
- 工具: `analyze_image` — 参数 `image_path`(必填)、`prompt`(可选)

## 项目产出

- 运行后 `plan.md` 保存 DeepSeek 生成的技术方案
- 代码默认生成在 `generated/` 目录下
