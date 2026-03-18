"""封面图生成脚本 - 使用PIL生成文字封面"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """查找可用的中文字体"""
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "C:/Windows/Fonts/arial.ttf",   # Arial (fallback)
    ]
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """按宽度折行"""
    lines = []
    current = ""
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def create_cover(title: str, subtitle: str, output: str, width: int = 900, height: int = 500) -> None:
    img = Image.new("RGB", (width, height), color=(30, 30, 50))
    draw = ImageDraw.Draw(img)

    # 渐变背景色块
    for i in range(height):
        r = int(30 + (60 - 30) * i / height)
        g = int(30 + (40 - 30) * i / height)
        b = int(50 + (80 - 50) * i / height)
        draw.line([(0, i), (width, i)], fill=(r, g, b))

    # 装饰线
    draw.rectangle([40, 40, width - 40, height - 40], outline=(100, 150, 255), width=2)
    draw.line([(60, 80), (width - 60, 80)], fill=(100, 150, 255), width=1)

    padding = 80
    max_w = width - padding * 2

    # 标题
    title_font = find_font(48)
    title_lines = wrap_text(title, title_font, max_w, draw)
    y = height // 2 - len(title_lines) * 60 // 2 - 30
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=title_font, fill=(255, 255, 255))
        y += 60

    # 副标题
    if subtitle:
        sub_font = find_font(28)
        sub_lines = wrap_text(subtitle, sub_font, max_w, draw)
        y += 20
        for line in sub_lines:
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            x = (width - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=sub_font, fill=(180, 200, 255))
            y += 40

    img.save(output)
    print(f"封面已生成: {output}")


def main():
    parser = argparse.ArgumentParser(description="生成公众号封面图")
    parser.add_argument("--title", required=True, help="标题")
    parser.add_argument("--subtitle", default="", help="副标题")
    parser.add_argument("--output", default="cover.jpg", help="输出文件路径")
    parser.add_argument("--width", type=int, default=900, help="宽度")
    parser.add_argument("--height", type=int, default=500, help="高度")
    args = parser.parse_args()

    create_cover(args.title, args.subtitle, args.output, args.width, args.height)


if __name__ == "__main__":
    main()
