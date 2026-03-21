#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示脚本 - 显示爬虫起始参数和限制收集功能
"""

import json
from pathlib import Path


def show_startup_parameters():
    """显示爬虫的起始参数"""
    print("\n" + "=" * 80)
    print("🔍 MissAV 爬虫 - 起始参数详解")
    print("=" * 80)
    
    print("\n📋 当前的爬虫起始参数:\n")
    
    # 显示参数
    params = {
        "查询字符串": ["a", "b", "c", "d", "e"],
        "查询字符串说明": "爬虫按顺序查询这些字母，每个查询最多获取 50 个视频",
        
        "每个查询获取数": 50,
        "每个查询说明": "单次查询向 API 请求的最大视频数",
        
        "本次运行默认限制": 500,
        "限制说明": "每次运行最多收集 500 条视频后停止（防止 IP 限制）",
        
        "最小延迟": "2 秒",
        "最大延迟": "5 秒",
        "延迟说明": "每个请求之间的随机延迟，避免被爬虫检测",
        
        "批次间延迟": "15 秒",
        "批次说明": "每 5 个大批次之间的额外延迟",
    }
    
    for key, value in params.items():
        if "说明" in key:
            print(f"  💡 {value}")
        else:
            print(f"  {key:<20} → {value}")
    
    print()


def show_collection_process():
    """显示收集过程"""
    print("=" * 80)
    print("📊 数据收集过程")
    print("=" * 80)
    
    print("\n【默认配置】收集 500 条视频:\n")
    
    queries = ["a", "b", "c", "d", "e"]
    per_query = 50
    max_videos = 500
    
    total = 0
    for idx, query in enumerate(queries, 1):
        if total >= max_videos:
            print(f"  ⏹ 已达到限制 ({max_videos} 条)，停止\n")
            break
        
        collected = min(per_query, max_videos - total)
        total += collected
        
        print(f"  查询 {idx}/5 '{query}': 获取 {collected} 条 → 累计 {total} 条")
    
    print(f"\n  ✓ 总共收集: {total} 条视频")
    print(f"  ⏱️  预计时间: 约 15-20 分钟")
    print(f"  🔒 IP 风险等级: 低")


def show_different_limits():
    """显示不同限制下的效果"""
    print("\n" + "=" * 80)
    print("🎯 不同限制数量的对比")
    print("=" * 80)
    
    configs = [
        {"limit": 200, "risk": "极低", "time": "8-12 分钟", "strategy": "保守型"},
        {"limit": 500, "risk": "低", "time": "15-20 分钟", "strategy": "推荐型"},
        {"limit": 1000, "risk": "中等", "time": "30-40 分钟", "strategy": "积极型"},
    ]
    
    print()
    for config in configs:
        limit = config["limit"]
        queries = ["a", "b", "c", "d", "e"]
        per_query = 50
        
        num_queries = min((limit + per_query - 1) // per_query, len(queries))
        
        print(f"  【{config['strategy']}】 --max-videos {limit}")
        print(f"    查询范围: {queries[:num_queries]}")
        print(f"    IP 风险: {config['risk']}")
        print(f"    预计时间: {config['time']}")
        print(f"    命令: python scraper_final.py --max-videos {limit}")
        print()


def show_usage_examples():
    """显示使用示例"""
    print("=" * 80)
    print("🚀 使用示例")
    print("=" * 80)
    
    examples = [
        {
            "title": "默认方式（推荐）",
            "desc": "500 条限制，推荐日常使用",
            "cmd": "python scraper_final.py"
        },
        {
            "title": "查看起始参数",
            "desc": "加详细日志，显示所有初始参数",
            "cmd": "python scraper_final.py -v"
        },
        {
            "title": "保守方式",
            "desc": "200 条限制，IP 已暴露时使用",
            "cmd": "python scraper_final.py --max-videos 200"
        },
        {
            "title": "积极方式",
            "desc": "1000 条限制，加快收集速度",
            "cmd": "python scraper_final.py --max-videos 1000"
        },
        {
            "title": "自定义输出 + 限制",
            "desc": "同时指定输出文件和限制数",
            "cmd": "python scraper_final.py -o my_list.m3u --max-videos 300"
        },
        {
            "title": "清除进度后运行",
            "desc": "删除上一次的进度，重新开始",
            "cmd": "python scraper_final.py --clean"
        },
    ]
    
    print()
    for idx, ex in enumerate(examples, 1):
        print(f"  {idx}. {ex['title']}")
        print(f"     说明: {ex['desc']}")
        print(f"     命令: {ex['cmd']}")
        print()


def show_progression_strategy():
    """显示渐进式爬取策略"""
    print("=" * 80)
    print("📈 推荐的渐进式爬取策略")
    print("=" * 80)
    
    print("\n每天运行一次，每次收集 500 条视频:\n")
    
    total = 0
    for day in range(1, 11):
        total += 500
        print(f"  Day {day:2}: 500 条 (总: {total:,})")
    
    print(f"\n  ✓ 优点:")
    print(f"    • 分散服务器压力")
    print(f"    • 避免 IP 被限制")
    print(f"    • 更稳定可靠")
    print(f"    • 数据持续增长")
    
    print(f"\n  设置定时任务 (Linux/Mac crontab):")
    print(f"    0 2 * * * cd /path/to/missav && python scraper_final.py --max-videos 500")
    print()


def show_file_structure():
    """显示文件结构和说明"""
    print("=" * 80)
    print("📁 文件结构说明")
    print("=" * 80)
    
    files = {
        "missav.m3u": "M3U 播放列表文件（持续增长，每次追加）",
        "scraper_state.json": "本次会话的进度和状态信息",
        "scraper_final.py": "主爬虫脚本（支持限制收集数量）",
    }
    
    print()
    for filename, desc in files.items():
        print(f"  {filename:<25} → {desc}")
    print()


def show_key_parameters():
    """突出显示关键参数"""
    print("=" * 80)
    print("⭐ 关键参数速查")
    print("=" * 80)
    
    print("""
  限制参数:
    --max-videos N         每次运行最多收集 N 条视频
    默认值: 500 (推荐)
    
  输出参数:
    -o, --output FILE      指定输出文件名
    默认值: missav.m3u
    
  进度参数:
    --clean                清除进度文件（保留 M3U）
    --clean-all            删除进度文件和 M3U 文件
    --no-checkpoint        禁用断点续爬
    
  调试参数:
    -v, --verbose          显示详细日志（包括起始参数）
    
  查询参数（代码中修改）:
    DEFAULT_QUERIES        查询字符串列表
    VIDEOS_PER_QUERY       每个查询的视频数
    MAX_VIDEOS_PER_RUN     默认运行限制
""")


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "MissAV 爬虫 - 参数和限制说明" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    
    try:
        show_startup_parameters()
        show_collection_process()
        show_different_limits()
        show_usage_examples()
        show_progression_strategy()
        show_file_structure()
        show_key_parameters()
        
        print("=" * 80)
        print("✓ 演示完成！")
        print("=" * 80)
        
        print("""
现在你可以运行爬虫了:

  【推荐】每次收集 500 条（平衡方案）:
    python scraper_final.py
    
  【保守】每次收集 200 条（IP 安全）:
    python scraper_final.py --max-videos 200
    
  【积极】每次收集 1000 条（快速积累）:
    python scraper_final.py --max-videos 1000

更多信息见 COLLECTION_LIMIT.md
""")
        
    except Exception as e:
        print(f"\n✗ 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
