"""千问 3.5-VL 图像理解模块"""

import base64
import io
import json
import sys
from pathlib import Path

import requests
from PIL import Image


MAX_IMAGE_KB = 150  # 超过此大小自动压缩
MAX_DIMENSION = 1920  # 最大边长（像素）


def load_config():
    cfg_path = Path(__file__).parent / "config.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compress_image(image_path: str) -> bytes:
    """压缩图片：缩小尺寸、降低质量，返回 PNG 字节"""
    img = Image.open(image_path)
    original_size = Path(image_path).stat().st_size

    # 如果图片已经很小，不做压缩
    if original_size < MAX_IMAGE_KB * 1024:
        with open(image_path, "rb") as f:
            return f.read()

    # 如果原始是 RGBA，转 RGB（减少体积）
    if img.mode in ("RGBA", "P"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = background

    # 缩放大图
    w, h = img.size
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        ratio = min(MAX_DIMENSION / w, MAX_DIMENSION / h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75, optimize=True)
    compressed = buf.getvalue()

    print(f"  图片压缩: {original_size//1024}KB → {len(compressed)//1024}KB")
    return compressed


def encode_image(image_path: str) -> str:
    """读取图片并转为 base64"""
    data = compress_image(image_path)
    return base64.b64encode(data).decode("utf-8")


def get_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".webp": "image/webp",
                ".gif": "image/gif", ".bmp": "image/bmp"}
    mime = mime_map.get(ext, "image/png")
    # 压缩后统一用 JPEG mime
    if Path(image_path).stat().st_size > MAX_IMAGE_KB * 1024:
        mime = "image/jpeg"
    return mime


def analyze(image_path: str, prompt: str = None) -> str:
    """
    调用千问 3.5-VL 分析图像
    :param image_path: 图片文件路径
    :param prompt: 自定义提示词，默认为详细描述
    :return: 图像描述文本
    """
    config = load_config()
    api_key = config["qwen"]["api_key"]
    model = config["qwen"]["model"]

    if prompt is None:
        prompt = (
            "请详细描述这张图片中的所有内容，包括：\n"
            "1. UI 元素（按钮、输入框、菜单、图标等）\n"
            "2. 文字内容（逐条列出所有可见文字）\n"
            "3. 布局结构（元素的排列方式和层级关系）\n"
            "4. 颜色和样式（主题色、字号、间距等）\n"
            "5. 交互状态（高亮、选中、禁用等）"
        )

    img_b64 = encode_image(image_path)
    mime = get_mime_type(image_path)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url",
                 "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                {"type": "text", "text": prompt}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 4096
    }

    resp = requests.post(config["qwen"]["api_url"],
                         json=payload, headers=headers, timeout=120)
    resp.raise_for_status()

    result = resp.json()
    return result["choices"][0]["message"]["content"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python qwen_vision.py <图片路径> [自定义提示]")
        sys.exit(1)

    image = sys.argv[1]
    custom_prompt = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        description = analyze(image, custom_prompt)
        print(description)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)
