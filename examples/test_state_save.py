#!/usr/bin/env python
"""
测试爬虫，限制为 5 个演员，观察状态保存情况
"""
import sys
import os
sys.path.insert(0, '/workspaces/missav/src')

# 设置日志级别以查看详细信息
os.environ['LOG_LEVEL'] = 'INFO'

from missav_scraper import MissAVScraper
from pathlib import Path
import json

print("=" * 70)
print("爬虫测试：限制 5 个演员，观察状态保存")
print("=" * 70)

# 创建爬虫实例，限制为 500 个条目让爬虫充分运行
scraper = MissAVScraper(
    output_file='/workspaces/missav/output/missav.m3u',
    enable_checkpoint=True,
    max_videos=500,  # 足够大让爬虫运行多个演员
    verbose=False
)

# 修改搜索列表为只有 5 个演员（用于测试）
original_queries = scraper.search_queries
test_queries = ["吉野笃史", "JULIA", "美竹铃", "樱ゆの", "つボみ"]
scraper.search_queries = test_queries
print(f"\n测试查询列表: {test_queries}")

# 运行爬虫
print("\n开始爬虫...")
print("-" * 70)
scraper.run()
print("-" * 70)

# 检查状态文件
state_file = Path('scraper_state.json')
m3u_file = Path('output/missav.m3u')

print("\n=== 运行结果 ===")
if state_file.exists():
    data = json.loads(state_file.read_text(encoding='utf-8'))
    print(f"✓ 状态文件已创建")
    print(f"  当前处理的查询索引: {data.get('current_query_index', 'N/A')}")
    print(f"  下一个查询: {data.get('next_query', 'N/A')}")
    print(f"  已收集视频条目数: {len(data.get('videos', []))}")
else:
    print(f"✗ 状态文件未创建！")

if m3u_file.exists():
    content = m3u_file.read_text(encoding='utf-8')
    extinf_count = content.count('#EXTINF')
    print(f"\nM3U 文件:")
    print(f"  条目数: {extinf_count}")
    print(f"  文件大小: {m3u_file.stat().st_size:,} 字节")
