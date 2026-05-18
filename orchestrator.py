"""多模型协作编排：千问 VL → DeepSeek 推理 → Claude Code 生成"""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

from qwen_vision import analyze as qwen_analyze

BASE_DIR = Path(__file__).parent

# 修复 Windows 终端 GBK 编码问题
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def load_config():
    with open(BASE_DIR / "config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def deepseek_reason(description: str, user_need: str) -> str:
    """DeepSeek 深度推理，生成技术方案"""
    config = load_config()
    ds = config["deepseek"]

    system_prompt = (
        "你是一个资深软件架构师。收到图像描述和用户需求后，"
        "输出一份完整的技术实现方案，包括：\n"
        "1. 架构设计（组件树/模块划分）\n"
        "2. 技术选型（语言、框架、库）\n"
        "3. 关键代码逻辑说明\n"
        "4. 文件结构和创建顺序\n"
        "5. 注意事项和边界情况处理\n\n"
        "输出格式为 Markdown，代码块用 ``` 包裹。"
    )

    headers = {
        "Authorization": f"Bearer {ds['api_key']}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": ds["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",
             "content": f"## 图像内容描述\n\n{description}\n\n## 用户需求\n\n{user_need}"}
        ],
        "temperature": 0.3,
        "max_tokens": 8192
    }

    resp = requests.post(ds["api_url"], json=payload,
                         headers=headers, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def invoke_claude_code(plan: str, output_dir: str = "generated") -> str:
    """调用 Claude Code (codex CLI) 根据方案生成代码"""
    plan_file = BASE_DIR / "plan.md"

    # 写入方案文件
    with open(plan_file, "w", encoding="utf-8") as f:
        f.write(plan)

    # 调用 codex 生成代码
    prompt = (
        f"根据 {plan_file} 中的技术方案，生成完整可运行的项目代码。"
        f"将所有代码文件创建在 {output_dir}/ 目录下。"
        f"严格按照方案中的文件结构和命名来创建。"
    )

    print("\n--- 调用 Claude Code 生成代码 ---")
    result = subprocess.run(
        ["codex", "exec", prompt],
        cwd=str(BASE_DIR),
        capture_output=False,
        timeout=300
    )

    if result.returncode != 0:
        raise RuntimeError(f"Claude Code 执行失败，退出码: {result.returncode}")

    return str(BASE_DIR / output_dir)


def run(image_path: str, user_need: str, auto_code: bool = True):
    """
    执行完整流水线
    :param image_path: 图片路径
    :param user_need: 用户需求描述
    :param auto_code: 是否自动调用 Claude Code 生成代码
    """
    start = time.time()

    # ---- 阶段 1：千问图像理解 ----
    print("=" * 60)
    print("[1/3] 千问 3.5-VL 分析图像...")
    print("=" * 60)
    image_desc = qwen_analyze(image_path)
    print(image_desc)
    print()

    # ---- 阶段 2：DeepSeek 深度推理 ----
    print("=" * 60)
    print("[2/3] DeepSeek 深度推理，生成技术方案...")
    print("=" * 60)
    plan = deepseek_reason(image_desc, user_need)
    print(plan)
    print()

    # 保存方案
    plan_file = BASE_DIR / "plan.md"
    with open(plan_file, "w", encoding="utf-8") as f:
        f.write(f"# 技术方案\n\n生成时间：{datetime.now()}\n\n---\n\n{plan}")
    print(f"方案已保存到: {plan_file}")

    # ---- 阶段 3：Claude Code 代码生成 ----
    if auto_code:
        print()
        print("=" * 60)
        print("[3/3] Claude Code 生成代码...")
        print("=" * 60)
        try:
            output_dir = invoke_claude_code(plan)
            elapsed = time.time() - start
            print(f"\n完成！耗时 {elapsed:.1f} 秒，代码目录: {output_dir}")
        except Exception as e:
            print(f"\n代码生成出错: {e}")
            print(f"你可以手动操作：在 Claude Code 中说 '根据 {plan_file} 生成代码'")
            elapsed = time.time() - start
    else:
        elapsed = time.time() - start
        print(f"\n方案生成完成！耗时 {elapsed:.1f} 秒")
        print("请将 plan.md 交给 Claude Code 继续生成代码")

    return plan


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python orchestrator.py <图片路径> [需求描述] [--no-code]")
        print()
        print("示例:")
        print('  python orchestrator.py ui.png "根据这个设计稿生成 React 组件"')
        print('  python orchestrator.py chart.png "分析图表数据生成 Python 分析脚本"')
        print('  python orchestrator.py screenshot.png --no-code')
        sys.exit(1)

    image = sys.argv[1]
    auto = "--no-code" not in sys.argv

    if len(sys.argv) >= 3 and sys.argv[2] != "--no-code":
        need = sys.argv[2]
    elif len(sys.argv) >= 4:
        need = sys.argv[3]
    else:
        need = "请根据这个图像内容生成对应的代码实现"

    run(image, need, auto_code=auto)
