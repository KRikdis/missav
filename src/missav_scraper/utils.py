#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具函数模块

提供通用的工具函数：日志、延迟、文件操作等
"""

import logging
import time
import random
from pathlib import Path
from typing import Set

from . import constants

# 配置日志
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    配置日志系统
    
    Args:
        verbose: 是否启用详细日志输出 (DEBUG 级别)
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format=constants.LOG_FORMAT
    )
    logging.getLogger(__name__).setLevel(level)


def random_delay(min_seconds: float = None, max_seconds: float = None) -> None:
    """
    随机延迟，避免请求被限流
    
    Args:
        min_seconds: 最小延迟时间 (秒)
        max_seconds: 最大延迟时间 (秒)
    """
    min_seconds = min_seconds or constants.MIN_DELAY
    max_seconds = max_seconds or constants.MAX_DELAY
    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"延迟 {delay:.2f} 秒...")
    time.sleep(delay)


def load_existing_urls(output_file: str) -> Set[str]:
    """
    从现有的 M3U 文件中读取所有 URL，用于去重
    
    Args:
        output_file: M3U 文件路径
        
    Returns:
        包含所有已存在 URL 的集合
    """
    existing_urls = set()
    try:
        m3u_path = Path(output_file)
        if m3u_path.exists():
            with open(m3u_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # 提取 URL（不以 # 开头的行）
                    if line and not line.startswith('#'):
                        existing_urls.add(line)
            
            if existing_urls:
                logger.info(f"从 {output_file} 读取到 {len(existing_urls)} 个已存在的 URL")
    except Exception as e:
        logger.warning(f"读取现有 M3U 文件失败: {e}")
    
    return existing_urls


def ensure_output_directory(output_file: str) -> Path:
    """
    确保输出目录存在
    
    Args:
        output_file: 输出文件路径
        
    Returns:
        输出文件的 Path 对象
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def normalize_genres(genres) -> list:
    """
    规范化 genres 数据
    
    Args:
        genres: 从 API 返回的 genres 数据
        
    Returns:
        规范化后的 genres 列表
    """
    if not genres:
        return [constants.DEFAULT_GENRE]
    
    if isinstance(genres, str):
        return [genres] if genres.strip() else [constants.DEFAULT_GENRE]
    
    if isinstance(genres, list):
        normalized = [str(g).strip() for g in genres if g]
        return normalized if normalized else [constants.DEFAULT_GENRE]
    
    return [constants.DEFAULT_GENRE]


def format_video_info(video_code: str, genres: list) -> str:
    """
    格式化视频信息用于日志显示
    
    Args:
        video_code: 视频代码
        genres: 分类列表
        
    Returns:
        格式化的字符串
    """
    genres_str = ', '.join(genres) if genres else 'N/A'
    return f"{video_code} | 分类: {genres_str}"
