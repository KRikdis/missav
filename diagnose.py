#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速诊断脚本 - 检查 API 是否被限流"""

from missav_api import Client
import time

print("="*50)
print("MissAV API 诊断工具")
print("="*50)

client = Client()

# 测试 1：简单搜索
print("\n[测试1] 单个查询 - 查询 'a':")
print("-" * 50)
start = time.time()
try:
    results = client.search(query="a", video_count=5)
    count = 0
    
    for video in results:
        print(f"  第 {count+1} 个视频: {video.video_code}")
        count += 1
        if count >= 1:  # 只显示第一个
            break
    
    elapsed = time.time() - start
    print(f"✓ 查询成功！耗时: {elapsed:.2f}秒")
    print(f"✓ 获取到: {count} 个视频")
    
except Exception as e:
    print(f"✗ 查询失败: {e}")
    elapsed = time.time() - start
    print(f"✗ 耗时: {elapsed:.2f}秒")

# 测试 2：检查网络连接
print("\n[测试2] 网络连接检查:")
print("-" * 50)

import requests
try:
    resp = requests.get("https://missav.ws/en/", timeout=5)
    print(f"✓ 网站可访问: {resp.status_code}")
except Exception as e:
    print(f"✗ 网站无法访问: {e}")

# 测试 3：查看 API 返回的原始信息
print("\n[测试3] API 响应信息:")
print("-" * 50)
try:
    results = client.search(query="test", video_count=1)
    for video in results:
        print(f"✓ Video 对象: {type(video)}")
        print(f"✓ video_code: {video.video_code}")
        print(f"✓ m3u8_base_url: {video.m3u8_base_url[:60]}...")
        break
except Exception as e:
    print(f"✗ 获取失败: {e}")

print("\n" + "="*50)
print("诊断完成")
print("="*50)
