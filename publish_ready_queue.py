# -*- coding: utf-8 -*-
"""
批量队列发布器

功能：
1. 扫描 drafts/queue/*/meta.json
2. 处理 status=ready 的文章，以及到达 schedule 时间的 status=scheduled 文章
3. 调用 publish_to_wechat.py --config ... --auto 推送到公众号草稿箱
4. 成功后将 meta.json 更新为 published，并记录 media_id / published_at
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from publish_to_wechat import append_publish_log


BASE_DIR = Path(__file__).parent
QUEUE_DIR = BASE_DIR / "drafts" / "queue"
PUBLISH_SCRIPT = BASE_DIR / "publish_to_wechat.py"


def load_meta(meta_path):
    with open(meta_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_meta(meta_path, data):
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def parse_schedule(schedule_str):
    """解析计划发布时间，格式：YYYY-MM-DD HH:MM 或 YYYY-MM-DD HH:MM:SS"""
    if not schedule_str:
        return None

    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(schedule_str, fmt)
        except ValueError:
            continue
    return None


def find_publishable_articles(queue_dir):
    publishable_items = []
    now = datetime.now()

    for meta_path in sorted(queue_dir.glob('*/meta.json')):
        if meta_path.parent.name.startswith('_'):
            continue
        try:
            meta = load_meta(meta_path)
        except Exception as e:
            print(f"[ERR] 读取 meta.json 失败: {meta_path} -> {e}")
            continue

        status = meta.get('status')
        schedule_value = meta.get('schedule')

        if status == 'ready':
            publishable_items.append((meta_path, meta))
            continue

        if status == 'scheduled':
            schedule_time = parse_schedule(schedule_value)
            if not schedule_time:
                print(f"[WARN] schedule 格式无效，跳过: {meta_path} -> {schedule_value}")
                continue
            if schedule_time <= now:
                publishable_items.append((meta_path, meta))
            else:
                print(f"[INFO] 未到发布时间，跳过: {meta.get('title', meta_path.parent.name)} -> {schedule_value}")

    return publishable_items


def extract_media_id(output_text):
    matches = re.findall(r'Media ID:\s*([\w\-]+)', output_text)
    if matches:
        return matches[-1]
    return None


def publish_one(meta_path):
    command = [
        sys.executable,
        str(PUBLISH_SCRIPT),
        '--config', str(meta_path),
        '--auto'
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    output = (result.stdout or '') + ('\n' + result.stderr if result.stderr else '')
    media_id = extract_media_id(output)
    success = result.returncode == 0 and media_id is not None

    return {
        'success': success,
        'media_id': media_id,
        'returncode': result.returncode,
        'output': output,
    }


def main():
    print('=' * 60)
    print('微信公众号批量队列发布器')
    print('=' * 60)
    print(f'队列目录: {QUEUE_DIR}')

    ready_items = find_publishable_articles(QUEUE_DIR)
    if not ready_items:
        print('[INFO] 没有可发布文章（ready 或已到时间的 scheduled），结束。')
        return

    print(f'[INFO] 待发布文章数: {len(ready_items)}')

    success_count = 0
    fail_count = 0

    for index, (meta_path, meta) in enumerate(ready_items, start=1):
        print('\n' + '-' * 60)
        print(f'[{index}/{len(ready_items)}] 发布: {meta.get("title", meta_path.parent.name)}')
        print(f'配置文件: {meta_path}')

        result = publish_one(meta_path)

        if result['success']:
            success_count += 1
            meta['status'] = 'published'
            meta['last_media_id'] = result['media_id']
            meta['published_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_meta(meta_path, meta)
            append_publish_log({
                'mode': 'queue',
                'status': 'success',
                'title': meta.get('title', meta_path.parent.name),
                'author': meta.get('author', ''),
                'digest': meta.get('digest', ''),
                'html': meta.get('html', ''),
                'cover': meta.get('cover', ''),
                'config_path': str(meta_path),
                'media_id': result['media_id'],
                'error': ''
            })
            print(f'[OK] 发布成功，Media ID: {result["media_id"]}')
        else:
            fail_count += 1
            meta['last_error_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            save_meta(meta_path, meta)
            append_publish_log({
                'mode': 'queue',
                'status': 'failed',
                'title': meta.get('title', meta_path.parent.name),
                'author': meta.get('author', ''),
                'digest': meta.get('digest', ''),
                'html': meta.get('html', ''),
                'cover': meta.get('cover', ''),
                'config_path': str(meta_path),
                'media_id': result.get('media_id', ''),
                'error': f"returncode={result['returncode']}"
            })
            print('[ERR] 发布失败')
            print(result['output'][-2000:])

    print('\n' + '=' * 60)
    print(f'[SUMMARY] 成功: {success_count} | 失败: {fail_count}')
    print('=' * 60)


if __name__ == '__main__':
    main()
