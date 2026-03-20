# -*- coding: utf-8 -*-
"""
微信公众号文章推送脚本
使用前请确保：
1. 已安装依赖: pip install wechatpy requests
2. 已配置 .env 文件中的 AppID 和 AppSecret
3. 封面图和文章HTML已准备好
"""

import os
import sys
import argparse
import requests
import json
import re
from pathlib import Path
from datetime import datetime

# 读取环境变量
from dotenv import load_dotenv
load_dotenv()

APPID = os.getenv('APPID', 'wx136c36b5d8a7d3bc')
APPSECRET = os.getenv('APPSECRET', 'cbfa6c8502e20e0e5dd935d5f7e2e80a')

class WeChatPublisher:
    def __init__(self, appid, appsecret):
        self.appid = appid
        self.appsecret = appsecret
        self.access_token = None
        
    def get_access_token(self):
        """获取微信access_token"""
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.appid}&secret={self.appsecret}"
        try:
            response = requests.get(url, timeout=30)
            data = response.json()
            if 'access_token' in data:
                self.access_token = data['access_token']
                print("[OK] Access token获取成功")
                return True
            else:
                print(f"[ERR] 获取token失败: {data}")
                return False
        except Exception as e:
            print(f"[ERR] 网络错误: {e}")
            return False
    
    def upload_image(self, image_path):
        """上传封面图片到微信服务器"""
        if not self.access_token:
            print("[ERR] 未获取access_token")
            return None
            
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={self.access_token}&type=image"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=60)
                data = response.json()
                
                if 'media_id' in data:
                    print(f"[OK] 图片上传成功: {data['media_id']}")
                    return data['media_id']
                elif 'url' in data:
                    print(f"[OK] 图片上传成功: {data['url']}")
                    return data['url']
                else:
                    print(f"[ERR] 图片上传失败: {data}")
                    return None
        except Exception as e:
            print(f"[ERR] 上传错误: {e}")
            return None
    
    def upload_material(self, image_path):
        """上传永久素材（用于封面图）"""
        if not self.access_token:
            print("[ERR] 未获取access_token")
            return None
            
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={self.access_token}&type=image"
        
        try:
            with open(image_path, 'rb') as f:
                files = {'media': f}
                response = requests.post(url, files=files, timeout=60)
                data = response.json()
                
                if 'media_id' in data:
                    print("[OK] 封面素材上传成功")
                    return data['media_id']
                else:
                    print(f"[ERR] 封面上传失败: {data}")
                    return None
        except Exception as e:
            print(f"[ERR] 上传错误: {e}")
            return None

    def upload_content_image(self, image_path):
        """上传正文图片，返回微信可用的图片 URL"""
        if not self.access_token:
            print("[ERR] 未获取access_token")
            return None

        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={self.access_token}"
        image_path = Path(image_path)

        try:
            with open(image_path, 'rb') as f:
                files = {'media': (image_path.name, f, 'image/jpeg')}
                response = requests.post(url, files=files, timeout=60)
                data = response.json()

                if 'url' in data:
                    print(f"[OK] 正文图片上传成功: {image_path.name} -> {data['url']}")
                    return data['url']

                print(f"[ERR] 正文图片上传失败 {image_path.name}: {data}")
                return None
        except Exception as e:
            print(f"[ERR] 正文图片上传错误 {image_path.name}: {e}")
            return None

    def extract_local_image_sources(self, html_content, html_path, cover_path=None):
        """从 HTML 中提取本地图片 src，跳过远程 URL、data URI 和封面图"""
        html_path = Path(html_path)
        cover_path = Path(cover_path).resolve() if cover_path else None
        src_list = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_content, flags=re.IGNORECASE)

        local_images = []
        seen = set()

        for src in src_list:
            src = src.strip()
            if not src or src.startswith(('http://', 'https://', 'data:')):
                continue

            image_path = (html_path.parent / src).resolve()
            if cover_path and image_path == cover_path:
                continue
            if not image_path.exists() or not image_path.is_file():
                print(f"[WARN] HTML 引用的图片不存在，跳过: {src}")
                continue
            if src in seen:
                continue

            seen.add(src)
            local_images.append((src, image_path))

        return local_images

    def upload_all_content_images(self, html_path, cover_path=None):
        """根据 HTML 实际引用上传正文图片，返回 {original_src: url} 映射"""
        html_path = Path(html_path)
        html_content = html_path.read_text(encoding='utf-8')
        image_map = {}

        local_images = self.extract_local_image_sources(html_content, html_path, cover_path)

        for original_src, image_path in local_images:
            image_url = self.upload_content_image(image_path)
            if image_url:
                image_map[original_src] = image_url
            else:
                print(f"[WARN] 跳过未成功上传的正文图片: {original_src}")

        print(f"[OK] 正文图片上传完成，共成功 {len(image_map)} 张")
        return image_map

    def process_html_with_images(self, html_path, image_map):
        """读取 HTML 并将本地正文图片路径替换为微信图片 URL"""
        html_path = Path(html_path)
        html_content = html_path.read_text(encoding='utf-8')

        for original_src, image_url in image_map.items():
            html_content = re.sub(
                rf'(<img[^>]+src=["\']){re.escape(original_src)}(["\'])',
                rf'\1{image_url}\2',
                html_content,
                flags=re.IGNORECASE
            )

        return html_content
    
    def add_draft(self, title, content, thumb_media_id, author="深蓝", digest=""):
        """添加草稿到公众号"""
        if not self.access_token:
            print("[ERR] 未获取access_token")
            return None
        
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={self.access_token}"
        
        articles = {
            "articles": [
                {
                    "title": title,
                    "content": content,
                    "thumb_media_id": thumb_media_id,
                    "author": author,
                    "digest": digest,
                    "show_cover_pic": 1,
                    "content_source_url": "",
                    "need_open_comment": 1,
                    "only_fans_can_comment": 0
                }
            ]
        }
        
        try:
            response = requests.post(
                url, 
                data=json.dumps(articles, ensure_ascii=False).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            data = response.json()
            
            if 'media_id' in data:
                print("[OK] 草稿创建成功!")
                print(f"  Media ID: {data['media_id']}")
                return data['media_id']
            else:
                print(f"[ERR] 草稿创建失败: {data}")
                return None
        except Exception as e:
            print(f"[ERR] 请求错误: {e}")
            return None

def parse_args():
    """解析命令行参数"""
    base_dir = Path(__file__).parent
    drafts_dir = base_dir / "drafts"

    parser = argparse.ArgumentParser(description="微信公众号文章推送工具")
    parser.add_argument("--config", help="meta.json 配置文件路径")
    parser.add_argument("--title", default="房产行业最危险的，不是卖不动了，而是没人再信了", help="文章标题")
    parser.add_argument("--html", default=str(drafts_dir / "article_five_dynasties.html"), help="HTML 文件路径")
    parser.add_argument("--cover", default=str(drafts_dir / "cover_five_dynasties.jpg"), help="封面图路径")
    parser.add_argument("--author", default="深蓝", help="作者")
    parser.add_argument("--digest", default="房产行业真正危险的，不是成交变难，而是信任地基正在流失。五代十国的乱世逻辑，正在倒逼行业进入信用重建时刻。", help="文章摘要")
    parser.add_argument("--auto", action="store_true", help="自动模式，跳过确认")
    return parser.parse_args()


def load_config(config_path):
    """读取 meta.json 配置，并按配置文件目录解析相对路径"""
    config_path = Path(config_path).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    config_dir = config_path.parent
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    def resolve_config_path(value):
        path = Path(value)
        if path.is_absolute():
            return str(path.resolve())
        return str((config_dir / path).resolve())

    if 'html' in config:
        config['html'] = resolve_config_path(config['html'])
    if 'cover' in config:
        config['cover'] = resolve_config_path(config['cover'])

    config['_config_path'] = str(config_path)
    return config


def append_publish_log(entry):
    """追加发布日志到 JSONL 和 CSV"""
    base_dir = Path(__file__).parent
    log_jsonl = base_dir / 'publish_log.jsonl'
    log_csv = base_dir / 'publish_log.csv'

    entry = dict(entry)
    entry.setdefault('logged_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    with open(log_jsonl, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    csv_headers = [
        'logged_at', 'mode', 'status', 'title', 'author', 'digest',
        'html', 'cover', 'config_path', 'media_id', 'error'
    ]

    if not log_csv.exists():
        with open(log_csv, 'w', encoding='utf-8', newline='') as f:
            f.write(','.join(csv_headers) + '\n')

    def csv_escape(value):
        text = '' if value is None else str(value)
        text = text.replace('"', '""')
        return f'"{text}"'

    row = [csv_escape(entry.get(header, '')) for header in csv_headers]
    with open(log_csv, 'a', encoding='utf-8', newline='') as f:
        f.write(','.join(row) + '\n')


def main():
    """主函数"""
    print("=" * 50)
    print("微信公众号文章推送工具")
    print("=" * 50)

    args = parse_args()
    config_path = None

    if args.config:
        try:
            config = load_config(args.config)
            config_path = config.get('_config_path')
            args.title = config.get('title', args.title)
            args.html = config.get('html', args.html)
            args.cover = config.get('cover', args.cover)
            args.author = config.get('author', args.author)
            args.digest = config.get('digest', args.digest)
        except Exception as e:
            print(f"[ERR] 读取配置失败: {e}")
            append_publish_log({
                'mode': 'single',
                'status': 'failed',
                'title': args.title,
                'author': args.author,
                'digest': args.digest,
                'html': args.html,
                'cover': args.cover,
                'config_path': args.config,
                'media_id': '',
                'error': f'读取配置失败: {e}'
            })
            return

    # 检查配置
    if not APPID or not APPSECRET:
        print("[ERR] 请在 .env 文件中配置 APPID 和 APPSECRET")
        return

    html_path = Path(args.html).expanduser().resolve()
    cover_path = Path(args.cover).expanduser().resolve()
    drafts_dir = html_path.parent

    # 检查文件
    if not cover_path.exists():
        print(f"[ERR] 封面图不存在: {cover_path}")
        return

    if not html_path.exists():
        print(f"[ERR] 文章HTML不存在: {html_path}")
        return

    print("\n文章信息:")
    print(f"  标题: {args.title}")
    print(f"  作者: {args.author}")
    print(f"  封面: {cover_path}")
    raw_content = html_path.read_text(encoding='utf-8')
    print(f"  HTML: {html_path}")
    print(f"  字数: {len(raw_content)} 字符")

    # 确认推送 (自动模式跳过确认)
    if not args.auto:
        confirm = input("\n确认推送到公众号草稿箱? (yes/no): ")
        if confirm.lower() != 'yes':
            print("已取消")
            return
    else:
        print("\n[自动模式] 直接推送...")

    # 初始化发布器
    publisher = WeChatPublisher(APPID, APPSECRET)

    # 获取access_token
    print("\n[1/4] 获取Access Token...")
    if not publisher.get_access_token():
        return

    # 上传封面图
    print("\n[2/4] 上传封面图...")
    thumb_media_id = publisher.upload_material(str(cover_path))
    if not thumb_media_id:
        print("[ERR] 封面上传失败，无法继续")
        return

    # 上传正文图片并处理 HTML
    print("\n[3/4] 上传正文图片并处理 HTML...")
    image_map = publisher.upload_all_content_images(html_path, cover_path)
    content = publisher.process_html_with_images(html_path, image_map)
    print(f"[OK] HTML 处理完成，成功替换 {len(image_map)} 张正文图片")

    # 添加草稿
    print("\n[4/4] 创建草稿...")
    draft_media_id = publisher.add_draft(
        title=args.title,
        content=content,
        thumb_media_id=thumb_media_id,
        author=args.author,
        digest=args.digest
    )

    if draft_media_id:
        append_publish_log({
            'mode': 'single',
            'status': 'success',
            'title': args.title,
            'author': args.author,
            'digest': args.digest,
            'html': str(html_path),
            'cover': str(cover_path),
            'config_path': config_path or '',
            'media_id': draft_media_id,
            'error': ''
        })
        print("\n" + "=" * 50)
        print("[OK] 推送成功!")
        print(f"[OK] 新草稿 Media ID: {draft_media_id}")
        print("=" * 50)
        print("\n请前往公众号后台查看:")
        print("  1. 登录 https://mp.weixin.qq.com")
        print("  2. 内容管理 - 草稿箱")
        print("  3. 找到文章并预览")
        print("  4. 确认无误后群发")
    else:
        append_publish_log({
            'mode': 'single',
            'status': 'failed',
            'title': args.title,
            'author': args.author,
            'digest': args.digest,
            'html': str(html_path),
            'cover': str(cover_path),
            'config_path': config_path or '',
            'media_id': '',
            'error': '草稿创建失败'
        })
        print("\n[ERR] 推送失败，请检查错误信息")

if __name__ == "__main__":
    main()
