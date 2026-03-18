from PIL import Image, ImageDraw, ImageFont
import os

def create_cover(title, subtitle, output_path):
    """生成公众号封面图 - 900x383 像素"""
    
    # 创建渐变背景
    width, height = 900, 383
    img = Image.new('RGB', (width, height), color='#1a237e')
    draw = ImageDraw.Draw(img)
    
    # 绘制渐变效果（模拟）
    for y in range(height):
        r = int(26 + (57-26) * y / height)
        g = int(35 + (73-35) * y / height)
        b = int(126 + (171-126) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # 添加装饰线条
    draw.line([(50, 300), (850, 300)], fill='#ffd700', width=3)
    
    # 尝试加载字体，如果没有则使用默认
    try:
        # Windows系统字体
        font_title = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 48)
        font_subtitle = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
    except:
        try:
            font_title = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 48)
            font_subtitle = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 24)
        except:
            font_title = ImageFont.load_default()
            font_subtitle = ImageFont.load_default()
    
    # 绘制标题
    title = "信任是场无限游戏"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = bbox[2] - bbox[0]
    title_x = (width - title_width) // 2
    draw.text((title_x, 120), title, font=font_title, fill='white')
    
    # 绘制副标题
    subtitle = "从学术期刊300年演化史说起"
    bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_width = bbox[2] - bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    draw.text((subtitle_x, 200), subtitle, font=font_subtitle, fill='#e0e0e0')
    
    # 添加装饰元素 - 时间轴示意
    years = ["1665", "1869", "1955", "2024"]
    x_positions = [150, 350, 550, 750]
    for i, (year, x) in enumerate(zip(years, x_positions)):
        draw.ellipse([x-5, 330, x+5, 340], fill='#ffd700')
        draw.text((x-20, 350), year, font=font_subtitle, fill='#ffd700')
        if i < len(years) - 1:
            draw.line([(x+5, 335), (x_positions[i+1]-5, 335)], fill='#ffd700', width=2)
    
    # 保存
    img.save(output_path, quality=95)
    print(f"Cover generated: {output_path}")
    return output_path

def create_illustration_1(output_path):
    """插图1: 学术出版商垄断示意图"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='#f5f5f5')
    draw = ImageDraw.Draw(img)
    
    # 三大出版商
    companies = [
        ("RELX/Elsevier", "37%利润率", "#d32f2f"),
        ("Springer Nature", "德国巨头", "#1976d2"),
        ("Wiley", "美国老牌", "#388e3c")
    ]
    
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 32)
        font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 20)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 绘制三个方块
    positions = [(100, 200), (300, 200), (500, 200)]
    for (name, desc, color), (x, y) in zip(companies, positions):
        draw.rectangle([x, y, x+180, y+200], fill=color, outline='white', width=3)
        draw.text((x+90, y+80), name, font=font, fill='white', anchor='mm')
        draw.text((x+90, y+130), desc, font=font_small, fill='white', anchor='mm')
    
    # 标题
    draw.text((400, 100), "全球学术出版三巨头", font=font, fill='#333', anchor='mm')
    draw.text((400, 450), "垄断全球50%+学术文献出版", font=font_small, fill='#666', anchor='mm')
    
    img.save(output_path, quality=95)
    print(f"Illustration 1 generated: {output_path}")

def create_illustration_2(output_path):
    """插图2: 学术期刊演化时间轴"""
    width, height = 1000, 400
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 24)
        font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 16)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 时间轴主线
    draw.line([(100, 200), (900, 200)], fill='#1a237e', width=4)
    
    # 关键节点
    events = [
        (1665, "《哲学汇刊》创刊", "无审稿制度"),
        (1869, "《自然》杂志创办", "吵架利器→学术门槛"),
        (1955, "影响因子诞生", "科学变刷分游戏"),
        (2024, "今天的困境", "格式暴政+指标焦虑")
    ]
    
    x_positions = [150, 350, 550, 750]
    for (year, title, desc), x in zip(events, x_positions):
        # 节点圆圈
        draw.ellipse([x-10, 190, x+10, 210], fill='#ffd700', outline='#1a237e', width=3)
        
        # 年份
        draw.text((x, 160), str(year), font=font, fill='#1a237e', anchor='mm')
        
        # 标题和描述
        if x < 500:
            draw.text((x, 240), title, font=font_small, fill='#333', anchor='mm')
            draw.text((x, 265), desc, font=font_small, fill='#666', anchor='mm')
        else:
            draw.text((x, 140), title, font=font_small, fill='#333', anchor='mm')
            draw.text((x, 115), desc, font=font_small, fill='#666', anchor='mm')
    
    # 主标题
    draw.text((500, 50), "学术期刊300年演化史", font=font, fill='#1a237e', anchor='mm')
    
    img.save(output_path, quality=95)
    print(f"Illustration 2 generated: {output_path}")

def create_illustration_3(output_path):
    """插图3: 信用复利 vs 违约归零"""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 32)
        font_small = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 24)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 左侧：信用复利（绿色上升曲线）
    draw.text((200, 80), "信用复利", font=font, fill='#2e7d32', anchor='mm')
    
    # 绘制上升曲线
    points = [(100, 400)]
    for i in range(1, 11):
        y = 400 - (i ** 1.5) * 8
        points.append((100 + i * 25, int(y)))
    
    for i in range(len(points)-1):
        draw.line([points[i], points[i+1]], fill='#4caf50', width=4)
    
    draw.text((200, 450), "100次履约 → 指数增长", font=font_small, fill='#2e7d32', anchor='mm')
    
    # 右侧：违约归零（红色断崖）
    draw.text((600, 80), "一次违约", font=font, fill='#c62828', anchor='mm')
    
    # 绘制断崖
    draw.line([(500, 150), (500, 380)], fill='#f44336', width=4)
    draw.line([(500, 380), (700, 380)], fill='#f44336', width=4)
    draw.polygon([(680, 360), (700, 380), (680, 400)], fill='#f44336')
    
    draw.text((600, 450), "指数归零", font=font_small, fill='#c62828', anchor='mm')
    
    # 中间分隔线
    draw.line([(400, 100), (400, 500)], fill='#ddd', width=2)
    
    # 底部金句
    draw.text((400, 550), "100次履约建立的信任，1次违约就能归零", 
              font=font_small, fill='#1a237e', anchor='mm')
    
    img.save(output_path, quality=95)
    print(f"Illustration 3 generated: {output_path}")

if __name__ == "__main__":
    import sys
    
    # 确保输出目录存在
    os.makedirs("drafts", exist_ok=True)
    
    # 生成封面
    create_cover("信任是场无限游戏", "从学术期刊300年演化史说起", "drafts/cover_final.jpg")
    
    # 生成插图
    create_illustration_1("drafts/illustration_1_publishers.jpg")
    create_illustration_2("drafts/illustration_2_timeline.jpg")
    create_illustration_3("drafts/illustration_3_trust.jpg")
    
    print("\nAll images generated!")
    print("Location: drafts/")
