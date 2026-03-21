#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本 - 详细测试 missav_api 的 search 功能
根据 https://github.com/EchterAlsFake/API_Docs/blob/master/Porn_APIs/missAV.md
"""

from missav_api import Client
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_search_api():
    """深度测试 search API 的行为"""
    client = Client()
    
    logger.info("=" * 70)
    logger.info("missav_api search() 功能诊断")
    logger.info("=" * 70)
    
    # 测试 1: 检查 search 的返回类型和生成器行为
    logger.info("\n测试 1: search 返回类型检查")
    logger.info("-" * 70)
    
    query = "鷲尾めい"
    logger.info(f"搜索: {query}")
    
    search_results = client.search(query=query, video_count=10)
    logger.info(f"search() 返回类型: {type(search_results)}")
    logger.info(f"是生成器吗? {hasattr(search_results, '__iter__') and hasattr(search_results, '__next__')}")
    
    # 测试 2: 逐一获取结果，看看能获取多少
    logger.info("\n测试 2: 逐个获取搜索结果")
    logger.info("-" * 70)
    
    search_results = client.search(query=query, video_count=10)
    count = 0
    max_show = 15  # 尝试获取 15 个
    
    try:
        for video_summary in search_results:
            count += 1
            logger.info(f"  {count}. {video_summary.video_code}")
            
            if count >= max_show:
                logger.info(f"  ... (已显示 {max_show} 条，可能还有更多)")
                break
    except StopIteration:
        logger.info(f"生成器已结束，总共获取 {count} 条")
    except Exception as e:
        logger.error(f"获取过程出错: {e}")
    
    # 测试 3: 检查 video_count 参数的影响
    logger.info("\n测试 3: video_count 参数影响测试")
    logger.info("-" * 70)
    
    for vc in [5, 20, 100, 1000]:
        logger.info(f"\n尝试 video_count={vc}:")
        search_results = client.search(query=query, video_count=vc)
        
        count = 0
        for video_summary in search_results:
            count += 1
            if count >= 5:  # 只计数，不逐一显示
                break
        
        # 继续计数直到结束
        try:
            for video_summary in search_results:
                count += 1
        except StopIteration:
            pass
        
        logger.info(f"  实际获取: {count} 条视频")
    
    # 测试 4: 检查是否有参数控制分页或限制
    logger.info("\n测试 4: search() 方法签名和参数")
    logger.info("-" * 70)
    
    import inspect
    sig = inspect.signature(client.search)
    logger.info(f"search() 方法签名:")
    for param_name, param in sig.parameters.items():
        logger.info(f"  - {param_name}: {param.annotation if param.annotation != inspect.Parameter.empty else 'no type'}")
        if param.default != inspect.Parameter.empty:
            logger.info(f"      默认值: {param.default}")
    
    # 测试 5: 查看返回对象的属性
    logger.info("\n测试 5: 搜索结果对象的属性")
    logger.info("-" * 70)
    
    search_results = client.search(query=query, video_count=1)
    try:
        video_summary = next(search_results)
        logger.info(f"video_summary 对象属性:")
        attrs = dir(video_summary)
        public_attrs = [a for a in attrs if not a.startswith('_')]
        for attr in public_attrs[:15]:  # 显示前 15 个
            try:
                value = getattr(video_summary, attr)
                if not callable(value):
                    if isinstance(value, str) and len(value) > 50:
                        logger.info(f"  - {attr}: {value[:50]}...")
                    else:
                        logger.info(f"  - {attr}: {value}")
            except:
                pass
    except StopIteration:
        logger.info("搜索结果为空")
    
    logger.info("\n" + "=" * 70)
    logger.info("诊断完成")
    logger.info("=" * 70)


if __name__ == '__main__':
    test_search_api()
