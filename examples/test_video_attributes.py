#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本 - 检查视频对象的所有属性
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_video_attributes():
    """获取一个视频对象并检查其属性"""
    try:
        from missav_api import Client
        
        logger.info("=" * 70)
        logger.info("获取视频对象并检查属性")
        logger.info("=" * 70)
        
        client = Client()
        
        # 尝试获取一个视频
        logger.info("\n开始搜索视频...")
        search_results = client.search(query="鷲尾めい", video_count=1)
        
        # 从生成器获取第一个结果
        try:
            video_summary = next(search_results)
        except StopIteration:
            logger.info("❌ 搜索结果为空")
            return
        video_code = video_summary.video_code
        logger.info(f"✓ 找到视频: {video_code}")
        
        # 获取完整视频信息
        video_url = f"https://missav.ws/cn/{video_code}"
        logger.info(f"\n获取完整视频信息: {video_url}")
        video_obj = client.get_video(video_url)
        
        # 检查视频对象的所有属性
        logger.info("\n" + "=" * 70)
        logger.info("视频对象的所有属性:")
        logger.info("=" * 70)
        
        # 1. 获取所有属性
        attributes = dir(video_obj)
        public_attributes = [attr for attr in attributes if not attr.startswith('_')]
        
        logger.info(f"\n总属性数: {len(attributes)} 个")
        logger.info(f"公开属性数: {len(public_attributes)} 个\n")
        
        # 2. 逐一检查每个属性
        logger.info("属性详情:")
        logger.info("-" * 70)
        
        for attr in public_attributes:
            try:
                value = getattr(video_obj, attr)
                # 跳过方法
                if callable(value):
                    continue
                
                # 获取值的类型和内容
                value_type = type(value).__name__
                
                # 对于长字符串，只显示前100个字符
                if isinstance(value, str):
                    if len(value) > 100:
                        display_value = f"{value[:100]}..."
                    else:
                        display_value = value
                elif isinstance(value, (list, dict)):
                    if len(str(value)) > 150:
                        display_value = f"{str(value)[:150]}..."
                    else:
                        display_value = value
                else:
                    display_value = value
                
                logger.info(f"\n  📌 {attr} ({value_type})")
                logger.info(f"     值: {display_value}")
            except Exception as e:
                logger.info(f"\n  ⚠️  {attr} - 获取失败: {e}")
        
        # 3. 特别强调关键属性
        logger.info("\n" + "=" * 70)
        logger.info("关键属性总结:")
        logger.info("=" * 70)
        
        key_attrs = {
            'video_code': '视频代码',
            'm3u8_base_url': 'M3U8 URL',
            'series': '系列/分类',
            'thumbnail': '缩略图',
            'title': '标题',
            'actresses': '女演员',
            'studio': '工作室',
            'release_date': '发布日期',
            'rating': '评分',
            'description': '描述',
        }
        
        for key, desc in key_attrs.items():
            if hasattr(video_obj, key):
                try:
                    value = getattr(video_obj, key)
                    if value is None:
                        logger.info(f"  ✗ {desc} ({key}): None")
                    elif isinstance(value, (list, dict)):
                        logger.info(f"  ✓ {desc} ({key}): {value}")
                    elif isinstance(value, str) and len(value) > 80:
                        logger.info(f"  ✓ {desc} ({key}): {value[:80]}...")
                    else:
                        logger.info(f"  ✓ {desc} ({key}): {value}")
                except Exception as e:
                    logger.info(f"  ⚠️  {desc} ({key}): 获取失败 - {e}")
            else:
                logger.info(f"  ✗ {desc} ({key}): 属性不存在")
        
        # 4. 打印原始对象
        logger.info("\n" + "=" * 70)
        logger.info("原始对象信息:")
        logger.info("=" * 70)
        logger.info(f"{video_obj}")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_video_attributes()
