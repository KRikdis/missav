#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试 missav_api 的使用方法"""

from missav_api import Client

client = Client()

# 尝试不同的查询方式
queries = ["", " ", "recent", "2024-01", "latest"]

for query in queries:
    print(f"=== 尝试查询: '{query}' ===")
    try:
        results = list(client.search(query=query, video_count=3))
        print(f"获取了 {len(results)} 个视频\n")
        
        if results:
            video = results[0]
            print(f"第一个视频: {video}")
            print(f"类型: {type(video)}")
            print(f"属性: {video.__dict__}\n")
            break
        
    except Exception as e:
        print(f"错误: {e}\n")

# 如果没有获取到任何视频，尝试 iterator 方法
print("\n=== 尝试使用 iterator 方法 ===")
try:
    iterator = client.iterator()
    count = 0
    for video in iterator:
        print(f"视频 {count}: {video}")
        print(f"属性: {video.__dict__}")
        count += 1
        if count >= 3:
            break
except Exception as e:
    print(f"iterator 方法错误: {e}")
    import traceback
    traceback.print_exc()
