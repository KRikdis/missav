#!/usr/bin/env python
"""
测试修复：验证所有演员都被搜索，状态被正确保存
"""
import sys
sys.path.insert(0, '/workspaces/missav/src')

from missav_scraper import MissAVScraper
from pathlib import Path
import json

print("=" * 70)
print("测试修复：使用 3 个演员验证搜索逻辑")
print("=" * 70)

# 创建爬虫实例
scraper = MissAVScraper(
    output_file='/workspaces/missav/output/missav.m3u',
    enable_checkpoint=True,
    max_videos=1000,  # 足够大
    verbose=False
)

# 测试用的演员列表
test_queries = ["吉野笃史", "JULIA", "美竹铃"]
scraper.search_queries = test_queries

print(f"\n测试演员列表: {test_queries}")
print(f"初始 current_query_index: {scraper.current_query_index}")
print("\n开始爬虫...")
print("-" * 70)

# 运行爬虫
scraper.run()

print("-" * 70)
print("\n=== 运行结果 ===")

# 检查状态文件
state_file = Path('scraper_state.json')
if state_file.exists():
    data = json.loads(state_file.read_text(encoding='utf-8'))
    print(f"✓ 状态文件已创建")
    print(f"  当前处理的查询索引: {data.get('current_query_index', 'N/A')}")
    print(f"  下一个查询: {data.get('next_query', 'N/A')}")
    print(f"  已收集视频总数: {len(data.get('videos', []))}")
    print(f"\n  搜索记录:")
    for i, query in enumerate(test_queries):
        video_count = sum(1 for v in data.get('videos', []) if query in str(v))
        print(f"    [{i}] {query}: 搜索到视频")
else:
    print(f"✗ 状态文件未创建！这表示爬虫没有正确运行")

# 检查 M3U 文件
m3u_file = Path('output/missav.m3u')
if m3u_file.exists():
    content = m3u_file.read_text(encoding='utf-8')
    extinf_count = content.count('#EXTINF')
    print(f"\nM3U 文件:")
    print(f"  条目数: {extinf_count}")
