"""微信公众号草稿推送脚本"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

APP_ID = os.getenv("WECHAT_APP_ID", "")
APP_SECRET = os.getenv("WECHAT_APP_SECRET", "")
TOKEN_CACHE_FILE = Path(__file__).parent.parent / "data" / ".wechat_token_cache.json"

BASE_URL = "https://api.weixin.qq.com/cgi-bin"


def get_access_token() -> str:
    """获取 access_token，带缓存"""
    if TOKEN_CACHE_FILE.exists():
        cache = json.loads(TOKEN_CACHE_FILE.read_text(encoding="utf-8"))
        if cache.get("expires_at", 0) > time.time() + 60:
            return cache["token"]

    if not APP_ID or not APP_SECRET:
        raise ValueError("未配置 WECHAT_APP_ID / WECHAT_APP_SECRET，请在 .env 中填写")

    resp = httpx.get(
        f"{BASE_URL}/token",
        params={"grant_type": "client_credential", "appid": APP_ID, "secret": APP_SECRET},
        timeout=10,
    )
    data = resp.json()
    if "errcode" in data:
        raise RuntimeError(f"获取 token 失败: {data}")

    token = data["access_token"]
    expires_in = data.get("expires_in", 7200)
    TOKEN_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_CACHE_FILE.write_text(
        json.dumps({"token": token, "expires_at": time.time() + expires_in}),
        encoding="utf-8",
    )
    return token


def test_connection() -> None:
    """测试公众号连接"""
    try:
        token = get_access_token()
        resp = httpx.get(
            f"{BASE_URL}/get_current_autoreply_info",
            params={"access_token": token},
            timeout=10,
        )
        data = resp.json()
        if data.get("errcode", 0) == 0:
            print("连接成功")
        else:
            print(f"连接失败: {data}")
    except ValueError as e:
        print(f"配置错误: {e}")
    except Exception as e:
        print(f"连接异常: {e}")


def upload_thumb(image_path: str, token: str) -> str:
    """上传封面图，返回 media_id"""
    with open(image_path, "rb") as f:
        resp = httpx.post(
            f"https://api.weixin.qq.com/cgi-bin/media/upload",
            params={"access_token": token, "type": "thumb"},
            files={"media": f},
            timeout=30,
        )
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"上传封面失败: {data}")
    return data["media_id"]


def add_draft(title: str, content: str, thumb_media_id: str, token: str) -> str:
    """创建草稿，返回 media_id"""
    payload = {
        "articles": [{
            "title": title,
            "content": content,
            "thumb_media_id": thumb_media_id,
            "author": "",
            "digest": "",
            "show_cover_pic": 1,
            "need_open_comment": 0,
        }]
    }
    resp = httpx.post(
        f"{BASE_URL}/draft/add",
        params={"access_token": token},
        json=payload,
        timeout=30,
    )
    data = resp.json()
    if "media_id" not in data:
        raise RuntimeError(f"创建草稿失败: {data}")
    return data["media_id"]


def main():
    parser = argparse.ArgumentParser(description="推送文章到微信公众号草稿箱")
    parser.add_argument("--title", help="文章标题")
    parser.add_argument("--content-file", help="文章内容文件路径（HTML）")
    parser.add_argument("--cover", help="封面图路径（可选）")
    parser.add_argument("--test-connection", action="store_true", help="仅测试连接")
    args = parser.parse_args()

    if args.test_connection:
        test_connection()
        return

    if not args.title or not args.content_file:
        parser.error("--title 和 --content-file 为必填项")

    content = Path(args.content_file).read_text(encoding="utf-8")
    token = get_access_token()

    thumb_media_id = ""
    if args.cover:
        print(f"上传封面: {args.cover}")
        thumb_media_id = upload_thumb(args.cover, token)
    else:
        # 使用默认占位 media_id（需提前上传一张图）
        thumb_media_id = os.getenv("WECHAT_DEFAULT_THUMB_ID", "")
        if not thumb_media_id:
            print("警告: 未提供封面图且未设置 WECHAT_DEFAULT_THUMB_ID，草稿可能创建失败")

    media_id = add_draft(args.title, content, thumb_media_id, token)
    print(f"草稿已创建，media_id: {media_id}")


if __name__ == "__main__":
    main()
