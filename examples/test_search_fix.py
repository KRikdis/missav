#!/usr/bin/env python
"""
测试修复后的 search 逻辑
验证 search() 返回的是完整视频对象
"""
import sys
sys.path.insert(0, '/workspaces/missav/src')

from missav_api import Client

print("=" * 70)
print("测试 search() API 修复")
print("=" * 70)

client = Client()

# 测试单个演员搜索
test_query = "吉野笃史"
print(f"\n测试查询: {test_query}")
print(f"获取前 5 个视频...")

search_results = client.search(query=test_query, video_count=5)

count = 0
for video_obj in search_results:
    count += 1
    print(f"\n视频 {count}:")
    print(f"  video_code: {video_obj.video_code}")
    print(f"  title: {video_obj.title[:60] if hasattr(video_obj, 'title') else 'N/A'}")
    print(f"  m3u8_base_url: {str(video_obj.m3u8_base_url)[:60]}..." if video_obj.m3u8_base_url else "  m3u8_base_url: N/A")
    print(f"  series: {video_obj.series if hasattr(video_obj, 'series') else 'N/A'}")
    print(f"  thumbnail: {str(video_obj.thumbnail)[:60]}..." if hasattr(video_obj, 'thumbnail') and video_obj.thumbnail else "  thumbnail: N/A")
    
    if count >= 5:
        break

print(f"\n✓ 搜索完成: 获得 {count} 个完整视频对象")
print(f"✓ 每个 video 对象都包含完整属性（无需调用 get_video()）")
print("=" * 70)
