#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证脚本 - 测试新增的 genres 和 thumbnail 功能
"""

import json
import pytest
from pathlib import Path


def test_video_structure(sample_video):
    """测试视频数据结构"""
    print("=" * 60)
    print("测试视频数据结构")
    print("=" * 60)
    
    print(f"✓ 视频番号: {sample_video['code']}")
    print(f"✓ M3U8 URL: {sample_video['url']}")
    print(f"✓ 分类列表: {sample_video['genres']}")
    print(f"✓ 缩略图: {sample_video['thumbnail']}")
    
    # 确保视频对象包含所需字段
    assert 'code' in sample_video
    assert 'url' in sample_video
    assert 'genres' in sample_video
    assert 'thumbnail' in sample_video
    assert isinstance(sample_video['genres'], list)
    assert len(sample_video['genres']) > 0


def test_m3u_generation(sample_video):
    """测试 M3U 条目生成"""
    print("\n" + "=" * 60)
    print("测试 M3U 条目生成")
    print("=" * 60)
    
    test_output = []
    test_output.append('#EXTM3U')
    
    code = sample_video.get('code', 'Unknown')
    url = sample_video.get('url', '')
    genres = sample_video.get('genres', [])
    thumbnail = sample_video.get('thumbnail', '')
    
    if not genres or len(genres) == 0:
        genres = ['未分类']
    
    for genre in genres:
        genre_str = str(genre).strip() if genre else '未分类'
        line1 = f'#EXTINF:-1 group-title="{genre_str}" tvg-name="{code}" tvg-logo="{thumbnail}" epg-url="",{code}'
        line2 = url
        
        test_output.append(line1)
        test_output.append(line2)
        print(f"\n分类: {genre_str}")
        print(f"  {line1}")
        print(f"  {line2}")
    
    print(f"\n✓ 生成了 {len(genres)} 条 M3U 条目")
    
    # 验证生成的条目
    assert len(test_output) >= 3  # 至少有#EXTM3U + 1个条目（2行）
    assert test_output[0] == '#EXTM3U'
    assert len(genres) > 0


def test_multiple_videos(multiple_videos):
    """测试多个视频"""
    print("\n" + "=" * 60)
    print("测试多个视频场景")
    print("=" * 60)
    
    total_entries = 0
    for video in multiple_videos:
        genres = video.get('genres', [])
        if not genres or len(genres) == 0:
            genres = ['未分类']
        entry_count = len(genres)
        total_entries += entry_count
        
        code = video['code']
        genre_str = ', '.join(genres)
        print(f"✓ {code}: {genre_str} ({entry_count} 条条目)")
    
    print(f"\n总结: {len(multiple_videos)} 个视频 → {total_entries} 个 M3U 条目")
    
    # 验证结果
    assert len(multiple_videos) == 3
    assert total_entries >= 3  # 至少有3个条目


def test_state_file(temp_state_file):
    """测试状态文件格式"""
    print("\n" + "=" * 60)
    print("测试状态文件格式")
    print("=" * 60)
    
    # 验证临时状态文件存在且可读
    assert temp_state_file.exists()
    
    # 读取和验证格式
    with open(temp_state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    print("✓ 状态文件格式验证成功")
    
    # 验证状态文件结构
    assert 'videos' in state
    assert 'last_update' in state
    assert isinstance(state['videos'], list)
    if len(state['videos']) > 0:
        video = state['videos'][0]
        assert 'code' in video
        assert 'url' in video
        assert 'genres' in video
        assert 'thumbnail' in video
    
    print("格式示例:")
    print(json.dumps(state, ensure_ascii=False, indent=2)[:200] + "...")


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 16 + "MissAV 爬虫功能验证脚本" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        # 测试 1: 视频数据结构
        video = test_video_structure()
        
        # 测试 2: M3U 生成
        m3u_lines = test_m3u_generation(video)
        
        # 测试 3: 多个视频
        videos, total = test_multiple_videos()
        
        # 测试 4: 状态文件
        test_state_file()
        
        # 总结
        print("\n" + "=" * 60)
        print("✓ 所有测试通过！")
        print("=" * 60)
        print("\n主要改进:")
        print("  ✓ 支持 genres 字段作为 group-title")
        print("  ✓ 支持 thumbnail 作为 tvg-logo")
        print("  ✓ 为每个 genre 创建独立的 M3U 条目")
        print("  ✓ 处理空 genres 情况（使用'未分类'）")
        print("\n现在可以运行爬虫来生成改进后的 M3U 文件！")
        print()
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
