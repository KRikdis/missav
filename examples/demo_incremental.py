#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示脚本 - 测试增量更新、去重和断点续爬功能
"""

from pathlib import Path
import json


def test_incremental_mode():
    """演示增量更新模式"""
    print("=" * 70)
    print("演示 1: 增量更新模式")
    print("=" * 70)
    
    # 创建测试 M3U 文件
    test_m3u = Path("test_demo.m3u")
    
    # 第一次运行 - 创建新文件
    print("\n【第一次运行】创建新 M3U 文件:\n")
    with open(test_m3u, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        f.write('#EXTINF:-1 group-title="日本" tvg-name="ABD-001" tvg-logo="" epg-url="",ABD-001\n')
        f.write('https://example.com/stream1.m3u8\n')
        f.write('#EXTINF:-1 group-title="高清" tvg-name="ABD-001" tvg-logo="" epg-url="",ABD-001\n')
        f.write('https://example.com/stream1.m3u8\n')
        f.write('#EXTINF:-1 group-title="新作" tvg-name="DEF-002" tvg-logo="" epg-url="",DEF-002\n')
        f.write('https://example.com/stream2.m3u8\n')
    
    print(f"✓ 创建了 {test_m3u} 文件")
    
    # 读取 URL
    with open(test_m3u, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        urls = [l.strip() for l in lines if l.strip() and not l.startswith('#')]
    
    print(f"  初始 URL 数: {len(urls)} ({len(set(urls))} 个唯一 URL)")
    print(f"  URL 列表: {urls}")
    
    # 第二次运行 - 追加新内容
    print("\n【第二次运行】追加新内容（增量模式）:\n")
    with open(test_m3u, 'a', encoding='utf-8') as f:
        # 新视频（不重复）
        f.write('#EXTINF:-1 group-title="欧美" tvg-name="GHI-003" tvg-logo="" epg-url="",GHI-003\n')
        f.write('https://example.com/stream3.m3u8\n')
        # 重复 URL（会在实际爬虫中被跳过）
        f.write('#EXTINF:-1 group-title="日本" tvg-name="ABD-001" tvg-logo="" epg-url="",ABD-001\n')
        f.write('https://example.com/stream1.m3u8\n')  # 重复！
    
    print("✓ 追加了新内容")
    
    # 统计
    with open(test_m3u, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        urls = [l.strip() for l in lines if l.strip() and not l.startswith('#')]
    
    print(f"  追加后 URL 总数: {len(urls)}")
    print(f"  唯一 URL 数: {len(set(urls))}")
    print(f"  重复 URL 数: {len(urls) - len(set(urls))}")
    
    # 清理
    test_m3u.unlink()
    print("\n✓ 演示完成\n")


def test_deduplication():
    """演示去重机制"""
    print("=" * 70)
    print("演示 2: URL 去重机制")
    print("=" * 70)
    
    # 模拟从 M3U 文件读取 URL
    existing_urls = {
        'https://example.com/stream1.m3u8',
        'https://example.com/stream2.m3u8',
        'https://example.com/stream3.m3u8',
    }
    
    print(f"\n✓ 现有 URL 集合 ({len(existing_urls)} 个):")
    for url in sorted(existing_urls):
        print(f"  - {url}")
    
    # 模拟新爬到的视频
    new_videos = [
        {'code': 'ABC-001', 'url': 'https://example.com/stream1.m3u8'},  # 重复
        {'code': 'GHI-003', 'url': 'https://example.com/stream4.m3u8'},  # 新
        {'code': 'JKL-004', 'url': 'https://example.com/stream5.m3u8'},  # 新
        {'code': 'MNO-005', 'url': 'https://example.com/stream2.m3u8'},  # 重复
    ]
    
    print(f"\n✓ 新爬到的视频 ({len(new_videos)} 个):")
    saved_count = 0
    skipped_count = 0
    
    for video in new_videos:
        if video['url'] in existing_urls:
            print(f"  ✗ {video['code']}: {video['url']} (重复，跳过)")
            skipped_count += 1
        else:
            print(f"  ✓ {video['code']}: {video['url']} (新，保存)")
            saved_count += 1
            existing_urls.add(video['url'])
    
    print(f"\n✓ 结果:")
    print(f"  新增: {saved_count} 个")
    print(f"  跳过: {skipped_count} 个")
    print(f"  总 URL: {len(existing_urls)} 个\n")


def test_checkpoint():
    """演示断点续爬"""
    print("=" * 70)
    print("演示 3: 断点续爬机制")
    print("=" * 70)
    
    state_file = Path("test_state.json")
    
    print("\n【会话 1】爬虫运行到一半:\n")
    state = {
        'videos': [
            {'code': 'ABC-001', 'url': 'https://...1', 'genres': ['日本'], 'thumbnail': '...'},
            {'code': 'DEF-002', 'url': 'https://...2', 'genres': ['高清'], 'thumbnail': '...'},
        ],
        'existing_urls_count': 100,
        'last_update': '2026-03-21T10:15:00',
        'total_videos_processed': 50
    }
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已采集 {len(state['videos'])} 个新视频")
    print(f"✓ 已处理 {state['total_videos_processed']} 个视频")
    print(f"✓ M3U 中已有 {state['existing_urls_count']} 个 URL")
    print(f"✓ 进度已保存到 {state_file}\n")
    
    print("【会话 2】恢复运行:\n")
    with open(state_file, 'r', encoding='utf-8') as f:
        loaded_state = json.load(f)
    
    print(f"✓ 加载了之前的状态:")
    print(f"  - 已有 {len(loaded_state['videos'])} 个视频")
    print(f"  - 已有 {loaded_state['existing_urls_count']} 个 URL")
    print(f"  - 最后更新: {loaded_state['last_update']}")
    
    # 继续爬虫
    loaded_state['videos'].append(
        {'code': 'GHI-003', 'url': 'https://...3', 'genres': ['新作'], 'thumbnail': '...'}
    )
    loaded_state['total_videos_processed'] = 75
    loaded_state['existing_urls_count'] = 111
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(loaded_state, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 继续爬虫并保存:")
    print(f"  - 现在有 {len(loaded_state['videos'])} 个视频")
    print(f"  - 现在有 {loaded_state['existing_urls_count']} 个 URL")
    print(f"  - 已处理 {loaded_state['total_videos_processed']} 个视频\n")
    
    state_file.unlink()


def test_progressive_growth():
    """演示数据的渐进式增长"""
    print("=" * 70)
    print("演示 4: 数据渐进式增长")
    print("=" * 70)
    
    print("\n模拟连续 5 次运行:\n")
    
    total_urls = 0
    total_videos = 0
    
    for session in range(1, 6):
        new_videos = 50 - (session - 1) * 5  # 逐次减少
        new_urls_per_video = 2.5  # 平均每个视频 2.5 个 URL
        new_urls = int(new_videos * new_urls_per_video)
        
        # 假设重复率
        duplicate_urls = int(new_urls * 0.2 * (session - 1))  # 后续会话有重复
        actual_new_urls = new_urls - duplicate_urls
        
        total_urls += actual_new_urls
        total_videos += new_videos
        
        print(f"【会话 {session}】")
        print(f"  爬虫获取: {new_videos} 个视频")
        print(f"  生成 URL: {new_urls} 个 (去重前)")
        print(f"  重复 URL: {duplicate_urls} 个")
        print(f"  新增 URL: {actual_new_urls} 个")
        print(f"  累计 URL: {total_urls} 个")
        print(f"  累计视频: {total_videos} 个")
        print()
    
    print(f"最终统计:")
    print(f"  - 总视频数: {total_videos}")
    print(f"  - 总 URL 数: {total_urls} (带分类)")
    print(f"  - 平均每个视频 {total_urls/total_videos:.2f} 个 URL")


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 18 + "增量更新、去重、断点续爬 演示" + " " * 18 + "║")
    print("╚" + "=" * 68 + "╝")
    print()
    
    try:
        test_incremental_mode()
        test_deduplication()
        test_checkpoint()
        test_progressive_growth()
        
        print("=" * 70)
        print("✓ 所有演示完成!")
        print("=" * 70)
        print()
        print("关键特性总结:")
        print("  ✅ 增量更新 - M3U 文件只追加，不覆盖")
        print("  ✅ URL 去重 - 检查重复的流链接，避免保存")
        print("  ✅ 断点续爬 - 进度自动保存，中断后可继续")
        print("  ✅ 自动分类 - 为每个 genre 创建独立条目")
        print()
        print("现在你可以运行爬虫了:")
        print("  python scraper_final.py   # 增量更新模式")
        print("  python scraper.py          # 高级选项版本")
        print("  python advanced_scraper.py # 完全功能版本")
        print()
        
    except Exception as e:
        print(f"\n✗ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
