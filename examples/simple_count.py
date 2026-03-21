#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单诊断 - 计数搜索结果
"""

from missav_api import Client

client = Client()

print("测试 search() 返回结果数量...")
print("=" * 70)

query = "鷲尾めい"
for video_count_param in [10, 50, 100, 500, 1000]:
    print(f"\n搜索: {query}, video_count={video_count_param}")
    
    search_results = client.search(query=query, video_count=video_count_param)
    
    actual_count = 0
    for video_summary in search_results:
        actual_count += 1
    
    print(f"  → 实际返回: {actual_count} 条")
    
    # 显示比例
    ratio = (actual_count / video_count_param) * 100
    print(f"  → 比例: {ratio:.1f}% (请求 {video_count_param}, 得到 {actual_count})")

print("\n" + "=" * 70)
print("总结: 如果实际返回远小于 video_count 参数值，")
print("可能说明:")
print("  1. video_count 是每页条数，需要分页")
print("  2. 某个关键词的结果本身就很少")
print("  3. API 有其他限制")
