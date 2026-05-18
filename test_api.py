"""快速测试千问 API 连通性"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from qwen_vision import analyze

# 准备一张测试截图放在项目目录下，命名为 test_screenshot.png
# 或者修改下面的路径
image_path = str(Path(__file__).parent / "test_screenshot.png")

start = time.time()
try:
    result = analyze(image_path,
                     "简要描述这张截图中有什么内容，控制在200字以内")
    elapsed = time.time() - start
    print(f"\n耗时 {elapsed:.1f} 秒")
    print(f"结果:\n{result}")
except Exception as e:
    elapsed = time.time() - start
    print(f"失败: {e} (耗时 {elapsed:.1f}s)")
