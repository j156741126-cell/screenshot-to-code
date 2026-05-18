"""MCP 服务器 - 为 Claude Code 提供千问图像理解能力

在 Claude Code 的 .mcp.json 中配置：
{
  "mcpServers": {
    "qwen-vision": {
      "command": "python",
      "args": ["<项目路径>/ai-pipeline/mcp_server.py"]
    }
  }
}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from qwen_vision import analyze as qwen_analyze

SERVER_NAME = "qwen-vision"
SERVER_VERSION = "1.0.0"


def send_response(request_id, result):
    msg = json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def send_error(request_id, code, message):
    msg = json.dumps({
        "jsonrpc": "2.0", "id": request_id,
        "error": {"code": code, "message": message}
    })
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def handle_initialize(req_id, params):
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "capabilities": {"tools": {}}
    }


def handle_tools_list(req_id, params):
    tools = [{
        "name": "analyze_image",
        "description": "使用千问 3.5-VL 分析图片内容，返回详细的文字描述。"
                       "支持截图、设计稿、流程图、照片等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "图片文件的完整路径"
                },
                "prompt": {
                    "type": "string",
                    "description": "可选的自定义分析提示词，不填则默认详细描述"
                }
            },
            "required": ["image_path"]
        }
    }]
    return {"tools": tools}


def handle_tools_call(req_id, params):
    tool_name = params.get("name")
    args = params.get("arguments", {})

    if tool_name == "analyze_image":
        image_path = args.get("image_path", "")
        prompt = args.get("prompt")

        if not image_path or not Path(image_path).exists():
            send_error(req_id, -32000, f"图片文件不存在: {image_path}")
            return

        try:
            result = qwen_analyze(image_path, prompt)
            return {
                "content": [{"type": "text", "text": result}]
            }
        except Exception as e:
            send_error(req_id, -32000, f"图像分析失败: {str(e)}")
            return

    send_error(req_id, -32601, f"未知工具: {tool_name}")


handlers = {
    "initialize": handle_initialize,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


def main():
    # 首次启动确认
    init_log = Path(__file__).parent / ".mcp_init"
    init_log.write_text("MCP server started")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        handler = handlers.get(method)
        if handler:
            result = handler(req_id, params)
            if result is not None:
                send_response(req_id, result)
        else:
            # 通知类消息（如 notifications/initialized）忽略
            if req_id is not None:
                send_error(req_id, -32601, f"未知方法: {method}")


if __name__ == "__main__":
    main()
