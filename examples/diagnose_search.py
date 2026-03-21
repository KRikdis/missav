#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本 - 测试搜索功能是否正常工作
"""

from missav_api import Client
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_search():
    """测试单个搜索查询"""
    client = Client()
    
    logger.info("=" * 70)
    logger.info("测试 1: 搜索一个演员名，获取 5 个视频")
    logger.info("=" * 70)
    
    query = "鷲尾めい"
    logger.info(f"\n搜索: {query}")
    logger.info(f"请求 5 个视频...")
    
    try:
        search_results = client.search(query=query, video_count=5)
        
        count = 0
        for video_summary in search_results:
            count += 1
            print(f"  {count}. {video_summary.video_code}")
            if count >= 5:
                break
        
        logger.info(f"\n✓ 搜索成功，获取 {count} 个视频")
        
    except Exception as e:
        logger.error(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 测试 2：检查演员列表
    logger.info("\n" + "=" * 70)
    logger.info("测试 2: 检查演员列表配置")
    logger.info("=" * 70)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from src.missav_scraper import constants
    actress_list = constants.ACTRESS_SEARCH_LIST
    logger.info(f"演员总数: {len(actress_list)}")
    logger.info(f"前 5 个演员: {actress_list[:5]}")
    logger.info(f"后 5 个演员: {actress_list[-5:]}")
    
    # 测试 3：搜索模式确认
    logger.info("\n" + "=" * 70)
    logger.info("测试 3: 搜索模式配置")
    logger.info("=" * 70)
    
    logger.info(f"爬虫模式: {constants.SCRAPER_MODE}")
    logger.info(f"每个查询的视频数: {constants.VIDEOS_PER_QUERY}")
    logger.info(f"每次运行最多视频数: {constants.MAX_VIDEOS_PER_RUN}")


if __name__ == '__main__':
    test_search()
