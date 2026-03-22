#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
去重逻辑测试

测试 scraper 的去重机制是否正常工作
"""

import json
import tempfile
from pathlib import Path
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from missav_scraper import MissAVScraper
from missav_scraper import constants


class MockVideoObject:
    """模拟视频对象"""
    def __init__(self, video_code, m3u8_url, series, thumbnail=""):
        self.video_code = video_code
        self.m3u8_base_url = m3u8_url
        self.series = series
        self.thumbnail = thumbnail


def test_deduplication_same_series_different_url():
    """
    测试1: 同一个 series 但不同 URL 不应该被去重
    """
    print("\n" + "=" * 70)
    print("测试1: 同一个 series，不同 URL - 不应该被去重")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.m3u")
        state_file = os.path.join(tmpdir, "state.json")
        
        # 临时修改常量
        original_state_file = constants.STATE_FILE
        original_output_file = constants.OUTPUT_FILE
        original_output_dir = constants.OUTPUT_DIR
        
        try:
            # 创建爬虫实例
            scraper = MissAVScraper(
                output_file=output_file,
                enable_checkpoint=False,
                max_videos=1000,
                verbose=False
            )
            
            # 创建模拟视频对象
            video1 = MockVideoObject(
                video_code="TEST-001",
                m3u8_url="https://example.com/video1.m3u8",
                series=["演员A"],
                thumbnail="https://example.com/thumb1.jpg"
            )
            
            video2 = MockVideoObject(
                video_code="TEST-002",
                m3u8_url="https://example.com/video2.m3u8",  # 不同URL
                series=["演员A"],  # 相同series
                thumbnail="https://example.com/thumb2.jpg"
            )
            
            # 处理第一个视频
            entries1 = scraper._process_video_object(video1, "actor_search")
            print(f"✓ 处理视频1: 新增 {entries1} 个条目")
            
            # 处理第二个视频
            entries2 = scraper._process_video_object(video2, "actor_search")
            print(f"✓ 处理视频2: 新增 {entries2} 个条目")
            
            # 验证结果
            assert entries1 == 1, f"视频1应该新增1个条目，实际: {entries1}"
            assert entries2 == 1, f"视频2应该新增1个条目，实际: {entries2}"
            assert len(scraper.videos) == 2, f"应该有2个视频条目，实际: {len(scraper.videos)}"
            
            print(f"✅ 测试1通过: 同一个 series，不同 URL 的视频都被保存")
            
        finally:
            constants.STATE_FILE = original_state_file
            constants.OUTPUT_FILE = original_output_file
            constants.OUTPUT_DIR = original_output_dir


def test_deduplication_same_url_different_series():
    """
    测试2: 同一个 URL，不同 series 应该生成多个条目（当前设计）
    
    注意: 这测试当前的去重逻辑 (group_title, url) 对
    如果同一 URL 关联多个 series，应该生成多个条目
    """
    print("\n" + "=" * 70)
    print("测试2: 同一个 URL，多个 series - 应该生成多个条目")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.m3u")
        
        try:
            scraper = MissAVScraper(
                output_file=output_file,
                enable_checkpoint=False,
                max_videos=1000,
                verbose=False
            )
            
            # 创建视频对象，一个 URL 关联多个 series
            video = MockVideoObject(
                video_code="TEST-003",
                m3u8_url="https://example.com/shared_video.m3u8",
                series=["演员B", "演员C", "演员D"],  # 多个 series
                thumbnail="https://example.com/thumb3.jpg"
            )
            
            # 处理视频
            entries = scraper._process_video_object(video, "batch_search")
            
            print(f"✓ 处理视频: 新增 {entries} 个条目")
            print(f"✓ existing_entries 中的条目数: {len(scraper.existing_entries)}")
            
            # 验证结果
            assert entries == 3, f"应该新增3个条目（每个 series 一个），实际: {entries}"
            assert len(scraper.videos) == 3, f"应该有3个视频条目，实际: {len(scraper.videos)}"
            
            # 验证每个条目有不同的 group_title 但相同的 URL
            urls_set = {v['url'] for v in scraper.videos}
            group_titles = {v['group_title'] for v in scraper.videos}
            
            assert len(urls_set) == 1, f"所有条目应该有相同URL，实际URL数: {len(urls_set)}"
            assert len(group_titles) == 3, f"应该有3个不同的 group_title，实际: {len(group_titles)}"
            
            print(f"✅ 测试2通过: 同一 URL 的多个 series 生成了 {entries} 个条目")
            
        finally:
            pass


def test_deduplication_duplicate_exact_match():
    """
    测试3: 完全相同的 (group_title, url) 对应该被去重
    """
    print("\n" + "=" * 70)
    print("测试3: 完全相同的 (group_title, url) 对 - 应该被去重")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.m3u")
        
        try:
            scraper = MissAVScraper(
                output_file=output_file,
                enable_checkpoint=False,
                max_videos=1000,
                verbose=False
            )
            
            # 创建两个相同的视频对象
            video1 = MockVideoObject(
                video_code="TEST-004",
                m3u8_url="https://example.com/duplicate.m3u8",
                series=["演员E"],
                thumbnail="https://example.com/thumb4.jpg"
            )
            
            video2 = MockVideoObject(
                video_code="TEST-004-DUP",  # 不同的 code，但相同的 series 和 URL
                m3u8_url="https://example.com/duplicate.m3u8",
                series=["演员E"],
                thumbnail="https://example.com/thumb4.jpg"
            )
            
            # 处理第一个视频
            entries1 = scraper._process_video_object(video1, "search")
            print(f"✓ 处理视频1: 新增 {entries1} 个条目")
            
            # 处理第二个视频 - 应该被去重
            entries2 = scraper._process_video_object(video2, "search")
            print(f"✓ 处理视频2 (重复): 新增 {entries2} 个条目")
            
            # 验证结果
            assert entries1 == 1, f"视频1应该新增1个条目，实际: {entries1}"
            assert entries2 == 0, f"视频2（重复）应该新增0个条目，实际: {entries2}"
            assert len(scraper.videos) == 1, f"应该只有1个视频条目，实际: {len(scraper.videos)}"
            
            print(f"✅ 测试3通过: 重复的 (group_title, url) 被成功去重")
            
        finally:
            pass


def test_deduplication_with_m3u_file():
    """
    测试4: 从 M3U 文件加载已存在的条目进行去重
    """
    print("\n" + "=" * 70)
    print("测试4: 从 M3U 文件加载已存在条目进行去重")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, "test.m3u")
        
        # 创建一个包含已有条目的 M3U 文件
        m3u_content = """#EXTM3U
