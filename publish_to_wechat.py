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
import requests
import json
import re
from pathlib import Path

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

    def upload_all_content_images(self, image_dir):
        """扫描并上传正文插图，返回 {filename: url} 映射"""
        image_dir = Path(image_dir)
        image_map = {}

        for i in range(1, 10):
            image_path = image_dir / f"illustration_{i}.jpg"
            if not image_path.exists():
                continue

            image_url = self.upload_content_image(image_path)
            if image_url:
                image_map[image_path.name] = image_url
            else:
                print(f"[WARN] 跳过未成功上传的正文图片: {image_path.name}")

        print(f"[OK] 正文图片上传完成，共成功 {len(image_map)} 张")
        return image_map

    def process_html_with_images(self, html_path, image_map):
        """读取 HTML 并将本地正文图片路径替换为微信图片 URL"""
        html_path = Path(html_path)
        html_content = html_path.read_text(encoding='utf-8')

        for filename, image_url in image_map.items():
            patterns = [
                rf'src="{re.escape(filename)}"',
                rf'src="\./{re.escape(filename)}"'
            ]
            for pattern in patterns:
                html_content = re.sub(pattern, f'src="{image_url}"', html_content)

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

def main():
    """主函数"""
    print("=" * 50)
    print("微信公众号文章推送工具")
    print("=" * 50)
    
    # 检查配置
    if not APPID or not APPSECRET:
        print("[ERR] 请在 .env 文件中配置 APPID 和 APPSECRET")
        return
    
    # 文件路径
    base_dir = Path(__file__).parent
    drafts_dir = base_dir / "drafts"
    cover_path = drafts_dir / "cover_five_dynasties.jpg"
    html_path = drafts_dir / "article_five_dynasties.html"
    
    # 检查文件
    if not cover_path.exists():
        print(f"[ERR] 封面图不存在: {cover_path}")
        return
    
    if not html_path.exists():
        print(f"[ERR] 文章HTML不存在: {html_path}")
        return
    
    print("\n文章信息:")
    print(f"  标题: 信任是场无限游戏，而我们都在透支未来")
    print(f"  作者: 深蓝")
    print(f"  封面: {cover_path}")
    raw_content = html_path.read_text(encoding='utf-8')
    print(f"  HTML: {html_path}")
    print(f"  字数: {len(raw_content)} 字符")
    
    # 确认推送 (自动模式跳过确认)
    auto_mode = '--auto' in sys.argv
    if not auto_mode:
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
    image_map = publisher.upload_all_content_images(drafts_dir)
    content = publisher.process_html_with_images(html_path, image_map)
    print(f"[OK] HTML 处理完成，成功替换 {len(image_map)} 张正文图片")
    
    # 添加草稿
    print("\n[4/4] 创建草稿...")
    draft_media_id = publisher.add_draft(
        title="房产行业，正在经历一场\"五代十国\"",
        content=content,
        thumb_media_id=thumb_media_id,
        author="深蓝",
        digest="从乱世到信用重建：五代十国的乱象正在房产行业重演，而宋朝的重建之路或许就是我们的出路。"
    )
    
    if draft_media_id:
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
        print("\n[ERR] 推送失败，请检查错误信息")

if __name__ == "__main__":
    main()
