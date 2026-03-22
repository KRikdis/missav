#!/usr/bin/env python
"""
小规模测试爬虫逻辑修复
限制为 100 个 M3U 条目（不是 100 个视频代码，因为每个视频可能产生多个条目）
"""
import sys
import os
sys.path.insert(0, '/workspaces/missav/src')

# 设置环保的日志级别
os.environ['LOG_LEVEL'] = 'INFO'

from missav_scraper import MissAVScraper

# 清除旧的状态并创建临时输出文件
from pathlib import Path
state_file = Path('/workspaces/missav/scraper_state.json')
if state_file.exists():
    state_file.unlink()
    print("✓ 已删除旧的 scraper_state.json\n")

# 创建爬虫实例，限制为 100 个条目
scraper = MissAVScraper(
    output_file='/tmp/test_missav.m3u',
    enable_checkpoint=True,
    max_videos=100,  # 限制为 100 个 M3U 条目
    verbose=False
)

# 运行爬虫
print("开始测试爬虫（最多 100 个条目）...")
print("=" * 70)
scraper.run()

# 检查输出文件
output_file = Path('/tmp/test_missav.m3u')
if output_file.exists():
    lines = output_file.read_text(encoding='utf-8').split('\n')
    extinf_count = sum(1 for line in lines if line.startswith('#EXTINF'))
    print(f"\n生成的 M3U 文件:")
    print(f"  路径: {output_file}")
    print(f"  文件大小: {output_file.stat().st_size} 字节")
    print(f"  条目数: {extinf_count}")
    print(f"  总行数: {len(lines)}")
else:
    print("\n✗ 未生成 M3U 文件")

# 检查状态文件
state_file = Path('/workspaces/missav/scraper_state.json')
if state_file.exists():
    import json
    state = json.loads(state_file.read_text(encoding='utf-8'))
    print(f"\n状态文件:")
    print(f"  已处理: {state.get('current_query_index', -1) + 1} 个演员")
    print(f"  视频总数: {len(state.get('videos', []))}")
    print(f"  下一个演员: {state.get('next_query', 'N/A')}")
else:
    print("\n✗ 未生成状态文件")

print("\n✓ 测试完成")
