# Screenshot to Code

一张截图进去，完整代码出来。三款 AI 模型各取所长，全自动协作流水线。

```
截图 → 千问 VL 视觉理解 → DeepSeek 深度推理 → 生成可运行代码
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 填写 API 密钥

编辑 `config.json`，填入 DashScope 和 DeepSeek 的 API Key（[DashScope 申请](https://dashscope.aliyun.com) | [DeepSeek 申请](https://platform.deepseek.com)）

### 3. 运行

```bash
python orchestrator.py design.png "根据这个设计稿生成 React 组件"
```

**仅出方案不生成代码：**
```bash
python orchestrator.py screenshot.png --no-code
```

### 4. MCP 服务器（可选）

让 Claude Code 直接调用千问视觉能力识别图片。配置 `.mcp.json` 到用户目录，重启 Claude Code 后可用 `analyze_image` 工具。

## 工作流程

| 步骤 | 模型 | 作用 |
|------|------|------|
| 1. 图像理解 | 千问 VL (qwen-vl-max) | 分析图片，输出 UI 元素、文字、布局、颜色 |
| 2. 深度推理 | DeepSeek (deepseek-reasoner) | 根据描述生成完整技术方案和架构设计 |
| 3. 代码生成 | Claude Code / DeepSeek | 输出可运行的前端代码到 `generated/` 目录 |

## 文件结构

```
├── config.json          # API 密钥和模型配置
├── qwen_vision.py       # 千问 VL 图像理解模块
├── orchestrator.py      # 完整流水线编排器
├── mcp_server.py        # MCP 服务器 (JSON-RPC 2.0)
├── test_api.py          # API 连通性测试
├── image-to-code.bat    # Windows 批处理快捷方式
└── requirements.txt     # Python 依赖
```

## 输出

- 技术方案保存到 `plan.md`
- 代码生成到 `generated/` 目录
"根据 CLAUDE.md 帮我配置并运行这个项目
提示词命令，一键配置
