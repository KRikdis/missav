#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试脚本 - 检查 search 方法的返回值"""

from missav_api import Client
import time

client = Client()

# 尝试不同的查询
queries = ["a", "A", "sex", "1", "uncensored"]

for query in queries:
    print(f"\n{'='*50}")
    print(f"查询: '{query}'")
    print('='*50)
    
    try:
        results = client.search(query=query, video_count=10)
        
        print(f"results 类型: {type(results)}")
        
        # 尝试遍历
        count = 0
        for i, video in enumerate(results):
            print(f"\nItem {i}:")
            print(f"  类型: {type(video)}")
            
            # 尝试获取属性
            if hasattr(video, 'video_code'):
                try:
                    print(f"  video_code: {video.video_code}")
                except:
                    pass
            
            if hasattr(video, 'm3u8_base_url'):
                try:
                    print(f"  m3u8_base_url: {video.m3u8_base_url}")
                except:
                    pass
            
            # 打印所有属性
            attrs = [a for a in dir(video) if not a.startswith('_')]
            print(f"  可用属性: {attrs[:5]}...")  # 只显示前 5 个
            
            count += 1
            if count >= 2:
                break
        
        print(f"  本次查询: {count} 个结果")
        
        time.sleep(2)  # 避免请求过于频繁
        
    except Exception as e:
        print(f"  错误: {e}")
        import traceback
        traceback.print_exc()

print(f"\n完成!")