#EXTINF:-1 group-title="演员F" tvg-name="TEST-005" tvg-logo="https://example.com/t.jpg" epg-url="",TEST-005
https://example.com/existing.m3u8
#EXTINF:-1 group-title="演员G" tvg-name="TEST-006" tvg-logo="https://example.com/t.jpg" epg-url="",TEST-006
https://example.com/other.m3u8
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(m3u_content)
        
        try:
            scraper = MissAVScraper(
                output_file=output_file,
                enable_checkpoint=False,
                max_videos=1000,
                verbose=False
            )
            
            print(f"✓ M3U 文件已加载，existing_entries 数: {len(scraper.existing_entries)}")
            
            # 尝试添加一个与 M3U 中相同的条目
            video_duplicate = MockVideoObject(
                video_code="TEST-005",
                m3u8_url="https://example.com/existing.m3u8",
                series=["演员F"],
                thumbnail="https://example.com/thumb5.jpg"
            )
            
            entries_dup = scraper._process_video_object(video_duplicate, "search")
            print(f"✓ 尝试添加已存在的条目: 新增 {entries_dup} 个条目")
            
            # 尝试添加一个新的条目
            video_new = MockVideoObject(
                video_code="TEST-007",
                m3u8_url="https://example.com/new.m3u8",
                series=["演员H"],
                thumbnail="https://example.com/thumb7.jpg"
            )
            
            entries_new = scraper._process_video_object(video_new, "search")
            print(f"✓ 添加新条目: 新增 {entries_new} 个条目")
            
            # 验证结果
            assert entries_dup == 0, f"重复的条目应该新增0个，实际: {entries_dup}"
            assert entries_new == 1, f"新条目应该新增1个，实际: {entries_new}"
            assert len(scraper.videos) == 1, f"应该只有1个新的视频条目，实际: {len(scraper.videos)}"
            
            print(f"✅ 测试4通过: M3U 文件中的条目被正确用于去重")
            
        finally:
            pass


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("MissAV 爬虫 - 去重逻辑测试")
    print("=" * 70)
    
    try:
        test_deduplication_same_series_different_url()
        test_deduplication_same_url_different_series()
        test_deduplication_duplicate_exact_match()
        test_deduplication_with_m3u_file()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过！去重逻辑运行正常")
        print("=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
